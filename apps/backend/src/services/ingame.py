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
)

def generate_mock_players(club_id: int) -> tuple[Player, list[Player]]:
    """지정된 클럽 ID를 갖는 목 투수 1명과 목 타자 9명을 생성합니다."""
    # 투수 생성
    pitcher = Player(
        id=club_id * 1000 + 1,
        name=f"Pitcher_{club_id}",
        club_id=club_id,
        speed=600,
        control=620,
        power=500,
        flexibility=580,
        focus=600,
        roster_status=RosterStatus.ACTIVE,
        position=IngameRole.PITCHER,
        personality=[500, 500, 500, 500],
        birthday=datetime(2000, 1, 1),
        height=185.0,
        weight=82.0
    )
    
    # 타자 9명 생성
    batters = []
    positions = [
        IngameRole.CATCHER, IngameRole.FIRST_BASE, IngameRole.SECOND_BASE,
        IngameRole.THIRD_BASE, IngameRole.SHORT_STOP, IngameRole.LEFT_FIELD,
        IngameRole.CENTER_FIELD, IngameRole.RIGHT_FIELD, IngameRole.DESIGNATED_HITTER
    ]
    
    for i, pos in enumerate(positions, 1):
        batter = Player(
            id=club_id * 1000 + 10 + i,
            name=f"Batter_{club_id}_{i}",
            club_id=club_id,
            speed=550 + i * 15,
            control=500,
            power=500 + i * 20,
            flexibility=530 + i * 10,
            focus=520 + i * 15,
            roster_status=RosterStatus.ACTIVE,
            position=pos,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, i, 1),
            height=180.0,
            weight=78.0
        )
        batters.append(batter)
        
    return pitcher, batters

def advance_runners(
    bases: dict[int, Player | None],
    batter: Player,
    advance_bases: int,
    logged_events: list,
    sim_timestamp: float
) -> tuple[dict[int, Player | None], int]:
    """주자들을 진루시키고 이번 진루로 얻은 득점(runs)을 반환합니다."""
    runs = 0
    new_bases: dict[int, Player | None] = {1: None, 2: None, 3: None}
    
    # 3루 주자부터 역순으로 진루 처리하여 덮어쓰기 방지
    for base in [3, 2, 1]:
        runner = bases[base]
        if runner is not None:
            new_base = base + advance_bases
            logged_events.append(IngameBaseRunStartEvent(
                event_type=IngameEventType.BASE_RUN_START,
                sim_timestamp=sim_timestamp,
                runner_id=runner.id,
                start_base=base,
                target_base=new_base,
                reason=IngameBaseRunReason.HIT_RUN
            ))
            if new_base >= 4:
                runs += 1
                logged_events.append(IngameBaseRunResultEvent(
                    event_type=IngameEventType.BASE_RUN_RESULT,
                    sim_timestamp=sim_timestamp,
                    runner_id=runner.id,
                    target_base=4,
                    result=IngameBaseRunResult.SAFE
                ))
            else:
                new_bases[new_base] = runner
                logged_events.append(IngameBaseRunResultEvent(
                    event_type=IngameEventType.BASE_RUN_RESULT,
                    sim_timestamp=sim_timestamp,
                    runner_id=runner.id,
                    target_base=new_base,
                    result=IngameBaseRunResult.SAFE
                ))
                
    # 타자 진루 처리
    logged_events.append(IngameBaseRunStartEvent(
        event_type=IngameEventType.BASE_RUN_START,
        sim_timestamp=sim_timestamp,
        runner_id=batter.id,
        start_base=0,
        target_base=advance_bases,
        reason=IngameBaseRunReason.HIT_RUN
    ))
    
    if advance_bases >= 4:
        runs += 1
        logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=sim_timestamp,
            runner_id=batter.id,
            target_base=4,
            result=IngameBaseRunResult.SAFE
        ))
    else:
        new_bases[advance_bases] = batter
        logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=sim_timestamp,
            runner_id=batter.id,
            target_base=advance_bases,
            result=IngameBaseRunResult.SAFE
        ))
        
    return new_bases, runs

def advance_runners_walk(
    bases: dict[int, Player | None],
    batter: Player,
    logged_events: list,
    sim_timestamp: float
) -> tuple[dict[int, Player | None], int]:
    """볼넷(또는 사구)으로 인한 강제 진루 처리"""
    runs = 0
    new_bases: dict[int, Player | None] = {1: bases[1], 2: bases[2], 3: bases[3]}
    
    will_advance = {1: False, 2: False, 3: False, 4: False}
    will_advance[1] = True
    
    if bases[1] is not None:
        will_advance[2] = True
        if bases[2] is not None:
            will_advance[3] = True
            if bases[3] is not None:
                will_advance[4] = True
                
    # 3루 주자 홈 진루
    if will_advance[4] and bases[3] is not None:
        runner = bases[3]
        logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            start_base=3,
            target_base=4,
            reason=IngameBaseRunReason.HIT_RUN
        ))
        runs += 1
        new_bases[3] = None
        logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            target_base=4,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 2루 주자 3루 진루
    if will_advance[3] and bases[2] is not None:
        runner = bases[2]
        logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            start_base=2,
            target_base=3,
            reason=IngameBaseRunReason.HIT_RUN
        ))
        new_bases[3] = runner
        new_bases[2] = None
        logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            target_base=3,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 1루 주자 2루 진루
    if will_advance[2] and bases[1] is not None:
        runner = bases[1]
        logged_events.append(IngameBaseRunStartEvent(
            event_type=IngameEventType.BASE_RUN_START,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            start_base=1,
            target_base=2,
            reason=IngameBaseRunReason.HIT_RUN
        ))
        new_bases[2] = runner
        new_bases[1] = None
        logged_events.append(IngameBaseRunResultEvent(
            event_type=IngameEventType.BASE_RUN_RESULT,
            sim_timestamp=sim_timestamp,
            runner_id=runner.id,
            target_base=2,
            result=IngameBaseRunResult.SAFE
        ))
        
    # 타자 1루 진루
    logged_events.append(IngameBaseRunStartEvent(
        event_type=IngameEventType.BASE_RUN_START,
        sim_timestamp=sim_timestamp,
        runner_id=batter.id,
        start_base=0,
        target_base=1,
        reason=IngameBaseRunReason.HIT_RUN
    ))
    new_bases[1] = batter
    logged_events.append(IngameBaseRunResultEvent(
        event_type=IngameEventType.BASE_RUN_RESULT,
        sim_timestamp=sim_timestamp,
        runner_id=batter.id,
        target_base=1,
        result=IngameBaseRunResult.SAFE
    ))
    
    return new_bases, runs

def simulate_plate_appearance(
    batter: Player,
    pitcher: Player,
    defense_lineup: list[Player],
    bases: dict[int, Player | None],
    outs: int,
    logged_events: list,
    sim_timestamp: float
) -> tuple[float, int, dict[int, Player | None], int]:
    """타석 하나를 시뮬레이션하고 업데이트된 시간, 아웃 수, 베이스 상태, 득점을 반환합니다."""
    sim_timestamp += random.uniform(5.0, 10.0)
    
    logged_events.append(IngameBatterEnterEvent(
        event_type=IngameEventType.BATTER_ENTER,
        sim_timestamp=sim_timestamp,
        batter_id=batter.id,
        pitcher_id=pitcher.id
    ))
    
    strikes = 0
    balls = 0
    runs_scored = 0
    
    while True:
        sim_timestamp += random.uniform(3.0, 5.0)
        
        pitch_type = random.choice(list(IngamePitchType))
        logged_events.append(IngamePitchStartEvent(
            event_type=IngameEventType.PITCH_START,
            sim_timestamp=sim_timestamp,
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
                strikes += 1
                logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE
                ))
                if strikes == 3:
                    outs += 1
                    break
            else:
                balls += 1
                logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.BALL
                ))
                if balls == 4:
                    bases, runs_scored = advance_runners_walk(bases, batter, logged_events, sim_timestamp)
                    break
        else:
            p_contact = 0.7 + (batter.focus - pitcher.control) / 2000.0
            p_contact = max(0.4, min(0.95, p_contact))
            
            did_contact = random.random() < p_contact
            
            if not did_contact:
                strikes += 1
                logged_events.append(IngamePitchEvent(
                    event_type=IngameEventType.PITCH,
                    sim_timestamp=sim_timestamp,
                    pitcher_id=pitcher.id,
                    batter_id=batter.id,
                    result=IngamePitchResult.STRIKE
                ))
                if strikes == 3:
                    outs += 1
                    break
            else:
                p_foul = 0.4
                is_foul = random.random() < p_foul
                
                if is_foul:
                    logged_events.append(IngameBatContactEvent(
                        event_type=IngameEventType.BAT_CONTACT,
                        sim_timestamp=sim_timestamp,
                        batter_id=batter.id,
                        contact_type=IngameContactType.FOUL,
                        hit_velocity=0.0,
                        launch_angle=0.0
                    ))
                    if strikes < 2:
                        strikes += 1
                else:
                    hit_velocity = random.uniform(70.0, 115.0)
                    launch_angle = random.uniform(-10.0, 45.0)
                    
                    logged_events.append(IngameBatContactEvent(
                        event_type=IngameEventType.BAT_CONTACT,
                        sim_timestamp=sim_timestamp,
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
                        power_factor = batter.power / 1000.0
                        speed_factor = batter.speed / 1000.0
                        
                        r = random.random()
                        p_hr = 0.05 + 0.15 * power_factor
                        p_3b = p_hr + 0.01 + 0.04 * speed_factor
                        p_2b = p_3b + 0.15 + 0.1 * power_factor
                        
                        logged_events.append(IngameFieldingActionEvent(
                            event_type=IngameEventType.FIELDING_ACTION,
                            sim_timestamp=sim_timestamp + 1.5,
                            fielder_id=fielder.id,
                            action_type=random.choice([IngameFieldingAction.DROP, IngameFieldingAction.ERROR])
                        ))
                        
                        if r < p_hr:
                            bases, runs_scored = advance_runners(bases, batter, 4, logged_events, sim_timestamp + 2.0)
                        elif r < p_3b:
                            bases, runs_scored = advance_runners(bases, batter, 3, logged_events, sim_timestamp + 2.0)
                        elif r < p_2b:
                            bases, runs_scored = advance_runners(bases, batter, 2, logged_events, sim_timestamp + 2.0)
                        else:
                            bases, runs_scored = advance_runners(bases, batter, 1, logged_events, sim_timestamp + 2.0)
                        break
                    else:
                        is_fly = launch_angle > 15.0
                        if is_fly:
                            logged_events.append(IngameFieldingActionEvent(
                                event_type=IngameEventType.FIELDING_ACTION,
                                sim_timestamp=sim_timestamp + 2.0,
                                fielder_id=fielder.id,
                                action_type=IngameFieldingAction.CATCH
                            ))
                            outs += 1
                        else:
                            logged_events.append(IngameFieldingActionEvent(
                                event_type=IngameEventType.FIELDING_ACTION,
                                sim_timestamp=sim_timestamp + 1.2,
                                fielder_id=fielder.id,
                                action_type=IngameFieldingAction.CATCH
                            ))
                            first_baseman = next((f for f in defense_lineup if f.position == IngameRole.FIRST_BASE), defense_lineup[0])
                            
                            logged_events.append(IngameThrowActionEvent(
                                event_type=IngameEventType.THROW_ACTION,
                                sim_timestamp=sim_timestamp + 2.0,
                                thrower_id=fielder.id,
                                receiver_id=first_baseman.id,
                                target_base=1,
                                is_successful=True
                            ))
                            
                            logged_events.append(IngameBaseRunStartEvent(
                                event_type=IngameEventType.BASE_RUN_START,
                                sim_timestamp=sim_timestamp + 1.5,
                                runner_id=batter.id,
                                start_base=0,
                                target_base=1,
                                reason=IngameBaseRunReason.HIT_RUN
                            ))
                            
                            logged_events.append(IngameBaseRunResultEvent(
                                event_type=IngameEventType.BASE_RUN_RESULT,
                                sim_timestamp=sim_timestamp + 2.3,
                                runner_id=batter.id,
                                target_base=1,
                                result=IngameBaseRunResult.OUT
                            ))
                            outs += 1
                        break
                        
    return sim_timestamp, outs, bases, runs_scored

def run_match(match: Match):
    """단일 매치를 시뮬레이션하여 세부 이벤트 대본을 남깁니다."""
    # 1. 목데이터 기반 라인업 빌드
    away_pitcher, away_batters = generate_mock_players(match.away_club_id)
    home_pitcher, home_batters = generate_mock_players(match.home_club_id)
    
    # 2. 게임 상태 및 누적 점수 변수 초기화
    home_score = 0
    away_score = 0
    sim_timestamp = 0.0
    logged_events = []
    
    logged_events.append(IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=sim_timestamp,
        state_type=IngameGameState.MATCH_START,
        inning=1,
        is_top=True,
        home_score=0,
        away_score=0
    ))
    
    inning = 1
    is_top = True
    
    away_batter_idx = 0
    home_batter_idx = 0
    
    max_innings = 11 if match.limit_extra_innings else 100
    game_over = False
    
    while not game_over:
        logged_events.append(IngameGameStateEvent(
            event_type=IngameEventType.GAME_STATE,
            sim_timestamp=sim_timestamp,
            state_type=IngameGameState.INNING_START,
            inning=inning,
            is_top=is_top,
            home_score=home_score,
            away_score=away_score
        ))
        
        outs = 0
        bases: dict[int, Player | None] = {1: None, 2: None, 3: None}
        
        if is_top:
            batters = away_batters
            pitcher = home_pitcher
            defense_lineup = home_batters
            current_batter_idx = away_batter_idx
        else:
            batters = home_batters
            pitcher = away_pitcher
            defense_lineup = away_batters
            current_batter_idx = home_batter_idx
            
        while outs < 3:
            # 9회말 또는 연장전 말에 홈팀이 리드하면 즉시 끝내기로 경기 종료
            if not is_top and inning >= 9 and home_score > away_score:
                game_over = True
                break
                
            batter = batters[current_batter_idx]
            
            sim_timestamp, outs, bases, runs = simulate_plate_appearance(
                batter, pitcher, defense_lineup, bases, outs, logged_events, sim_timestamp
            )
            
            if runs > 0:
                if is_top:
                    away_score += runs
                else:
                    home_score += runs
                    
            current_batter_idx = (current_batter_idx + 1) % 9
            
        if is_top:
            away_batter_idx = current_batter_idx
        else:
            home_batter_idx = current_batter_idx
            
        if game_over:
            break
            
        logged_events.append(IngameGameStateEvent(
            event_type=IngameEventType.GAME_STATE,
            sim_timestamp=sim_timestamp,
            state_type=IngameGameState.INNING_END,
            inning=inning,
            is_top=is_top,
            home_score=home_score,
            away_score=away_score
        ))
        
        sim_timestamp += 120.0
        
        # 경기 종료 판정
        if inning == 9 and is_top and home_score < away_score:
            game_over = True
        elif not is_top and inning >= 9:
            if home_score != away_score:
                game_over = True
            elif inning >= max_innings:
                game_over = True
                
        if not game_over:
            if is_top:
                is_top = False
            else:
                is_top = True
                inning += 1
                
    match.home_score = home_score
    match.away_score = away_score
    match.status = MatchStatus.COMPLETED
    
    logged_events.append(IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=sim_timestamp,
        state_type=IngameGameState.MATCH_END,
        inning=inning,
        is_top=is_top,
        home_score=home_score,
        away_score=away_score
    ))
    
    match.match_log = IngameInstructionLog(
        simulation_version=CONFIG.simulation_version,
        logged_events=logged_events
    )
