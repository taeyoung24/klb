from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func, asc
from settings import CONFIG
from src.models import DailyClubStanding, WorldState
from src.services.common import get_session
from src.services.date_utils import date_to_sim_day

router = APIRouter(prefix="/standings", tags=["Standings"])


@router.get("/latest", response_model=list[DailyClubStanding])
def get_latest_standings(
    year: Optional[int] = None,
    league_id: Optional[int] = None,
    is_postseason: bool = False,
    session: Session = Depends(get_session)
):
    """
    지정된 연도(기본값: 현재 시즌)의 가장 최신/최종 일차(max sim_day) 스냅샷 목록을 단일 쿼리로 반환합니다.
    league_id를 생략하면 해당 시즌의 모든 리그(또는 정예리그 전체) 스탠딩을 한 번에 반환합니다.
    """
    target_year = year if year is not None else CONFIG.base_datetime.year
    jan_1_sim_day = date_to_sim_day(f"{target_year}-01-01")
    dec_31_sim_day = date_to_sim_day(f"{target_year}-12-31")

    if league_id is not None:
        max_day_subquery = (
            select(func.max(DailyClubStanding.sim_day))
            .where(DailyClubStanding.league_id == league_id)
            .where(DailyClubStanding.is_postseason == is_postseason)
            .where(DailyClubStanding.sim_day >= jan_1_sim_day)
            .where(DailyClubStanding.sim_day <= dec_31_sim_day)
            .scalar_subquery()
        )
        query = (
            select(DailyClubStanding)
            .where(DailyClubStanding.league_id == league_id)
            .where(DailyClubStanding.is_postseason == is_postseason)
            .where(DailyClubStanding.sim_day == max_day_subquery)
            .order_by(asc(DailyClubStanding.rank))
        )
        return session.exec(query).all()

    # league_id가 미지정된 경우: 해당 연도의 is_postseason 조건 최신 sim_day 기준 전체 반환
    max_day_subquery = (
        select(func.max(DailyClubStanding.sim_day))
        .where(DailyClubStanding.is_postseason == is_postseason)
        .where(DailyClubStanding.sim_day >= jan_1_sim_day)
        .where(DailyClubStanding.sim_day <= dec_31_sim_day)
        .scalar_subquery()
    )
    query = (
        select(DailyClubStanding)
        .where(DailyClubStanding.is_postseason == is_postseason)
        .where(DailyClubStanding.sim_day == max_day_subquery)
        .order_by(asc(DailyClubStanding.league_id), asc(DailyClubStanding.rank))
    )
    return session.exec(query).all()


@router.get("", response_model=list[DailyClubStanding])
def get_standings(
    league_id: int,
    sim_day: Optional[int] = None,
    date: Optional[str] = None,
    is_postseason: bool = False,
    session: Session = Depends(get_session)
):
    """
    특정 일자/sim_day 시점(타임머신 조회)의 스탠딩 스냅샷을 단일 서브쿼리로 반환합니다.
    """
    if date is not None:
        sim_day = date_to_sim_day(date)
    elif sim_day is None:
        world_state = session.get(WorldState, 1)
        if world_state:
            sim_day = max(1, world_state.current_sim_day - 1)
        else:
            sim_day = 1

    max_day_subquery = (
        select(func.max(DailyClubStanding.sim_day))
        .where(DailyClubStanding.league_id == league_id)
        .where(DailyClubStanding.is_postseason == is_postseason)
        .where(DailyClubStanding.sim_day <= sim_day)
        .scalar_subquery()
    )

    query = (
        select(DailyClubStanding)
        .where(DailyClubStanding.league_id == league_id)
        .where(DailyClubStanding.is_postseason == is_postseason)
        .where(DailyClubStanding.sim_day == max_day_subquery)
        .order_by(asc(DailyClubStanding.rank))
    )
    return session.exec(query).all()
