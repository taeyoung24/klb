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
