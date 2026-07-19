# uv run -m scripts.simulate_full_season
import datetime
import sys
import random
import yaml
from sqlmodel import Session, SQLModel, create_engine, select, asc

from settings import DATABASE_URL, CONFIG
from src.models import League, Club, Match, WorldState, DailyClubStanding, MatchPlaceholder
from src.enums import MatchStatus
from src.services.schedule_utils import (
    generate_regular_schedule,
    generate_krown_elite_schedule,
    generate_knockout_schedule,
    save_knockout_placeholders,
)
from src.services.ingame import run_match
from src.services.standing import update_daily_standings
from src.utils.logger import logger

engine = create_engine(DATABASE_URL)

def init_database():
    """데이터베이스 초기화 및 기본 메이저리그 4대 리그 정규시즌 일정 시딩"""
    logger.info("데이터베이스 초기화(Drop & Create) 및 초기 데이터 시딩을 시작합니다...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    logger.success("모든 테이블 초기화 완료")

    with open("./data/initial_leagues.yml", "r", encoding="utf-8") as f:
        initial_leagues_rawdata = yaml.safe_load(f)

    with Session(engine) as session:
        # 1. WorldState 초기화
        world_state = WorldState(id=1, current_sim_day=1)
        session.add(world_state)
        session.commit()

        for league_rawdata in initial_leagues_rawdata:
            league = League(
                name=league_rawdata["name"],
                name_ko=league_rawdata["name_ko"],
                mascot_ko=league_rawdata["mascot_ko"],
                league_code=league_rawdata["league_code"],
                lore=league_rawdata["lore"]
            )
            session.add(league)
            session.commit()
            session.refresh(league)

            league_clubs = []
            for club_rawdata in league_rawdata["clubs"]:
                club = Club(
                    name=club_rawdata["name"],
                    name_ko=club_rawdata["name_ko"],
                    hometown=club_rawdata["hometown"],
                    hometown_ko=club_rawdata["hometown_ko"],
                    team_code=club_rawdata["team_code"],
                    abbr_name=club_rawdata["abbr_name"],
                    stadium_name=club_rawdata["stadium_name"],
                    stadium_name_ko=club_rawdata["stadium_name_ko"],
                    league_id=league.id
                )
                session.add(club)
                league_clubs.append(club)

            session.commit()
            for c in league_clubs:
                session.refresh(c)

            # 정규리그 스케줄 및 초기 순위표 생성
            if len(league_clubs) == 10:
                matches = generate_regular_schedule(league_clubs, CONFIG.base_datetime.year, 1)
                for m in matches:
                    session.add(m)

                start_sim_day = min(m.sim_day for m in matches)
                standing_sim_day = start_sim_day - 1

                for club in league_clubs:
                    standing = DailyClubStanding(
                        sim_day=standing_sim_day,
                        league_id=league.id,
                        club_id=club.id,
                        rank=1,
                        win_rate=0.0,
                        games_back=0,
                        wins=0,
                        draws=0,
                        losses=0,
                        games_played=0,
                        streak=0,
                        batting_average=0.0,
                        era=0.0
                    )
                    session.add(standing)
                session.commit()
                logger.info(f"리그 '{league.name_ko}' 스케줄 및 초기화 완료")
        
        logger.success("데이터베이스 시딩 완료")

def run_regular_season() -> int:
    """정규시즌 일정에 맞춰 하루씩 시뮬레이션 완주"""
    logger.info("=========================================")
    logger.info("1단계: 정규시즌 시뮬레이션을 시작합니다.")
    logger.info("=========================================")

    with Session(engine) as session:
        # DB에 등록된 정규시즌 경기들의 최대 sim_day 동적 조회
        all_regular_days = session.exec(select(Match.sim_day)).all()
        max_regular_day = max(all_regular_days) if all_regular_days else 168
        logger.info(f"정규시즌 시뮬레이션 기간: Sim Day 1 ~ {max_regular_day}")

        for day in range(1, max_regular_day + 1):
            # 1. 해당 일자의 scheduled 경기 조회
            matches = session.exec(
                select(Match)
                .where(Match.sim_day == day)
                .where(Match.status == MatchStatus.SCHEDULED)
            ).all()

            # 2. 경기 시뮬레이션 진행
            if matches:
                for match in matches:
                    run_match(match)
                    session.add(match)

            # 3. 경기 종료 후 순위표 갱신
            update_daily_standings(session, day)

            # 4. 가상 시계 갱신 및 커밋
            world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
            if world_state is None:
                raise RuntimeError("Record for WorldState with id=1 not found.")

            world_state.current_sim_day = day + 1
            session.add(world_state)
            session.commit()

            if day % 20 == 0 or day == max_regular_day:
                logger.info(f"[Sim Day {day}] 정규리그 진행 중... (완료)")

    logger.success(f"정규시즌 {max_regular_day}일 일정이 성공적으로 완료되었습니다.")
    return max_regular_day

def select_playoff_teams(max_regular_day: int):
    """정규시즌 최종 순위를 토대로 16개 포스트시즌 구단 추출 및 개최지 리그 선정"""
    logger.info("=========================================")
    logger.info("2단계: 포스트시즌 진출팀 선별 및 개최지(Host Region) 결정")
    logger.info("=========================================")

    with Session(engine) as session:
        leagues = session.exec(select(League)).all()
        playoff_teams = []
        league_win_sums = {}

        for league in leagues:
            # 정규리그 최종 순위 기준 1~4위 구단 조회
            standings = session.exec(
                select(DailyClubStanding)
                .where(DailyClubStanding.league_id == league.id)
                .where(DailyClubStanding.sim_day == max_regular_day)
                .order_by(asc(DailyClubStanding.rank))
            ).all()

            top_4_standings = standings[:4]
            top_4_clubs = []
            win_sum = 0.0

            for std in top_4_standings:
                club = session.get(Club, std.club_id)
                if club is None:
                    raise RuntimeError(f"Club with id={std.club_id} not found.")
                top_4_clubs.append(club)
                win_sum += std.win_rate
                playoff_teams.append(club)

            league_win_sums[league.id] = win_sum
            logger.info(
                f"[{league.name_ko} 진출팀]: "
                f"1위 {top_4_clubs[0].name_ko} ({top_4_standings[0].win_rate:.3f}) | "
                f"2위 {top_4_clubs[1].name_ko} ({top_4_standings[1].win_rate:.3f}) | "
                f"3위 {top_4_clubs[2].name_ko} ({top_4_standings[2].win_rate:.3f}) | "
                f"4위 {top_4_clubs[3].name_ko} ({top_4_standings[3].win_rate:.3f})"
            )

        # 개최 리그 선정 (초대 대회이므로 정규시즌 진출팀 승률 합산 우위 기준)
        host_league_id = max(league_win_sums, key=lambda k: league_win_sums[k])
        host_league = session.get(League, host_league_id)
        if host_league is None:
            raise RuntimeError(f"League with id={host_league_id} not found.")
        
        logger.success(
            f"포스트시즌 집중 개최 리그(Host Region)로 "
            f"'{host_league.name_ko}'(승률 합: {league_win_sums[host_league_id]:.3f})가 선정되었습니다."
        )

        return playoff_teams

def run_krown_elite_league(playoff_clubs, max_regular_day: int) -> tuple[list[Club], int]:
    """크라운 정예리그 30경기 일정 생성 및 시뮬레이션 진행 (sim_day max_regular_day + 4 ➔ )"""
    logger.info("=========================================")
    logger.info("3단계: 크라운 정예리그 (Krown Elite League) 진행")
    logger.info("=========================================")

    # 1. sim_day를 정규시즌 종료일 + 4일 휴식 후 시작하도록 오프셋 계산
    start_offset = max_regular_day + 4
    start_day = start_offset + 1
    
    # 2. 정예리그 더블 라운드 로빈 스케줄 생성 (시작일 전달)
    matches = generate_krown_elite_schedule(playoff_clubs, start_day)
    end_day = max(m.sim_day for m in matches) if matches else start_day
    
    with Session(engine) as session:
        for match in matches:
            session.add(match)
        session.commit()
        logger.info(f"정예리그 {len(matches)}경기 일정 적재 완료 (Sim Day {start_day} -> {end_day})")

        # 3. 30일 동안 하루씩 시뮬레이션
        for day in range(start_day, end_day + 1):
            day_matches = session.exec(
                select(Match)
                .where(Match.sim_day == day)
                .where(Match.status == MatchStatus.SCHEDULED)
            ).all()

            for match in day_matches:
                run_match(match)
                session.add(match)

            world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
            if world_state is None:
                raise RuntimeError("Record for WorldState with id=1 not found.")
            
            world_state.current_sim_day = day + 1
            session.add(world_state)
            session.commit()

            if (day - start_offset) % 10 == 0 or day == end_day:
                logger.info(f"[정예리그] {day - start_offset}일차 경기 완료 (Sim Day {day})")

        logger.success("크라운 정예리그 30일(240경기) 일정이 모두 마감되었습니다.")

        # 4. 정예리그 최종 성적 정산 및 상위 8개 시드 추출
        team_stats = {c.id: {"club": c, "wins": 0, "losses": 0, "draws": 0} for c in playoff_clubs}
        elite_matches = session.exec(
            select(Match)
            .where(Match.sim_day >= start_day)
            .where(Match.sim_day <= end_day)
        ).all()

        for m in elite_matches:
            home_score = m.home_score if m.home_score is not None else 0
            away_score = m.away_score if m.away_score is not None else 0
            if home_score > away_score:
                team_stats[m.home_club_id]["wins"] += 1
                team_stats[m.away_club_id]["losses"] += 1
            elif home_score < away_score:
                team_stats[m.home_club_id]["losses"] += 1
                team_stats[m.away_club_id]["wins"] += 1
            else:
                team_stats[m.home_club_id]["draws"] += 1
                team_stats[m.away_club_id]["draws"] += 1

        # 승률 계산
        ranking_list = []
        for cid, stat in team_stats.items():
            wins = stat["wins"]
            losses = stat["losses"]
            draws = stat["draws"]
            win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0
            ranking_list.append({
                "club": stat["club"],
                "wins": wins,
                "losses": losses,
                "draws": draws,
                "win_rate": win_rate
            })

        # 승률 -> 승리 수 내림차순 정렬
        ranking_list.sort(key=lambda x: (x["win_rate"], x["wins"]), reverse=True)

        logger.info("\n--- [정예리그 최종 순위표] ---")
        for rank, item in enumerate(ranking_list, 1):
            club = item["club"]
            logger.info(
                f"{rank:02d}위: {club.name_ko:<10} | "
                f"{item['wins']}승 {item['draws']}무 {item['losses']}패 | "
                f"승률: {item['win_rate']:.3f}"
            )

        top_8_clubs = [item["club"] for item in ranking_list[:8]]
        logger.success("정예리그 상위 8개 팀이 확정되어 토너먼트 시드가 배정되었습니다.")
        return top_8_clubs, end_day

def run_knockout_stage(top_8_clubs, elite_end_day: int):
    """토너먼트 스테이지(8강 Bo3 1승선취, 4강 Bo5, 결승 Bo7) 시뮬레이션 진행"""
    logger.info("=========================================")
    logger.info("4단계: 녹아웃 토너먼트 (Knockout Stage) 진행")
    logger.info("=========================================")

    # 1. 8강 대진 플레이스홀더 생성 및 DB 저장
    placeholders = generate_knockout_schedule(top_8_clubs, elite_end_day + 1)
    with Session(engine) as session:
        saved_placeholders = save_knockout_placeholders(session, placeholders)
        session.commit()
        placeholders = session.exec(select(MatchPlaceholder)).all()

    q_nodes = sorted([p for p in placeholders if p.round == "ROUND_OF_8"], key=lambda x: x.id)
    s_nodes = sorted([p for p in placeholders if p.round == "SEMI_FINAL"], key=lambda x: x.id)
    f_node = [p for p in placeholders if p.round == "FINAL"][0]

    q_winners = {} # q_node.id: winner_club_id

    # 1. 8강 1차전 (Day = elite_end_day + 2) - 동시 진행
    day1 = elite_end_day + 2
    logger.info(">>> 8강전 1차전 시작 (4개 매치 동시 진행)")
    with Session(engine) as session:
        for idx, q in enumerate(q_nodes):
            home_club_id = q.home_club_id
            away_club_id = q.away_club_id
            if home_club_id is None or away_club_id is None:
                raise RuntimeError("Knockout matchup does not have assigned clubs.")

            home_club = session.get(Club, home_club_id)
            away_club = session.get(Club, away_club_id)
            
            m1 = Match(
                home_club_id=home_club_id,
                away_club_id=away_club_id,
                sim_day=day1,
                status=MatchStatus.SCHEDULED,
                limit_extra_innings=False
            )
            run_match(m1)
            session.add(m1)
            session.flush()

            q.actual_match_id = m1.id
            session.add(q)
            session.commit()

            home_score = m1.home_score if m1.home_score is not None else 0
            away_score = m1.away_score if m1.away_score is not None else 0
            if home_score > away_score:
                q_winners[idx] = home_club_id
                logger.info(
                    f"  [8강 1차전] {home_club.name_ko} 2승 선취 진출! "
                    f"({home_score}:{away_score} 승)"
                )
            else:
                logger.info(
                    f"  [8강 1차전] {away_club.name_ko} 승리하며 타이 형성! "
                    f"({home_score}:{away_score} 패)"
                )

        # 2. 8강 2차전 (Day = elite_end_day + 3) - 타이 매치 동시 진행
        day2 = day1 + 1
        logger.info("\n>>> 8강전 2차전 시작 (타이 매치 동시 진행)")
        for idx, q in enumerate(q_nodes):
            if idx in q_winners:
                continue

            home_club_id = q.home_club_id
            away_club_id = q.away_club_id
            
            m2 = Match(
                home_club_id=home_club_id,
                away_club_id=away_club_id,
                sim_day=day2,
                status=MatchStatus.SCHEDULED,
                limit_extra_innings=False
            )
            run_match(m2)
            session.add(m2)
            session.commit()

            home_score = m2.home_score if m2.home_score is not None else 0
            away_score = m2.away_score if m2.away_score is not None else 0
            if home_score > away_score:
                q_winners[idx] = home_club_id
                logger.info(
                    f"  [8강 2차전] {session.get(Club, home_club_id).name_ko} 최종 2승 1패 진출! "
                    f"({home_score}:{away_score} 승)"
                )
            else:
                q_winners[idx] = away_club_id
                logger.info(
                    f"  [8강 2차전] {session.get(Club, away_club_id).name_ko} 대역전 2승 1패 진출! "
                    f"({home_score}:{away_score} 패)"
                )

        db_s1 = session.get(MatchPlaceholder, s_nodes[0].id)
        db_s2 = session.get(MatchPlaceholder, s_nodes[1].id)
        def get_higher_seed(c1_id, c2_id):
            idx1 = [c.id for c in top_8_clubs].index(c1_id)
            idx2 = [c.id for c in top_8_clubs].index(c2_id)
            return (c1_id, c2_id) if idx1 < idx2 else (c2_id, c1_id)

        s1_home, s1_away = get_higher_seed(q_winners[0], q_winners[1])
        s2_home, s2_away = get_higher_seed(q_winners[2], q_winners[3])
        db_s1.home_club_id = s1_home
        db_s1.away_club_id = s1_away
        db_s2.home_club_id = s2_home
        db_s2.away_club_id = s2_away
        session.commit()
        logger.success("8강 종료 및 4강 대진 확정")

    # 4강전 시뮬레이션
    logger.info("\n>>> 4강전 시뮬레이션 시작 (Bo5 동시 진행, 2일 경기 후 1일 휴식)")
    semi_start_day = day2 + 2
    
    with Session(engine) as session:
        db_s1, db_s2 = session.get(MatchPlaceholder, s_nodes[0].id), session.get(MatchPlaceholder, s_nodes[1].id)
        s1_home_club, s1_away_club = session.get(Club, db_s1.home_club_id), session.get(Club, db_s1.away_club_id)
        s2_home_club, s2_away_club = session.get(Club, db_s2.home_club_id), session.get(Club, db_s2.away_club_id)
        s1_wins, s1_losses, s2_wins, s2_losses = 0, 0, 0, 0
        semi_offsets = {1: 0, 2: 1, 3: 3, 4: 4, 5: 6}
        semi_end_day = semi_start_day

        for game_num in range(1, 6):
            if (s1_wins == 3 or s1_losses == 3) and (s2_wins == 3 or s2_losses == 3): break
            sim_day = semi_start_day + semi_offsets[game_num]
            semi_end_day = sim_day
            for i, (win, loss, home, away, h_club, a_club, h_id, a_id) in enumerate([
                [s1_wins, s1_losses, s1_home_club, s1_away_club, s1_home_club, s1_away_club, db_s1.home_club_id, db_s1.away_club_id],
                [s2_wins, s2_losses, s2_home_club, s2_away_club, s2_home_club, s2_away_club, db_s2.home_club_id, db_s2.away_club_id]
            ]):
                if (win == 3 or loss == 3): continue
                is_home = game_num in [1, 2, 5]
                m = Match(
                    home_club_id=(h_id if is_home else a_id),
                    away_club_id=(a_id if is_home else h_id),
                    sim_day=sim_day,
                    status=MatchStatus.SCHEDULED,
                    limit_extra_innings=False
                )
                run_match(m); session.add(m); session.flush()
                if (m.home_score > m.away_score if is_home else m.away_score > m.home_score):
                    if i == 0: s1_wins += 1 
                    else: s2_wins += 1
                else:
                    if i == 0: s1_losses += 1
                    else: s2_losses += 1
                logger.info(f"  [4강 {i+1}경기] {game_num}차전: {(h_club if is_home else a_club).name_ko} vs {(a_club if is_home else h_club).name_ko}")
            session.commit()
        
        db_f = session.get(MatchPlaceholder, f_node.id)
        def get_higher_seed(c1_id, c2_id):
            idx1 = [c.id for c in top_8_clubs].index(c1_id)
            idx2 = [c.id for c in top_8_clubs].index(c2_id)
            return (c1_id, c2_id) if idx1 < idx2 else (c2_id, c1_id)
        f_home, f_away = get_higher_seed((db_s1.home_club_id if s1_wins == 3 else db_s1.away_club_id), (db_s2.home_club_id if s2_wins == 3 else db_s2.away_club_id))
        db_f.home_club_id, db_f.away_club_id = f_home, f_away
        session.commit()

    logger.info("\n>>> 결승전(Krown Series) 시뮬레이션 시작 (Bo7, 3일 경기 후 1일 휴식)")
    final_start_day = semi_end_day + 2
    with Session(engine) as session:
        db_f = session.get(MatchPlaceholder, f_node.id)
        if db_f is None:
            raise RuntimeError("Final placeholder not found.")
        home_id = db_f.home_club_id
        away_id = db_f.away_club_id
        if home_id is None or away_id is None:
            raise RuntimeError("Final teams are not fully assigned.")
        home_club = session.get(Club, home_id)
        away_club = session.get(Club, away_id)
        if home_club is None or away_club is None:
            raise RuntimeError("Final clubs not found in DB.")

        home_wins = 0
        away_wins = 0
        final_offsets = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5, 6: 6, 7: 8}
        final_end_day = final_start_day

        for game_num in range(1, 8):
            if home_wins == 4 or away_wins == 4:
                break
                
            is_home_game = game_num in [1, 2, 3, 7]
            actual_home = home_id if is_home_game else away_id
            actual_away = away_id if is_home_game else home_id
            
            actual_home_club = home_club if is_home_game else away_club
            actual_away_club = away_club if is_home_game else home_club
            
            sim_day = final_start_day + final_offsets[game_num]
            final_end_day = sim_day

            m = Match(
                home_club_id=actual_home,
                away_club_id=actual_away,
                sim_day=sim_day,
                status=MatchStatus.SCHEDULED,
                limit_extra_innings=False
            )
            run_match(m)
            session.add(m)
            session.commit()
            
            # 승자 판정
            home_score = m.home_score if m.home_score is not None else 0
            away_score = m.away_score if m.away_score is not None else 0
            if home_score > away_score:
                winner_id = actual_home
            else:
                winner_id = actual_away
                
            if winner_id == home_id:
                home_wins += 1
            else:
                away_wins += 1
                
            logger.info(
                f"  [결승전] {game_num}차전: "
                f"{actual_home_club.name_ko} {home_score} vs "
                f"{actual_away_club.name_ko} {away_score} "
                f"({home_wins}W - {away_wins}L)"
            )
            
        final_winner = home_id if home_wins == 4 else away_id
        champion_club = home_club if final_winner == home_id else away_club
        
        # 세계관 가상 시계의 최종일 마감
        world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
        if world_state is None:
            raise RuntimeError("Record for WorldState with id=1 not found.")
        
        world_state.current_sim_day = final_end_day + 1
        session.add(world_state)
        session.commit()
        
        logger.info("=========================================")
        logger.success(f"*** KLB 2026시즌 최종 챔피언 등극: [{champion_club.name_ko}] ***")
        logger.info("=========================================")

def main():
    init_database()
    max_reg_day = run_regular_season()
    playoff_clubs = select_playoff_teams(max_reg_day)
    top_8_clubs, elite_end_day = run_krown_elite_league(playoff_clubs, max_reg_day)
    run_knockout_stage(top_8_clubs, elite_end_day)

if __name__ == "__main__":
    main()
