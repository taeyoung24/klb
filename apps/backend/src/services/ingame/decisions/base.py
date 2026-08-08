from abc import ABC, abstractmethod
from typing import Any
from src.enums import (
    IngamePitchAction,
    IngameBattingStrategy,
)
from src.models import (
    IngameContext,
    Player,
    PitchSelectionResult,
)


class BaseDecisionEngine(ABC):
    """
    인게임 시뮬레이션의 모든 의사결정(투수, 타자, 주자, 야수, 감독)을 위한 추상 판단 인터페이스.
    기본 룰베이스 구현체 및 AI 신경망(RL Policy) 추론 구현체의 공통 기반 클래스 역할을 수행합니다.
    """

    @abstractmethod
    def decide_pitch_action(self, context: IngameContext) -> IngamePitchAction:
        """투수의 행위 판단 (투구 vs 견제)"""
        pass

    @abstractmethod
    def decide_pitch_selection(self, context: IngameContext) -> PitchSelectionResult:
        """투수의 구종 및 투구 코스/존 선택 판단"""
        pass

    @abstractmethod
    def decide_batting_strategy(self, context: IngameContext) -> IngameBattingStrategy:
        """타자의 타석 전략 판단 (강공 / 번트 / 웨이팅 / 히트앤런)"""
        pass

    @abstractmethod
    def decide_swing_intent(self, context: IngameContext, pitch_info: PitchSelectionResult) -> bool:
        """들어오는 투구를 보고 타자의 스윙 여부 판단"""
        pass

    @abstractmethod
    def decide_steal(self, context: IngameContext) -> bool:
        """주자의 도루 시도 여부 판단"""
        pass

    @abstractmethod
    def decide_advance_base(self, context: IngameContext, runner: Player, hit_info: dict[str, Any]) -> int:
        """인플레이 타구/뜬공 발생 시 주자의 추가 진루 목표 베이스(1~4) 판단"""
        pass

    @abstractmethod
    def decide_throw_target(self, context: IngameContext, fielder: Player, ball_trajectory: dict[str, Any]) -> int:
        """포구 후 수비 야수의 송구 목표 베이스(1~4) 판단"""
        pass

    @abstractmethod
    def decide_pitcher_change(self, context: IngameContext) -> Player | None:
        """감독의 투수 교체 판단 및 교체 투수 선택"""
        pass
