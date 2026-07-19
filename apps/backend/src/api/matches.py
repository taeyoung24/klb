from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, asc
from sqlalchemy.orm import defer
from src.models import Match, Club
from src.services.common import get_session

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("", response_model=list[Match])
def get_matches(
    league_id: Optional[int] = None,
    club_id: Optional[int] = None,
    sim_day: Optional[int] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Match).options(
        defer(Match.match_log),  # type: ignore
        defer(Match.match_log_json)  # type: ignore
    )
    
    if club_id is not None:
        query = query.where((Match.home_club_id == club_id) | (Match.away_club_id == club_id))
        
    if league_id is not None:
        query = query.join(Club, onclause=(Match.home_club_id == Club.id)).where(Club.league_id == league_id) # type: ignore
        
    if sim_day is not None:
        query = query.where(Match.sim_day == sim_day)
        
    if status is not None:
        query = query.where(Match.status == status)
        
    query = query.order_by(asc(Match.sim_day), asc(Match.home_club_id))
    return session.exec(query).all()
