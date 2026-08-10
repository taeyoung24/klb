import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from src.models import League, Club, Region, HighSchool, Player, PlayerTransactionHistory
from src.enums import IngameRole, PlayerTransactionType
from src.services.generation_utils import generate_high_school, generate_player
from src.services.draft import run_league_rookie_draft, run_all_rookie_drafts


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 테스트용 리그 1개, 구단 10개, 지역 1개, 고등학교 2개 생성
        league = League(name="Test League", name_ko="테스트 리그", mascot_ko="마스코트", league_code="TL")
        session.add(league)
        session.commit()
        session.refresh(league)

        region = Region(name="TestRegion", name_ko="테스트지역")
        session.add(region)
        session.commit()
        session.refresh(region)

        hs1 = generate_high_school(region_id=region.id)
        hs2 = generate_high_school(region_id=region.id)
        session.add(hs1)
        session.add(hs2)
        session.commit()
        session.refresh(hs1)
        session.refresh(hs2)

        clubs = []
        for i in range(10):
            club = Club(
                name=f"Club{i}",
                name_ko=f"구단{i}",
                hometown="TestRegion",
                hometown_ko="테스트지역",
                team_code=f"C0{i}",
                abbr_name=f"C.{i}",
                stadium_name="TestStadium",
                stadium_name_ko="테스트구장",
                league_id=league.id,
                region_id=region.id
            )
            session.add(club)
            clubs.append(club)
        session.commit()

        yield session


def test_rookie_draft_execution(db_session: Session):
    league = db_session.exec(select(League)).first()
    assert league is not None

    # 드래프트 실행 (2026년, sim_day=270)
    result = run_league_rookie_draft(db_session, league_id=league.id, year=2026, sim_day=270)

    assert result["league_id"] == league.id
    assert result["total_rounds"] > 0
    assert result["total_picks"] > 0

    # 지명된 선수들의 Transaction History 적재 검증
    histories = list(db_session.exec(
        select(PlayerTransactionHistory)
        .where(PlayerTransactionHistory.transaction_type == PlayerTransactionType.DRAFT)
    ).all())

    assert len(histories) == result["total_picks"]
    first_pick = histories[0]
    assert first_pick.draft_overall_pick == 1
    assert first_pick.draft_round == 1
    assert first_pick.to_club_id is not None
