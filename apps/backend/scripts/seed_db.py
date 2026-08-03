# uv run -m scripts.seed_db
from sqlmodel import Session, SQLModel, create_engine
import yaml

from settings import DATABASE_URL, CONFIG
from src.enums import IngameRole
from src.models import League, Club, Player, Stadium, WorldState, DailyClubStanding
from src.services.generation_utils import generate_player, generate_stadium
from src.services.schedule_utils import generate_regular_schedule
from src.utils.logger import logger

engine = create_engine(DATABASE_URL)

def main():
    SQLModel.metadata.drop_all(engine)
    logger.success("모든 테이블 삭제 완료 (Drop All)")

    SQLModel.metadata.create_all(engine)
    logger.success("모든 테이블 새로 생성 완료 (Create All)")

    with open("./data/initial_leagues.yml", "r", encoding="utf-8") as f:
        initial_leagues_rawdata = yaml.safe_load(f)

    with Session(engine) as session:
        # 1. 전역 가상 시계(WorldState) 초기화 (id=1, current_sim_day=1)
        world_state = WorldState(id=1, current_sim_day=1)
        session.add(world_state)
        session.commit()
        logger.info("WorldState 초기 레코드 등록 완료")

        for league_rawdata in initial_leagues_rawdata:
            league = League(
                name=league_rawdata["name"],
                name_ko=league_rawdata["name_ko"],
                mascot_ko=league_rawdata["mascot_ko"],
                league_code=league_rawdata["league_code"],
            )
            session.add(league)
            session.commit()
            session.refresh(league)

            league_clubs = []
            for club_rawdata in league_rawdata["clubs"]:
                stadium = generate_stadium(
                    name=club_rawdata["stadium_name"],
                    name_ko=club_rawdata["stadium_name_ko"]
                )
                session.add(stadium)
                session.commit()
                session.refresh(stadium)

                club = Club(
                    name=club_rawdata["name"], 
                    name_ko=club_rawdata["name_ko"],
                    hometown=club_rawdata["hometown"],
                    hometown_ko=club_rawdata["hometown_ko"],
                    team_code=club_rawdata["team_code"],
                    abbr_name=club_rawdata["abbr_name"],
                    stadium_name=club_rawdata["stadium_name"],
                    stadium_name_ko=club_rawdata["stadium_name_ko"],
                    league_id=league.id,
                    home_stadium_id=stadium.id
                )
                session.add(club)
                league_clubs.append(club)

            session.commit()
            
            # 클럽 ID를 생성받기 위해 세션 리프레시 진행 및 구단별 규격 선수단 시딩 (CONFIG.roster_player_count 명)
            # TODO: 시딩 시 등번호 중복 검증 없이 무작위로 할당 중. 구단 내 중복 방지 처리 로직 추가 필요 (26. 8. 3. Antigravity)
            roster_positions = (
                [IngameRole.PITCHER] * 14 +
                [IngameRole.CATCHER] * 2 +
                [IngameRole.FIRST_BASE] * 2 +
                [IngameRole.SECOND_BASE] * 2 +
                [IngameRole.THIRD_BASE] * 2 +
                [IngameRole.SHORT_STOP] * 2 +
                [IngameRole.LEFT_FIELD] * 2 +
                [IngameRole.CENTER_FIELD] * 2 +
                [IngameRole.RIGHT_FIELD] * 2 +
                [IngameRole.DESIGNATED_HITTER] * 2
            )
            assert len(roster_positions) == CONFIG.roster_player_count

            for c in league_clubs:
                session.refresh(c)
                for pos in roster_positions:
                    player = generate_player(
                        club_id=c.id,
                        position=pos,
                        general=True,
                        current_year=CONFIG.base_datetime.year
                    )
                    session.add(player)
            
            session.commit()
            logger.info(f"리그 '{league.name}' 소속 구단 선수 로스터(구단당 {CONFIG.roster_player_count}명) 데이터 생성 완료")

            # 리그 소속 구단이 10개인 경우 정규시즌 일정 및 초기 순위 데이터 적재
            if len(league_clubs) == 10:
                # 정규시즌 일정 생성
                matches = generate_regular_schedule(league_clubs, CONFIG.base_datetime.year, 1)
                for m in matches:
                    session.add(m)
                
                # 첫 경기 시작 sim_day 확인 및 전날 산출
                start_sim_day = min(m.sim_day for m in matches)
                standing_sim_day = start_sim_day - 1
                
                # 각 구단별 초기 순위(모두 공동 1위 타이) 데이터 생성
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
                logger.info(f"리그 '{league.name}'의 정규시즌 일정(720경기) 및 초기 순위표(sim_day={standing_sim_day}) 저장 완료")

            logger.info(f"리그 '{league.name}'과 소속 클럽 데이터 추가됨")
        
        logger.success("초기 시딩 데이터 적재 완료")

if __name__ == "__main__":
    main()