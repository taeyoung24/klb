import random
from datetime import datetime
from settings import CONFIG
from src.enums import (
    MatchStatus,
    IngameEventType,
    IngameGameState,
    IngamePitchType,
    IngamePitchResult,
    IngameContactType,
    IngameFieldingAction,
    IngameBaseRunReason,
    IngameBaseRunResult,
    IngameRole,
    RosterStatus,
    IngamePitchAction,
    IngameBattingStrategy,
)
from src.models import (
    Match,
    IngameInstructionLog,
    Player,
    IngameNoticeEvent,
    IngameGameStateEvent,
    IngameBatterEnterEvent,
    IngamePitchStartEvent,
    IngamePitchEvent,
    IngameBatContactEvent,
    IngameFieldingActionEvent,
    IngameThrowActionEvent,
    IngameBaseRunStartEvent,
    IngameBaseRunResultEvent,
    IngameContext,
)
from .decisions import BaseDecisionEngine, RuleBasedDecisionEngine
from .energy import (
    drain_pitcher_energy,
    drain_batter_energy,
    drain_runner_energy,
    drain_fielder_energy,
)
from .physics import (
    calculate_pitch_physics,
    calculate_batting_physics,
    calculate_swing_contact_probability,
    calculate_trajectory_physics,
    calculate_fielding_physics,
    calculate_baserunning_physics,
    HitOutcome,
)



def advance_runners(
    context: IngameContext,
    advance_bases: int,
    reason: IngameBaseRunReason = IngameBaseRunReason.HIT_RUN,
    skip_batter_start_event: bool = False,
) -> int:
    """주자들을 진루시키고 context 베이스 및 이벤트 대본을 업데이트하며 득점(runs)을 반환합니다."""
    runs = 0
    batter = context.current_batter
    if not batter:
        return 0

    # 3루, 2루, 1루 주자 순서대로 진루 연산
    runners_on_base = [(3, context.runner_3b), (2, context.runner_2b), (1, context.runner_1b)]
    new_runner_1b: Player | None = None
    new_runner_2b: Player | None = None
    new_runner_3b: Player | None = None

    for base, runner in runners_on_base:
        if runner is not None:
            new_base = base + advance_bases
            drain_runner_energy(runner, advance_bases)
            context.logged_events.append(IngameBaseRunStartEvent(
                event_type=IngameEventType.BASE_RUN_START,
                sim_timestamp=context.sim_timestamp,
                runner_id=runner.id,
                start_base=base,
                target_base=new_base,
                reason=reason
            ))
            if new_base >= 4:
                runs += 1
                context.logged_events.append(IngameBaseRunResultEvent(
                    event_type=IngameEventType.BASE_RUN_RESULT,
                    sim_timestamp=context.sim_timestamp,
                    runner_id=runner.id,
                    target_base=4,
                    result=IngameBaseRunResult.SAFE
                ))
            else:
                if new_base == 1:
                    new_runner_1b = runner
                elif new_base == 2:
                    new_runner_2b = runner
                elif new_base == 3:
                    new_runner_3b = runner

                context.logged_events.append(IngameBaseRunResultEvent(
                    event_type=IngameEventType.BASE_RUN_RESULT,
                    sim_timestamp=context.sim_timestamp,
                    runner_id=runner.id,
                    target_base=new_base,
                    result=IngameBaseRunResult.SAFE
                ))
                
    # 타자 진루 처리
    if not skip_batter_start_event:
        context.logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=context.sim_timestamp,
            runner_id=batter.id,
            start_base=0,
            target_base=advance_bases,
            reason=reason
        ))
    
    if advance_bases >= 4:
        runs += 1
        context.logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=context.sim_timestamp,
            runner_id=batter.id,
            target_base=4,
            result=IngameBaseRunResult.SAFE
        ))
    else:
        if advance_bases == 1:
            new_runner_1b = batter
        elif advance_bases == 2:
            new_runner_2b = batter
        elif advance_bases == 3:
            new_runner_3b = batter

        context.logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=context.sim_timestamp,
            runner_id=batter.id,
            target_base=advance_bases,
            result=IngameBaseRunResult.SAFE
        ))

    context.runner_1b = new_runner_1b
    context.runner_2b = new_runner_2b
    context.runner_3b = new_runner_3b
    return runs


def advance_runners_walk(
    context: IngameContext,
) -> int:
    """볼넷(또는 사구)으로 인한 강제 진루 처리"""
    runs = 0
    batter = context.current_batter
    if not batter:
        return 0

    will_advance = {1: True, 2: False, 3: False, 4: False}
    
    if context.runner_1b is not None:
        will_advance[2] = True
        if context.runner_2b is not None:
            will_advance[3] = True
            if context.runner_3b is not None:
                will_advance[4] = True
                
    new_runner_1b: Player | None = context.runner_1b
    new_runner_2b: Player | None = context.runner_2b
    new_runner_3b: Player | None = context.runner_3b

    # 3루 주자 홈 진루
    if will_advance[4] and context.runner_3b is not None:
        runner = context.runner_3b
        context.logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            start_base=3,
            target_base=4,
            reason=IngameBaseRunReason.WALK
        ))
        runs += 1
        new_runner_3b = None
        context.logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            target_base=4,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 2루 주자 3루 진루
    if will_advance[3] and context.runner_2b is not None:
        runner = context.runner_2b
        context.logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            start_base=2,
            target_base=3,
            reason=IngameBaseRunReason.WALK
        ))
        new_runner_3b = runner
        new_runner_2b = None
        context.logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            target_base=3,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 1루 주자 2루 진루
    if will_advance[2] and context.runner_1b is not None:
        runner = context.runner_1b
        context.logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            start_base=1,
            target_base=2,
            reason=IngameBaseRunReason.WALK
        ))
        new_runner_2b = runner
        new_runner_1b = None
        context.logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=context.sim_timestamp,
            runner_id=runner.id,
            target_base=2,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 타자 1루 진루
    context.logged_events.append(IngameBaseRunStartEvent(
        event_type=IngameEventType.BASE_RUN_START,
        sim_timestamp=context.sim_timestamp,
        runner_id=batter.id,
        start_base=0,
        target_base=1,
        reason=IngameBaseRunReason.WALK
    ))
    new_runner_1b = batter
    context.logged_events.append(IngameBaseRunResultEvent(
        event_type=IngameEventType.BASE_RUN_RESULT,
        sim_timestamp=context.sim_timestamp,
        runner_id=batter.id,
        target_base=1,
        result=IngameBaseRunResult.SAFE
    ))
    
    context.runner_1b = new_runner_1b
    context.runner_2b = new_runner_2b
    context.runner_3b = new_runner_3b
    return runs


def simulate_plate_appearance(
    context: IngameContext,
    defense_lineup: list[Player],
    decision_engine: BaseDecisionEngine | None = None,
) -> int:
    """
    IngameContext를 받아 단일 타석을 시뮬레이션하고 발생 득점(runs_scored)을 반환합니다.
    BaseDecisionEngine (RuleBasedDecisionEngine 또는 NNDecisionEngine)을 활용하여
    투수/타자의 행위, 구종/코스 선택, 타석 전략, 스윙 여부를 결정합니다.
    """
    engine = decision_engine or RuleBasedDecisionEngine()

    batter = context.current_batter
    pitcher = context.current_pitcher
    if not batter or not pitcher:
        return 0

    context.sim_timestamp += random.uniform(5.0, 10.0)
    
    context.logged_events.append(IngameBatterEnterEvent(
        event_type=IngameEventType.BATTER_ENTER,
        sim_timestamp=context.sim_timestamp,
        batter_id=batter.id,
        pitcher_id=pitcher.id
    ))
    
    context.scoreboard.strikes = 0
    context.scoreboard.balls = 0
    runs_scored = 0
    pitch_count_in_pa = 0
    
    while True:
        context.sim_timestamp += random.uniform(3.0, 5.0)
        pitch_count_in_pa += 1
        
        # 1. 투수 행위 판단 (투구 vs 견제구)
        pitch_action = engine.decide_pitch_action(context)
        if pitch_action == IngamePitchAction.PICK_OFF:
            context.sim_timestamp += random.uniform(2.0, 4.0)
            # 견제구 투구 처리 (향후 견제구 이벤트 확장 가능)
            pass

        # 2. 투수 구종 및 투구 코스/존 선택
        pitch_info = engine.decide_pitch_selection(context)
        pitch_type = pitch_info.pitch_type

        # 2-1. 투수 스탯(power, control) 기반 물리 연산 수행 (실측 구속 & 가우시안 탄착점)
        pitch_physics = calculate_pitch_physics(pitcher, pitch_info)

        # 투수 체력 소진 (2스트라이크 결정구 또는 견제구 시 전력투구 가중치)
        is_power_pitch = (context.scoreboard.strikes == 2 or pitch_action == IngamePitchAction.PICK_OFF)
        drain_pitcher_energy(pitcher, is_power_pitch=is_power_pitch)

        context.logged_events.append(IngamePitchStartEvent(
            event_type=IngameEventType.PITCH_START,
            sim_timestamp=context.sim_timestamp,
            pitcher_id=pitcher.id,
            pitch_type=pitch_type,
            pitch_velocity=pitch_physics.pitch_velocity
        ))
        
        # 3. 타자 타석 전략 및 스윙 의도 판단
        batting_strategy = engine.decide_batting_strategy(context)
        did_swing = engine.decide_swing_intent(context, pitch_info)
        
        # 투수의 제구(control) 스탯 기반 정밀 탄착점 결과로 스트라이크 판정
        is_strike_pitch = pitch_physics.is_strike_zone
        
        if not did_swing:
            if is_strike_pitch:
                context.scoreboard.strikes += 1
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE,
                    pitch_velocity=pitch_physics.pitch_velocity
                ))
                if context.scoreboard.strikes == 3:
                    context.scoreboard.outs += 1
                    break
            else:
                context.scoreboard.balls += 1
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.BALL,
                    pitch_velocity=pitch_physics.pitch_velocity
                ))
                if context.scoreboard.balls == 4:
                    runs_scored = advance_runners_walk(context)
                    if context.is_top:
                        context.scoreboard.away_b += 1
                    else:
                        context.scoreboard.home_b += 1
                    break
        else:
            # batting.py 모듈의 타자/투수 스탯 및 상황 부담가중치 기반 컨택트 확률 함수 호출
            p_contact = calculate_swing_contact_probability(batter, pitcher, pitch_physics, context)
            did_contact = random.random() < p_contact
            
            if not did_contact:
                context.scoreboard.strikes += 1
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE_SWINGING,
                    pitch_velocity=pitch_physics.pitch_velocity
                ))
                if context.scoreboard.strikes == 3:
                    context.scoreboard.outs += 1
                    break
            else:
                # 1. 타자 스탯(power, focus) 및 투구 물리 기반 3D 타구 벡터 연산
                batting_physics = calculate_batting_physics(batter, pitch_physics, batting_strategy)

                # 2. 공기저항, 백스핀, 구장 펜스 반영 타구 궤적 & 비거리/홈런 연산
                trajectory_physics = calculate_trajectory_physics(batting_physics, context.stadium)

                # [투구 결과 이벤트 기록] 타격된 투구(IN_PLAY 또는 FOUL)를 PITCH 이벤트로 먼저 기록
                pitch_result = (
                    IngamePitchResult.IN_PLAY
                    if batting_physics.is_fair_territory
                    else IngamePitchResult.FOUL
                )
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=pitch_result,
                    pitch_velocity=pitch_physics.pitch_velocity
                ))

                # [타격 이벤트 기록] 타격 발생 시점(sim_timestamp)에 기록
                context.logged_events.append(IngameBatContactEvent(
                    event_type=IngameEventType.BAT_CONTACT,
                    sim_timestamp=context.sim_timestamp,
                    batter_id=batter.id,
                    contact_type=IngameContactType.CONTACT_IN_PLAY if batting_physics.is_fair_territory else IngameContactType.FOUL,
                    hit_velocity=batting_physics.hit_velocity,
                    launch_angle=batting_physics.launch_angle
                ))

                # [경우 A] 장외 홈런 (HitOutcome.HOME_RUN)
                if trajectory_physics.outcome == HitOutcome.HOME_RUN:
                    if context.is_top:
                        context.scoreboard.away_h += 1
                    else:
                        context.scoreboard.home_h += 1

                    # 타자 주루 체력 소진 (홈런 주루: 4베이스)
                    drain_runner_energy(batter, 4)

                    # 주자 수에 따른 홈런 유형 및 득점 연산 (1~4점)
                    base_runners = [r for r in [context.runner_1b, context.runner_2b, context.runner_3b] if r is not None]
                    for r in base_runners:
                        drain_runner_energy(r, 3)

                    homerun_runs = 1 + len(base_runners)
                    runs_scored += homerun_runs

                    homerun_type_map = {
                        1: "솔로 홈런",
                        2: "2점 홈런",
                        3: "3점 홈런",
                        4: "만루 홈런"
                    }
                    homerun_label = homerun_type_map.get(homerun_runs, f"{homerun_runs}점 홈런")
                    distance_m = round(trajectory_physics.distance_m, 1)

                    # 주자가 있을 경우 주자 이름 목록 포맷팅 (예: "주자 노지혁, 김서래")
                    runner_names = [r.name for r in base_runners]
                    runner_detail = f", 주자 {', '.join(runner_names)}" if runner_names else ""
                    homerun_message = f"{homerun_label} (비거리 {distance_m}m{runner_detail})"

                    # 베이스 주자 전원 클리어
                    context.runner_1b = None
                    context.runner_2b = None
                    context.runner_3b = None

                    # 홈런 안내 및 타자 득점 이벤트 기록
                    context.logged_events.append(IngameNoticeEvent(
                        event_type=IngameEventType.NOTICE,
                        sim_timestamp=context.sim_timestamp + 3.5,
                        message=homerun_message
                    ))
                    context.logged_events.append(IngameBaseRunResultEvent(
                        event_type=IngameEventType.BASE_RUN_RESULT,
                        sim_timestamp=context.sim_timestamp + 4.0,
                        runner_id=batter.id,
                        target_base=4,
                        result=IngameBaseRunResult.SAFE
                    ))
                    break

                # [경우 B] 인플레이 타구 (IN_FIELD, FENCE_HIT, FOUL_OUT)
                # 의사결정 엔진(engine)을 통해 주자의 진루 목표 베이스(1루 vs 2루타 도전) 판단
                fielding_physics_est = calculate_fielding_physics(defense_lineup, trajectory_physics, target_base=1)
                target_base = engine.decide_baserunning_target_base(context, batter, fielding_physics_est)

                # 3. 야수 수비 도달시간/포구/송구 완류 연산 (파울 지역 포함)
                fielding_physics = calculate_fielding_physics(defense_lineup, trajectory_physics, target_base=target_base)

                # 수비수 체력 소진
                if fielding_physics and fielding_physics.fielder:
                    drain_fielder_energy(fielding_physics.fielder, is_difficult_play=fielding_physics.is_caught_in_air)

                # [경우 B-1] 공중 뜬공 포구 아웃 (Fly Out / Foul Fly Out)
                if fielding_physics.is_caught_in_air:
                    context.logged_events.append(IngameFieldingActionEvent(
                        event_type=IngameEventType.FIELDING_ACTION,
                        sim_timestamp=context.sim_timestamp + fielding_physics.reach_time_sec,
                        fielder_id=fielding_physics.fielder.id,
                        action_type=fielding_physics.fielding_action
                    ))
                    context.scoreboard.outs += 1
                    break

                # [경우 B-2] 공중 포구 실패 및 바운드 파울 (일반 파울 - 수비 에러 미발생)
                if not batting_physics.is_fair_territory:
                    # 야수가 파울 지면 타구를 공중에서 못 잡은 경우 -> 일반 파울 (Foul Ball, 수비 이벤트 불필요)
                    if context.scoreboard.strikes < 2:
                        context.scoreboard.strikes += 1
                else:
                    # [경우 B-3] 페어 지역 인플레이 타구 (안타 또는 땅볼 수비)
                    is_error = fielding_physics.fielding_action in [IngameFieldingAction.ERROR, IngameFieldingAction.DROP]
                    run_reason = IngameBaseRunReason.ERROR if is_error else IngameBaseRunReason.HIT_RUN

                    # 1. [주루 시작 이벤트] 타격 직후 타자 주자 및 기존 베이스 주자들의 스타트 기록
                    context.logged_events.append(IngameBaseRunStartEvent(
                        event_type=IngameEventType.BASE_RUN_START,
                        sim_timestamp=context.sim_timestamp,
                        runner_id=batter.id,
                        start_base=0,
                        target_base=target_base,
                        reason=run_reason
                    ))

                    # 2. [수비수 포구 이벤트] 야수가 타구 지점으로 이동하여 포구
                    context.logged_events.append(IngameFieldingActionEvent(
                        event_type=IngameEventType.FIELDING_ACTION,
                        sim_timestamp=context.sim_timestamp + fielding_physics.reach_time_sec,
                        fielder_id=fielding_physics.fielder.id,
                        action_type=fielding_physics.fielding_action
                    ))

                    # 3. [수비수 송구 이벤트] 포구 야수가 목표 베이스 수비수에게 송구
                    role_map = {1: IngameRole.FIRST_BASE, 2: IngameRole.SECOND_BASE, 3: IngameRole.THIRD_BASE, 4: IngameRole.CATCHER}
                    target_role = role_map.get(target_base)
                    receiver = next((p for p in defense_lineup if p.position == target_role), defense_lineup[0]) if defense_lineup else fielding_physics.fielder

                    if receiver and receiver.id != fielding_physics.fielder.id:
                        context.logged_events.append(IngameThrowActionEvent(
                            event_type=IngameEventType.THROW_ACTION,
                            sim_timestamp=context.sim_timestamp + fielding_physics.reach_time_sec + 0.3,
                            thrower_id=fielding_physics.fielder.id,
                            receiver_id=receiver.id,
                            target_base=target_base,
                            is_successful=not is_error
                        ))

                    # 4. [주루 도달 및 아웃/세이프 판정]
                    baserunning_physics = calculate_baserunning_physics(batter, start_base=0, target_base=target_base, fielding_physics=fielding_physics)

                    if baserunning_physics.is_safe:
                        # 세이프! (안타 또는 실책 출루)
                        if not is_error:
                            if context.is_top:
                                context.scoreboard.away_h += 1
                            else:
                                context.scoreboard.home_h += 1
                        else:
                            # 수비측 실책(Error) 카운트 증가
                            if context.is_top:
                                context.scoreboard.home_e += 1
                            else:
                                context.scoreboard.away_e += 1

                        runs_scored += advance_runners(context, target_base, reason=run_reason, skip_batter_start_event=True)
                    else:
                        # 아웃! (땅볼 / 1루 포스아웃 / 2루 태그아웃)
                        context.scoreboard.outs += 1

                        # 목표 베이스 최종 아웃 판정 이벤트 발행
                        context.logged_events.append(IngameBaseRunResultEvent(
                            event_type=IngameEventType.BASE_RUN_RESULT,
                            sim_timestamp=context.sim_timestamp + fielding_physics.throw_time_sec,
                            runner_id=batter.id,
                            target_base=target_base,
                            result=IngameBaseRunResult.OUT
                        ))

                    break

    # 타석 종료 시 타자 체력 소진 반영
    drain_batter_energy(batter, pitch_count_in_pa)

    return runs_scored

