from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, desc, asc
from src.models import DailyClubStanding, WorldState
from src.services.common import get_session
from src.utils.date_utils import date_to_sim_day

router = APIRouter(prefix="/standings", tags=["Standings"])

@router.get("", response_model=list[DailyClubStanding])
def get_standings(
    league_id: int,
    sim_day: Optional[int] = None,
    date: Optional[str] = None,
    is_postseason: bool = False,
    session: Session = Depends(get_session)
):
    if date is not None:
        sim_day = date_to_sim_day(date)
    elif sim_day is None:
        world_state = session.get(WorldState, 1)
        if world_state:
            sim_day = max(1, world_state.current_sim_day - 1)
        else:
            sim_day = 1

    recent_day_query = select(DailyClubStanding.sim_day)\
        .where(DailyClubStanding.league_id == league_id)\
        .where(DailyClubStanding.is_postseason == is_postseason)\
        .where(DailyClubStanding.sim_day <= sim_day)\
        .order_by(desc(DailyClubStanding.sim_day))\
        .limit(1)
    
    target_day = session.exec(recent_day_query).first()
    if target_day is None:
        first_day_query = select(DailyClubStanding.sim_day)\
            .where(DailyClubStanding.league_id == league_id)\
            .where(DailyClubStanding.is_postseason == is_postseason)\
            .order_by(asc(DailyClubStanding.sim_day))\
            .limit(1)
        target_day = session.exec(first_day_query).first()

    if target_day is None:
        return []

    query = select(DailyClubStanding)\
        .where(DailyClubStanding.league_id == league_id)\
        .where(DailyClubStanding.is_postseason == is_postseason)\
        .where(DailyClubStanding.sim_day == target_day)\
        .order_by(asc(DailyClubStanding.rank))
        
    return session.exec(query).all()
