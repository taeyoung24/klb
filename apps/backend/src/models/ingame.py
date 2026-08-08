from typing import Annotated, Union, Literal, Optional
from sqlmodel import SQLModel, Field
from src.enums import (
    IngameEventType,
    IngameGameState,
    IngamePitchType,
    IngamePitchResult,
    IngameContactType,
    IngameFieldingAction,
    IngameBaseRunReason,
    IngameBaseRunResult,
)
from .base import Player, Stadium


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


class PitcherTracker:
    def __init__(self, pitcher: Player, is_starter: bool, team: str, entry_inning: int, entry_top: bool, away_score: int, home_score: int, on_base_count: int):
        self.pitcher = pitcher
        self.is_starter = is_starter
        self.team = team  # 'away' or 'home'
        self.entry_inning = entry_inning
        self.entry_top = entry_top
        self.entry_away_score = away_score
        self.entry_home_score = home_score
        self.entry_on_base = on_base_count
        self.outs_recorded: int = 0
        self.exit_inning: int | None = None
        self.exit_top: bool | None = None
        self.exit_away_score: int | None = None
        self.exit_home_score: int | None = None

    @property
    def entry_lead(self) -> int:
        if self.team == 'away':
            return self.entry_away_score - self.entry_home_score
        else:
            return self.entry_home_score - self.entry_away_score

    @property
    def exit_lead(self) -> int:
        if self.exit_away_score is None or self.exit_home_score is None:
            return self.entry_lead
        if self.team == 'away':
            return self.exit_away_score - self.exit_home_score
        else:
            return self.exit_home_score - self.exit_away_score


class IngameContext(SQLModel):
    """
    인게임 시뮬레이션 진행 전체 데이터 및 상태 캡슐화 컨텍스트 모델.
    전광판(Scoreboard), 루상 주자, 벤치/투수진 상태, 구장 환경 특성 등 
    시뮬레이션 로직 통제 및 인공신경망 입력 피처 파이프라인으로 직접 대입 가능.
    """
    model_config = {"arbitrary_types_allowed": True}

    match_id: int | None = None
    stadium_id: int | None = None

    stadium: Optional[Stadium] = None

    # 실시간 전광판 및 카운터 상태 (Scoreboard일원화)
    scoreboard: IngameScoreboard = Field(
        default_factory=lambda: IngameScoreboard(
            current_inning=1,
            is_top=True,
            balls=0,
            strikes=0,
            outs=0,
            away_innings=[],
            away_r=0,
            away_h=0,
            away_e=0,
            away_b=0,
            home_innings=[],
            home_r=0,
            home_h=0,
            home_e=0,
            home_b=0,
        )
    )

    # 이닝 및 타임스탬프
    inning: int = 1
    is_top: bool = True  # True: 초(어웨이), False: 말(홈)
    sim_timestamp: float = 0.0

    # 누적 점수
    away_score: int = 0
    home_score: int = 0

    # 루상 주자 상황 (1루, 2루, 3루 주자)
    runner_1b: Optional[Player] = None
    runner_2b: Optional[Player] = None
    runner_3b: Optional[Player] = None

    # 대결 선수 (현재 타석 타자 & 마운드 투수)
    current_batter: Optional[Player] = None
    current_pitcher: Optional[Player] = None

    # 팀별 라인업 및 타순 인덱스
    away_batters: list[Player] = Field(default_factory=list)
    home_batters: list[Player] = Field(default_factory=list)
    away_batter_idx: int = 0
    home_batter_idx: int = 0

    # 팀별 투수진 및 인덱스
    away_pitchers: list[Player] = Field(default_factory=list)
    home_pitchers: list[Player] = Field(default_factory=list)
    away_pitcher_idx: int = 0
    home_pitcher_idx: int = 0

    # 벤치 및 불펜 자원 (대타, 대주자, 구원 투수진)
    away_bench: list[Player] = Field(default_factory=list)
    home_bench: list[Player] = Field(default_factory=list)
    away_bullpen: list[Player] = Field(default_factory=list)
    home_bullpen: list[Player] = Field(default_factory=list)

    # 투수 기록 및 결승점/책임 투수 트래킹 데이터
    current_away_pitcher_log: Optional[PitcherTracker] = None
    current_home_pitcher_log: Optional[PitcherTracker] = None
    away_pitcher_logs: list[PitcherTracker] = Field(default_factory=list)
    home_pitcher_logs: list[PitcherTracker] = Field(default_factory=list)

    go_ahead_pitcher_away: Optional[PitcherTracker] = None
    go_ahead_pitcher_home: Optional[PitcherTracker] = None
    go_ahead_resp_pitcher_away: Optional[PitcherTracker] = None
    go_ahead_resp_pitcher_home: Optional[PitcherTracker] = None

    # 시뮬레이션 타임라인 로그 이벤트 대본
    logged_events: list[IngameEventConcrete] = Field(default_factory=list)
