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
)
from src.models import (
    Match,
    IngameInstructionLog,
    Player,
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


def advance_runners(
    context: IngameContext,
    advance_bases: int,
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
            context.logged_events.append(IngameBaseRunStartEvent(
                event_type=IngameEventType.BASE_RUN_START,
                sim_timestamp=context.sim_timestamp,
                runner_id=runner.id,
                start_base=base,
                target_base=new_base,
                reason=IngameBaseRunReason.HIT_RUN
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
    context.logged_events.append(IngameBaseRunStartEvent(
        event_type=IngameEventType.BASE_RUN_START,
        sim_timestamp=context.sim_timestamp,
        runner_id=batter.id,
        start_base=0,
        target_base=advance_bases,
        reason=IngameBaseRunReason.HIT_RUN
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
            reason=IngameBaseRunReason.HIT_RUN
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
            reason=IngameBaseRunReason.HIT_RUN
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
            reason=IngameBaseRunReason.HIT_RUN
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
        reason=IngameBaseRunReason.HIT_RUN
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
) -> int:
    """
    IngameContext를 받아 단일 타석을 시뮬레이션하고 발생 득점(runs_scored)을 반환합니다.
    context 내 타임스탬프, 아웃/볼/스트라이크 카운트, 스코어보드가 직접 업데이트됩니다.
    """
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
    
    while True:
        context.sim_timestamp += random.uniform(3.0, 5.0)
        
        pitch_type = random.choice(list(IngamePitchType))
        context.logged_events.append(IngamePitchStartEvent(
            event_type=IngameEventType.PITCH_START,
            sim_timestamp=context.sim_timestamp,
            pitcher_id=pitcher.id,
            pitch_type=pitch_type
        ))
        
        p_strike = 0.5 + (pitcher.control - 500) / 2000.0
        p_strike = max(0.3, min(0.7, p_strike))
        
        is_strike_pitch = random.random() < p_strike
        if is_strike_pitch:
            p_swing = 0.6 + (batter.focus - 500) / 2000.0
        else:
            p_swing = 0.2 - (batter.focus - 500) / 2000.0
        p_swing = max(0.05, min(0.9, p_swing))
        
        did_swing = random.random() < p_swing
        
        if not did_swing:
            if is_strike_pitch:
                context.scoreboard.strikes += 1
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE
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
                    result=IngamePitchResult.BALL
                ))
                if context.scoreboard.balls == 4:
                    runs_scored = advance_runners_walk(context)
                    if context.is_top:
                        context.scoreboard.away_b += 1
                    else:
                        context.scoreboard.home_b += 1
                    break
        else:
            p_contact = 0.7 + (batter.focus - pitcher.control) / 2000.0
            p_contact = max(0.4, min(0.95, p_contact))
            
            did_contact = random.random() < p_contact
            
            if not did_contact:
                context.scoreboard.strikes += 1
                context.logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=context.sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE
                ))
                if context.scoreboard.strikes == 3:
                    context.scoreboard.outs += 1
                    break
            else:
                p_foul = 0.4
                is_foul = random.random() < p_foul
                
                if is_foul:
                    context.logged_events.append(IngameBatContactEvent(
                        event_type=IngameEventType.BAT_CONTACT,
                        sim_timestamp=context.sim_timestamp,
                        batter_id=batter.id,
                        contact_type=IngameContactType.FOUL,
                        hit_velocity=0.0,
                        launch_angle=0.0
                    ))
                    if context.scoreboard.strikes < 2:
                        context.scoreboard.strikes += 1
                else:
                    hit_velocity = random.uniform(70.0, 115.0)
                    launch_angle = random.uniform(-10.0, 45.0)
                    
                    context.logged_events.append(IngameBatContactEvent(
                        event_type=IngameEventType.BAT_CONTACT,
                        sim_timestamp=context.sim_timestamp,
                        batter_id=batter.id,
                        contact_type=IngameContactType.CONTACT_IN_PLAY,
                        hit_velocity=hit_velocity,
                        launch_angle=launch_angle
                    ))
                    
                    p_hit = 0.3 + (batter.power - 500) / 2000.0
                    p_hit = max(0.15, min(0.5, p_hit))
                    
                    is_hit = random.random() < p_hit
                    fielder = random.choice(defense_lineup)
                    
                    if is_hit:
                        if context.is_top:
                            context.scoreboard.away_h += 1
                        else:
                            context.scoreboard.home_h += 1

                        power_factor = batter.power / 1000.0
                        speed_factor = batter.speed / 1000.0
                        
                        r = random.random()
                        p_hr = 0.05 + 0.15 * power_factor
                        p_3b = p_hr + 0.01 + 0.04 * speed_factor
                        p_2b = p_3b + 0.15 + 0.1 * power_factor
                        
                        context.logged_events.append(IngameFieldingActionEvent(
                            event_type=IngameEventType.FIELDING_ACTION,
                            sim_timestamp=context.sim_timestamp + 1.5,
                            fielder_id=fielder.id,
                            action_type=random.choice([IngameFieldingAction.DROP, IngameFieldingAction.ERROR])
                        ))
                        
                        if r < p_hr:
                            runs_scored = advance_runners(context, 4)
                        elif r < p_3b:
                            runs_scored = advance_runners(context, 3)
                        elif r < p_2b:
                            runs_scored = advance_runners(context, 2)
                        else:
                            runs_scored = advance_runners(context, 1)
                        break
                    else:
                        is_fly = launch_angle > 15.0
                        if is_fly:
                            context.logged_events.append(IngameFieldingActionEvent(
                                event_type=IngameEventType.FIELDING_ACTION,
                                sim_timestamp=context.sim_timestamp + 2.0,
                                fielder_id=fielder.id,
                                action_type=IngameFieldingAction.CATCH
                            ))
                            context.scoreboard.outs += 1
                        else:
                            context.logged_events.append(IngameFieldingActionEvent(
                                event_type=IngameEventType.FIELDING_ACTION,
                                sim_timestamp=context.sim_timestamp + 1.2,
                                fielder_id=fielder.id,
                                action_type=IngameFieldingAction.CATCH
                            ))
                            first_baseman = next((f for f in defense_lineup if f.position == IngameRole.FIRST_BASE), defense_lineup[0])
                            
                            context.logged_events.append(IngameThrowActionEvent(
                                event_type=IngameEventType.THROW_ACTION,
                                sim_timestamp=context.sim_timestamp + 2.0,
                                thrower_id=fielder.id,
                                receiver_id=first_baseman.id,
                                target_base=1,
                                is_successful=True
                            ))
                            
                            context.logged_events.append(IngameBaseRunStartEvent(
                                event_type=IngameEventType.BASE_RUN_START,
                                sim_timestamp=context.sim_timestamp + 1.5,
                                runner_id=batter.id,
                                start_base=0,
                                target_base=1,
                                reason=IngameBaseRunReason.HIT_RUN
                            ))
                            
                            context.logged_events.append(IngameBaseRunResultEvent(
                                event_type=IngameEventType.BASE_RUN_RESULT,
                                sim_timestamp=context.sim_timestamp + 2.3,
                                runner_id=batter.id,
                                target_base=1,
                                result=IngameBaseRunResult.OUT
                            ))
                            context.scoreboard.outs += 1
                        break
                        
    return runs_scored

