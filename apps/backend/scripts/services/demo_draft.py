# uv run -m scripts.services.demo_draft
import random
from sqlmodel import Session, SQLModel, create_engine, select

from settings import CONFIG
from src.models import League, Club, Region, HighSchool, PlayerTransactionHistory
from src.services.generation_utils import generate_high_school, generate_player
from src.services.draft import run_all_rookie_drafts
from src.utils.logger import logger

# 데모 실행용 인메모리 데이터베이스 엔진 생성
engine = create_engine("sqlite:///:memory:")


def setup_demo_environment(session: Session):
    """데모 드래프트를 위한 테스트 유니버스(리그 2개, 구단 20개, 고등학교 10개) 환경 구축"""
    logger.info("드래프트 데모용 인메모리 환경 구축 중...")

    # 1. 지역 및 고등학교 10개 생성
    region = Region(name="Metropolis", name_ko="메트로폴리스")
    session.add(region)
    session.commit()
    session.refresh(region)

    high_schools = []
    for _ in range(10):
        hs = generate_high_school(region_id=region.id)
        session.add(hs)
        high_schools.append(hs)

    session.commit()
    for hs in high_schools:
        session.refresh(hs)

    # 2. 리그 2개 및 구단 20개 생성
    for l_idx in range(1, 3):
        league = League(
            name=f"League {l_idx}",
            name_ko=f"리그 {l_idx}",
            mascot_ko=f"마스코트{l_idx}",
            league_code=f"L{l_idx}"
        )
        session.add(league)
        session.commit()
        session.refresh(league)

        for c_idx in range(1, 11):
            club = Club(
                name=f"Team {l_idx}-{c_idx}",
                name_ko=f"구단 {l_idx}-{c_idx}",
                hometown="Metropolis",
                hometown_ko="메트로폴리스",
                team_code=f"T{l_idx}{c_idx}",
                abbr_name=f"T.{l_idx}{c_idx}",
                stadium_name="Demo Stadium",
                stadium_name_ko="데모 스타디움",
                league_id=league.id,
                region_id=region.id
            )
            session.add(club)
            session.commit()
            session.refresh(club)

            # 초기 로스터 32명 시딩
            for _ in range(CONFIG.roster_player_count):
                hs = random.choice(high_schools)
                p = generate_player(
                    region_id=hs.region_id,
                    high_school_id=hs.id,
                    club_id=club.id,
                    general=True
                )
                session.add(p)

        session.commit()

    logger.success("데모용 환경 구축 완료! (리그 2개, 구단 20개, 고등학교 10개 준비됨)")


def main():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        setup_demo_environment(session)

        logger.info("\n========================================================")
        logger.info("   [DRAFT] KLB 신인 드래프트 (Rookie Draft) 시뮬레이션 데모 시작")
        logger.info("========================================================\n")

        # 신인 드래프트 실행 (sim_day=270)
        run_all_rookie_drafts(session, year=CONFIG.base_datetime.year, sim_day=270)

        # DB 장부 적재 검증 및 결과 확인
        total_histories = list(session.exec(select(PlayerTransactionHistory)).all())
        draft_histories = [h for h in total_histories if h.transaction_type == "DRAFT"]

        logger.info("\n========================================================")
        logger.info(f"   [CHECK] 사무국 행정 장부(PlayerTransactionHistory) 적재 건수: 총 {len(draft_histories)}건 확인 완료!")
        logger.info("========================================================")

        for h in draft_histories[:5]:
            logger.info(f"  * 전체 {h.draft_overall_pick:02d}순위 ({h.draft_round}R) | 지명 기록: {h.details}")


if __name__ == "__main__":
    main()
