import pytest
import datetime
from src.services.season_calendar import get_first_monday_of_october, get_season_calendar_events
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


def test_get_first_monday_of_october():
    # 2026년 10월 1일은 목요일 -> 10월 1일이 속한 주의 월요일은 2026-09-28
    # 2026년 10월 1일이 목요일(weekday=3)이므로 첫번째 목요일 = 10월 1일. 
    # 해당 주의 월요일 = 2026-09-28.
    monday_2026 = get_first_monday_of_october(2026)
    assert monday_2026 == datetime.date(2026, 9, 28)

    # 2027년 10월: 10월 1일은 금요일.첫번째 목요일은 10월 7일 -> 그 주의 월요일은 10월 4일
    monday_2027 = get_first_monday_of_october(2027)
    assert monday_2027 == datetime.date(2027, 10, 4)


def test_calendar_events_schema():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        events = get_season_calendar_events(session, 2026)
        assert len(events) >= 1
        # 신인 드래프트 이벤트가 포함되어 있는지 확인
        draft_events = [e for e in events if e.label == "신인 드래프트"]
        assert len(draft_events) == 1
        assert draft_events[0].date == "2026-09-28"
