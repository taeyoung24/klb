# uv run -m scripts.seed_db
import random
from sqlmodel import Session, SQLModel, create_engine
import yaml

from settings import DATABASE_URL, CONFIG
from src.enums import IngameRole
from src.models import League, Club, Player, Stadium, WorldState, Region, HighSchool
from src.services.generation_utils import generate_player, generate_stadium, generate_high_school
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

        regions_by_name: dict[str, Region] = {}
        all_high_schools: list[HighSchool] = []
        league_high_schools_map: dict[int, list[HighSchool]] = {}
        all_clubs: list[Club] = []

        # Step 1: 모든 리그, 지역(Region), 고등학교(HighSchool), 구장(Stadium), 구단(Club) 생성 및 DB 적재
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

            league_high_schools_map[league.id] = []

            for club_rawdata in league_rawdata["clubs"]:
                ht_name = club_rawdata["hometown"]
                ht_name_ko = club_rawdata["hometown_ko"]

                # 연고지(Region) 생성 또는 조회
                if ht_name not in regions_by_name:
                    region = Region(name=ht_name, name_ko=ht_name_ko)
                    session.add(region)
                    session.commit()
                    session.refresh(region)
                    regions_by_name[ht_name] = region
                else:
                    region = regions_by_name[ht_name]

                # 고등학교 생성 (highschool_counts 수만큼 생성 및 region 연결)
                hs_count = club_rawdata["highschool_counts"]
                for _ in range(hs_count):
                    high_school = generate_high_school(region_id=region.id)
                    session.add(high_school)
                    session.commit()
                    session.refresh(high_school)

                    all_high_schools.append(high_school)
                    league_high_schools_map[league.id].append(high_school)

                # 구장(Stadium) 생성 및 region_id 연결
                stadium = generate_stadium(
                    name=club_rawdata["stadium_name"],
                    name_ko=club_rawdata["stadium_name_ko"],
                    region_id=region.id
                )
                session.add(stadium)
                session.commit()
                session.refresh(stadium)

                # 구단(Club) 생성 및 region_id, home_stadium_id 연결
                club = Club(
                    name=club_rawdata["name"],
                    name_ko=club_rawdata["name_ko"],
                    hometown=ht_name,
                    hometown_ko=ht_name_ko,
                    team_code=club_rawdata["team_code"],
                    abbr_name=club_rawdata["abbr_name"],
                    stadium_name=club_rawdata["stadium_name"],
                    stadium_name_ko=club_rawdata["stadium_name_ko"],
                    league_id=league.id,
                    home_stadium_id=stadium.id,
                    region_id=region.id
                )
                session.add(club)
                session.commit()
                session.refresh(club)

                all_clubs.append(club)

            logger.info(
                f"리그 '{league.name}' 데이터 적재 완료 "
                f"(소속 구단: {len(league_rawdata['clubs'])}개, 고등학교: {len(league_high_schools_map[league.id])}개)"
            )

        # Step 2: 구단별 규격 선수단 시딩 (CONFIG.roster_player_count 명)
        # 선수 출신 고등학교 할당 비율: 80% 단일 리그 내 고등학교, 20% 타 리그/외부 고등학교
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

        for c in all_clubs:
            league_hs_list = league_high_schools_map[c.league_id]

            for pos in roster_positions:
                # 80% 확률로 해당 리그 내 고등학교, 20% 확률로 전체/타 리그 고등학교 무작위 선택
                if random.random() < 0.8:
                    selected_hs = random.choice(league_hs_list)
                else:
                    selected_hs = random.choice(all_high_schools)

                player = generate_player(
                    club_id=c.id,
                    region_id=selected_hs.region_id,
                    high_school_id=selected_hs.id,
                    position=pos,
                    general=True,
                    current_year=CONFIG.base_datetime.year
                )
                session.add(player)

            session.commit()
            logger.info(f"구단 '{c.name_ko}' 선수 로스터({CONFIG.roster_player_count}명, 고교 출신 비율 8:2 적용) 적재 완료")

        total_players_count = len(all_clubs) * CONFIG.roster_player_count
        logger.success(
            f"모든 초기 시딩 데이터 적재 완료 "
            f"(리그 {len(initial_leagues_rawdata)}개, 지역 {len(regions_by_name)}개, "
            f"구단 {len(all_clubs)}개, 고등학교 {len(all_high_schools)}개, 선수 {total_players_count}명)"
        )


if __name__ == "__main__":
    main()