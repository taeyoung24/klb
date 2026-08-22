import random
import datetime
from sqlmodel import Session, select, asc, desc, col, func
from sqlalchemy import and_
from typing import Optional, Sequence
from src.models import League, Club, Match, DailyClubStanding
from src.enums import MatchStatus, MatchStage
from src.services.date_utils import sim_day_to_date, date_obj_to_sim_day


def get_h2h_stats(session: Session, club_ids: list[int], max_sim_day: int) -> dict[int, dict[str, int]]:
    """
    지정된 club_ids 그룹 내부에서 치러진 상대 전적(승, 패, 득점, 실점)을 계산합니다.
    """
    stats = {cid: {"wins": 0, "losses": 0, "runs_scored": 0, "runs_allowed": 0} for cid in club_ids}

    matches = session.exec(
        select(Match)
        .where(Match.sim_day <= max_sim_day)
        .where(Match.status == MatchStatus.COMPLETED)
        .where(Match.home_club_id.in_(club_ids))  # type: ignore
        .where(Match.away_club_id.in_(club_ids))  # type: ignore
    ).all()

    for m in matches:
        if m.home_club_id not in stats or m.away_club_id not in stats:
            continue
        h_score = m.home_score if m.home_score is not None else 0
        a_score = m.away_score if m.away_score is not None else 0

        stats[m.home_club_id]["runs_scored"] += h_score
        stats[m.home_club_id]["runs_allowed"] += a_score
        stats[m.away_club_id]["runs_scored"] += a_score
        stats[m.away_club_id]["runs_allowed"] += h_score

        if h_score > a_score:
            stats[m.home_club_id]["wins"] += 1
            stats[m.away_club_id]["losses"] += 1
        elif a_score > h_score:
            stats[m.away_club_id]["wins"] += 1
            stats[m.home_club_id]["losses"] += 1

    return stats


def get_previous_season_rank(session: Session, club_id: int, current_sim_day: int) -> Optional[int]:
    """
    전년도 최종 정규리그 순위 스냅샷을 조회합니다.
    전년도 기록이 없는 경우(최초 시즌 등) None을 반환합니다.
    """
    prev_standing = session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.club_id == club_id)
        .where(DailyClubStanding.sim_day < current_sim_day - 100)
        .order_by(desc(DailyClubStanding.sim_day))
    ).first()

    return prev_standing.rank if prev_standing else None


def resolve_tiebreaker_home_away(
    session: Session,
    club_a_id: int,
    club_b_id: int,
    max_sim_day: int,
) -> tuple[int, int]:
    """
    2팀 타이브레이크 순위결정전 경기 필요 시 홈/원정 구장을 결정합니다.
    - 홈구장 배정 1기준: 상대 다득점(Total Scored in H2H) 우세 팀
    - 홈구장 배정 2기준: 전년도 최종 순위 우세(낮은 숫자) 팀
    - 홈구장 배정 3기준: 무작위(랜덤)
    반환값: (home_club_id, away_club_id)
    """
    h2h = get_h2h_stats(session, [club_a_id, club_b_id], max_sim_day)
    a_runs = h2h[club_a_id]["runs_scored"]
    b_runs = h2h[club_b_id]["runs_scored"]

    if a_runs > b_runs:
        return club_a_id, club_b_id
    elif b_runs > a_runs:
        return club_b_id, club_a_id

    a_prev = get_previous_season_rank(session, club_a_id, max_sim_day)
    b_prev = get_previous_season_rank(session, club_b_id, max_sim_day)

    if a_prev is not None and b_prev is not None and a_prev != b_prev:
        return (club_a_id, club_b_id) if a_prev < b_prev else (club_b_id, club_a_id)
    elif a_prev is not None and b_prev is None:
        return club_a_id, club_b_id
    elif a_prev is None and b_prev is not None:
        return club_b_id, club_a_id

    return (club_a_id, club_b_id) if random.random() < 0.5 else (club_b_id, club_a_id)


def resolve_tied_clubs(
    session: Session,
    tied_club_ids: list[int],
    max_sim_day: int,
    is_season_final: bool = False,
) -> tuple[list[int], list[tuple[int, int]]]:
    """
    동률 승률을 가진 club_ids 집단에 대해 승자승 및 타이브레이크 규정을 적용하여
    정렬된 구단 ID 리스트와 필요한 단판 타이브레이크 경기 매치업(home_id, away_id) 목록을 반환합니다.

    [규칙 적용]
    1) 2팀 동률 시:
       - 1순위: 승자승(H2H) 상대전적 우세 팀 상위
       - 승자승까지 완전 동률 시:
         - is_season_final인 경우: 타이브레이크 순위결정전 경기 생성 (홈: 상대 다득점 > 전년도 순위 > 랜덤)
         - 이미 치러진 후이거나 일반 정렬: 상대 다득점 -> 전년도 순위 -> 랜덤 순 정렬
    2) 3팀 이상 다자 동률 시:
       - 타이브레이크 순위결정전 경기는 열리지 않음('없다').
       - 1순위: 다자 간 승자승 상대전적 승률 (H2H Win Rate)
       - 2순위: 전년도 최종 순위 (낮은 숫자 우선)
       - 3순위: 무작위 (Random)
    """
    if len(tied_club_ids) <= 1:
        return tied_club_ids, []

    tb_matches: list[tuple[int, int]] = []
    h2h_stats = get_h2h_stats(session, tied_club_ids, max_sim_day)

    if len(tied_club_ids) == 2:
        c1, c2 = tied_club_ids[0], tied_club_ids[1]
        c1_w = h2h_stats[c1]["wins"]
        c2_w = h2h_stats[c2]["wins"]

        if c1_w > c2_w:
            return [c1, c2], []
        elif c2_w > c1_w:
            return [c2, c1], []
        else:
            # 승자승 완전 동률
            home_id, away_id = resolve_tiebreaker_home_away(session, c1, c2, max_sim_day)
            if is_season_final:
                tb_matches.append((home_id, away_id))
            return [home_id, away_id], tb_matches
    else:
        # 3팀 이상 다자 동률: 타이브레이크 경기는 생성하지 않음('없다')
        def get_multi_tie_score(cid: int) -> tuple[float, float, float]:
            w = h2h_stats[cid]["wins"]
            l = h2h_stats[cid]["losses"]
            h2h_win_rate = w / (w + l) if (w + l) > 0 else 0.0

            prev_rank = get_previous_season_rank(session, cid, max_sim_day)
            rank_score = prev_rank if prev_rank is not None else 999

            rand_val = random.random()
            return (h2h_win_rate, -rank_score, rand_val)

        sorted_ids = sorted(tied_club_ids, key=get_multi_tie_score, reverse=True)
        return sorted_ids, []


def apply_tiebreaker_rules_to_standings(
    session: Session,
    league_id: int,
    sim_day: int,
    is_season_final: bool = False,
) -> list[tuple[int, int]]:
    """
    지정된 league_id와 sim_day의 DailyClubStanding 스냅샷에서 승률 동률 팀들을 감지하여
    타이브레이크 규정을 적용하고, 순위를 1~N위 단일 순위로 정돈하여 DB에 업데이트합니다.
    필요 시 2팀 동률 타이브레이크 순위결정전 매치업 (home_id, away_id) 목록을 반환합니다.
    """
    standings = session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.league_id == league_id)
        .where(DailyClubStanding.sim_day == sim_day)
        .order_by(desc(DailyClubStanding.win_rate), desc(DailyClubStanding.wins))
    ).all()

    if not standings:
        return []

    # 동률 승률/승수 별 그룹핑
    groups: list[list[DailyClubStanding]] = []
    for std in standings:
        if not groups:
            groups.append([std])
        else:
            prev = groups[-1][0]
            if std.win_rate == prev.win_rate and std.wins == prev.wins:
                groups[-1].append(std)
            else:
                groups.append([std])

    final_ordered_standings: list[DailyClubStanding] = []
    all_tb_matches: list[tuple[int, int]] = []

    for grp in groups:
        if len(grp) == 1:
            final_ordered_standings.append(grp[0])
        else:
            club_ids = [s.club_id for s in grp]
            sorted_ids, tb_matches = resolve_tied_clubs(
                session, club_ids, max_sim_day=sim_day, is_season_final=is_season_final
            )
            all_tb_matches.extend(tb_matches)

            # sorted_ids 순서대로 grp 내 DailyClubStanding 매핑
            id_to_std = {s.club_id: s for s in grp}
            for cid in sorted_ids:
                if cid in id_to_std:
                    final_ordered_standings.append(id_to_std[cid])

    # 순위(rank) 재배정 (1위부터 N위까지 단일 순위 부여)
    for idx, std in enumerate(final_ordered_standings, 1):
        std.rank = idx
        session.add(std)

    session.commit()
    return all_tb_matches


def update_daily_standings(session: Session, sim_day: int):
    """
    지정된 sim_day의 경기 결과를 반영하여 리그별 클럽들의 누적 성적과 순위 스냅샷(DailyClubStanding)을 계산해 저장합니다.
    전일 스탠딩을 클럽별 개별 쿼리(N+1) 없이 1회 배치 조회로 최적화합니다.
    """
    curr_date = sim_day_to_date(sim_day)
    season_start_sim_day = date_obj_to_sim_day(datetime.date(curr_date.year, 1, 1))

    # 1. 모든 리그 조회
    leagues = session.exec(select(League)).all()

    # 2. 전일 스탠딩을 전 클럽 대상 1회 배치 쿼리로 로드 (N+1 → 1회)
    #    각 club_id별 최신(max) sim_day를 구하는 서브쿼리
    prev_max_subq = (
        select(
            DailyClubStanding.club_id,
            func.max(DailyClubStanding.sim_day).label("max_day"),
        )
        .where(col(DailyClubStanding.is_postseason) == False)
        .where(col(DailyClubStanding.sim_day) >= season_start_sim_day)
        .where(col(DailyClubStanding.sim_day) < sim_day)
        .group_by(col(DailyClubStanding.club_id))
        .subquery()
    )
    prev_rows = session.exec(
        select(DailyClubStanding).join(
            prev_max_subq,
            and_(
                col(DailyClubStanding.club_id) == prev_max_subq.c.club_id,
                col(DailyClubStanding.sim_day) == prev_max_subq.c.max_day,
            ),
        )
    ).all()
    prev_map: dict[int, DailyClubStanding] = {s.club_id: s for s in prev_rows}

    for league in leagues:
        # 3. 해당 리그 소속 클럽 조회
        clubs = session.exec(select(Club).where(Club.league_id == league.id)).all()

        # 오늘 날짜에 완료된 해당 리그 정규/타이브레이커 경기 목록 조회
        matches = session.exec(
            select(Match)
            .where(Match.sim_day == sim_day)
            .where(Match.status == MatchStatus.COMPLETED)
            .where(col(Match.stage).in_((MatchStage.REGULAR, MatchStage.TIEBREAKER)))
        ).all()

        # 클럽별 당일 경기 결과 정리용 매핑
        match_results: dict[int, Optional[str]] = {c.id: None for c in clubs}

        for match in matches:
            if match.home_club_id in match_results:
                if match.home_score is None or match.away_score is None:
                    raise ValueError(f"Completed match {match.id} has missing scores (None).")

                if match.home_score > match.away_score:
                    match_results[match.home_club_id] = "W"
                    match_results[match.away_club_id] = "L"
                elif match.home_score < match.away_score:
                    match_results[match.home_club_id] = "L"
                    match_results[match.away_club_id] = "W"
                else:
                    match_results[match.home_club_id] = "D"
                    match_results[match.away_club_id] = "D"

        today_standings_data = []

        for club in clubs:
            # 배치 로드된 맵에서 O(1) 접근 (DB 쿼리 없음)
            yesterday_standing = prev_map.get(club.id)

            if yesterday_standing:
                wins = yesterday_standing.wins
                draws = yesterday_standing.draws
                losses = yesterday_standing.losses
                games_played = yesterday_standing.games_played
                streak = yesterday_standing.streak
            else:
                wins = 0
                draws = 0
                losses = 0
                games_played = 0
                streak = 0

            result = match_results.get(club.id)
            if result:
                games_played += 1
                if result == "W":
                    wins += 1
                    streak = (streak + 1) if streak > 0 else 1
                elif result == "L":
                    losses += 1
                    streak = (streak - 1) if streak < 0 else -1
                elif result == "D":
                    draws += 1
                    streak = 0

            win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0

            today_standings_data.append({
                "club_id": club.id,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "games_played": games_played,
                "streak": streak,
                "win_rate": win_rate,
                "rank": 1,
                "games_back": 0,
            })

        today_standings_data.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)

        for idx, item in enumerate(today_standings_data):
            if idx > 0:
                prev_item = today_standings_data[idx - 1]
                if item["win_rate"] == prev_item["win_rate"] and item["wins"] == prev_item["wins"]:
                    item["rank"] = prev_item["rank"]
                else:
                    item["rank"] = idx + 1
            else:
                item["rank"] = 1

        first_place = today_standings_data[0]
        wins_1st = first_place["wins"]
        losses_1st = first_place["losses"]

        for item in today_standings_data:
            games_back = int(((wins_1st - item["wins"]) + (item["losses"] - losses_1st)) / 2 * 10)

            standing_record = DailyClubStanding(
                sim_day=sim_day,
                league_id=league.id,
                club_id=item["club_id"],
                rank=item["rank"],
                win_rate=item["win_rate"],
                games_back=games_back,
                wins=item["wins"],
                draws=item["draws"],
                losses=item["losses"],
                games_played=item["games_played"],
                streak=item["streak"],
                batting_average=0.0,
                era=0.0,
            )
            session.add(standing_record)

    session.commit()


def get_playoff_host_league(session: Session, max_regular_day: int = 168) -> Optional[League]:
    """
    정규시즌 최종 순위를 토대로 각 리그의 1~4위 진출팀의 승률 합산을 비교하여
    크라운 정예리그의 집중 개최 리그(Host Region)를 동적으로 선정해 반환합니다.
    """
    any_standing = session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.sim_day == max_regular_day)
    ).first()

    if not any_standing:
        return None

    leagues = session.exec(select(League)).all()
    league_win_sums = {}

    for league in leagues:
        standings = session.exec(
            select(DailyClubStanding)
            .where(DailyClubStanding.league_id == league.id)
            .where(DailyClubStanding.sim_day == max_regular_day)
            .order_by(asc(DailyClubStanding.rank))
        ).all()

        top_4_standings = standings[:4]
        if len(top_4_standings) < 4:
            continue
        win_sum = sum(std.win_rate for std in top_4_standings)
        league_win_sums[league.id] = win_sum

    if not league_win_sums:
        return None

    host_league_id = max(league_win_sums, key=lambda k: league_win_sums[k])
    return session.get(League, host_league_id)


def get_previous_elite_season_rank(session: Session, club_id: int, current_sim_day: int) -> Optional[int]:
    """
    전년도 정예리그(포스트리그) 최종 순위를 조회합니다.
    전년도 기록이 없는 경우(최초 시즌) None을 반환합니다.
    """
    prev_standing = session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.club_id == club_id)
        .where(DailyClubStanding.sim_day < current_sim_day - 100)
        .order_by(desc(DailyClubStanding.sim_day))
    ).first()

    return prev_standing.rank if prev_standing else None


def resolve_elite_league_ties(
    session: Session,
    ranking_list: list[dict],
    elite_start_day: int,
    elite_end_day: int,
    regular_max_day: int = 168,
    *,
    reg_map: Optional[dict[int, DailyClubStanding]] = None,
    elite_matches: Optional[Sequence[Match]] = None,
    prev_rank_map: Optional[dict[int, int]] = None,
) -> list[dict]:
    """
    크라운 정예리그 최종 순위표(ranking_list)에서 동률 승률 팀들에 대해
    추가 경기 생성 없이 6단계 순위 결정 기준을 적용하여 1~16위 단일 순위를 확정하여 반환합니다.

    reg_map, elite_matches, prev_rank_map은 호출측에서 미리 로드하여 전달합니다.
    미전달 시 내부에서 자체 쿼리합니다. (하위 호환성 유지)

    [6단계 동률 해소 기준]
    1. 1순위: 정예리그 상대 전적(H2H) 승률 (H2H Win Rate)
    2. 2순위: 정규시즌 시드 (정규시즌 rank가 우세한/낮은 숫자 팀 상위)
    3. 3순위: 정규시즌 승률 (정규시즌 win_rate가 높은 팀 상위)
    4. 4순위: 정예리그 상대 전적 다득점 (H2H Total Runs Scored)
    5. 5순위: 전년도 정예리그/포스트리그 최종 시드/순위 (rank가 우세한/낮은 숫자 팀 상위)
    6. 6순위: 무작위 (Random)
    """
    if not ranking_list:
        return []

    # 정규시즌 최종 standing 스냅샷 (미전달 시 내부 쿼리 — 하위 호환)
    if reg_map is None:
        reg_standings = session.exec(
            select(DailyClubStanding)
            .where(col(DailyClubStanding.sim_day) == regular_max_day)
        ).all()
        reg_map = {s.club_id: s for s in reg_standings}

    # 정예리그 완료 경기 (미전달 시 내부 쿼리 — 하위 호환)
    actual_elite_matches: Sequence[Match] = (
        elite_matches
        if elite_matches is not None
        else session.exec(
            select(Match)
            .where(col(Match.sim_day) >= elite_start_day)
            .where(col(Match.sim_day) <= elite_end_day)
            .where(col(Match.status) == MatchStatus.COMPLETED)
        ).all()
    )

    # 전년도 순위맵 (미전달 시 빈 맵 — 동률 5순위 기준에서 전원 999)
    if prev_rank_map is None:
        prev_rank_map = {}

    # 승률 및 승수 기준 1차 그룹핑
    groups: list[list[dict]] = []
    sorted_base = sorted(ranking_list, key=lambda x: (x["win_rate"], x["wins"]), reverse=True)

    for item in sorted_base:
        if not groups:
            groups.append([item])
        else:
            prev = groups[-1][0]
            if item["win_rate"] == prev["win_rate"] and item["wins"] == prev["wins"]:
                groups[-1].append(item)
            else:
                groups.append([item])

    final_ranking_list: list[dict] = []

    for grp in groups:
        if len(grp) == 1:
            final_ranking_list.append(grp[0])
        else:
            tied_club_ids = [item["club"].id for item in grp]
            item_map = {item["club"].id: item for item in grp}

            # 동률 그룹 내 H2H 통계 계산
            h2h_stats = {cid: {"wins": 0, "losses": 0, "runs_scored": 0} for cid in tied_club_ids}
            for m in actual_elite_matches:
                if m.home_club_id in h2h_stats and m.away_club_id in h2h_stats:
                    h_score = m.home_score if m.home_score is not None else 0
                    a_score = m.away_score if m.away_score is not None else 0

                    h2h_stats[m.home_club_id]["runs_scored"] += h_score
                    h2h_stats[m.away_club_id]["runs_scored"] += a_score

                    if h_score > a_score:
                        h2h_stats[m.home_club_id]["wins"] += 1
                        h2h_stats[m.away_club_id]["losses"] += 1
                    elif a_score > h_score:
                        h2h_stats[m.away_club_id]["wins"] += 1
                        h2h_stats[m.home_club_id]["losses"] += 1

            # 1~4단계 키 헬퍼 (1: H2H 승률, 2: 정규시즌 시드, 3: 정규시즌 승률, 4: H2H 다득점)
            def get_stage1_to_4_key(cid: int) -> tuple[float, float, float, float]:
                w = h2h_stats[cid]["wins"]
                l = h2h_stats[cid]["losses"]
                h2h_win_rate = w / (w + l) if (w + l) > 0 else 0.0
                reg_std = reg_map.get(cid)
                reg_seed = reg_std.rank if reg_std else 999
                reg_win_rate = reg_std.win_rate if reg_std else 0.0
                h2h_runs = h2h_stats[cid]["runs_scored"]
                return (
                    h2h_win_rate,
                    -float(reg_seed),
                    reg_win_rate,
                    float(h2h_runs),
                )

            # 1~4단계 기준으로 서브그룹 분할
            sub_groups: dict[tuple[float, float, float, float], list[int]] = {}
            for cid in tied_club_ids:
                k = get_stage1_to_4_key(cid)
                sub_groups.setdefault(k, []).append(cid)

            # 1~4단계 기준 내림차순 정렬
            sorted_sub_keys = sorted(sub_groups.keys(), reverse=True)

            for k in sorted_sub_keys:
                sub_cids = sub_groups[k]
                if len(sub_cids) == 1:
                    final_ranking_list.append(item_map[sub_cids[0]])
                else:
                    # 1~4순위로도 동률이 해소되지 않은 경우에만 5순위(전년도 순위)를 Lazy Load
                    if prev_rank_map is None:
                        prev_rank_map = _batch_load_prev_elite_season_ranks(session, tied_club_ids, elite_start_day)

                    def get_stage5_to_6_key(cid: int) -> tuple[float, float]:
                        prev_rank_score = prev_rank_map.get(cid, 999) if prev_rank_map else 999
                        return (-float(prev_rank_score), random.random())

                    sorted_remaining_ids = sorted(sub_cids, key=get_stage5_to_6_key, reverse=True)
                    for cid in sorted_remaining_ids:
                        final_ranking_list.append(item_map[cid])

    return final_ranking_list


def _batch_load_prev_elite_season_ranks(
    session: Session, club_ids: list[int], elite_start_day: int
) -> dict[int, int]:
    """
    전년도 정예리그 최종 순위를 전 참가 구단 대상 1회 배치 쿼리로 로드합니다.
    반환: {club_id: rank} (기록 없는 구단은 포함되지 않음 → 호출측에서 .get(cid, 999))
    """
    # 전년도 = elite_start_day 보다 100일 이상 앞선 스탠딩의 최신 스냅샷
    cutoff_sim_day = elite_start_day - 100

    prev_max_subq = (
        select(
            DailyClubStanding.club_id,
            func.max(DailyClubStanding.sim_day).label("max_day"),
        )
        .where(col(DailyClubStanding.is_postseason) == True)
        .where(col(DailyClubStanding.sim_day) < cutoff_sim_day)
        .where(col(DailyClubStanding.club_id).in_(club_ids))
        .group_by(col(DailyClubStanding.club_id))
        .subquery()
    )
    prev_rows = session.exec(
        select(DailyClubStanding).join(
            prev_max_subq,
            and_(
                col(DailyClubStanding.club_id) == prev_max_subq.c.club_id,
                col(DailyClubStanding.sim_day) == prev_max_subq.c.max_day,
            ),
        )
    ).all()
    return {s.club_id: s.rank for s in prev_rows}


def update_elite_daily_standings(
    session: Session,
    sim_day: int,
    elite_start_day: int,
    host_league_id: int,
    playoff_club_ids: list[int],
    regular_max_day: int = 168,
    *,
    elite_matches: Optional[Sequence[Match]] = None,
):
    """
    지정된 sim_day(정예리그 기간)까지 완료된 정예리그 매치 결과를 바탕으로
    16개 참가 구단의 성적, streak, games_back을 계산하고 6단계 타이브레이크를 적용하여
    DailyClubStanding 스냅샷 (is_postseason=True, league_id=host_league_id)을 DB에 저장합니다.

    최적화:
    - elite_matches: 외부 전달 시 재활용하여 중복 쿼리 제거
    - 구단 배치 조회: session.get × 16 → IN 쿼리 1회
    - streak 계산: 16 × N 루프 → 클럽별 경기 인덱스 사전 구축
    - reg_map: resolve_elite_league_ties 내부 매번 재쿼리 → 1회 선로드 후 주입
    - prev_rank_map: 매일 무조건 실행하지 않고 1~4순위 동률 시 Lazy Loading
    """
    # [최적화 1] 정예리그 경기 조회 (외부 미전달 시 1회 조회)
    if elite_matches is None:
        elite_matches = session.exec(
            select(Match)
            .where(col(Match.sim_day) >= elite_start_day)
            .where(col(Match.sim_day) <= sim_day)
            .where(col(Match.status) == MatchStatus.COMPLETED)
        ).all()
    else:
        # COMPLETED 상태의 경기만 필터링 (필요시)
        elite_matches = [m for m in elite_matches if m.status == MatchStatus.COMPLETED and m.sim_day <= sim_day]

    # [최적화 2] 클럽 배치 조회 (session.get × N → IN 1회)
    club_rows = session.exec(
        select(Club).where(col(Club.id).in_(playoff_club_ids))  # type: ignore
    ).all()
    club_map: dict[int, Club] = {c.id: c for c in club_rows}

    stats: dict[int, dict] = {
        cid: {
            "club_id": cid,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "games_played": 0,
            "win_rate": 0.0,
            "streak": 0,
        }
        for cid in playoff_club_ids
    }

    # [최적화 3] 클럽별 경기 인덱스 사전 구축 (streak 계산용 O(N) → O(1) 접근)
    club_matches_index: dict[int, list] = {cid: [] for cid in playoff_club_ids}

    for m in elite_matches:
        if m.home_club_id in stats and m.away_club_id in stats:
            stats[m.home_club_id]["games_played"] += 1
            stats[m.away_club_id]["games_played"] += 1
            h_score = m.home_score if m.home_score is not None else 0
            a_score = m.away_score if m.away_score is not None else 0

            if h_score > a_score:
                stats[m.home_club_id]["wins"] += 1
                stats[m.away_club_id]["losses"] += 1
            elif h_score < a_score:
                stats[m.away_club_id]["wins"] += 1
                stats[m.home_club_id]["losses"] += 1
            else:
                stats[m.home_club_id]["draws"] += 1
                stats[m.away_club_id]["draws"] += 1

        if m.home_club_id in club_matches_index:
            club_matches_index[m.home_club_id].append(m)
        if m.away_club_id in club_matches_index:
            club_matches_index[m.away_club_id].append(m)

    for cid, s in stats.items():
        w_l = s["wins"] + s["losses"]
        s["win_rate"] = s["wins"] / w_l if w_l > 0 else 0.0

    # streak 계산: 사전 인덱스 사용으로 16 × N 루프 제거
    for cid in playoff_club_ids:
        club_matches = sorted(
            club_matches_index[cid],
            key=lambda x: x.sim_day,
            reverse=True,
        )
        streak = 0
        if club_matches:
            first = club_matches[0]
            fh_s = first.home_score if first.home_score is not None else 0
            fa_s = first.away_score if first.away_score is not None else 0
            is_win = (first.home_club_id == cid and fh_s > fa_s) or (first.away_club_id == cid and fa_s > fh_s)
            is_loss = (first.home_club_id == cid and fh_s < fa_s) or (first.away_club_id == cid and fa_s < fh_s)

            if is_win:
                streak = 1
                for m in club_matches[1:]:
                    hs = m.home_score if m.home_score is not None else 0
                    aws = m.away_score if m.away_score is not None else 0
                    if (m.home_club_id == cid and hs > aws) or (m.away_club_id == cid and aws > hs):
                        streak += 1
                    else:
                        break
            elif is_loss:
                streak = -1
                for m in club_matches[1:]:
                    hs = m.home_score if m.home_score is not None else 0
                    aws = m.away_score if m.away_score is not None else 0
                    if (m.home_club_id == cid and hs < aws) or (m.away_club_id == cid and aws < hs):
                        streak -= 1
                    else:
                        break
        stats[cid]["streak"] = streak

    # [최적화 4] reg_map 선로드 (resolve 내부 반복 쿼리 제거)
    reg_standings = session.exec(
        select(DailyClubStanding)
        .where(col(DailyClubStanding.sim_day) == regular_max_day)
    ).all()
    reg_map = {s.club_id: s for s in reg_standings}

    ranking_list = [
        {
            "club": club_map.get(cid),
            "wins": s["wins"],
            "losses": s["losses"],
            "draws": s["draws"],
            "win_rate": s["win_rate"],
        }
        for cid, s in stats.items()
        if club_map.get(cid) is not None
    ]
    resolved_ranking = resolve_elite_league_ties(
        session,
        ranking_list,
        elite_start_day,
        sim_day,
        regular_max_day,
        reg_map=reg_map,
        elite_matches=elite_matches,
        prev_rank_map=None,  # 필요 시 내부에서 5순위 동률 시 Lazy Load
    )

    ordered_cids = [item["club"].id for item in resolved_ranking if item["club"] is not None]

    first_cid = ordered_cids[0] if ordered_cids else playoff_club_ids[0]
    wins_1st = stats[first_cid]["wins"]
    losses_1st = stats[first_cid]["losses"]

    for rank_idx, cid in enumerate(ordered_cids, 1):
        s = stats[cid]
        games_back = int(((wins_1st - s["wins"]) + (s["losses"] - losses_1st)) / 2 * 10)
        rec = DailyClubStanding(
            sim_day=sim_day,
            league_id=host_league_id,
            club_id=cid,
            is_postseason=True,
            rank=rank_idx,
            win_rate=s["win_rate"],
            games_back=max(0, games_back),
            wins=s["wins"],
            draws=s["draws"],
            losses=s["losses"],
            games_played=s["games_played"],
            streak=s["streak"],
            batting_average=0.0,
            era=0.0,
        )
        session.add(rec)

    session.commit()
