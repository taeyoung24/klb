from datetime import datetime
from typing import Any, Optional
from sqlmodel import SQLModel, Field, JSON, Relationship

from src.enums import (
    TurfType,
    IngameRole,
    RosterStatus,
)


class WorldState(SQLModel, table=True):
    """
    KLB 유니버스의 현재 가상 시계를 저장하는 전역 메타데이터 장부.
    데이터베이스 전체에 단 '1개의 행(id=1)'만 존재하며, 매일 이 행을 업데이트함.
    """
    id: int = Field(default=1, primary_key=True)
    current_sim_day: int = Field(default=1)


class League(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str
    mascot_ko: str
    league_code: str


class Stadium(SQLModel, table=True):
    """
    KLB 유니버스의 구장 메타데이터.
    코어 시뮬레이터의 물리 엔진(타구 궤적 연산, 홈런/펜스 판정)에 직접 관여함.
    """
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str
    
    # --- 환경 및 비즈니스 특성 ---
    is_dome: bool = Field(default=False)
    capacity: int = Field(ge=0)
    turf_type: TurfType = Field(default=TurfType.NATURAL)
    altitude: float = Field(default=0.0) # 해발 고도(m) - 공기 저항 및 비거리 계수
    
    # --- 기하학적 외야 모델링 (Parametric Design) ---
    fence_profile: list[dict[str, Any]] = Field(default=[], sa_type=JSON)
    
    # 곡률 계수 (0 = 폴리곤 직선 연결, 1 = 스플라인 곡선(부채꼴) 연결)
    curvature: float = Field(default=0.5, ge=0.0, le=1.0)

    # 1:N 역참조 (이 구장을 홈으로 쓰는 구단들)
    home_clubs: list["Club"] = Relationship(back_populates="home_stadium")


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
    home_stadium_id: Optional[int] = Field(default=None, foreign_key="stadium.id")
    home_stadium: Optional[Stadium] = Relationship(back_populates="home_clubs")
    players: list["Player"] = Relationship(back_populates="club")


class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    club_id: int = Field(foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="players")

    uniform_number: str = Field(...)

    speed: int        = Field(ge=1, le=1000)
    control: int      = Field(ge=1, le=1000)
    power: int        = Field(ge=1, le=1000)
    flexibility: int  = Field(ge=1, le=1000)
    focus: int        = Field(ge=1, le=1000)

    roster_status: RosterStatus
    position: IngameRole

    personality: list[int] = Field(sa_type=JSON)
    birthday: datetime
    height: float = Field(ge=0)
    weight: float = Field(ge=0)
