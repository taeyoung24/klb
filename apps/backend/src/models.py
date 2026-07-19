from datetime import datetime
from typing import Any, Optional, Annotated, Union, Literal
from sqlmodel import SQLModel, Field, JSON
from sqlalchemy import Column
from sqlalchemy.types import TypeDecorator

from .enums import (
    MatchStatus,
    IngameRole,
    RosterStatus,
    IngameEventType,
    IngameGameState,
    IngamePitchType,
    IngamePitchResult,
    IngameContactType,
    IngameFieldingAction,
    IngameBaseRunReason,
    IngameBaseRunResult,
)

class IngameInstructionLogType(TypeDecorator):
    """Pydantic IngameInstructionLog 모델을 데이터베이스 JSON 컬럼과 자동으로 매핑하는 커스텀 타입"""
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # 선언 순서 문제를 피하기 위해 globals()에서 IngameInstructionLog 조회
        model_cls = globals().get("IngameInstructionLog")
        if model_cls:
            return model_cls.model_validate(value)
        return value

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

    roster_status: RosterStatus
    position: IngameRole

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
    limit_extra_innings: bool = Field()
    
    # 경기 예정이거나 취소 상태일 때는 Null(None) 허용
    home_score: Optional[int] = Field(default=None)
    away_score: Optional[int] = Field(default=None)
    
    # 끝난 매치에 대한 raw 레벨 가공 JSON 인스트럭션 로그 (Data-Driven Playback)
    match_log_json: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    
    # 구조화된 인게임 로그 객체 컬럼 (Pydantic 모델 타입으로 자동 직렬화/역직렬화)
    match_log: Optional['IngameInstructionLog'] = Field(
        default=None,
        sa_column=Column(IngameInstructionLogType)
    )

class MatchPlaceholder(SQLModel, table=True):
    """
    토너먼트(녹아웃) 대진 스키마를 표현하는 플레이스홀더 테이블.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    round: str  # "ROUND_OF_8", "SEMI_FINAL", "FINAL"
    sim_day: int  # 경기가 치러질 예정 시뮬레이션 일자
    limit_extra_innings: bool = Field()
    
    # 8강처럼 최초 구단이 고정된 경우에만 값을 가짐
    home_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    away_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    
    # 대진 트리 상에서 이 노드의 홈/어웨이 팀의 승자가 결정될 이전 플레이스홀더 매치
    home_parent_id: Optional[int] = Field(default=None, foreign_key="matchplaceholder.id")
    away_parent_id: Optional[int] = Field(default=None, foreign_key="matchplaceholder.id")

    # 이 플레이스홀더를 통해 실제로 생성된 경기 ID (추적 용도)
    actual_match_id: Optional[int] = Field(default=None, foreign_key="match.id")



# ##### 인게임 인스트럭션 로그 모델부 시작
# 인스트럭션 로그는 db 릴레이션이 아닌 json 형태로 저장

class IngameEvent(SQLModel):
    event_type: IngameEventType
    sim_timestamp: float # 초 단위, 소수점 허용 (밀리초)


class IngameNoticeEvent(IngameEvent):
    event_type: Literal[IngameEventType.NOTICE] = IngameEventType.NOTICE
    message: str


class IngameGameStateEvent(IngameEvent):
    event_type: Literal[IngameEventType.GAME_STATE] = IngameEventType.GAME_STATE
    state_type: IngameGameState
    inning: int
    is_top: bool
    home_score: int
    away_score: int


class IngameBatterEnterEvent(IngameEvent):
    event_type: Literal[IngameEventType.BATTER_ENTER] = IngameEventType.BATTER_ENTER
    batter_id: int
    pitcher_id: int


class IngamePitchStartEvent(IngameEvent):
    event_type: Literal[IngameEventType.PITCH_START] = IngameEventType.PITCH_START
    pitcher_id: int
    pitch_type: IngamePitchType


class IngamePitchEvent(IngameEvent):
    event_type: Literal[IngameEventType.PITCH] = IngameEventType.PITCH
    pitcher_id: int
    batter_id: int
    result: IngamePitchResult


class IngameBatContactEvent(IngameEvent):
    event_type: Literal[IngameEventType.BAT_CONTACT] = IngameEventType.BAT_CONTACT
    batter_id: int
    contact_type: IngameContactType
    hit_velocity: float
    launch_angle: float


class IngameFieldingActionEvent(IngameEvent):
    event_type: Literal[IngameEventType.FIELDING_ACTION] = IngameEventType.FIELDING_ACTION
    fielder_id: int
    action_type: IngameFieldingAction


class IngameThrowActionEvent(IngameEvent):
    event_type: Literal[IngameEventType.THROW_ACTION] = IngameEventType.THROW_ACTION
    thrower_id: int
    receiver_id: int
    target_base: int
    is_successful: bool


class IngameBaseRunStartEvent(IngameEvent):
    event_type: Literal[IngameEventType.BASE_RUN_START] = IngameEventType.BASE_RUN_START
    runner_id: int
    start_base: int
    target_base: int
    reason: IngameBaseRunReason


class IngameBaseRunResultEvent(IngameEvent):
    event_type: Literal[IngameEventType.BASE_RUN_RESULT] = IngameEventType.BASE_RUN_RESULT
    runner_id: int
    target_base: int
    result: IngameBaseRunResult


# discriminator를 사용하여 event_type 값에 따라 올바른 자식 클래스로 자동 역직렬화되도록 지정합니다.
IngameEventConcrete = Annotated[
    Union[
        IngameNoticeEvent,
        IngameGameStateEvent,
        IngameBatterEnterEvent,
        IngamePitchStartEvent,
        IngamePitchEvent,
        IngameBatContactEvent,
        IngameFieldingActionEvent,
        IngameThrowActionEvent,
        IngameBaseRunStartEvent,
        IngameBaseRunResultEvent
    ],
    Field(discriminator="event_type")
]


class IngameInstructionLog(SQLModel):
    '''
    인게임 시뮬레이션의 전체 진행 과정을 기록한 인스트럭션 로그 모델.
    이 모델은 Match 모델의 match_log 컬럼에 JSON 형태로 저장되며, 시뮬레이션 재생 및 분석에 사용됨.
    더 많은 변수를 표현할 수 있고 현실적인 시뮬레이션을 위해 이벤트 기준 나열이 아닌 시간 기준(sim_timestamp)으로 정렬된 이벤트 시퀀스를 저장함.
    '''
    simulation_version: str
    logged_events: list[IngameEventConcrete]


