from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from src.models import League
from src.services.common import get_session

router = APIRouter(prefix="/leagues", tags=["Leagues"])

@router.get("", response_model=list[League])
def get_leagues(session: Session = Depends(get_session)):
    return session.exec(select(League)).all()

@router.get("/{league_id}", response_model=League)
def get_league(league_id: int, session: Session = Depends(get_session)):
    league = session.get(League, league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league
