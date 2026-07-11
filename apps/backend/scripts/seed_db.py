from sqlmodel import Session, SQLModel, create_engine
import yaml

from settings import DATABASE_URL
from src.models import League, Club, Player
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
        for league_rawdata in initial_leagues_rawdata:
            league = League(name=league_rawdata["name"])
            session.add(league)
            session.commit()
            session.refresh(league)

            for club_rawdata in league_rawdata["clubs"]:
                club = Club(name=club_rawdata["name"], league_id=league.id)
                session.add(club)

            session.commit()
            session.refresh(club)
            logger.info(f"리그 '{league.name}'과 소속 클럽 데이터 추가됨")
        
        logger.success("초기 시딩 데이터 적재 완료")

if __name__ == "__main__":
    main()
    