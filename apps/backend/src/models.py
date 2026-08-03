from datetime import datetime
from typing import Any, Optional, Annotated, Union, Literal
from sqlmodel import SQLModel, Field, JSON, Relationship
from sqlalchemy import Column
from sqlalchemy.types import TypeDecorator

from .enums import (
    TurfType,
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
    
class DailyClubStanding(SQLModel, table=True):
    """
    매일의 정규 시즌 및 포스트시즌(정예리그) 리그 순위 스냅샷 장부 (통합 단일 테이블).
    """
    id: int         = Field(default=None, primary_key=True)
    sim_day: int    = Field(index=True)
    league_id: int  = Field(foreign_key="league.id")
    club_id: int    = Field(foreign_key="club.id")
    is_postseason: bool = Field(default=False, index=True)
    
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
    stadium_id: Optional[int] = Field(default=None, foreign_key="stadium.id")
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

    stadium: Optional[Stadium] = Relationship()

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



# ##### 뉴스 소식 관련 모델부 시작

class NewsAgency(SQLModel, table=True):
    """
    뉴스 언론사/보도매체 정보를 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(index=True)
    description: str = Field(default="")
    lore: str = Field(default="")

    articles: list["Article"] = Relationship(back_populates="news_agency")


class Article(SQLModel, table=True):
    """
    리그 주요 뉴스, 경기 리뷰, 인터뷰, 하이라이트 소식을 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str
    category: str = Field(default="리뷰", index=True)
    sim_day: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    likes: int = Field(default=0)
    
    match_id: Optional[int] = Field(default=None, foreign_key="match.id")
    club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    image_url: Optional[str] = Field(default=None)

    # 뉴스사 외래키 및 관계
    news_agency_id: Optional[int] = Field(default=None, foreign_key="newsagency.id")
    news_agency: Optional[NewsAgency] = Relationship(back_populates="articles")

    # 기사 댓글 목록 관계
    comments: list["ArticleComment"] = Relationship(
        back_populates="article",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ArticleComment(SQLModel, table=True):
    """
    기사에 작성된 댓글 정보를 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id", index=True)
    author_name: str = Field(default="익명팬")
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    likes: int = Field(default=0)
    dislikes: int = Field(default=0)

    article: Article = Relationship(back_populates="comments")




# ##### 인게임 인스트럭션 로그 모델부 시작
# 인스트럭션 로그는 db 릴레이션이 아닌 json 형태로 저장

class IngameEvent(SQLModel):
    """
    시뮬레이션 타임라인을 구성하는 모든 인게임 이벤트의 최상위 기반 모델.
    """
    event_type: IngameEventType  # 이벤트의 구체적인 유형
    sim_timestamp: float  # 시뮬레이션 경과 시간 (초 단위, 밀리초 소수점 허용)


class IngameNoticeEvent(IngameEvent):
    """
    경기 중 시스템 안내, 전광판 공지, 주요 상황 알림 텍스트 이벤트.
    """
    event_type: Literal[IngameEventType.NOTICE] = IngameEventType.NOTICE
    message: str  # 전달할 알림/공지 메시지 텍스트


class IngameGameStateEvent(IngameEvent):
    """
    이닝 변경, 경기 시작/종료, 점수 변동 등 게임 전체 진행 상태의 변화를 기록하는 이벤트.
    """
    event_type: Literal[IngameEventType.GAME_STATE] = IngameEventType.GAME_STATE
    state_type: IngameGameState  # 진행 상태 유형 (시작, 이닝교대, 종료 등)
    inning: int  # 현재 진행 중인 이닝 (1이닝~)
    is_top: bool  # 초(Top)/말(Bottom) 여부 (True: 초/어웨이, False: 말/홈)
    home_score: int  # 홈팀 현재 누적 점수
    away_score: int  # 어웨이팀 현재 누적 점수


class IngameBatterEnterEvent(IngameEvent):
    """
    새로운 타자가 타석에 들어서고 투수와의 대결이 시작됨을 알리는 이벤트.
    """
    event_type: Literal[IngameEventType.BATTER_ENTER] = IngameEventType.BATTER_ENTER
    batter_id: int  # 타석에 들어선 타자의 선수 ID
    pitcher_id: int  # 마운드에 선 투수의 선수 ID


class IngamePitchStartEvent(IngameEvent):
    """
    투수가 와인드업/투구 동작을 시작하며 구종을 결정했음을 알리는 이벤트.
    """
    event_type: Literal[IngameEventType.PITCH_START] = IngameEventType.PITCH_START
    pitcher_id: int  # 투구 동작을 시작한 투수의 선수 ID
    pitch_type: IngamePitchType  # 던질 예정인 선택 구종 (직구, 슬라이더 등)


class IngamePitchEvent(IngameEvent):
    """
    투구가 포수 미트에 도달하거나 볼/스트라이크 등 판정 결과가 결정된 이벤트.
    """
    event_type: Literal[IngameEventType.PITCH] = IngameEventType.PITCH
    pitcher_id: int  # 투수 선수 ID
    batter_id: int  # 타자 선수 ID
    result: IngamePitchResult  # 투구 판정 결과 (스트라이크, 볼, 파울, 인플레이 등)


class IngameBatContactEvent(IngameEvent):
    """
    타자가 배트로 공을 맞혀 물리 타구가 발생했을 때의 기하학적 데이터 이벤트.
    """
    event_type: Literal[IngameEventType.BAT_CONTACT] = IngameEventType.BAT_CONTACT
    batter_id: int  # 타격을 한 타자의 선수 ID
    contact_type: IngameContactType  # 타구 임팩트 성질 (정타, 약한 타구 등)
    hit_velocity: float  # 타구 속도 (km/h)
    launch_angle: float  # 타구 발사 각도 (도)


class IngameFieldingActionEvent(IngameEvent):
    """
    수비수가 타구를 처리하거나 포구/다이빙 등의 수비 동작을 수행하는 이벤트.
    """
    event_type: Literal[IngameEventType.FIELDING_ACTION] = IngameEventType.FIELDING_ACTION
    fielder_id: int  # 수비 동작을 수행하는 수비수의 선수 ID
    action_type: IngameFieldingAction  # 수비 행위 유형 (땅볼포구, 뜬공포구, 다이빙 등)


class IngameThrowActionEvent(IngameEvent):
    """
    수비수가 아웃 또는 주자 견제를 위해 베이스로 공을 송구하는 이벤트.
    """
    event_type: Literal[IngameEventType.THROW_ACTION] = IngameEventType.THROW_ACTION
    thrower_id: int  # 송구한 수비수 선수 ID
    receiver_id: int  # 송구를 받는 야수/수비수 선수 ID
    target_base: int  # 송구 목표 베이스 번호 (1: 1루, 2: 2루, 3: 3루, 4: 홈)
    is_successful: bool  # 송구 성공 여부 (True: 정송구, False: 악송구/에러)


class IngameBaseRunStartEvent(IngameEvent):
    """
    주자가 다음 베이스로 진루, 도루, 또는 태그업 등을 위해 주루를 시작하는 이벤트.
    """
    event_type: Literal[IngameEventType.BASE_RUN_START] = IngameEventType.BASE_RUN_START
    runner_id: int  # 주자 선수 ID
    start_base: int  # 출발 베이스 (0: 타석/본루, 1: 1루, 2: 2루, 3: 3루)
    target_base: int  # 진루 목표 베이스 (1: 1루, 2: 2루, 3: 3루, 4: 홈)
    reason: IngameBaseRunReason  # 주루 시작 사유 (안타진루, 도루, 태그업 등)


class IngameBaseRunResultEvent(IngameEvent):
    """
    주자의 베이스 도달 및 아웃/세이프 최종 주루 판정 결과 이벤트.
    """
    event_type: Literal[IngameEventType.BASE_RUN_RESULT] = IngameEventType.BASE_RUN_RESULT
    runner_id: int  # 주자 선수 ID
    target_base: int  # 점령 시도한 목표 베이스 번호 (1~4)
    result: IngameBaseRunResult  # 주루 결과 (세이프, 태그아웃, 포스아웃 등)


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


class IngameScoreboard(SQLModel):
    current_inning: int
    is_top: bool
    balls: int
    strikes: int
    outs: int
    away_innings: list[int]
    away_r: int
    away_h: int
    away_e: int
    away_b: int
    home_innings: list[int]
    home_r: int
    home_h: int
    home_e: int
    home_b: int
