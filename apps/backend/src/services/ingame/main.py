from sqlmodel import Session

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
    MatchLineup,
    PitcherTracker,
    IngameContext,
    MatchStatCollector,
)
from .decisions import BaseDecisionEngine, RuleBasedDecisionEngine
from .simulation import simulate_plate_appearance
from .lineup import select_team_roster_for_match
from .utils import generate_mock_players


def determine_decisions(
    match: Match,
    context: IngameContext,
):
    """
    제출된 야구 규정에 맞추어 IngameContext의 투수 기록 데이터를 조회하여 승리/패전/세이브 투수 ID를 결정합니다.
    """
    if match.away_score is None or match.home_score is None or match.away_score == match.home_score:
        match.winning_pitcher_id = None
        match.losing_pitcher_id = None
        match.save_pitcher_id = None
        return

    win_team = 'away' if match.away_score > match.home_score else 'home'
    win_logs = context.away_pitcher_logs if win_team == 'away' else context.home_pitcher_logs
    lose_logs = context.home_pitcher_logs if win_team == 'away' else context.away_pitcher_logs

    go_ahead_win_pitcher = context.go_ahead_pitcher_away if win_team == 'away' else context.go_ahead_pitcher_home
    go_ahead_lose_resp_pitcher = context.go_ahead_resp_pitcher_home if win_team == 'away' else context.go_ahead_resp_pitcher_away

    winning_pitcher_log: PitcherTracker | None = None

    # 1. 승리 투수 조건 검증
    starter = win_logs[0] if win_logs else None
    if starter and starter.outs_recorded >= 15 and starter.exit_lead > 0:
        # 선발 투수: 5이닝(15 아웃) 이상 및 강판 시점 팀 리드 상태
        winning_pitcher_log = starter
    else:
        # 구원: 선발 요건 미달 또는 결승 리드를 잡은 시점의 투수
        if go_ahead_win_pitcher in win_logs:
            winning_pitcher_log = go_ahead_win_pitcher
        else:
            # fallback: 승리팀 투수 중 아웃수를 가장 많이 잡았거나 유의미한 구원 투수 선택
            relievers = [l for l in win_logs if not l.is_starter]
            if relievers:
                winning_pitcher_log = max(relievers, key=lambda l: l.outs_recorded)
            elif starter:
                winning_pitcher_log = starter

    if winning_pitcher_log:
        match.winning_pitcher_id = winning_pitcher_log.pitcher.id
    else:
        match.winning_pitcher_id = win_logs[0].pitcher.id if win_logs else None

    # 2. 패전 투수 조건 검증
    # 기준: 상대 팀의 결승점이 된 주자(책임 주자)를 출루시킨 투수
    losing_pitcher_log: PitcherTracker | None = None
    if go_ahead_lose_resp_pitcher in lose_logs:
        losing_pitcher_log = go_ahead_lose_resp_pitcher
    elif lose_logs:
        # fallback: 패배팀에서 가장 많은 실점을 하거나 결승점 시점 던진 투수
        losing_pitcher_log = lose_logs[0]

    if losing_pitcher_log:
        match.losing_pitcher_id = losing_pitcher_log.pitcher.id

    # 3. 세이브 투수 조건 검증
    # 공통: 승리 팀의 경기 종료 시점 마지막 투수 (승리 투수와 중복 불가)
    last_win_pitcher_log = win_logs[-1] if win_logs else None
    save_pitcher_id: int | None = None

    if last_win_pitcher_log and winning_pitcher_log and last_win_pitcher_log.pitcher.id != winning_pitcher_log.pitcher.id:
        outs = last_win_pitcher_log.outs_recorded
        entry_lead = last_win_pitcher_log.entry_lead
        on_base = last_win_pitcher_log.entry_on_base

        # 요건 1: 3점 이하 리드 상황 등판 + 최소 1이닝(3아웃) 이상 투구
        c1 = (entry_lead <= 3 and outs >= 3)
        # 요건 2: 상대 홈런 시 동점 유발 범위(등판 시점: 점수차 - 루상 주자수 <= 2) 내 등판 + 최소 1아웃 매듭
        c2 = ((entry_lead - on_base) <= 2 and outs >= 1)
        # 요건 3: 점수 차 무관 + 최소 3이닝(9아웃) 이상 투구 마무리
        c3 = (outs >= 9)

        if c1 or c2 or c3:
            save_pitcher_id = last_win_pitcher_log.pitcher.id

    match.save_pitcher_id = save_pitcher_id


def run_match(
    match: Match,
    session: Session | None = None,
    decision_engine: BaseDecisionEngine | None = None,
    roster_map: dict[int, list[Player]] | None = None,
) -> MatchStatCollector:
    """단일 매치를 IngameContext 객체 중심으로 시뮬레이션하고 발생 스탯을 MatchStatCollector로 반환합니다."""
    engine = decision_engine or RuleBasedDecisionEngine()
    collector = MatchStatCollector()

    away_roster = roster_map.get(match.away_club_id) if roster_map else None
    home_roster = roster_map.get(match.home_club_id) if roster_map else None

    # 1. 라인업 및 투수 스쿼드, 벤치 추출
    away_sp, away_bp, away_batters, away_bench = select_team_roster_for_match(
        match.away_club_id, session=session, decision_engine=engine, preloaded_roster=away_roster
    )
    home_sp, home_bp, home_batters, home_bench = select_team_roster_for_match(
        match.home_club_id, session=session, decision_engine=engine, preloaded_roster=home_roster
    )

    if away_sp and away_sp.id:
        match.away_starting_pitcher_id = away_sp.id
        collector.get(away_sp.id).pitch_starts += 1
        collector.get(away_sp.id).pitch_games += 1
    if home_sp and home_sp.id:
        match.home_starting_pitcher_id = home_sp.id
        collector.get(home_sp.id).pitch_starts += 1
        collector.get(home_sp.id).pitch_games += 1

    for b in away_batters:
        if b and b.id:
            collector.get(b.id).bat_games += 1
    for b in home_batters:
        if b and b.id:
            collector.get(b.id).bat_games += 1

    # 세션이 제공된 경우 DB에 MatchLineup 레코드 생성/추가 (커밋은 상위 호출부에서 일괄 처리)
    if session and match.id:
        # 어웨이팀 선발 투수
        if away_sp and away_sp.id:
            session.add(MatchLineup(
                match_id=match.id,
                club_id=match.away_club_id,
                player_id=away_sp.id,
                position=away_sp.position,
                batting_order=None,
                is_starter=True
            ))
        # 어웨이팀 선발 타자 9명
        for idx, b in enumerate(away_batters, 1):
            if b and b.id:
                session.add(MatchLineup(
                    match_id=match.id,
                    club_id=match.away_club_id,
                    player_id=b.id,
                    position=b.position,
                    batting_order=idx,
                    is_starter=True
                ))

        # 홈팀 선발 투수
        if home_sp and home_sp.id:
            session.add(MatchLineup(
                match_id=match.id,
                club_id=match.home_club_id,
                player_id=home_sp.id,
                position=home_sp.position,
                batting_order=None,
                is_starter=True
            ))
        # 홈팀 선발 타자 9명
        for idx, b in enumerate(home_batters, 1):
            if b and b.id:
                session.add(MatchLineup(
                    match_id=match.id,
                    club_id=match.home_club_id,
                    player_id=b.id,
                    position=b.position,
                    batting_order=idx,
                    is_starter=True
                ))

    # 2. IngameContext 캡슐화 객체 생성 및 초기화
    context = IngameContext(
        match_id=match.id,
        stadium_id=match.stadium_id,
        away_batters=away_batters,
        home_batters=home_batters,
        away_pitchers=[away_sp] + away_bp,
        home_pitchers=[home_sp] + home_bp,
        away_bench=away_bench,
        home_bench=home_bench,
    )

    context.current_away_pitcher_log = PitcherTracker(context.away_pitchers[0], True, 'away', 1, True, 0, 0, 0)
    context.current_home_pitcher_log = PitcherTracker(context.home_pitchers[0], True, 'home', 1, True, 0, 0, 0)
    context.away_pitcher_logs.append(context.current_away_pitcher_log)
    context.home_pitcher_logs.append(context.current_home_pitcher_log)

    current_pitcher_responsible_away = context.current_away_pitcher_log
    current_pitcher_responsible_home = context.current_home_pitcher_log

    def _apply_pitcher_change_if_needed():
        nonlocal current_pitcher_responsible_home, current_pitcher_responsible_away
        next_p = engine.decide_pitcher_change(context)
        if next_p is not None:
            if context.is_top and context.home_pitcher_idx < len(context.home_pitchers) - 1:
                if context.current_home_pitcher_log:
                    context.current_home_pitcher_log.exit_inning = context.inning
                    context.current_home_pitcher_log.exit_top = context.is_top
                    context.current_home_pitcher_log.exit_away_score = context.away_score
                    context.current_home_pitcher_log.exit_home_score = context.home_score

                context.home_pitcher_idx += 1
                on_base_cnt = sum(1 for r in [context.runner_1b, context.runner_2b, context.runner_3b] if r is not None)
                context.current_home_pitcher_log = PitcherTracker(
                    next_p, False, 'home', context.inning, context.is_top, context.away_score, context.home_score, on_base_cnt
                )
                context.home_pitcher_logs.append(context.current_home_pitcher_log)
                current_pitcher_responsible_home = context.current_home_pitcher_log
                context.current_pitcher = next_p
                if next_p.id:
                    collector.get(next_p.id).pitch_games += 1

            elif not context.is_top and context.away_pitcher_idx < len(context.away_pitchers) - 1:
                if context.current_away_pitcher_log:
                    context.current_away_pitcher_log.exit_inning = context.inning
                    context.current_away_pitcher_log.exit_top = context.is_top
                    context.current_away_pitcher_log.exit_away_score = context.away_score
                    context.current_away_pitcher_log.exit_home_score = context.home_score

                context.away_pitcher_idx += 1
                on_base_cnt = sum(1 for r in [context.runner_1b, context.runner_2b, context.runner_3b] if r is not None)
                context.current_away_pitcher_log = PitcherTracker(
                    next_p, False, 'away', context.inning, context.is_top, context.away_score, context.home_score, on_base_cnt
                )
                context.away_pitcher_logs.append(context.current_away_pitcher_log)
                current_pitcher_responsible_away = context.current_away_pitcher_log
                context.current_pitcher = next_p
                if next_p.id:
                    collector.get(next_p.id).pitch_games += 1

    context.logged_events.append(IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=context.sim_timestamp,
        state_type=IngameGameState.MATCH_START,
        inning=1,
        is_top=True,
        home_score=0,
        away_score=0
    ))

    max_innings = 11 if match.limit_extra_innings else 100
    game_over = False

    while not game_over:
        # 이닝 시작 전 수비 투수 교체 검토
        _apply_pitcher_change_if_needed()

        # 이닝 시작 전 수비팀 대수비 교체 검토
        defense_sub = engine.decide_defense_substitution(context)
        if defense_sub is not None:
            sub_pos_idx, sub_player = defense_sub
            if context.is_top:
                # 홈팀 수비
                if 0 <= sub_pos_idx < len(context.home_batters):
                    context.home_batters[sub_pos_idx] = sub_player
                    if sub_player in context.home_bench:
                        context.home_bench.remove(sub_player)
                    if sub_player.id:
                        collector.get(sub_player.id).bat_games += 1
            else:
                # 어웨이팀 수비
                if 0 <= sub_pos_idx < len(context.away_batters):
                    context.away_batters[sub_pos_idx] = sub_player
                    if sub_player in context.away_bench:
                        context.away_bench.remove(sub_player)
                    if sub_player.id:
                        collector.get(sub_player.id).bat_games += 1

        context.logged_events.append(IngameGameStateEvent(
            event_type=IngameEventType.GAME_STATE,
            sim_timestamp=context.sim_timestamp,
            state_type=IngameGameState.INNING_START,
            inning=context.inning,
            is_top=context.is_top,
            home_score=context.home_score,
            away_score=context.away_score
        ))

        context.scoreboard.outs = 0
        context.runner_1b = None
        context.runner_2b = None
        context.runner_3b = None

        if context.is_top:
            batters = context.away_batters
            context.current_pitcher = context.current_home_pitcher_log.pitcher
            defense_lineup = context.home_batters
            current_batter_idx = context.away_batter_idx
        else:
            batters = context.home_batters
            context.current_pitcher = context.current_away_pitcher_log.pitcher
            defense_lineup = context.away_batters
            current_batter_idx = context.home_batter_idx

        while context.scoreboard.outs < 3:
            # 9회말 또는 연장전 말에 홈팀이 리드하면 즉시 끝내기로 경기 종료
            if not context.is_top and context.inning >= 9 and context.home_score > context.away_score:
                game_over = True
                break

            context.current_batter = batters[current_batter_idx]

            # 1. 매 타석 전 수비팀 투수 교체 검토
            _apply_pitcher_change_if_needed()

            # 2. 매 타석 전 공격팀 대타(Pinch Hitter) 교체 검토
            pinch_hitter = engine.decide_pinch_hitter(context)
            if pinch_hitter is not None:
                batters[current_batter_idx] = pinch_hitter
                context.current_batter = pinch_hitter
                curr_bench = context.away_bench if context.is_top else context.home_bench
                if pinch_hitter in curr_bench:
                    curr_bench.remove(pinch_hitter)
                if pinch_hitter.id:
                    collector.get(pinch_hitter.id).bat_games += 1

            prev_outs = context.scoreboard.outs
            prev_away = context.away_score
            prev_home = context.home_score

            runs = simulate_plate_appearance(context, defense_lineup, decision_engine=engine, stat_collector=collector)


            # 아웃 추가량 기록
            outs_added = context.scoreboard.outs - prev_outs
            if outs_added > 0:
                if context.is_top:
                    context.current_home_pitcher_log.outs_recorded += outs_added
                else:
                    context.current_away_pitcher_log.outs_recorded += outs_added

            # 득점 발생 시 결승점 및 책임 투수 트래킹
            if runs > 0:
                if context.is_top:
                    context.away_score += runs
                    context.scoreboard.away_r = context.away_score
                    if prev_away <= prev_home and context.away_score > context.home_score:
                        context.go_ahead_pitcher_away = context.current_away_pitcher_log
                        context.go_ahead_resp_pitcher_home = current_pitcher_responsible_home
                else:
                    context.home_score += runs
                    context.scoreboard.home_r = context.home_score
                    if prev_home <= prev_away and context.home_score > context.away_score:
                        context.go_ahead_pitcher_home = context.current_home_pitcher_log
                        context.go_ahead_resp_pitcher_away = current_pitcher_responsible_away

            current_batter_idx = (current_batter_idx + 1) % 9

        if context.is_top:
            context.away_batter_idx = current_batter_idx
        else:
            context.home_batter_idx = current_batter_idx

        if game_over:
            break

        context.logged_events.append(IngameGameStateEvent(
            event_type=IngameEventType.GAME_STATE,
            sim_timestamp=context.sim_timestamp,
            state_type=IngameGameState.INNING_END,
            inning=context.inning,
            is_top=context.is_top,
            home_score=context.home_score,
            away_score=context.away_score
        ))

        context.sim_timestamp += 120.0

        # 경기 종료 판정
        if context.inning == 9 and context.is_top and context.home_score > context.away_score:
            game_over = True
        elif not context.is_top and context.inning >= 9:
            if context.home_score != context.away_score:
                game_over = True
            elif context.inning >= max_innings:
                game_over = True

        if not game_over:
            if context.is_top:
                context.is_top = False
            else:
                context.is_top = True
                context.inning += 1

    # 강판 점수 동기화
    if context.current_away_pitcher_log:
        context.current_away_pitcher_log.exit_inning = context.inning
        context.current_away_pitcher_log.exit_top = context.is_top
        context.current_away_pitcher_log.exit_away_score = context.away_score
        context.current_away_pitcher_log.exit_home_score = context.home_score

    if context.current_home_pitcher_log:
        context.current_home_pitcher_log.exit_inning = context.inning
        context.current_home_pitcher_log.exit_top = context.is_top
        context.current_home_pitcher_log.exit_away_score = context.away_score
        context.current_home_pitcher_log.exit_home_score = context.home_score

    match.home_score = context.home_score
    match.away_score = context.away_score
    match.status = MatchStatus.COMPLETED

    # 승/패/세 투수 결정 알고리즘 실행 (context 전달)
    determine_decisions(match, context)

    if match.winning_pitcher_id:
        collector.get(match.winning_pitcher_id).pitch_wins += 1
    if match.losing_pitcher_id:
        collector.get(match.losing_pitcher_id).pitch_losses += 1
    if match.save_pitcher_id:
        collector.get(match.save_pitcher_id).pitch_saves += 1

    context.logged_events.append(IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=context.sim_timestamp,
        state_type=IngameGameState.MATCH_END,
        inning=context.inning,
        is_top=context.is_top,
        home_score=context.home_score,
        away_score=context.away_score
    ))

    match.match_log = IngameInstructionLog(
        simulation_version=CONFIG.simulation_version,
        logged_events=context.logged_events
    )

    # 3. 경기 출전 선수들의 소진된 체력(current_energy) DB 세션 반영
    if session:
        all_participants = (
            context.away_pitchers + context.home_pitchers +
            context.away_batters + context.home_batters
        )
        for p in all_participants:
            if p and p.id:
                session.add(p)

    return collector



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
