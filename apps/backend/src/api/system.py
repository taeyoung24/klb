from fastapi import APIRouter, Depends
from sqlmodel import Session
from src.models import WorldState
from src.services.common import get_session
from src.services.standing import get_playoff_host_league
from settings import CONFIG
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional

class SystemInfo(BaseModel):
    season_year: int
    current_sim_day: int
    current_date: str
    host_league_id: Optional[int] = None
    host_league_name: Optional[str] = None
    host_league_name_ko: Optional[str] = None

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/season-year", response_model=int)
def get_season_year(session: Session = Depends(get_session)):
    world_state = session.get(WorldState, 1)
    current_sim_day = world_state.current_sim_day if world_state else 1
    current_date = CONFIG.base_datetime + timedelta(days=current_sim_day - 1)
    return current_date.year

@router.get("/info", response_model=SystemInfo)
def get_system_info(session: Session = Depends(get_session)):
    world_state = session.get(WorldState, 1)
    current_sim_day = world_state.current_sim_day if world_state else 1
    
    current_date = CONFIG.base_datetime + timedelta(days=current_sim_day - 1)
    
    host_league = get_playoff_host_league(session, max_regular_day=228)
    
    return SystemInfo(
        season_year=current_date.year,
        current_sim_day=current_sim_day,
        current_date=current_date.strftime("%Y-%m-%d"),
        host_league_id=host_league.id if host_league else None,
        host_league_name=host_league.name if host_league else None,
        host_league_name_ko=host_league.name_ko if host_league else None
    )
