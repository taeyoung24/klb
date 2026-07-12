from datetime import datetime
from typing import Any, Optional
from sqlmodel import SQLModel, Field, JSON

from .enums import MatchStatus, RosterStatus 

class League(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str
    mascot_ko: str
    league_code: str
    lore: str

class Club(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str
    hometown: str
    hometown_ko: str
    team_code: str
    abbr_name: str
    stadium_name: str
    stadium_name_ko: str

    league_id: int = Field(foreign_key="league.id")

class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    club_id: int = Field(foreign_key="club.id")

    speed: int        = Field(ge=1, le=1000)
    control: int      = Field(ge=1, le=1000)
    power: int        = Field(ge=1, le=1000)
    flexibility: int  = Field(ge=1, le=1000)
    focus: int        = Field(ge=1, le=1000)

    roster_status: RosterStatus = Field(default=RosterStatus.ACTIVE)

    personality: list[int] = Field(sa_type=JSON)
    birthday: datetime
    height: float = Field(ge=0)
    weight: float = Field(ge=0)
    
class DailyClubStanding(SQLModel, table=True):
    """
    매일의 정규 시즌 리그 순위 스냅샷 장부 (통합 단일 테이블).
    """
    id: int         = Field(default=None, primary_key=True)
    sim_day: int    = Field(index=True)
    league_id: int  = Field(foreign_key="league.id")
    club_id: int    = Field(foreign_key="club.id")
    
    rank: int
    win_rate: float
    games_back: int
    wins: int
    draws: int
    losses: int
    games_played: int
    streak: int
    batting_average: float
    era: float

class Match(SQLModel, table=True):
    """
    매치 일정과 결과를 모두 포괄하는 통합 매치 장부.
    시즌 시작 시 SCHEDULED로 생성되고, 시뮬레이션 종료 시 COMPLETED로 전환
    """
    id: int              = Field(default=None, primary_key=True)
    away_club_id: int    = Field(foreign_key="club.id")
    home_club_id: int    = Field(foreign_key="club.id")
    sim_day: int         = Field(index=True)
    status: MatchStatus  = Field(default=MatchStatus.SCHEDULED, index=True)
    
    # 경기 예정이거나 취소 상태일 때는 Null(None) 허용
    home_score: Optional[int] = Field(default=None)
    away_score: Optional[int] = Field(default=None)
    
    # 끝난 매치에 대한 raw 레벨 가공 JSON 인스트럭션 로그 (Data-Driven Playback)
    match_log_json: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
