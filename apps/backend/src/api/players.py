from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from src.models import Player
from src.services.common import get_session

router = APIRouter(prefix="/players", tags=["Players"])

@router.get("", response_model=list[Player])
def get_players(
    club_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    query = select(Player)
    if club_id is not None:
        query = query.where(Player.club_id == club_id)
    return session.exec(query).all()
