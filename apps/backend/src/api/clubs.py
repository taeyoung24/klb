from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from src.models import Club
from src.services.common import get_session

router = APIRouter(prefix="/clubs", tags=["Clubs"])

@router.get("", response_model=list[Club])
def get_clubs(league_id: Optional[int] = None, session: Session = Depends(get_session)):
    query = select(Club)
    if league_id is not None:
        query = query.where(Club.league_id == league_id)
    return session.exec(query).all()

@router.get("/{club_id}", response_model=Club)
def get_club(club_id: int, session: Session = Depends(get_session)):
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club
