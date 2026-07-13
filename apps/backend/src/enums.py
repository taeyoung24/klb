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
