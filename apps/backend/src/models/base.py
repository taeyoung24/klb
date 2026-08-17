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


class Region(SQLModel, table=True):
    """
    지역/연고지 메타데이터 테이블.
    고등학교, 구장, 구단, 선수(출신지)와 1:N 관계를 가짐.
    """
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str

    high_schools: list["HighSchool"] = Relationship(back_populates="region")
    stadiums: list["Stadium"] = Relationship(back_populates="region")
    clubs: list["Club"] = Relationship(back_populates="region")
    players: list["Player"] = Relationship(back_populates="region")


class HighSchool(SQLModel, table=True):
    """
    고등학교 메타데이터 테이블.
    지역(Region)과 1:N 관계를 가짐.
    """
    id: int = Field(default=None, primary_key=True)
    name: str
    name_ko: str

    is_specialized: bool = Field(default=False) # 야구 전문고 여부 (True: 야구전문고, False: 일반고)
    capacity: int = Field(ge=0) # 최대 학생 수용량

    region_id: int = Field(foreign_key="region.id")
    region: Optional[Region] = Relationship(back_populates="high_schools")
    players: list["Player"] = Relationship(back_populates="high_school")


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

    # 1:N 역참조 (구장이 위치한 지역)
    region_id: int = Field(foreign_key="region.id")
    region: Optional[Region] = Relationship(back_populates="stadiums")


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

    # 1:N 역참조 (구단의 연고지 지역)
    region_id: int = Field(foreign_key="region.id")
    region: Optional[Region] = Relationship(back_populates="clubs")


class Player(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="players")

    uniform_number: str = Field(...)

    # 스탯은 고정 상수이며 대개 계수로 사용됨.
    speed: int        = Field(ge=1, le=1000) # 주력
    control: int      = Field(ge=1, le=1000) # 제구, 신체 제어 능력
    power: int        = Field(ge=1, le=1000) # 힘
    flexibility: int  = Field(ge=1, le=1000) # 유연성 (부상 관련)
    focus: int        = Field(ge=1, le=1000) # 집중력 (버프/디버프 계수)
    stamina: int      = Field(ge=1, le=1000) # 지구력 (체력 소진 억제)

    # 실시간 체력 및 최대 체력
    current_energy: int = Field(default=10000, ge=0) # 현재 체력/에너지 (경기 시뮬레이션 소진/회복)
    max_energy: int     = Field(default=10000, ge=1) # 최대 체력/에너지

    roster_status: RosterStatus
    position: IngameRole

    personality: list[int] = Field(sa_type=JSON)
    birthday: datetime
    height: float = Field(ge=0)
    weight: float = Field(ge=0)

    # 1:N 역참조 (선수의 출신 지역 및 출신 고등학교)
    region_id: int = Field(foreign_key="region.id") # 출생지
    region: Optional[Region] = Relationship(back_populates="players")

    high_school_id: int = Field(foreign_key="highschool.id") # 졸업 기준
    high_school: Optional[HighSchool] = Relationship(back_populates="players")
