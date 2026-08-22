# uv run -m scripts.rebuild_player_season_stats
"""
선수 시즌별 누적 타격/투구 통합 집계 테이블(PlayerSeasonStat) 전면 재구축 및 백필(Backfill) 스크립트.

[스크립트 역할 및 목적]
1. 기존 `PlayerSeasonStat` 테이블의 모든 레코드를 안전하게 초기화합니다.
2. 데이터베이스에 존재하는 모든 완료된 경기(Match, status='COMPLETED')의 원천 로그(logged_events)를 전수 탐색합니다.
3. 타자별/투수별 연도(시즌), 소속 구단 단위로 모든 상세 지표(타수, 안타, 홈런, 타점, 이닝 아웃, 실점, 승/패 등)를 정밀 집계합니다.
4. 재집계된 최종 시즌 스탯 데이터를 `PlayerSeasonStat` 테이블에 일괄 적재(Bulk Insert)하여 향후 선수 상세 조회(PlayerDetail API) 시 O(1) 속도를 보장합니다.
"""

from typing import Any, Optional
from sqlmodel import Session, create_engine, select, delete, SQLModel, col
from settings import DATABASE_URL, CONFIG
from src.models import Match, PlayerSeasonStat, Player
from src.utils.logger import logger

engine = create_engine(DATABASE_URL)


def _get_val(ev: Any, attr: str, default: Any = None) -> Any:
    if isinstance(ev, dict):
        return ev.get(attr, default)
    return getattr(ev, attr, default)


def rebuild_player_season_stats():
    logger.info("선수 시즌 집계 테이블(PlayerSeasonStat) 재구축 작업을 시작합니다.")

    # 1. 테이블 생성 보장 및 기존 데이터 초기화
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        deleted_count = session.exec(delete(PlayerSeasonStat)).rowcount
        session.commit()
        logger.info(f"기존 PlayerSeasonStat 레코드 초기화 완료 (삭제 건수: {deleted_count}건)")

    # 2. 모든 완료 경기 및 선수 정보 조회
    with Session(engine) as session:
        # 선수들의 기본 소속 구단 매핑 (경기 로그에 club_id가 명시되지 않은 경우 대비)
        players = session.exec(select(Player)).all()
        player_club_map = {p.id: p.club_id for p in players}
        logger.info(f"등록 선수 {len(players)}명의 소속 구단 매핑 정보 로드 완료")

        matches = list(
            session.exec(
                select(Match)
                .where(Match.status == "COMPLETED")
                .order_by(col(Match.sim_day).asc())
            ).all()
        )
        total_matches = len(matches)
        logger.info(f"총 {total_matches}개의 완료된 경기 로그 분석을 시작합니다.")

        if total_matches == 0:
            logger.warning("완료된 경기가 존재하지 않습니다. 스크립트를 종료합니다.")
            return

        # (player_id, season_year, club_id) -> PlayerSeasonStat 인메모리 누적 딕셔너리
        stat_map: dict[tuple[int, int, Optional[int]], PlayerSeasonStat] = {}

        def _get_or_create_stat(p_id: int, year: int, c_id: Optional[int]) -> PlayerSeasonStat:
            # 구단 ID가 없을 경우 선수의 현재 구단 ID로 보정
            eff_club_id = c_id if c_id is not None else player_club_map.get(p_id)
            key = (p_id, year, eff_club_id)
            if key not in stat_map:
                stat_map[key] = PlayerSeasonStat(
                    player_id=p_id,
                    season_year=year,
                    club_id=eff_club_id,
                )
            return stat_map[key]

        parsed_match_count = 0

        for idx, m in enumerate(matches, start=1):
            events = None
            if m.match_log and hasattr(m.match_log, "logged_events"):
                events = m.match_log.logged_events
            elif m.match_log_json and isinstance(m.match_log_json, dict):
                events = m.match_log_json.get("logged_events", [])

            if not events:
                continue

            parsed_match_count += 1
            year_num = CONFIG.base_datetime.year + (max(1, m.sim_day) - 1) // 365

            participated_batters: set[int] = set()
            participated_pitchers: set[int] = set()
            starting_pitchers_marked: set[int] = set()

            curr_batter_id: Optional[int] = None
            curr_pitcher_id: Optional[int] = None
            strikes = 0
            balls = 0

            for ev in events:
                etype = _get_val(ev, "event_type")

                if etype == "BATTER_ENTER":
                    curr_batter_id = _get_val(ev, "batter_id")
                    curr_pitcher_id = _get_val(ev, "pitcher_id")
                    strikes = 0
                    balls = 0

                    if curr_batter_id is not None:
                        participated_batters.add(curr_batter_id)
                        b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                        b_stat.bat_pa += 1

                    if curr_pitcher_id is not None:
                        participated_pitchers.add(curr_pitcher_id)
                        p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                        # 첫 이닝 첫 타자 상대 투수를 선발투수로 기록
                        if curr_pitcher_id not in starting_pitchers_marked and len(starting_pitchers_marked) < 2:
                            starting_pitchers_marked.add(curr_pitcher_id)
                            p_stat.pitch_starts += 1

                elif etype == "PITCH":
                    res = _get_val(ev, "result")

                    if curr_pitcher_id is not None:
                        p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                        p_stat.pitch_pitches += 1

                    if res == "BALL":
                        balls += 1
                        if balls == 4:
                            if curr_batter_id is not None:
                                b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                                b_stat.bat_bb += 1
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_bb += 1

                    elif res in ("STRIKE", "STRIKE_LOOKING", "STRIKE_SWINGING"):
                        strikes += 1
                        if strikes == 3:
                            if curr_batter_id is not None:
                                b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                                b_stat.bat_ab += 1
                                b_stat.bat_so += 1
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_so += 1
                                p_stat.pitch_outs += 1

                    elif res == "FOUL":
                        if strikes < 2:
                            strikes += 1

                    elif res in ("HIT_BY_PITCH", "DEAD_BALL", "HBP"):
                        if curr_batter_id is not None:
                            b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                            b_stat.bat_hbp += 1
                        if curr_pitcher_id is not None:
                            p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                            p_stat.pitch_hbp += 1

                elif etype == "NOTICE":
                    msg = _get_val(ev, "message", "")
                    if "홈런" in str(msg):
                        if curr_batter_id is not None:
                            b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                            b_stat.bat_ab += 1
                            b_stat.bat_hits += 1
                            b_stat.bat_homeruns += 1
                            b_stat.bat_tb += 4
                            b_stat.bat_rbi += 1
                            b_stat.bat_runs += 1
                        if curr_pitcher_id is not None:
                            p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                            p_stat.pitch_hits += 1
                            p_stat.pitch_homeruns += 1
                            p_stat.pitch_runs += 1
                            p_stat.pitch_earned_runs += 1

                elif etype == "BASE_RUN_RESULT":
                    target_base = _get_val(ev, "target_base")
                    res = _get_val(ev, "result")
                    reason = _get_val(ev, "reason")
                    runner_id = _get_val(ev, "runner_id")

                    if runner_id is None or runner_id == curr_batter_id:
                        # 타자 주자의 인플레이 타구 결과 집계
                        if res == "OUT":
                            if curr_batter_id is not None:
                                b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                                b_stat.bat_ab += 1
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_outs += 1
                        elif res == "SAFE" and target_base and 1 <= target_base <= 3 and reason != "WALK":
                            if curr_batter_id is not None:
                                b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                                b_stat.bat_ab += 1
                                b_stat.bat_hits += 1
                                b_stat.bat_tb += target_base
                                if target_base == 2:
                                    b_stat.bat_doubles += 1
                                elif target_base == 3:
                                    b_stat.bat_triples += 1
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_hits += 1
                    else:
                        # 루상 주자의 진루 및 아웃 처리
                        if res == "OUT":
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_outs += 1
                        elif res == "SAFE" and target_base == 4:
                            # 득점 발생
                            r_stat = _get_or_create_stat(runner_id, year_num, None)
                            r_stat.bat_runs += 1
                            if curr_batter_id is not None:
                                b_stat = _get_or_create_stat(curr_batter_id, year_num, None)
                                b_stat.bat_rbi += 1
                            if curr_pitcher_id is not None:
                                p_stat = _get_or_create_stat(curr_pitcher_id, year_num, None)
                                p_stat.pitch_runs += 1
                                p_stat.pitch_earned_runs += 1

            # 경기 출전수 및 투수 승/패/세이브 마킹
            for b_id in participated_batters:
                b_stat = _get_or_create_stat(b_id, year_num, None)
                b_stat.bat_games += 1

            for p_id in participated_pitchers:
                p_stat = _get_or_create_stat(p_id, year_num, None)
                p_stat.pitch_games += 1
                if getattr(m, "winning_pitcher_id", None) == p_id:
                    p_stat.pitch_wins += 1
                if getattr(m, "losing_pitcher_id", None) == p_id:
                    p_stat.pitch_losses += 1
                if getattr(m, "save_pitcher_id", None) == p_id:
                    p_stat.pitch_saves += 1

            if idx % 100 == 0 or idx == total_matches:
                logger.info(f"  [진행 현황] {idx}/{total_matches} 경기 분석 완료 (누적 시즌 스탯 레코드: {len(stat_map)}건)")

        # 3. 데이터베이스에 일괄 적재 (Bulk Save)
        stat_records = list(stat_map.values())
        logger.info(f"데이터베이스 적재 시작 (총 {len(stat_records)}건의 시즌 스탯 레코드 저장 중...)")
        session.add_all(stat_records)
        session.commit()

        logger.success(
            f"선수 시즌 집계 재구축 완료! "
            f"(분석 경기: {parsed_match_count}경기, 생성된 시즌 스탯 레코드: 총 {len(stat_records)}건)"
        )


if __name__ == "__main__":
    rebuild_player_season_stats()
