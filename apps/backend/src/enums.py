from enum import StrEnum

class MatchStatus(StrEnum):
    """경기 상태"""
    SCHEDULED    = "SCHEDULED" # 예정
    IN_PROGRESS  = "IN_PROGRESS" # 진행중
    COMPLETED    = "COMPLETED" # 완료
    CANCELED     = "CANCELED" # 취소

class RosterStatus(StrEnum):
    """출전 가능 여부"""
    ACTIVE   = "ACTIVE" # 보통/정상 (출전 가능)
    INJURED  = "INJURED" # 부상 (출전 불가)
    OTHER    = "OTHER" # 기타 사유 (징계, 휴식 등 출전 불가)

class IngameRole(StrEnum):
    """게임 내 역할"""
    PITCHER            = "PITCHER" # 투수
    CATCHER            = "CATCHER" # 포수
    FIRST_BASE         = "FIRST_BASE" # 1루수
    SECOND_BASE        = "SECOND_BASE" # 2루수
    THIRD_BASE         = "THIRD_BASE" # 3루수
    SHORT_STOP         = "SHORT_STOP" # 유격수
    LEFT_FIELD         = "LEFT_FIELD" # 좌익수
    CENTER_FIELD       = "CENTER_FIELD" # 중견수
    RIGHT_FIELD        = "RIGHT_FIELD" # 우익수
    DESIGNATED_HITTER  = "DESIGNATED_HITTER" # 지명타자
    PINCH_HITTER       = "PINCH_HITTER" # 대타
    PINCH_RUNNER       = "PINCH_RUNNER" # 대주자

class IngameEventType(StrEnum):
    """게임 내 이벤트 타입"""
    NOTICE            = "NOTICE"            # 일반 안내/공지 (이닝 전광판, 텍스트 중계 등)
    GAME_STATE        = "GAME_STATE"        # 게임 상태 전이 (경기 시작/종료, 이닝 교대 등)
    BATTER_ENTER      = "BATTER_ENTER"      # 타자 타석 진입
    PITCH_START       = "PITCH_START"       # 투수 투구 동작 시작 (와인드업 등 애니메이션 시점)
    PITCH             = "PITCH"             # 투구 결과 판정 (스트라이크, 볼 등 배트 접촉이 없는 경우)
    BAT_CONTACT       = "BAT_CONTACT"       # 타격 접촉 발생 (파울, 인플레이 타구 형성 시점)
    FIELDING_ACTION   = "FIELDING_ACTION"   # 수비수의 타구 처리 (포구, 에러 등)
    THROW_ACTION      = "THROW_ACTION"      # 수비수/포수의 송구 (도루 저지 송구, 1루 송구 등)
    BASE_RUN_START    = "BASE_RUN_START"    # 주자의 진루/도루 시작 시점
    BASE_RUN_RESULT   = "BASE_RUN_RESULT"   # 주자의 베이스 세이프/아웃 최종 판정 시점


class IngameGameState(StrEnum):
    """인게임 경기 상태 흐름"""
    MATCH_START   = "MATCH_START"
    INNING_START  = "INNING_START"
    INNING_END    = "INNING_END"
    MATCH_END     = "MATCH_END"


class IngamePitchType(StrEnum):
    """투구 종류"""
    FASTBALL   = "FASTBALL"
    SLIDER     = "SLIDER"
    CURVEBALL  = "CURVEBALL"
    CHANGEUP   = "CHANGEUP"
    SINKER     = "SINKER"
    SPLITTER   = "SPLITTER"


class IngamePitchResult(StrEnum):
    """배트 비접촉 투구 결과"""
    STRIKE            = "STRIKE"
    BALL              = "BALL"
    HIT_BY_PITCH      = "HIT_BY_PITCH"
    WILD_PITCH        = "WILD_PITCH"
    INTENTIONAL_WALK  = "INTENTIONAL_WALK"


class IngameContactType(StrEnum):
    """배트 접촉 타격 타입"""
    CONTACT_IN_PLAY  = "CONTACT_IN_PLAY"
    FOUL             = "FOUL"
    BUNT             = "BUNT"


class IngameFieldingAction(StrEnum):
    """수비 액션 타입"""
    CATCH  = "CATCH"
    ERROR  = "ERROR"
    DROP   = "DROP"


class IngameBaseRunReason(StrEnum):
    """진루 시작 원인"""
    STEAL    = "STEAL"
    HIT_RUN  = "HIT_RUN"
    TAG_UP   = "TAG_UP"


class IngameBaseRunResult(StrEnum):
    """진루/도루 결과"""
    SAFE  = "SAFE"
    OUT   = "OUT"


