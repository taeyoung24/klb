"""
KLB 코어 시뮬레이션 엔진 (Core Simulation Engine)

유니버스 가상 시계(WorldState.current_sim_day)를 1일 단위로 진전시키며,
행정 일정(Administrative Schedule) 상수 규칙 및 시각(Time/Order) 정보에 따라
스케줄 생성, 경기 시뮬레이션, 순위표 정산, 토너먼트 진행을 순차적으로 수행합니다.
"""

import datetime
from typing import NamedTuple
from sqlmodel import Session, select, asc, desc, func, col
from src.models import WorldState, Match, Club, League, DailyClubStanding, MatchPlaceholder, Player
from src.enums import MatchStatus, MatchStage
from src.services.schedule_utils import (
    generate_regular_schedule,
    generate_krown_elite_schedule,
    generate_knockout_schedule,
    save_knockout_placeholders,
    generate_tiebreaker_schedule,
    update_knockout_placeholders_realtime,
)
from src.services.ingame import run_match, recover_player_energy_daily
from src.services.standing import (
    update_daily_standings,
    apply_tiebreaker_rules_to_standings,
    resolve_elite_league_ties,
    update_elite_daily_standings,
    get_playoff_host_league,
)
from src.services.date_utils import sim_day_to_date, date_obj_to_sim_day
from src.utils.date_ext import get_first_monday_of_october
from src.services.draft import run_all_rookie_drafts
from src.services.roster_management import (
    process_season_end_retirements,
    process_season_end_releases,
    process_pre_draft_releases,
    process_annual_player_progression,
)
from src.services.front_office.trade import process_daily_trade_market
from src.services.front_office.free_agency import process_daily_fa_market
from src.utils.logger import logger


def is_third_monday_of_february(target_date: datetime.date) -> bool:
    """해당 날짜가 2월 셋째 주 월요일인지 판별합니다."""
    if target_date.month != 2 or target_date.weekday() != 0:
        return False
    feb_first = datetime.date(target_date.year, 2, 1)
    days_to_monday = (0 - feb_first.weekday() + 7) % 7
    first_monday_day = 1 + days_to_monday
    third_monday_day = first_monday_day + 14
    return target_date.day == third_monday_day



# ==============================================================================
# 행정 일정 스케줄 상수 (Administrative Schedule Constants)
# ==============================================================================
TIME_ADMIN_TASK = "09:00"        # 행정 일정 생성, 대진표 등록 등
TIME_MATCH_SIMULATION = "14:00"  # 경기 시뮬레이션 (run_match)
TIME_STANDINGS_UPDATE = "22:00"  # 순위표 및 정산 갱신
TIME_DAY_FINALIZE = "23:59"      # 가상 시계 1일 진전 및 DB 커밋


class AdminTaskRule(NamedTuple):
    """행정 태스크 트리거 규칙"""
    name: str
    schedule_time: str
    priority: int


# 주요 행정 일정 이벤트 상수
ADMIN_EVENT_SEASON_SCHEDULE_GEN = AdminTaskRule("정규시즌 일정 생성 및 등록 (매년 2월 3주차 월요일)", TIME_ADMIN_TASK, 1)
ADMIN_EVENT_TIEBREAKER_CHECK = AdminTaskRule("타이브레이크 매치 판정 및 생성", TIME_ADMIN_TASK, 2)
ADMIN_EVENT_ELITE_SCHEDULE_GEN = AdminTaskRule("크라운 정예리그 대진 생성", TIME_ADMIN_TASK, 3)
ADMIN_EVENT_KNOCKOUT_SCHEDULE_GEN = AdminTaskRule("녹아웃 토너먼트 대진표 생성 및 관리", TIME_ADMIN_TASK, 4)
ADMIN_EVENT_ROOKIE_DRAFT = AdminTaskRule("KLB 리그별 신인 드래프트 개최 (매년 10월 1주차 월요일)", TIME_ADMIN_TASK, 5)


def get_higher_seed(top_8_clubs: list[Club], c1_id: int, c2_id: int) -> tuple[int, int]:
    """정예리그 순위(시드)가 높은 구단을 홈팀으로 반환합니다."""
    ids = [c.id for c in top_8_clubs]
    idx1 = ids.index(c1_id)
    idx2 = ids.index(c2_id)
    return (c1_id, c2_id) if idx1 < idx2 else (c2_id, c1_id)


# ==============================================================================
# 행정 일정 및 토너먼트 진행 처리기 (09:00~10:00)
# ==============================================================================

def _check_and_run_admin_tasks(session: Session, sim_day: int) -> None:
    """
    09:00 시각: 현재 sim_day에 수행되어야 할 행정 스케줄(일정 생성, 대진표 등록 등)이 있는지 검토하고 실행합니다.
    """
    logger.debug(f"[{TIME_ADMIN_TASK}] [Sim Day {sim_day}] 행정 일정(Administrative Task) 검토 중...")
    current_date = sim_day_to_date(sim_day)
    current_year = current_date.year

    # 1. 매년 2월 셋째 주 월요일: 해당 연도 정규시즌 경기 일정 자동 생성 및 적재
    if is_third_monday_of_february(current_date):
        jan_1_date = datetime.date(current_year, 1, 1)
        year_base_sim_day = date_obj_to_sim_day(jan_1_date)

        jan_1_sim_day = year_base_sim_day
        dec_31_sim_day = year_base_sim_day + 365
        existing_matches = session.exec(
            select(Match)
            .where(Match.sim_day >= jan_1_sim_day)
            .where(Match.sim_day <= dec_31_sim_day)
        ).all()

        if not existing_matches:
            leagues = session.exec(select(League)).all()
            total_matches_count = 0
            for league in leagues:
                league_clubs = list(session.exec(select(Club).where(Club.league_id == league.id)).all())
                if len(league_clubs) == 10:
                    reg_matches = generate_regular_schedule(league_clubs, year=current_year, base_sim_day=year_base_sim_day)
                    for m in reg_matches:
                        session.add(m)
                    total_matches_count += len(reg_matches)

            if total_matches_count > 0:
                session.commit()
                logger.info(f"[{ADMIN_EVENT_SEASON_SCHEDULE_GEN.name}] 실행: {current_year}시즌 전체 리그 정규시즌 일정({total_matches_count}경기) 적재 (Sim Day: {sim_day})")

    # 2. 정규시즌 마감 후 타이브레이크 판정 검토
    jan_1_sim_day = date_obj_to_sim_day(datetime.date(current_year, 1, 1))
    dec_31_sim_day = date_obj_to_sim_day(datetime.date(current_year, 12, 31))

    all_regular_days = session.exec(
        select(Match.sim_day)
        .where(col(Match.stage).in_((MatchStage.REGULAR, MatchStage.TIEBREAKER)))
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
    ).all()
    if not all_regular_days:
        return
    max_regular_day = max(all_regular_days)

    if sim_day == max_regular_day + 1:
        leagues = session.exec(select(League)).all()
        has_tb = False
        for league in leagues:
            tb_matches = apply_tiebreaker_rules_to_standings(
                session, league.id, max_regular_day, is_season_final=True
            )
            if tb_matches:
                has_tb = True
                logger.info(f"[{ADMIN_EVENT_TIEBREAKER_CHECK.name}] [{league.name_ko}] 타이브레이크 경기({len(tb_matches)}건) 생성")
                for home_id, away_id in tb_matches:
                    tb_match = generate_tiebreaker_schedule(home_id, away_id, sim_day)
                    session.add(tb_match)
        if has_tb:
            session.commit()

    # 3. 정예리그 일정 생성 검토 (정규시즌 마감 + 4일 휴식 후 시작)
    elite_start_day = max_regular_day + 5
    if sim_day == max_regular_day + 4:
        existing_elite = session.exec(
            select(Match)
            .where(Match.stage == MatchStage.ELITE)
            .where(Match.sim_day >= jan_1_sim_day)
            .where(Match.sim_day <= dec_31_sim_day)
        ).all()
        if not existing_elite:
            logger.info(f"[{ADMIN_EVENT_ELITE_SCHEDULE_GEN.name}] 실행: {current_year}시즌 크라운 정예리그 대진 편성")
            leagues = session.exec(select(League)).all()
            playoff_clubs = []
            for league in leagues:
                max_std_day = session.exec(
                    select(func.max(DailyClubStanding.sim_day))
                    .where(DailyClubStanding.league_id == league.id)
                    .where(DailyClubStanding.is_postseason == False)
                    .where(DailyClubStanding.sim_day <= max_regular_day)
                ).first()
                if max_std_day:
                    standings = session.exec(
                        select(DailyClubStanding)
                        .where(DailyClubStanding.league_id == league.id)
                        .where(DailyClubStanding.is_postseason == False)
                        .where(DailyClubStanding.sim_day == max_std_day)
                        .order_by(asc(DailyClubStanding.rank))
                    ).all()
                    for std in standings[:4]:
                        club = session.get(Club, std.club_id)
                        if club:
                            playoff_clubs.append(club)

            if len(playoff_clubs) == 16:
                elite_matches = generate_krown_elite_schedule(playoff_clubs, elite_start_day)
                for m in elite_matches:
                    session.add(m)
                session.commit()

    # 4. 녹아웃 토너먼트 진행 및 동적 경기 편성
    elite_matches = session.exec(
        select(Match.sim_day)
        .where(Match.stage == MatchStage.ELITE)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
    ).all()
    if not elite_matches:
        return
    elite_end_day = max(elite_matches)

    # 4-1. elite_end_day + 1 (휴식일): 8강 대진표 플레이스홀더 생성
    if sim_day == elite_end_day + 1:
        existing_placeholders = session.exec(
            select(MatchPlaceholder)
            .where(MatchPlaceholder.sim_day >= jan_1_sim_day)
            .where(MatchPlaceholder.sim_day <= dec_31_sim_day)
        ).all()
        if not existing_placeholders:
            logger.info(f"[{ADMIN_EVENT_KNOCKOUT_SCHEDULE_GEN.name}] 정예리그 마감 ➔ 상위 8개 팀 시드 확정 및 8강 대진표 등록")
            playoff_club_ids = list(set([
                m.home_club_id for m in session.exec(
                    select(Match)
                    .where(Match.stage == MatchStage.ELITE)
                    .where(Match.sim_day >= jan_1_sim_day)
                    .where(Match.sim_day <= dec_31_sim_day)
                ).all()
            ]))
            playoff_clubs = [session.get(Club, cid) for cid in playoff_club_ids if session.get(Club, cid) is not None]

            team_stats = {c.id: {"club": c, "wins": 0, "losses": 0, "draws": 0} for c in playoff_clubs if c is not None}
            for m in session.exec(
                select(Match)
                .where(Match.stage == MatchStage.ELITE)
                .where(Match.sim_day >= jan_1_sim_day)
                .where(Match.sim_day <= dec_31_sim_day)
            ).all():
                h_score = m.home_score if m.home_score is not None else 0
                a_score = m.away_score if m.away_score is not None else 0
                if h_score > a_score:
                    team_stats[m.home_club_id]["wins"] += 1
                    team_stats[m.away_club_id]["losses"] += 1
                elif h_score < a_score:
                    team_stats[m.home_club_id]["losses"] += 1
                    team_stats[m.away_club_id]["wins"] += 1
                else:
                    team_stats[m.home_club_id]["draws"] += 1
                    team_stats[m.away_club_id]["draws"] += 1

            ranking_list = []
            for cid, stat in team_stats.items():
                w, l, d = stat["wins"], stat["losses"], stat["draws"]
                wr = w / (w + l) if (w + l) > 0 else 0.0
                ranking_list.append({"club": stat["club"], "wins": w, "losses": l, "draws": d, "win_rate": wr})

            ranking_list = resolve_elite_league_ties(session, ranking_list, elite_start_day, elite_end_day)
            top_8_clubs = [item["club"] for item in ranking_list[:8]]

            placeholders = generate_knockout_schedule(top_8_clubs, elite_end_day + 1)
            save_knockout_placeholders(session, placeholders)

            # 8강 1차전 (elite_end_day + 2) 사전 Match 생성
            q_nodes = sorted([p for p in placeholders if p.round == "ROUND_OF_8"], key=lambda x: x.id)
            for q in q_nodes:
                if q.home_club_id and q.away_club_id:
                    h_club = session.get(Club, q.home_club_id)
                    m = Match(
                        home_club_id=q.home_club_id,
                        away_club_id=q.away_club_id,
                        stadium_id=h_club.home_stadium_id if h_club else None,
                        sim_day=elite_end_day + 2,
                        status=MatchStatus.SCHEDULED,
                        stage=MatchStage.KNOCKOUT,
                        limit_extra_innings=False
                    )
                    session.add(m)

            session.commit()

    # 4-2. 녹아웃 경기 동적 편성
    placeholders = session.exec(
        select(MatchPlaceholder)
        .where(MatchPlaceholder.sim_day >= jan_1_sim_day)
        .where(MatchPlaceholder.sim_day <= dec_31_sim_day)
    ).all()
    if not placeholders:
        return

    q_nodes = sorted([p for p in placeholders if p.round == "ROUND_OF_8"], key=lambda x: x.id)
    s_nodes = sorted([p for p in placeholders if p.round == "SEMI_FINAL"], key=lambda x: x.id)
    f_node = [p for p in placeholders if p.round == "FINAL"][0] if any(p.round == "FINAL" for p in placeholders) else None

    # 8강 1차전: elite_end_day + 2
    if sim_day == elite_end_day + 2:
        existing_day1 = session.exec(select(Match).where(Match.sim_day == sim_day).where(Match.stage == MatchStage.KNOCKOUT)).all()
        if not existing_day1:
            logger.info(">>> 녹아웃 8강 1차전 매치 편성")
            for q in q_nodes:
                if q.home_club_id and q.away_club_id:
                    h_club = session.get(Club, q.home_club_id)
                    m = Match(
                        home_club_id=q.home_club_id,
                        away_club_id=q.away_club_id,
                        stadium_id=h_club.home_stadium_id if h_club else None,
                        sim_day=sim_day,
                        status=MatchStatus.SCHEDULED,
                        stage=MatchStage.KNOCKOUT,
                        limit_extra_innings=False
                    )
                    session.add(m)
            session.commit()

    # 8강 2차전: elite_end_day + 3 (1차전 결과 1승 1패인 타이 매치 진행)
    elif sim_day == elite_end_day + 3:
        # 1차전 매치 결과 확인
        day1_matches = session.exec(select(Match).where(Match.sim_day == elite_end_day + 2)).all()
        q_winners = {}
        for idx, m in enumerate(day1_matches):
            h_score = m.home_score if m.home_score is not None else 0
            a_score = m.away_score if m.away_score is not None else 0
            if h_score > a_score:
                q_winners[idx] = m.home_club_id
            else:
                # 1차전 원정 승리 -> 2차전 타이브레이커 경기 개최
                q = q_nodes[idx] if idx < len(q_nodes) else None
                if q and q.home_club_id and q.away_club_id:
                    h_club = session.get(Club, q.home_club_id)
                    m2 = Match(
                        home_club_id=q.home_club_id,
                        away_club_id=q.away_club_id,
                        stadium_id=h_club.home_stadium_id if h_club else None,
                        sim_day=sim_day,
                        status=MatchStatus.SCHEDULED,
                        stage=MatchStage.KNOCKOUT,
                        limit_extra_innings=False
                    )
                    session.add(m2)
        session.commit()

    # 8강 종료 후 4강 대진 배치: elite_end_day + 4
    elif sim_day == elite_end_day + 4:
        # 8강 최종 승자 계산 및 4강 MatchPlaceholder 할당
        all_q_matches = session.exec(select(Match).where(Match.sim_day >= elite_end_day + 2).where(Match.sim_day <= elite_end_day + 3)).all()
        # 대진별 승자 판정
        q_winners_list = []
        for q in q_nodes:
            q_m = [m for m in all_q_matches if m.home_club_id == q.home_club_id and m.away_club_id == q.away_club_id]
            if q_m:
                last_m = q_m[-1]
                h_score = last_m.home_score if last_m.home_score is not None else 0
                a_score = last_m.away_score if last_m.away_score is not None else 0
                winner = q.home_club_id if h_score > a_score else q.away_club_id
                q_winners_list.append(winner)

        if len(q_winners_list) == 4:
            s1_home = q_winners_list[0]
            s1_away = q_winners_list[1]
            s2_home = q_winners_list[2]
            s2_away = q_winners_list[3]
            s_nodes[0].home_club_id = s1_home
            s_nodes[0].away_club_id = s1_away
            s_nodes[1].home_club_id = s2_home
            s_nodes[1].away_club_id = s2_away
            session.add(s_nodes[0])
            session.add(s_nodes[1])

            # 4강전 (Semi-Finals Bo5) 필수 1, 2, 3차전 Match 사전 생성
            semi_start_day = elite_end_day + 5
            essential_semi_games = [(0, 1), (1, 2), (3, 3)]  # (offset, game_num)
            for s in s_nodes:
                if not s.home_club_id or not s.away_club_id:
                    continue
                for offset, g_num in essential_semi_games:
                    target_sim_day = semi_start_day + offset
                    is_home = g_num in [1, 2, 5]
                    actual_home = s.home_club_id if is_home else s.away_club_id
                    actual_away = s.away_club_id if is_home else s.home_club_id
                    if not actual_home or not actual_away:
                        continue
                    h_club = session.get(Club, actual_home)
                    m = Match(
                        home_club_id=actual_home,
                        away_club_id=actual_away,
                        stadium_id=h_club.home_stadium_id if h_club else None,
                        sim_day=target_sim_day,
                        status=MatchStatus.SCHEDULED,
                        stage=MatchStage.KNOCKOUT,
                        limit_extra_innings=False
                    )
                    session.add(m)

            session.commit()
            logger.info(">>> 녹아웃 8강전 완주 ➔ 4강 대진표 확정 및 1~3차전 사전 매치 등록")

    # 4강전 (Semi-Finals Bo5): semi_start_day = elite_end_day + 5
    # offsets: 1차전: Day 0 (+5), 2차전: Day 1 (+6), 3차전: Day 3 (+8), 4차전: Day 4 (+9), 5차전: Day 6 (+11)
    semi_start_day = elite_end_day + 5
    semi_offsets = {0: 1, 1: 2, 3: 3, 4: 4, 6: 5} # day_offset: game_num
    day_offset_from_semi = sim_day - semi_start_day

    if day_offset_from_semi in semi_offsets:
        game_num = semi_offsets[day_offset_from_semi]
        for s in s_nodes:
            if not s.home_club_id or not s.away_club_id:
                continue

            # 해당 sim_day에 이미 생성된 Match가 존재하는지 확인 (사전 생성된 1~3차전 등)
            existing_match = session.exec(
                select(Match)
                .where(Match.sim_day == sim_day)
                .where(
                    ((Match.home_club_id == s.home_club_id) & (Match.away_club_id == s.away_club_id)) |
                    ((Match.home_club_id == s.away_club_id) & (Match.away_club_id == s.home_club_id))
                )
            ).first()
            if existing_match:
                continue

            # 기존 승수 확인
            s_matches = session.exec(
                select(Match)
                .where(Match.sim_day >= semi_start_day)
                .where(Match.sim_day < sim_day)
                .where(
                    ((Match.home_club_id == s.home_club_id) & (Match.away_club_id == s.away_club_id)) |
                    ((Match.home_club_id == s.away_club_id) & (Match.away_club_id == s.home_club_id))
                )
            ).all()

            h_wins = sum(1 for m in s_matches if (m.home_score or 0) > (m.away_score or 0) and m.home_club_id == s.home_club_id) + \
                     sum(1 for m in s_matches if (m.away_score or 0) > (m.home_score or 0) and m.away_club_id == s.home_club_id)
            a_wins = len(s_matches) - h_wins

            if h_wins < 3 and a_wins < 3:
                is_home = game_num in [1, 2, 5]
                actual_home = s.home_club_id if is_home else s.away_club_id
                actual_away = s.away_club_id if is_home else s.home_club_id
                h_club = session.get(Club, actual_home)
                m = Match(
                    home_club_id=actual_home,
                    away_club_id=actual_away,
                    stadium_id=h_club.home_stadium_id if h_club else None,
                    sim_day=sim_day,
                    status=MatchStatus.SCHEDULED,
                    stage=MatchStage.KNOCKOUT,
                    limit_extra_innings=False
                )
                session.add(m)
        session.commit()

    # 4강전 종료 판정 및 결승전 대진 배치: semi_start_day + 7 (Day offset = 7)
    elif day_offset_from_semi == 7:
        if f_node and s_nodes[0].home_club_id and s_nodes[1].home_club_id:
            s1_matches = session.exec(
                select(Match).where(Match.sim_day >= semi_start_day).where(Match.sim_day < sim_day)
                .where(((Match.home_club_id == s_nodes[0].home_club_id) & (Match.away_club_id == s_nodes[0].away_club_id)) |
                       ((Match.home_club_id == s_nodes[0].away_club_id) & (Match.away_club_id == s_nodes[0].home_club_id)))
            ).all()
            s2_matches = session.exec(
                select(Match).where(Match.sim_day >= semi_start_day).where(Match.sim_day < sim_day)
                .where(((Match.home_club_id == s_nodes[1].home_club_id) & (Match.away_club_id == s_nodes[1].away_club_id)) |
                       ((Match.home_club_id == s_nodes[1].away_club_id) & (Match.away_club_id == s_nodes[1].home_club_id)))
            ).all()

            s1_h_wins = sum(1 for m in s1_matches if (m.home_score or 0) > (m.away_score or 0) and m.home_club_id == s_nodes[0].home_club_id) + \
                        sum(1 for m in s1_matches if (m.away_score or 0) > (m.home_score or 0) and m.away_club_id == s_nodes[0].home_club_id)
            s1_winner = s_nodes[0].home_club_id if s1_h_wins >= 3 else s_nodes[0].away_club_id

            s2_h_wins = sum(1 for m in s2_matches if (m.home_score or 0) > (m.away_score or 0) and m.home_club_id == s_nodes[1].home_club_id) + \
                        sum(1 for m in s2_matches if (m.away_score or 0) > (m.home_score or 0) and m.away_club_id == s_nodes[1].home_club_id)
            s2_winner = s_nodes[1].home_club_id if s2_h_wins >= 3 else s_nodes[1].away_club_id

            f_node.home_club_id = s1_winner
            f_node.away_club_id = s2_winner
            session.add(f_node)

            # 결승전 (Final Bo7) 필수 1, 2, 3차전 Match 사전 생성
            final_start_day = semi_start_day + 8
            essential_final_games = [(0, 1), (1, 2), (2, 3)]  # (offset, game_num)
            for offset, g_num in essential_final_games:
                target_sim_day = final_start_day + offset
                is_home = g_num in [1, 2, 3, 7]
                actual_home = f_node.home_club_id if is_home else f_node.away_club_id
                actual_away = f_node.away_club_id if is_home else f_node.home_club_id
                if not actual_home or not actual_away:
                    continue
                h_club = session.get(Club, actual_home)
                m = Match(
                    home_club_id=actual_home,
                    away_club_id=actual_away,
                    stadium_id=h_club.home_stadium_id if h_club else None,
                    sim_day=target_sim_day,
                    status=MatchStatus.SCHEDULED,
                    stage=MatchStage.KNOCKOUT,
                    limit_extra_innings=False
                )
                session.add(m)

            session.commit()
            logger.info(">>> 녹아웃 4강전 완주 ➔ 결승전(Krown Series) 대진표 확정 및 1~3차전 사전 매치 등록")

    # 결승전 (Final Bo7): final_start_day = semi_start_day + 8 (elite_end_day + 13)
    # offsets: 1,2,3차전: Day 0,1,2 (+13, +14, +15), 4,5,6차전: Day 4,5,6 (+17, +18, +19), 7차전: Day 8 (+21)
    final_start_day = semi_start_day + 8
    final_offsets = {0: 1, 1: 2, 2: 3, 4: 4, 5: 5, 6: 6, 8: 7}
    day_offset_from_final = sim_day - final_start_day

    if day_offset_from_final in final_offsets and f_node and f_node.home_club_id and f_node.away_club_id:
        game_num = final_offsets[day_offset_from_final]

        # 해당 sim_day에 이미 생성된 Match가 존재하는지 확인 (사전 생성된 1~3차전 등)
        existing_match = session.exec(
            select(Match)
            .where(Match.sim_day == sim_day)
            .where(
                ((Match.home_club_id == f_node.home_club_id) & (Match.away_club_id == f_node.away_club_id)) |
                ((Match.home_club_id == f_node.away_club_id) & (Match.away_club_id == f_node.home_club_id))
            )
        ).first()

        if not existing_match:
            f_matches = session.exec(
                select(Match)
                .where(Match.sim_day >= final_start_day)
                .where(Match.sim_day < sim_day)
                .where(
                    ((Match.home_club_id == f_node.home_club_id) & (Match.away_club_id == f_node.away_club_id)) |
                    ((Match.home_club_id == f_node.away_club_id) & (Match.away_club_id == f_node.home_club_id))
                )
            ).all()

            h_wins = sum(1 for m in f_matches if (m.home_score or 0) > (m.away_score or 0) and m.home_club_id == f_node.home_club_id) + \
                     sum(1 for m in f_matches if (m.away_score or 0) > (m.home_score or 0) and m.away_club_id == f_node.home_club_id)
            a_wins = len(f_matches) - h_wins

            if h_wins < 4 and a_wins < 4:
                is_home = game_num in [1, 2, 3, 7]
                actual_home = f_node.home_club_id if is_home else f_node.away_club_id
                actual_away = f_node.away_club_id if is_home else f_node.home_club_id
                h_club = session.get(Club, actual_home)
                m = Match(
                    home_club_id=actual_home,
                    away_club_id=actual_away,
                    stadium_id=h_club.home_stadium_id if h_club else None,
                    sim_day=sim_day,
                    status=MatchStatus.SCHEDULED,
                    stage=MatchStage.KNOCKOUT,
                    limit_extra_innings=False
                )
                session.add(m)
                session.commit()

    # 5. 매년 10월 첫째 주차 월요일: 2차 방출(드래프트 대비 정원 확보) 및 신인 드래프트 개최
    draft_date = get_first_monday_of_october(current_date.year)
    draft_sim_day = date_obj_to_sim_day(draft_date)
    if sim_day == draft_sim_day:
        # 5-1. 드래프트 직전 로스터 공간 확보를 위한 2차 방출
        process_pre_draft_releases(session, year=current_date.year, sim_day=sim_day)

        # 5-2. 신인 드래프트 개최
        logger.info(f"[{ADMIN_EVENT_ROOKIE_DRAFT.name}] 실행: {current_date.year}시즌 KLB 신인 드래프트 개최 (Sim Day: {sim_day})")
        run_all_rookie_drafts(session, year=current_date.year, sim_day=sim_day)
        logger.success(f"[{ADMIN_EVENT_ROOKIE_DRAFT.name}] 완주: 신인 드래프트 완주 및 장부 적재 완료")

    # 6. 결승전(KS) 종료 직후 / 시즌 종료 마감일: 은퇴(Retire) 및 1차 방출(Release) 행정 처리
    if f_node and f_node.sim_day == sim_day:
        logger.info(f"[{current_date.year}시즌 종료 행정] 은퇴 및 1차 방출 처리 진행")
        process_season_end_retirements(session, year=current_date.year, sim_day=sim_day)
        process_season_end_releases(session, year=current_date.year, sim_day=sim_day)

    # 7. 매년 마지막 날(12월 31일): 연간 에이징 커브 스텝업/다운 처리 (Annual Progression & Regression)
    if current_date.month == 12 and current_date.day == 31:
        logger.info(f"[{current_date.year}년 연말 결산] 전 선수 연간 에이징 커브 스텝업/다운 처리 진행 (Sim Day: {sim_day})")
        process_annual_player_progression(session, year=current_date.year, sim_day=sim_day)

    # 8. 일일 상호 협의 트레이드(Trade) 및 FA 영입 시장 체크
    is_ps_ended = f_node is not None and sim_day > f_node.sim_day
    process_daily_trade_market(session, year=current_date.year, sim_day=sim_day, current_date=current_date, is_postseason_ended=is_ps_ended)
    process_daily_fa_market(session, year=current_date.year, sim_day=sim_day, current_date=current_date, is_postseason_ended=is_ps_ended)


def _run_scheduled_matches(session: Session, sim_day: int) -> None:
    """
    14:00 시각: 현재 sim_day에 SCHEDULED 상태인 매치들을 시뮬레이션합니다.
    """
    logger.debug(f"[{TIME_MATCH_SIMULATION}] [Sim Day {sim_day}] 경기 시뮬레이션 진행 중...")
    matches = session.exec(
        select(Match)
        .where(Match.sim_day == sim_day)
        .where(Match.status == MatchStatus.SCHEDULED)
    ).all()

    if matches:
        for match in matches:
            away_club = session.get(Club, match.away_club_id)
            home_club = session.get(Club, match.home_club_id)
            away_abbr = away_club.abbr_name if away_club and away_club.abbr_name else (away_club.name if away_club else f"Club#{match.away_club_id}")
            home_abbr = home_club.abbr_name if home_club and home_club.abbr_name else (home_club.name if home_club else f"Club#{match.home_club_id}")

            logger.info(f"  [Match {match.id:>4}] {away_abbr:>15} vs {home_abbr:<15} 진행 중...")
            run_match(match, session=session)
            session.add(match)
        session.commit()
        logger.debug(f"  ➔ [Sim Day {sim_day}] {len(matches)}경기 시뮬레이션 완료")
        update_knockout_placeholders_realtime(session, sim_day=sim_day)


def _update_standings_and_rankings(session: Session, sim_day: int) -> None:
    """
    22:00 시각: 당일 경기 결과를 기반으로 순위표 및 정산 데이터를 갱신합니다.
    """
    logger.debug(f"[{TIME_STANDINGS_UPDATE}] [Sim Day {sim_day}] 순위표 정산 중...")

    # 당일 완료된 경기 목록 조회
    today_completed_matches = session.exec(
        select(Match)
        .where(Match.sim_day == sim_day)
        .where(Match.status == MatchStatus.COMPLETED)
    ).all()

    if not today_completed_matches:
        return

    # 1. 정규리그 또는 타이브레이커 경기가 치러진 경우: 정규시즌 스탠딩 갱신
    has_regular_or_tb = any(m.stage in (MatchStage.REGULAR, MatchStage.TIEBREAKER) for m in today_completed_matches)
    if has_regular_or_tb:
        update_daily_standings(session, sim_day)

    # 2. 정예리그(ELITE) 경기가 치러진 경우: 정예리그 스탠딩 갱신
    has_elite = any(m.stage == MatchStage.ELITE for m in today_completed_matches)
    if has_elite:
        curr_date = sim_day_to_date(sim_day)
        season_start_sim_day = date_obj_to_sim_day(datetime.date(curr_date.year, 1, 1))

        # 현재 시즌 정예리그 경기만 조회 (시즌 경계 필터 추가)
        elite_matches = session.exec(
            select(Match)
            .where(Match.stage == MatchStage.ELITE)
            .where(Match.sim_day >= season_start_sim_day)
            .where(Match.sim_day <= sim_day)
        ).all()
        playoff_club_ids = list(set(m.home_club_id for m in elite_matches))
        elite_start_day = min(m.sim_day for m in elite_matches) if elite_matches else sim_day

        # func.max()로 단일 스칼라 집계 (전체 행 로드 제거) + 시즌 경계 필터
        max_regular_day = session.exec(
            select(func.max(Match.sim_day))
            .where(col(Match.stage).in_((MatchStage.REGULAR, MatchStage.TIEBREAKER)))
            .where(Match.sim_day >= season_start_sim_day)
            .where(Match.sim_day < sim_day)
        ).first() or (sim_day - 5)

        host_league = get_playoff_host_league(session, max_regular_day)
        host_league_id = host_league.id if host_league is not None else 1

        if playoff_club_ids:
            update_elite_daily_standings(
                session=session,
                sim_day=sim_day,
                elite_start_day=elite_start_day,
                host_league_id=host_league_id,
                playoff_club_ids=playoff_club_ids,
                regular_max_day=max_regular_day,
                elite_matches=elite_matches,
            )


def _recover_daily_energy(session: Session, sim_day: int) -> None:
    """
    23:59 시각: 하루가 마감될 때 모든 선수의 일일 자연 체력 회복을 수행합니다.
    - 미출전/휴식 선수: +1800 회복 (4~5일 휴식 시 100% 완충)
    - 출전 타자: +450 회복
    - 등판 투수: +300 회복
    - 원정(Away) 경기 구단 선수: 회복량의 70%(AWAY_RECOVERY_RATIO)만 적용
    """
    # 1. 당일 완료된 경기 조회 및 홈/원정 구단 ID 수집
    today_matches = session.exec(
        select(Match)
        .where(Match.sim_day == sim_day)
        .where(Match.status == MatchStatus.COMPLETED)
    ).all()

    home_club_ids = {m.home_club_id for m in today_matches}
    away_club_ids = {m.away_club_id for m in today_matches}
    played_club_ids = home_club_ids | away_club_ids

    # 2. 모든 등록 선수 조회 후 체력 회복
    all_players = session.exec(select(Player)).all()
    for player in all_players:
        if player.current_energy >= player.max_energy:
            continue

        is_away = player.club_id in away_club_ids
        participated = player.club_id in played_club_ids
        is_pitcher = (player.position == "PITCHER")

        recover_player_energy_daily(
            player,
            participated=participated,
            is_pitcher=is_pitcher,
            is_away=is_away,
        )
        session.add(player)


# ==============================================================================
# 메인 1일 단위 시뮬레이션 단일 함수 (Main Core Simulation Function)
# ==============================================================================

def step_simulation_day(session: Session) -> None:
    """
    WorldState.current_sim_day를 1일 진전시키는 코어 시뮬레이션 메인 함수입니다.
    동일 날짜 내에서 시각(Time Order) 순으로 행정 스케줄, 경기 실행, 순위 정산, 자정 마감을 수행합니다.

    :param session: SQLModel Database Session
    :return: None (Void 반환, 내부 로깅 처리)
    """
    world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
    if not world_state:
        logger.error("WorldState(id=1)를 찾을 수 없습니다. seed_db.py를 먼저 실행해 주세요.")
        return

    sim_day = world_state.current_sim_day
    logger.debug(f"=== [Sim Day {sim_day}] 일일 시뮬레이션 시작 ===")

    # 1. 09:00 행정 일정 태스크 검토 및 일정/대진/토너먼트 경기 동적 생성
    _check_and_run_admin_tasks(session, sim_day)

    # 2. 14:00 당일 예정 경기 시뮬레이션 실행
    _run_scheduled_matches(session, sim_day)

    # 3. 22:00 일일 순위표 및 기록 정산
    _update_standings_and_rankings(session, sim_day)

    # 4. 23:59 일일 마감, 선수 체력 자연 회복 및 WorldState 시각 1일 진전
    _recover_daily_energy(session, sim_day)
    world_state.current_sim_day = sim_day + 1
    session.add(world_state)
    session.commit()

    logger.debug(f"[{TIME_DAY_FINALIZE}] [Sim Day {sim_day}] 일일 시뮬레이션 완주 -> Next Sim Day: {world_state.current_sim_day}")
