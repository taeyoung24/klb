from enum import StrEnum

class TurfType(StrEnum):
    """구장 잔디 종류"""
    NATURAL     = "NATURAL"    # 천연잔디
    ARTIFICIAL  = "ARTIFICIAL" # 인조잔디
    HYBRID      = "HYBRID"     # 하이브리드 잔디

class MatchStatus(StrEnum):
    """경기 상태"""
    SCHEDULED    = "SCHEDULED" # 예정
    IN_PROGRESS  = "IN_PROGRESS" # 진행중
    COMPLETED    = "COMPLETED" # 완료
    CANCELED     = "CANCELED" # 취소

class MatchStage(StrEnum):
    """경기 진행 단계/종류"""
    REGULAR     = "REGULAR"      # 정규시즌
    TIEBREAKER  = "TIEBREAKER"   # 정규시즌 동률 타이브레이크
    INTERLEAGUE = "INTERLEAGUE"  # 인터리그
    ELITE       = "ELITE"        # 크라운 정예리그
    KNOCKOUT    = "KNOCKOUT"     # 녹아웃 토너먼트 (포스트시즌 8강/4강/결승)

class RosterStatus(StrEnum):
    """출전 가능 여부"""
    ACTIVE   = "ACTIVE" # 보통/정상 (출전 가능)
    INJURED  = "INJURED" # 부상 (출전 불가)
    OTHER    = "OTHER" # 기타 사유 (징계, 휴식 등 출전 불가)

class PlayerTransactionType(StrEnum):
    """선수 계약, 지명 및 이적 트랜잭션 종류"""
    DRAFT          = "DRAFT"          # 공식 신인 드래프트 지명
    UNDRAFTED_SIGN = "UNDRAFTED_SIGN" # 드래프트 미지명 육성선수 입단
    TRADE          = "TRADE"          # 구단 간 트레이드
    FA             = "FA"             # 자유계약선수(FA) 계약
    RELEASE        = "RELEASE"        # 방출 / 계약 해지
    WAIVER         = "WAIVER"         # 웨이버 공시 및 영입
    RETIRE         = "RETIRE"         # 선수 은퇴

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
    """투구 결과"""
    STRIKE            = "STRIKE"
    STRIKE_SWINGING   = "STRIKE_SWINGING"
    BALL              = "BALL"
    FOUL              = "FOUL"
    IN_PLAY           = "IN_PLAY"
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
    FLY_CATCH     = "FLY_CATCH"     # 공중 뜬공 포구 (플라이 아웃)
    GROUND_CATCH  = "GROUND_CATCH"  # 지면 바운드 타구 포구
    CATCH         = "CATCH"         # 일반 포구
    ERROR         = "ERROR"         # 수비 실책
    DROP          = "DROP"          # 포구 실패 / 낙구


class IngameBaseRunReason(StrEnum):
    """진루 시작 원인"""
    STEAL         = "STEAL"          # 도루 시도
    HIT_RUN       = "HIT_RUN"        # 안타/인플레이 타구 진루
    HOMERUN       = "HOMERUN"        # 홈런 진루
    WALK          = "WALK"           # 볼넷 강제 진루
    HIT_BY_PITCH  = "HIT_BY_PITCH"   # 사구 강제 진루
    ERROR         = "ERROR"          # 수비 실책으로 인한 진루
    WILD_PITCH    = "WILD_PITCH"     # 폭투/낫아웃 진루
    TAG_UP        = "TAG_UP"         # 뜬공 포구 후 태그업 진루


class IngameBaseRunResult(StrEnum):
    """진루/도루 결과"""
    SAFE  = "SAFE"
    OUT   = "OUT"


class IngamePitchAction(StrEnum):
    """투수 행위 결정"""
    PITCH    = "PITCH"     # 마운드 투구
    PICK_OFF = "PICK_OFF"  # 견제구 투구


class IngameBattingStrategy(StrEnum):
    """타자 타석 전략 결정"""
    SWING_FULL  = "SWING_FULL"   # 강공 스윙
    BUNT        = "BUNT"         # 기습 번트
    TAKE        = "TAKE"         # 웨이팅 (투구 지켜보기)
    HIT_AND_RUN = "HIT_AND_RUN"  # 히트앤런


class IngamePitchZone(StrEnum):
    """투수 투구 목표 코스/존"""
    ZONE_CENTER       = "ZONE_CENTER"        # 중앙 스트라이크
    ZONE_HIGH_INSIDE  = "ZONE_HIGH_INSIDE"   # 높은 몸쪽 스트라이크
    ZONE_HIGH_OUTSIDE = "ZONE_HIGH_OUTSIDE"  # 높은 바깥쪽 스트라이크
    ZONE_LOW_INSIDE   = "ZONE_LOW_INSIDE"    # 낮은 몸쪽 스트라이크
    ZONE_LOW_OUTSIDE  = "ZONE_LOW_OUTSIDE"   # 낮은 바깥쪽 스트라이크
    BALL_HIGH         = "BALL_HIGH"          # 유인구 (높은 볼)
    BALL_LOW          = "BALL_LOW"           # 유인구 (낮은 볼)
    BALL_INSIDE       = "BALL_INSIDE"        # 유인구 (몸쪽 볼)
    BALL_OUTSIDE      = "BALL_OUTSIDE"       # 유인구 (바깥쪽 볼)



