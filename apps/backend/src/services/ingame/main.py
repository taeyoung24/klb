from settings import CONFIG
from src.enums import (
    MatchStatus,
    IngameEventType,
    IngameGameState,
    IngamePitchResult,
    IngameContactType,
    IngameFieldingAction,
    IngameBaseRunResult,
)
from src.models import (
    Match,
    IngameInstructionLog,
    Player,
    IngameGameStateEvent,
    IngameScoreboard,
)
from .simulation import simulate_plate_appearance
from .lineup import select_starting_lineup
from .utils import generate_mock_players


def get_scoreboard(match_log: IngameInstructionLog) -> IngameScoreboard:
    current_inning = 1
    is_top = True
    balls = 0
    strikes = 0
    outs = 0

    away_innings: list[int] = [0]
    home_innings: list[int] = [0]

    away_r = 0
    away_h = 0
    away_e = 0
    away_b = 0

    home_r = 0
    home_h = 0
    home_e = 0
    home_b = 0

    # 타격 후 안타 판정 추적용 변수
    hit_pending_batter_id = None

    for event in match_log.logged_events:
        event_type = event.event_type

        if event_type == IngameEventType.GAME_STATE:
            state_type = getattr(event, "state_type", None)
            inning = getattr(event, "inning", current_inning)
            top_flag = getattr(event, "is_top", is_top)

            if state_type == IngameGameState.MATCH_START:
                current_inning = 1
                is_top = True
                away_innings = [0]
                home_innings = [0]
            elif state_type == IngameGameState.INNING_START:
                current_inning = inning
                is_top = top_flag
                balls = 0
                strikes = 0
                outs = 0

                while len(away_innings) < current_inning:
                    away_innings.append(0)
                while len(home_innings) < current_inning:
                    home_innings.append(0)

        elif event_type == IngameEventType.BATTER_ENTER:
            balls = 0
            strikes = 0
            hit_pending_batter_id = None

        elif event_type == IngameEventType.PITCH:
            result = getattr(event, "result", None)
            if result == IngamePitchResult.STRIKE:
                strikes += 1
                if strikes >= 3:
                    outs += 1
                    balls = 0
                    strikes = 0
            elif result == IngamePitchResult.BALL:
                balls += 1
                if balls >= 4:
                    if is_top:
                        away_b += 1
                    else:
                        home_b += 1
                    balls = 0
                    strikes = 0
            elif result in (IngamePitchResult.HIT_BY_PITCH, IngamePitchResult.INTENTIONAL_WALK):
                if is_top:
                    away_b += 1
                else:
                    home_b += 1
                balls = 0
                strikes = 0

        elif event_type == IngameEventType.BAT_CONTACT:
            contact_type = getattr(event, "contact_type", None)
            if contact_type == IngameContactType.FOUL:
                if strikes < 2:
                    strikes += 1
            elif contact_type == IngameContactType.CONTACT_IN_PLAY:
                batter_id = getattr(event, "batter_id", None)
                hit_pending_batter_id = batter_id

        elif event_type == IngameEventType.FIELDING_ACTION:
            action_type = getattr(event, "action_type", None)
            if action_type in (IngameFieldingAction.ERROR, IngameFieldingAction.DROP):
                if is_top:
                    home_e += 1
                else:
                    away_e += 1
            elif action_type == IngameFieldingAction.CATCH:
                hit_pending_batter_id = None

        elif event_type == IngameEventType.THROW_ACTION:
            is_successful = getattr(event, "is_successful", True)
            if not is_successful:
                if is_top:
                    home_e += 1
                else:
                    away_e += 1

        elif event_type == IngameEventType.BASE_RUN_RESULT:
            runner_id = getattr(event, "runner_id", None)
            target_base = getattr(event, "target_base", None)
            res = getattr(event, "result", None)

            if hit_pending_batter_id is not None and runner_id == hit_pending_batter_id:
                if res == IngameBaseRunResult.SAFE:
                    if is_top:
                        away_h += 1
                    else:
                        home_h += 1
                hit_pending_batter_id = None

            if res == IngameBaseRunResult.SAFE and target_base == 4:
                if is_top:
                    away_r += 1
                    if len(away_innings) >= current_inning:
                        away_innings[current_inning - 1] += 1
                else:
                    home_r += 1
                    if len(home_innings) >= current_inning:
                        home_innings[current_inning - 1] += 1
            elif res == IngameBaseRunResult.OUT:
                outs += 1
                if outs >= 3:
                    balls = 0
                    strikes = 0

    return IngameScoreboard(
        current_inning=current_inning,
        is_top=is_top,
        balls=balls,
        strikes=strikes,
        outs=outs,
        away_innings=away_innings,
        away_r=away_r,
        away_h=away_h,
        away_e=away_e,
        away_b=away_b,
        home_innings=home_innings,
        home_r=home_r,
        home_h=home_h,
        home_e=home_e,
        home_b=home_b,
    )


def run_match(match: Match, session=None):
    """단일 매치를 시뮬레이션하여 세부 이벤트 대본을 남깁니다."""
    # 1. 라인업 추출 (DB 실제 선수 및 감독 선발 로직 캡슐화)
    away_pitcher, away_batters = select_starting_lineup(match.away_club_id, session=session)
    home_pitcher, home_batters = select_starting_lineup(match.home_club_id, session=session)
    
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
