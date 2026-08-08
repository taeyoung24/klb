import random
from typing import Any
from src.models import IngameContext, Player
from src.enums import (
    IngamePitchAction,
    IngameBattingStrategy,
    IngamePitchType,
    IngamePitchZone,
)
from .base import BaseDecisionEngine, PitchSelectionResult


class RuleBasedDecisionEngine(BaseDecisionEngine):
    """
    기본 확률 및 휴리스틱 룰에 기반하여 인게임 의사결정을 수행하는 판단 엔진.
    AI 신경망 모델이 적용되지 않거나 테스트 및 fallback 환경에서 기본으로 동작합니다.
    """

    def decide_pitch_action(self, context: IngameContext) -> IngamePitchAction:
        return IngamePitchAction.PITCH

    def decide_pitch_selection(self, context: IngameContext) -> PitchSelectionResult:
        pitch_type = random.choice(list(IngamePitchType))
        target_zone = random.choice(list(IngamePitchZone))
        return PitchSelectionResult(pitch_type=pitch_type, target_zone=target_zone)

    def decide_batting_strategy(self, context: IngameContext) -> IngameBattingStrategy:
        return IngameBattingStrategy.SWING_FULL

    def decide_swing_intent(self, context: IngameContext, pitch_info: PitchSelectionResult) -> bool:
        return random.random() < 0.6

    def decide_steal(self, context: IngameContext) -> bool:
        return False

    def decide_advance_base(self, context: IngameContext, runner: Player, hit_info: dict[str, Any]) -> int:
        return 1

    def decide_throw_target(self, context: IngameContext, fielder: Player, ball_trajectory: dict[str, Any]) -> int:
        return 1

    def decide_pitcher_change(self, context: IngameContext) -> Player | None:
        return None
