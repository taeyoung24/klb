from sqlmodel import Session, select
from src.models import League, Club, Match, DailyClubStanding
from src.enums import MatchStatus

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
        # match_results[club_id] = "W" | "L" | "D" | None
        match_results = {}
        for c in clubs:
            match_results[c.id] = None

        for match in matches:
            # 홈/어웨이 중 해당 리그 소속 팀이 있는 경우 결과 처리
            if match.home_club_id in match_results:
                if match.home_score > match.away_score:
                    match_results[match.home_club_id] = "W"
                    match_results[match.away_club_id] = "L"
                elif match.home_score < match.away_score:
                    match_results[match.home_club_id] = "L"
                    match_results[match.away_club_id] = "W"
                else:
                    match_results[match.home_club_id] = "D"
                    match_results[match.away_club_id] = "D"

        # 각 클럽별 오늘자 누적 데이터 계산
        today_standings_data = []

        for club in clubs:
            # 어제자 순위 스냅샷 조회
            yesterday_standing = session.exec(
                select(DailyClubStanding)
                .where(DailyClubStanding.club_id == club.id)
                .where(DailyClubStanding.sim_day == sim_day - 1)
            ).first()

            # 어제 데이터가 없다면 초기화
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

            # 오늘 경기 결과 반영
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
            # 오늘 경기가 없었던 경우 streak 유지

            # 승률 계산 (KBO 방식: 승 / (승 + 패) 적용, 분모가 0이면 0.0)
            win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0

            # 임시 스냅샷 객체 정보 저장
            today_standings_data.append({
                "club_id": club.id,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "games_played": games_played,
                "streak": streak,
                "win_rate": win_rate,
                # 순위와 게임차는 정렬 후 확정
                "rank": 1,
                "games_back": 0
            })

        # 승률 및 승수 기준으로 내림차순 정렬하여 순위 배정
        today_standings_data.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)

        # 공동 순위 계산용 변수
        current_rank = 1
        for idx, item in enumerate(today_standings_data):
            if idx > 0:
                prev_item = today_standings_data[idx - 1]
                # 이전 구단과 승률 및 승수가 같으면 공동 순위 부여
                if item["win_rate"] == prev_item["win_rate"] and item["wins"] == prev_item["wins"]:
                    item["rank"] = prev_item["rank"]
                else:
                    item["rank"] = idx + 1
            else:
                item["rank"] = 1

        # 1위 팀의 승/패 정보 획득 (게임차 계산용)
        first_place = today_standings_data[0]
        wins_1st = first_place["wins"]
        losses_1st = first_place["losses"]

        # 최종 객체 빌드 및 세션 추가
        for item in today_standings_data:
            # 게임차 계산: 0.5 게임차 단위를 표현하기 위해 실제 게임차에 10을 곱한 정수값으로 저장합니다.
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
                batting_average=0.0, # 미구현 스탯 초기화
                era=0.0
            )
            session.add(standing_record)
