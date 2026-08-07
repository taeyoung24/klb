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
)
from .simulation import simulate_plate_appearance
from .lineup import select_team_roster_for_match
from .utils import generate_mock_players


class PitcherTracker:
    def __init__(self, pitcher: Player, is_starter: bool, team: str, entry_inning: int, entry_top: bool, away_score: int, home_score: int, on_base_count: int):
        self.pitcher = pitcher
        self.is_starter = is_starter
        self.team = team  # 'away' or 'home'
        self.entry_inning = entry_inning
        self.entry_top = entry_top
        self.entry_away_score = away_score
        self.entry_home_score = home_score
        self.entry_on_base = on_base_count
        self.outs_recorded = 0
        self.exit_inning = None
        self.exit_top = None
        self.exit_away_score = None
        self.exit_home_score = None

    @property
    def entry_lead(self) -> int:
        if self.team == 'away':
            return self.entry_away_score - self.entry_home_score
        else:
            return self.entry_home_score - self.entry_away_score

    @property
    def exit_lead(self) -> int:
        if self.exit_away_score is None or self.exit_home_score is None:
            return self.entry_lead
        if self.team == 'away':
            return self.exit_away_score - self.exit_home_score
        else:
            return self.exit_home_score - self.exit_away_score


def determine_decisions(
    match: Match,
    away_logs: list[PitcherTracker],
    home_logs: list[PitcherTracker],
    go_ahead_pitcher_away: PitcherTracker | None,
    go_ahead_pitcher_home: PitcherTracker | None,
    go_ahead_responsible_pitcher_away: PitcherTracker | None,
    go_ahead_responsible_pitcher_home: PitcherTracker | None,
):
    """
    제출된 야구 규정에 맞추어 승리/패전/세이브 투수 ID를 결정합니다.
    """
    if match.away_score is None or match.home_score is None or match.away_score == match.home_score:
        match.winning_pitcher_id = None
        match.losing_pitcher_id = None
        match.save_pitcher_id = None
        return

    win_team = 'away' if match.away_score > match.home_score else 'home'
    win_logs = away_logs if win_team == 'away' else home_logs
    lose_logs = home_logs if win_team == 'away' else away_logs

    go_ahead_win_pitcher = go_ahead_pitcher_away if win_team == 'away' else go_ahead_pitcher_home
    go_ahead_lose_resp_pitcher = go_ahead_responsible_pitcher_home if win_team == 'away' else go_ahead_responsible_pitcher_away

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


def run_match(match: Match, session=None):
    """단일 매치를 시뮬레이션하여 세부 이벤트 대본을 남깁니다."""
    # 1. 라인업 및 투수 스쿼드 추출
    away_sp, away_bp, away_batters = select_team_roster_for_match(match.away_club_id, session=session)
    home_sp, home_bp, home_batters = select_team_roster_for_match(match.home_club_id, session=session)

    if away_sp and away_sp.id:
        match.away_starting_pitcher_id = away_sp.id
    if home_sp and home_sp.id:
        match.home_starting_pitcher_id = home_sp.id

    # 세션이 제공된 경우 DB에 MatchLineup 레코드 생성/저장
    if session and match.id:
        try:
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
            session.flush()
        except Exception as e:
            print("Failed to save MatchLineup in run_match:", e)

    away_pitchers = [away_sp] + away_bp
    home_pitchers = [home_sp] + home_bp

    away_p_idx = 0
    home_p_idx = 0

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

    # 투수 등판 트래커
    current_away_pitcher_log = PitcherTracker(away_pitchers[0], True, 'away', 1, True, 0, 0, 0)
    current_home_pitcher_log = PitcherTracker(home_pitchers[0], True, 'home', 1, True, 0, 0, 0)

    away_pitcher_logs: list[PitcherTracker] = [current_away_pitcher_log]
    home_pitcher_logs: list[PitcherTracker] = [current_home_pitcher_log]

    # 결승 리드 형성 및 책임 투수 트래킹
    go_ahead_pitcher_away: PitcherTracker | None = None
    go_ahead_pitcher_home: PitcherTracker | None = None
    go_ahead_resp_pitcher_away: PitcherTracker | None = None
    go_ahead_resp_pitcher_home: PitcherTracker | None = None

    current_pitcher_responsible_away = current_away_pitcher_log
    current_pitcher_responsible_home = current_home_pitcher_log

    max_innings = 11 if match.limit_extra_innings else 100
    game_over = False

    while not game_over:
        # 투수 교체 훅 (선발 5이닝/아웃15 이상 완료 시 계투 교체, 8/9회 마무리 교체 등)
        if is_top:
            # 홈팀 수비투수 교체 검토
            if home_p_idx < len(home_pitchers) - 1:
                # 선발 투수가 5이닝(15아웃) 이상 투구 후 다음 투수로 교체
                if current_home_pitcher_log.outs_recorded >= 15 or (inning >= 8 and home_p_idx < len(home_pitchers) - 1):
                    current_home_pitcher_log.exit_inning = inning
                    current_home_pitcher_log.exit_top = is_top
                    current_home_pitcher_log.exit_away_score = away_score
                    current_home_pitcher_log.exit_home_score = home_score

                    home_p_idx += 1
                    on_base_cnt = sum(1 for b in [None, None, None] if b is not None)
                    current_home_pitcher_log = PitcherTracker(
                        home_pitchers[home_p_idx], False, 'home', inning, is_top, away_score, home_score, on_base_cnt
                    )
                    home_pitcher_logs.append(current_home_pitcher_log)
                    current_pitcher_responsible_home = current_home_pitcher_log
        else:
            # 어웨이팀 수비투수 교체 검토
            if away_p_idx < len(away_pitchers) - 1:
                if current_away_pitcher_log.outs_recorded >= 15 or (inning >= 8 and away_p_idx < len(away_pitchers) - 1):
                    current_away_pitcher_log.exit_inning = inning
                    current_away_pitcher_log.exit_top = is_top
                    current_away_pitcher_log.exit_away_score = away_score
                    current_away_pitcher_log.exit_home_score = home_score

                    away_p_idx += 1
                    on_base_cnt = sum(1 for b in [None, None, None] if b is not None)
                    current_away_pitcher_log = PitcherTracker(
                        away_pitchers[away_p_idx], False, 'away', inning, is_top, away_score, home_score, on_base_cnt
                    )
                    away_pitcher_logs.append(current_away_pitcher_log)
                    current_pitcher_responsible_away = current_away_pitcher_log

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
            pitcher = current_home_pitcher_log.pitcher
            defense_lineup = home_batters
            current_batter_idx = away_batter_idx
        else:
            batters = home_batters
            pitcher = current_away_pitcher_log.pitcher
            defense_lineup = away_batters
            current_batter_idx = home_batter_idx

        while outs < 3:
            # 9회말 또는 연장전 말에 홈팀이 리드하면 즉시 끝내기로 경기 종료
            if not is_top and inning >= 9 and home_score > away_score:
                game_over = True
                break

            batter = batters[current_batter_idx]

            prev_outs = outs
            prev_away = away_score
            prev_home = home_score

            sim_timestamp, outs, bases, runs = simulate_plate_appearance(
                batter, pitcher, defense_lineup, bases, outs, logged_events, sim_timestamp
            )

            # 아웃 추가량 기록
            outs_added = outs - prev_outs
            if outs_added > 0:
                if is_top:
                    current_home_pitcher_log.outs_recorded += outs_added
                else:
                    current_away_pitcher_log.outs_recorded += outs_added

            # 득점 발생 시 결승점 및 책임 투수 트래킹
            if runs > 0:
                if is_top:
                    away_score += runs
                    # 어웨이가 결승 리드를 잡거나 굳히는 점수인지 판정
                    if prev_away <= prev_home and away_score > home_score:
                        go_ahead_pitcher_away = current_away_pitcher_log
                        go_ahead_resp_pitcher_home = current_pitcher_responsible_home
                else:
                    home_score += runs
                    if prev_home <= prev_away and home_score > away_score:
                        go_ahead_pitcher_home = current_home_pitcher_log
                        go_ahead_resp_pitcher_away = current_pitcher_responsible_away

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
        if inning == 9 and is_top and home_score > away_score:
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

    # 강판 점수 동기화
    current_away_pitcher_log.exit_inning = inning
    current_away_pitcher_log.exit_top = is_top
    current_away_pitcher_log.exit_away_score = away_score
    current_away_pitcher_log.exit_home_score = home_score

    current_home_pitcher_log.exit_inning = inning
    current_home_pitcher_log.exit_top = is_top
    current_home_pitcher_log.exit_away_score = away_score
    current_home_pitcher_log.exit_home_score = home_score

    match.home_score = home_score
    match.away_score = away_score
    match.status = MatchStatus.COMPLETED

    # 승/패/세 투수 결정 알고리즘 실행
    determine_decisions(
        match,
        away_pitcher_logs,
        home_pitcher_logs,
        go_ahead_pitcher_away,
        go_ahead_pitcher_home,
        go_ahead_resp_pitcher_away,
        go_ahead_resp_pitcher_home,
    )

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
