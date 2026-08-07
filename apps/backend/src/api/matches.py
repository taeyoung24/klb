import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, asc, SQLModel
from sqlalchemy.orm import defer
from src.models import Match, Club, IngameInstructionLog, IngameScoreboard, MatchPlaceholder, MatchLineup
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


class MatchLineupResponse(SQLModel):
    away_lineup: list[MatchLineup]
    home_lineup: list[MatchLineup]


@router.get("/{match_id}/lineup", response_model=MatchLineupResponse)
def get_match_lineup(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    lineups = session.exec(
        select(MatchLineup).where(MatchLineup.match_id == match_id)
    ).all()

    away_lineup = [l for l in lineups if l.club_id == match.away_club_id]
    home_lineup = [l for l in lineups if l.club_id == match.home_club_id]

    # DB에 MatchLineup이 없는 경우 fallback (동적 추출/생성)
    if not away_lineup or not home_lineup:
        from src.services.ingame.lineup import select_team_roster_for_match
        away_sp, _, away_batters = select_team_roster_for_match(match.away_club_id, session=session)
        home_sp, _, home_batters = select_team_roster_for_match(match.home_club_id, session=session)

        if not away_lineup:
            away_lineup = [
                MatchLineup(match_id=match_id, club_id=match.away_club_id, player_id=away_sp.id, position=away_sp.position, batting_order=None, is_starter=True)
            ] + [
                MatchLineup(match_id=match_id, club_id=match.away_club_id, player_id=b.id, position=b.position, batting_order=idx, is_starter=True)
                for idx, b in enumerate(away_batters, 1)
            ]

        if not home_lineup:
            home_lineup = [
                MatchLineup(match_id=match_id, club_id=match.home_club_id, player_id=home_sp.id, position=home_sp.position, batting_order=None, is_starter=True)
            ] + [
                MatchLineup(match_id=match_id, club_id=match.home_club_id, player_id=b.id, position=b.position, batting_order=idx, is_starter=True)
                for idx, b in enumerate(home_batters, 1)
            ]

    # 타순 정렬 (투수 -> 타자 1~9번)
    def sort_key(l: MatchLineup):
        return l.batting_order if l.batting_order is not None else 0

    away_lineup.sort(key=sort_key)
    home_lineup.sort(key=sort_key)

    return MatchLineupResponse(
        away_lineup=away_lineup,
        home_lineup=home_lineup
    )
