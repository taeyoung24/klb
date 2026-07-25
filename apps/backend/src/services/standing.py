import random
from sqlmodel import Session, select, asc, desc
from typing import Optional
from src.models import League, Club, Match, DailyClubStanding
from src.enums import MatchStatus


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
    이전 날(sim_day - 1)의 성적을 기반으로 오늘 있었던 경기를 누적 반영합니다.
    """
    # 1. 모든 리그 조회
    leagues = session.exec(select(League)).all()

    for league in leagues:
        # 2. 해당 리그 소속 클럽 조회
        clubs = session.exec(select(Club).where(Club.league_id == league.id)).all()

        # 오늘 날짜에 완료된 해당 리그 경기 목록 조회
        matches = session.exec(
            select(Match)
            .where(Match.sim_day == sim_day)
            .where(Match.status == MatchStatus.COMPLETED)
        ).all()

        # 클럽별 당일 경기 결과 정리용 매핑
        match_results = {}
        for c in clubs:
            match_results[c.id] = None

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
            yesterday_standing = session.exec(
                select(DailyClubStanding)
                .where(DailyClubStanding.club_id == club.id)
                .where(DailyClubStanding.sim_day == sim_day - 1)
            ).first()

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

