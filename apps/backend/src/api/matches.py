import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, asc
from sqlalchemy.orm import defer
from src.models import Match, Club, IngameInstructionLog, IngameScoreboard, MatchPlaceholder
from src.services.common import get_session
from src.services.ingame.main import get_scoreboard

router = APIRouter(prefix="/matches", tags=["Matches"])

@router.get("/placeholders", response_model=list[MatchPlaceholder])
def get_match_placeholders(
    session: Session = Depends(get_session)
):
    query = select(MatchPlaceholder).order_by(asc(MatchPlaceholder.id))
    return session.exec(query).all()

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

@router.get("/{match_id}", response_model=Match)
def get_match(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # match_log_json이 없고 match_log가 존재하는 경우 match_log_json으로 딕셔너리 매핑
    if match.match_log_json is None and match.match_log is not None:
        try:
            if hasattr(match.match_log, "model_dump"):
                match.match_log_json = match.match_log.model_dump()
            elif hasattr(match.match_log, "dict"):
                match.match_log_json = match.match_log.dict()
        except Exception:
            pass
            
    return match

@router.get("/{match_id}/scoreboard", response_model=IngameScoreboard)
def get_match_scoreboard(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.match_log:
        return get_scoreboard(match.match_log)
    elif match.match_log_json:
        try:
            if isinstance(match.match_log_json, str):
                log_data = json.loads(match.match_log_json)
            else:
                log_data = match.match_log_json
            match_log = IngameInstructionLog.model_validate(log_data)
            return get_scoreboard(match_log)
        except Exception:
            pass

    away_r = match.away_score if match.away_score is not None else 0
    home_r = match.home_score if match.home_score is not None else 0

    return IngameScoreboard(
        current_inning=9 if match.status == "COMPLETED" else 1,
        is_top=False if match.status == "COMPLETED" else True,
        balls=0,
        strikes=0,
        outs=3 if match.status == "COMPLETED" else 0,
        away_innings=[0] * 9,
        away_r=away_r,
        away_h=9 if match.status == "COMPLETED" else 0,
        away_e=0,
        away_b=4 if match.status == "COMPLETED" else 0,
        home_innings=[0] * 9,
        home_r=home_r,
        home_h=6 if match.status == "COMPLETED" else 0,
        home_e=1 if match.status == "COMPLETED" else 0,
        home_b=3 if match.status == "COMPLETED" else 0,
    )
