import random
from typing import Any
from src.models import IngameContext, Player
from src.enums import (
    IngamePitchAction,
    IngameBattingStrategy,
    IngamePitchType,
    IngamePitchZone,
    IngameRole,
)
from ..physics import FieldingPhysicsResult, calculate_baserunning_physics
from .base import BaseDecisionEngine, PitchSelectionResult






class RuleBasedDecisionEngine(BaseDecisionEngine):
    """
    기본 확률 및 휴리스틱 룰에 기반하여 인게임 의사결정을 수행하는 판단 엔진.
    AI 신경망 모델이 적용되지 않거나 테스트 및 fallback 환경에서 기본으로 동작합니다.
    """

    def decide_pitch_action(self, context: IngameContext) -> IngamePitchAction:
        """
        투수의 행위 (마운드 투구 vs 견제구) 룰베이스 판단.
        - 루상 주자(1루, 2루)가 존재하고 아웃카운트가 2아웃 미만일 때 약 12% 확률로 견제구 선택.
        """
        has_runners = (context.runner_1b is not None or context.runner_2b is not None)
        if has_runners and context.scoreboard.outs < 2:
            if random.random() < 0.12:
                return IngamePitchAction.PICK_OFF
        return IngamePitchAction.PITCH

    def decide_pitch_selection(self, context: IngameContext) -> PitchSelectionResult:
        """
        투수의 구종 및 투구 코스/존 선택 룰베이스 판단.
        - 볼카운트(볼/스트라이크) 및 상황에 따른 구종 및 코스 확률 분포 배칭.
        - 2스트라이크(투수 유리): 유인구 코스(BALL_LOW, BALL_OUTSIDE 등) 및 변화구 비율 증가.
        - 3볼(타자 유리): 스트라이크존(ZONE_CENTER, 모서리 코스) 집중.
        """
        strikes = context.scoreboard.strikes
        balls = context.scoreboard.balls

        # 1. 구종 선택 (카운트에 따른 변화구/직구 비율 조정)
        pitch_types = [
            IngamePitchType.FASTBALL,
            IngamePitchType.SLIDER,
            IngamePitchType.CURVEBALL,
            IngamePitchType.CHANGEUP,
            IngamePitchType.SINKER,
            IngamePitchType.SPLITTER,
        ]
        
        if strikes == 2:
            # 2스트라이크 결정구 상황: 변화구 및 꺾이는 구종 비율 증가
            weights = [35, 25, 10, 15, 5, 10]
        else:
            # 일반 상황: 직구(카운트 잡기) 비중 중심
            weights = [50, 20, 10, 10, 5, 5]

        chosen_pitch = random.choices(pitch_types, weights=weights, k=1)[0]

        # 2. 코스/존 선택 (볼카운트 상황 반영)
        zones = [
            IngamePitchZone.ZONE_CENTER,
            IngamePitchZone.ZONE_HIGH_INSIDE,
            IngamePitchZone.ZONE_HIGH_OUTSIDE,
            IngamePitchZone.ZONE_LOW_INSIDE,
            IngamePitchZone.ZONE_LOW_OUTSIDE,
            IngamePitchZone.BALL_HIGH,
            IngamePitchZone.BALL_LOW,
            IngamePitchZone.BALL_INSIDE,
            IngamePitchZone.BALL_OUTSIDE,
        ]

        if strikes == 2:
            # 2스트라이크: 유인구(볼존) 선택 비율 60% 이상으로 상승
            zone_weights = [10, 5, 5, 10, 10, 15, 25, 5, 15]
        elif balls == 3:
            # 3볼: 스트라이크 존 집중 투구 85%
            zone_weights = [35, 15, 15, 10, 10, 5, 5, 2, 3]
        else:
            # 일반 카운트 상황: 존 내부 80%, 볼존 20%
            zone_weights = [20, 10, 10, 15, 15, 8, 12, 5, 5]



        chosen_zone = random.choices(zones, weights=zone_weights, k=1)[0]

        return PitchSelectionResult(pitch_type=chosen_pitch, target_zone=chosen_zone)


    def decide_batting_strategy(self, context: IngameContext) -> IngameBattingStrategy:
        """
        타자의 타석 전략 룰베이스 판단.
        - 3볼 0스트라이크: 약 80% 확률로 볼 지켜보기(TAKE)
        - 노아웃/1아웃 주자 1루 상황: 약 15% 번트(BUNT) 또는 히트앤런(HIT_AND_RUN)
        - 일반 상황: 강공 스윙(SWING_FULL)
        """
        balls = context.scoreboard.balls
        strikes = context.scoreboard.strikes
        outs = context.scoreboard.outs

        if balls == 3 and strikes == 0:
            if random.random() < 0.80:
                return IngameBattingStrategy.TAKE

        if outs < 2 and context.runner_1b is not None and context.runner_2b is None:
            r = random.random()
            if r < 0.10:
                return IngameBattingStrategy.BUNT
            elif r < 0.20:
                return IngameBattingStrategy.HIT_AND_RUN

        return IngameBattingStrategy.SWING_FULL

    def decide_swing_intent(self, context: IngameContext, pitch_info: PitchSelectionResult) -> bool:
        """
        들어오는 투구 정보(코스/존)와 볼카운트, 타자 선구안을 바탕으로 스윙 여부 룰베이스 판단.
        - 스트라이크 존 투구: 80~90% 스윙 시도
        - 유인구(볼존): 2스트라이크 상황에는 45% 커트 스윙, 3볼 Situation에서는 스윙 참기(5% 미만)
        """
        strikes = context.scoreboard.strikes
        balls = context.scoreboard.balls
        is_strike_zone = pitch_info.target_zone.value.startswith("ZONE_")

        if is_strike_zone:
            # 스트라이크 존 공: 높음/중앙 여부 따라 높은 스윙 비율
            return random.random() < 0.85
        else:
            # 볼존 유인구 공 참기 비율 강화 (볼넷 생성 향상)
            if strikes == 2:
                # 2스트라이크 불리한 카운트: 유인구 커트 스윙 (28% 스윙)
                return random.random() < 0.28
            elif balls == 3:
                # 3볼: 볼 참기 (3% 스윙)
                return random.random() < 0.03
            else:
                # 일반 카운트 볼존: 참기 (10% 스윙)
                return random.random() < 0.10


    def decide_steal(self, context: IngameContext) -> bool:
        """
        주자의 도루 시도 여부 룰베이스 판단.
        - 1루 주자가 존재하고 2루가 비어있으며, 주자의 주력(speed)이 650 이상인 경우 주력에 비례하여 도루 시도.
        """
        if context.runner_1b is not None and context.runner_2b is None and context.scoreboard.outs < 2:
            runner_speed = context.runner_1b.speed
            if runner_speed >= 650:
                steal_prob = (runner_speed - 650) / 1500.0  # 0.0 ~ 0.23 범위
                return random.random() < steal_prob

        return False

    def decide_advance_base(self, context: IngameContext, runner: Player, hit_info: dict[str, Any]) -> int:
        """
        인플레이 타구 발생 시 주자의 추가 진루 목표 베이스(1~4) 룰베이스 판단.
        """
        advance_bases = hit_info.get("advance_bases", 1)
        # 기본적으로 타구 득점 및 진루 루틴 연산 기반 목표 베이스 반환
        return advance_bases

    def decide_throw_target(self, context: IngameContext, fielder: Player, ball_trajectory: dict[str, Any]) -> int:
        """
        수비 야수의 포구 후 송구 목표 베이스(1: 1루, 2: 2루, 3: 3루, 4: 홈) 룰베이스 판단.
        - 3루 주자 태그업/홈 진루 시 4루(홈) 송구
        - 내야 땅볼 일반 상황 시 1루 송구
        """
        is_fly_ball = ball_trajectory.get("is_fly", False)
        if is_fly_ball and context.runner_3b is not None:
            return 4  # 홈 송구
        
        if context.runner_1b is not None and context.scoreboard.outs < 2:
            return 2  # 2루 병살/포스아웃 송구
            
        return 1  # 기본 1루 송구

    def decide_pitcher_change(self, context: IngameContext) -> Player | None:
        """
        감독의 수비 투수 교체 룰베이스 고도화 판단.
        
        [고도화 판단 전략]
        1. 경기 종반 마무리/셋업 투입 (9회 3점차 이하 리드/동점 시 마무리 투수 전격 등판)
        2. 이닝/아웃수 기반 제한 (선발 5이닝/15아웃 이상, 구원투수 1이닝/3아웃 이상 완료 시 교체)
        3. 득점권 위기 관리 (득점권 주자 출루 시 불펜 교체 검토)
        """
        is_top = context.is_top
        pitchers = context.home_pitchers if is_top else context.away_pitchers
        p_idx = context.home_pitcher_idx if is_top else context.away_pitcher_idx
        current_log = context.current_home_pitcher_log if is_top else context.current_away_pitcher_log

        if not current_log or p_idx >= len(pitchers) - 1:
            return None

        def_score = context.home_score if is_top else context.away_score
        off_score = context.away_score if is_top else context.home_score
        lead_margin = def_score - off_score

        is_starter = current_log.is_starter
        outs_recorded = current_log.outs_recorded

        should_change = False

        # 조건 1: 9회 이상 경기 종반 세이브/마무리 상황 (3점차 이하 리드 또는 동점)
        if context.inning >= 9 and 0 <= lead_margin <= 3 and outs_recorded >= 3:
            should_change = True
        # 조건 2: 현재 투수 체력 고갈 (current_energy 3000 이하)
        elif current_log.pitcher and current_log.pitcher.current_energy < 3000:
            should_change = True
        # 조건 3: 선발 투수(Starter)의 5이닝(15아웃) 투구 완료 시점
        elif is_starter and outs_recorded >= 15:
            should_change = True
        # 조건 4: 구원 투수(Reliever)의 1이닝(3아웃) 이상 투구 완료 시점
        elif not is_starter and outs_recorded >= 3:
            should_change = True
        # 조건 5: 득점권 위기 (2,3루 주자 출루 시 릴리프 교체 검토)
        elif (context.runner_2b is not None or context.runner_3b is not None) and context.scoreboard.outs < 2 and outs_recorded >= 9:
            should_change = True

        if should_change:
            # 9회 이상 리드 상황에서는 불펜의 마지막 세이브/마무리(Closer) 투수 투입
            if context.inning >= 9 and lead_margin > 0:
                return pitchers[-1]
            
            # 일반 계투 교체 상황: 다음 순번 불펜 투수 반환
            return pitchers[p_idx + 1]

        return None

    def decide_baserunning_target_base(
        self,
        context: IngameContext,
        runner: Player,
        fielding_physics: FieldingPhysicsResult,
    ) -> int:
        """
        타격 이후 주자/타자의 2루타 도전 여부 의사결정 룰베이스 판단 (추후 인공신경망 NN 모델로 대체될 판단 엔진 영역).
        - 공중 포구 아웃 판정이거나 수비 도달시간이 없으면 안전하게 1루 진루.
        - 주자의 2루 도달 시간 vs 수비 야수의 2루 송구 완류시간(throw_time_sec)을 실시간 비교하여 2루타 도전 결정.
        """
        if fielding_physics is None or fielding_physics.is_caught_in_air:
            return 1

        est_2b_result = calculate_baserunning_physics(runner, start_base=0, target_base=2, fielding_physics=fielding_physics)

        if est_2b_result.safe_margin_sec > -0.3:
            return 2
        return 1

    def decide_starting_pitcher(self, pitchers: list[Player]) -> Player:
        """
        투수들 중 선발 투수를 선택합니다.
        (기본 룰베이스 전략: 제구력 + 구속 종합 능력치가 가장 높은 투수 선택)
        """
        return max(pitchers, key=lambda p: p.control + p.speed)

    def decide_batting_order(self, batters: list[Player]) -> list[Player]:
        """
        야수/타자들 중 9명의 선발 라인업 및 타순을 결정합니다.
        (기본 룰베이스 전략: 각 주요 포지션별 최고 능력치 선수 1명씩 우선 배치 후 타순 배치)
        """
        target_positions = [
            IngameRole.CATCHER,
            IngameRole.FIRST_BASE,
            IngameRole.SECOND_BASE,
            IngameRole.THIRD_BASE,
            IngameRole.SHORT_STOP,
            IngameRole.LEFT_FIELD,
            IngameRole.CENTER_FIELD,
            IngameRole.RIGHT_FIELD,
            IngameRole.DESIGNATED_HITTER,
        ]

        selected_batters: list[Player] = []
        used_player_ids = set()

        # 1. 각 포지션별 가장 능력이 뛰어난 선수 1명씩 우선 배치
        for pos in target_positions:
            candidates = [
                p for p in batters
                if p.position == pos and p.id not in used_player_ids
            ]
            if candidates:
                best_player = max(candidates, key=lambda p: p.power + p.speed + p.focus)
                selected_batters.append(best_player)
                if best_player.id:
                    used_player_ids.add(best_player.id)

        # 2. 남은 자리가 있다면 남은 타자 중 종합 능력치순으로 채움
        remaining = [p for p in batters if p.id not in used_player_ids]
        remaining.sort(key=lambda p: p.power + p.speed + p.focus, reverse=True)

        while len(selected_batters) < 9 and remaining:
            player = remaining.pop(0)
            selected_batters.append(player)
            if player.id:
                used_player_ids.add(player.id)

        return selected_batters[:9]

    def decide_pinch_hitter(self, context: IngameContext) -> Player | None:
        """
        공격팀 감독의 대타(Pinch Hitter) 출전 룰베이스 판단.
        (추후 인공신경망 NN 모델로 치환될 상시 의사결정 영역)

        [룰베이스 전략]
        1. 벤치 타자 자원이 없거나 현재 타자가 없으면 스킵.
        2. 경기 후반(7회 이상) 또는 득점권 찬스(2,3루 주자) 상황.
        3. 현재 타자의 체력이 3000 미만으로 고갈되었거나, 벤치에 공격력(power+speed+focus)이 더 높은 선수가 있을 때 대타 기용.
        """
        is_top = context.is_top
        bench_batters = context.away_bench if is_top else context.home_bench
        current_batter = context.current_batter

        if not bench_batters or not current_batter:
            return None

        # 득점권 주자 존재 여부
        has_scoring_chance = context.runner_2b is not None or context.runner_3b is not None
        is_late_game = context.inning >= 7
        is_exhausted = current_batter.current_energy < 3000

        if not (is_late_game or has_scoring_chance or is_exhausted):
            return None

        curr_offense = current_batter.power + current_batter.speed + current_batter.focus
        # 벤치 타자 중 공격력이 가장 높은 선수 탐색
        best_bench = max(bench_batters, key=lambda p: p.power + p.speed + p.focus)
        best_bench_offense = best_bench.power + best_bench.speed + best_bench.focus

        if is_exhausted or best_bench_offense > curr_offense:
            return best_bench

        return None

    def decide_defense_substitution(self, context: IngameContext) -> tuple[int, Player] | None:
        """
        수비팀 감독의 대수비/야수 교체 룰베이스 판단.
        (추후 인공신경망 NN 모델로 치환될 상시 의사결정 영역)

        [룰베이스 전략]
        1. 8회 이후 수비팀이 1~3점차 리드하고 있을 때.
        2. 벤치에 현재 수비수보다 수비력(flexibility + speed)이 우수한 동포지션/외야 야수가 있을 시 교체.
        """
        is_top = context.is_top
        # 수비팀 벤치 및 수비 라인업
        defense_bench = context.home_bench if is_top else context.away_bench
        defense_lineup = context.home_batters if is_top else context.away_batters

        if not defense_bench or context.inning < 8:
            return None

        def_score = context.home_score if is_top else context.away_score
        off_score = context.away_score if is_top else context.home_score
        lead_margin = def_score - off_score

        # 리드 상황(1~3점차)이 아니면 대수비 스킵
        if not (1 <= lead_margin <= 3):
            return None

        # 라인업 중 지명타자(DH)를 제외한 야수 중 수비력 개선 가능한 포지션 검색
        for idx, fielder in enumerate(defense_lineup):
            if fielder.position == IngameRole.DESIGNATED_HITTER:
                continue
            fielder_def = fielder.flexibility + fielder.speed
            # 동일 포지션 벤치 야수 탐색
            pos_candidates = [b for b in defense_bench if b.position == fielder.position]
            if pos_candidates:
                best_sub = max(pos_candidates, key=lambda p: p.flexibility + p.speed)
                if (best_sub.flexibility + best_sub.speed) > fielder_def + 50:
                    return idx, best_sub

        return None






