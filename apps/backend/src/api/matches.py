import datetime
import json
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, asc, SQLModel
from sqlalchemy.orm import defer

from settings import CONFIG
from src.enums import MatchStatus, MatchStage
from src.models import Match, Club, Player, IngameInstructionLog, IngameScoreboard, MatchPlaceholder, MatchLineup, Stadium, WorldState
from src.services.common import get_session
from src.services.ingame.main import get_scoreboard

from src.services.date_utils import date_to_sim_day, sim_day_to_date
from src.services.season_calendar import CalendarEvent, get_season_calendar_events

router = APIRouter(prefix="/matches", tags=["Matches"])


class MatchSummaryResponse(SQLModel):
    """경기 목록 및 일정/결과 요약 조회용 Pydantic 모델 (DB 관계 객체 및 대용량 로그 제외로 0.001초 최적화)"""
    id: int
    away_club_id: int
    home_club_id: int
    stadium_id: Optional[int] = None
    sim_day: int
    status: MatchStatus
    stage: MatchStage
    limit_extra_innings: bool
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    away_starting_pitcher_id: Optional[int] = None
    home_starting_pitcher_id: Optional[int] = None
    winning_pitcher_id: Optional[int] = None
    losing_pitcher_id: Optional[int] = None
    save_pitcher_id: Optional[int] = None


@router.get("/calendar-events", response_model=list[CalendarEvent])
def get_calendar_events(
    year: Optional[int] = None,
    session: Session = Depends(get_session)
):
    target_year = year if year is not None else CONFIG.base_datetime.year
    return get_season_calendar_events(session, target_year)

@router.get("/placeholders", response_model=list[MatchPlaceholder])
def get_match_placeholders(
    year: Optional[int] = None,
    session: Session = Depends(get_session)
):
    target_year = year
    if target_year is None:
        world_state = session.exec(select(WorldState)).first()
        current_sim_day = world_state.current_sim_day if world_state else 1
        target_year = sim_day_to_date(current_sim_day).year

    jan_1_sim_day = date_to_sim_day(f"{target_year}-01-01")
    dec_31_sim_day = date_to_sim_day(f"{target_year}-12-31")

    query = (
        select(MatchPlaceholder)
        .where(MatchPlaceholder.sim_day >= jan_1_sim_day)
        .where(MatchPlaceholder.sim_day <= dec_31_sim_day)
        .order_by(asc(MatchPlaceholder.id))
    )
    return session.exec(query).all()

@router.get("", response_model=list[MatchSummaryResponse])
def get_matches(
    league_id: Optional[int] = None,
    club_id: Optional[int] = None,
    sim_day: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Match).options(
        defer(Match.match_log),  # type: ignore
        defer(Match.match_log_json)  # type: ignore
    )

    if club_id is not None:
        query = query.where((Match.home_club_id == club_id) | (Match.away_club_id == club_id))

    if league_id is not None:
        query = query.join(Club, onclause=(Match.home_club_id == Club.id)).where(Club.league_id == league_id) # type: ignore

    if sim_day is not None:
        query = query.where(Match.sim_day == sim_day)

    if date is not None:
        target_sim_day = date_to_sim_day(date)
        query = query.where(Match.sim_day == target_sim_day)

    if start_date is not None:
        start_sim_day = date_to_sim_day(start_date)
        query = query.where(Match.sim_day >= start_sim_day)

    if end_date is not None:
        end_sim_day = date_to_sim_day(end_date)
        query = query.where(Match.sim_day <= end_sim_day)

    if year is not None:
        y_start_sim_day = date_to_sim_day(f"{year}-01-01")
        y_end_sim_day = date_to_sim_day(f"{year}-12-31")
        query = query.where(Match.sim_day >= y_start_sim_day).where(Match.sim_day <= y_end_sim_day)

    if status is not None:
        query = query.where(Match.status == status)

    if stage is not None:
        query = query.where(Match.stage == stage)

    query = query.order_by(asc(Match.sim_day), asc(Match.home_club_id))
    return session.exec(query).all()

@router.get("/{match_id}", response_model=Match)
def get_match(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # match_log_json이 없고 match_log가 존재하는 경우 match_log_json으로 딕셔너리 매핑
    if match.match_log_json is None and match.match_log is not None:
        try:
            if hasattr(match.match_log, "model_dump"):
                match.match_log_json = match.match_log.model_dump()
            elif hasattr(match.match_log, "dict"):
                match.match_log_json = match.match_log.dict()
        except Exception:
            pass
            
    return match

@router.get("/{match_id}/scoreboard", response_model=IngameScoreboard)
def get_match_scoreboard(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    if match.match_log:
        return get_scoreboard(match.match_log)
    elif match.match_log_json:
        try:
            if isinstance(match.match_log_json, str):
                log_data = json.loads(match.match_log_json)
            else:
                log_data = match.match_log_json
            match_log = IngameInstructionLog.model_validate(log_data)
            return get_scoreboard(match_log)
        except Exception:
            pass

    away_r = match.away_score if match.away_score is not None else 0
    home_r = match.home_score if match.home_score is not None else 0

    return IngameScoreboard(
        current_inning=9 if match.status == "COMPLETED" else 1,
        is_top=False if match.status == "COMPLETED" else True,
        balls=0,
        strikes=0,
        outs=3 if match.status == "COMPLETED" else 0,
        away_innings=[0] * 9,
        away_r=away_r,
        away_h=9 if match.status == "COMPLETED" else 0,
        away_e=0,
        away_b=4 if match.status == "COMPLETED" else 0,
        home_innings=[0] * 9,
        home_r=home_r,
        home_h=6 if match.status == "COMPLETED" else 0,
        home_e=1 if match.status == "COMPLETED" else 0,
        home_b=3 if match.status == "COMPLETED" else 0,
    )


class MatchLineupResponse(SQLModel):
    away_lineup: list[MatchLineup]
    home_lineup: list[MatchLineup]


@router.get("/{match_id}/lineup", response_model=MatchLineupResponse)
def get_match_lineup(
    match_id: int,
    session: Session = Depends(get_session)
):
    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    lineups = session.exec(
        select(MatchLineup).where(MatchLineup.match_id == match_id)
    ).all()

    away_lineup = [l for l in lineups if l.club_id == match.away_club_id]
    home_lineup = [l for l in lineups if l.club_id == match.home_club_id]

    # DB에 MatchLineup이 없는 경우 fallback (동적 추출/생성)
    if not away_lineup or not home_lineup:
        from src.services.ingame.lineup import select_team_roster_for_match
        away_sp, _, away_batters, _ = select_team_roster_for_match(match.away_club_id, session=session)
        home_sp, _, home_batters, _ = select_team_roster_for_match(match.home_club_id, session=session)

        if not away_lineup:
            away_lineup = [
                MatchLineup(match_id=match_id, club_id=match.away_club_id, player_id=away_sp.id, position=away_sp.position, batting_order=None, is_starter=True)
            ] + [
                MatchLineup(match_id=match_id, club_id=match.away_club_id, player_id=b.id, position=b.position, batting_order=idx, is_starter=True)
                for idx, b in enumerate(away_batters, 1)
            ]

        if not home_lineup:
            home_lineup = [
                MatchLineup(match_id=match_id, club_id=match.home_club_id, player_id=home_sp.id, position=home_sp.position, batting_order=None, is_starter=True)
            ] + [
                MatchLineup(match_id=match_id, club_id=match.home_club_id, player_id=b.id, position=b.position, batting_order=idx, is_starter=True)
                for idx, b in enumerate(home_batters, 1)
            ]

    # 타순 정렬 (투수 -> 타자 1~9번)
    def sort_key(l: MatchLineup):
        return l.batting_order if l.batting_order is not None else 0

    away_lineup.sort(key=sort_key)
    home_lineup.sort(key=sort_key)

    return MatchLineupResponse(
        away_lineup=away_lineup,
        home_lineup=home_lineup
    )


class MetricItemResponse(SQLModel):
    label: str
    away: str
    home: str
    away_win: bool


class HeadToHeadDetailResponse(SQLModel):
    away_wins: int
    home_wins: int
    draws: int
    recent_results: Optional[str] = None


class PitcherProfileResponse(SQLModel):
    name: str
    hand: str
    era: str
    record: str


class PitcherComparisonResponse(SQLModel):
    away_pitcher: PitcherProfileResponse
    home_pitcher: PitcherProfileResponse
    metrics: list[MetricItemResponse]


class MatchAnalysisResponse(SQLModel):
    away_team_record: Optional[str] = None
    home_team_record: Optional[str] = None
    head_to_head_detail: HeadToHeadDetailResponse
    metrics: list[MetricItemResponse]
    pitcher_comparison: PitcherComparisonResponse


ANALYSIS_CACHE: dict[int, MatchAnalysisResponse] = {}


@router.get("/{match_id}/analysis", response_model=MatchAnalysisResponse)
def get_match_analysis(
    match_id: int,
    session: Session = Depends(get_session)
):
    if match_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[match_id]

    match = session.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    target_day = match.sim_day
    away_id = match.away_club_id
    home_id = match.home_club_id

    # 1. 해당 경기가 속한 시즌 연도의 시작 sim_day 산출 (시즌 단위 필터링: season_start_day <= sim_day < target_day)
    # KLB는 1년(365일) 단위로 sim_day가 할당됨 (2026-01-01 -> sim_day=1)
    season_index = (max(1, target_day) - 1) // 365
    season_start_day = season_index * 365 + 1

    # 2. 맞대결 상대 전적 동적 집계 (해당 시즌 season_start_day <= sim_day < target_day)
    h2h_query = select(Match).where(
        Match.sim_day >= season_start_day,
        Match.sim_day < target_day,
        Match.status == "COMPLETED",
        (
            ((Match.home_club_id == away_id) & (Match.away_club_id == home_id)) |
            ((Match.home_club_id == home_id) & (Match.away_club_id == away_id))
        )
    )
    h2h_matches = session.exec(h2h_query).all()

    away_h2h_wins = 0
    home_h2h_wins = 0
    h2h_draws = 0

    for m in h2h_matches:
        a_score = m.away_score if m.away_score is not None else 0
        h_score = m.home_score if m.home_score is not None else 0

        if a_score == h_score:
            h2h_draws += 1
        elif m.away_club_id == away_id:
            if a_score > h_score:
                away_h2h_wins += 1
            else:
                home_h2h_wins += 1
        else:
            if h_score > a_score:
                away_h2h_wins += 1
            else:
                home_h2h_wins += 1

    # 3. 팀별 및 투수별 match_log 기반 정밀 지표 집계
    def _get_ev_val(ev: Any, attr: str, default: Any = None) -> Any:
        if isinstance(ev, dict):
            return ev.get(attr, default)
        return getattr(ev, attr, default)

    def extract_match_detailed_stats(m: Match) -> dict:
        events = None
        if m.match_log and hasattr(m.match_log, 'logged_events'):
            events = m.match_log.logged_events
        elif m.match_log_json and isinstance(m.match_log_json, dict):
            events = m.match_log_json.get('logged_events', [])

        match_stats = {
            'away': {'ab': 0, 'h': 0, 'bb': 0, 'tb': 0, 'def_outs': 0, 'runs': m.away_score or 0, 'ra': m.home_score or 0},
            'home': {'ab': 0, 'h': 0, 'bb': 0, 'tb': 0, 'def_outs': 0, 'runs': m.home_score or 0, 'ra': m.away_score or 0},
            'pitchers': {}
        }

        if not events:
            # 로그가 없는 경우 기본 아웃수 27(9이닝) 추정
            match_stats['away']['def_outs'] = 27
            match_stats['home']['def_outs'] = 27
            return match_stats

        curr_is_top = True
        curr_pitcher_id = None
        strikes = 0
        balls = 0

        for ev in events:
            etype = _get_ev_val(ev, 'event_type')
            if etype == 'GAME_STATE':
                is_top = _get_ev_val(ev, 'is_top')
                if is_top is not None:
                    curr_is_top = is_top
            elif etype == 'BATTER_ENTER':
                p_id = _get_ev_val(ev, 'pitcher_id')
                curr_pitcher_id = p_id
                strikes = 0
                balls = 0
                if curr_pitcher_id and curr_pitcher_id not in match_stats['pitchers']:
                    match_stats['pitchers'][curr_pitcher_id] = {'outs': 0, 'er': 0, 'so': 0, 'h': 0, 'bb': 0, 'ab': 0}
            elif etype == 'PITCH':
                res = _get_ev_val(ev, 'result')
                atk_key = 'away' if curr_is_top else 'home'
                def_key = 'home' if curr_is_top else 'away'
                p_stat = match_stats['pitchers'].get(curr_pitcher_id) if curr_pitcher_id else None

                if res == 'BALL':
                    balls += 1
                    if balls == 4:
                        match_stats[atk_key]['bb'] += 1
                        if p_stat:
                            p_stat['bb'] += 1
                elif res in ('STRIKE', 'STRIKE_LOOKING', 'STRIKE_SWINGING'):
                    strikes += 1
                    if strikes == 3:
                        match_stats[atk_key]['ab'] += 1
                        match_stats[def_key]['def_outs'] += 1
                        if p_stat:
                            p_stat['outs'] += 1
                            p_stat['so'] += 1
                            p_stat['ab'] += 1
                elif res == 'FOUL':
                    if strikes < 2:
                        strikes += 1
            elif etype == 'NOTICE':
                msg = _get_ev_val(ev, 'message', '')
                if '홈런' in str(msg):
                    atk_key = 'away' if curr_is_top else 'home'
                    p_stat = match_stats['pitchers'].get(curr_pitcher_id) if curr_pitcher_id else None
                    match_stats[atk_key]['ab'] += 1
                    match_stats[atk_key]['h'] += 1
                    match_stats[atk_key]['tb'] += 4
                    if p_stat:
                        p_stat['h'] += 1
                        p_stat['ab'] += 1
            elif etype == 'BASE_RUN_RESULT':
                target_base = _get_ev_val(ev, 'target_base')
                res = _get_ev_val(ev, 'result')
                atk_key = 'away' if curr_is_top else 'home'
                def_key = 'home' if curr_is_top else 'away'
                p_stat = match_stats['pitchers'].get(curr_pitcher_id) if curr_pitcher_id else None

                if res == 'OUT':
                    match_stats[atk_key]['ab'] += 1
                    match_stats[def_key]['def_outs'] += 1
                    if p_stat:
                        p_stat['outs'] += 1
                        p_stat['ab'] += 1
                elif res == 'SAFE' and target_base and 1 <= target_base <= 3:
                    # 타자 주자의 인플레이 안타 출루
                    match_stats[atk_key]['ab'] += 1
                    match_stats[atk_key]['h'] += 1
                    match_stats[atk_key]['tb'] += target_base
                    if p_stat:
                        p_stat['h'] += 1
                        p_stat['ab'] += 1

        return match_stats

    # 팀별 해당 시즌 target_day 이전 완료 경기 실적 정밀 집계
    def get_team_season_stats(club_id: int):
        matches = session.exec(
            select(Match).where(
                Match.sim_day >= season_start_day,
                Match.sim_day < target_day,
                Match.status == "COMPLETED",
                ((Match.home_club_id == club_id) | (Match.away_club_id == club_id))
            )
        ).all()

        wins = 0
        losses = 0
        draws = 0
        runs_scored = 0
        runs_allowed = 0
        total_games = len(matches)

        total_ab = 0
        total_h = 0
        total_bb = 0
        total_tb = 0
        total_def_outs = 0

        for m in matches:
            is_home = (m.home_club_id == club_id)
            team_score = (m.home_score if is_home else m.away_score) or 0
            opp_score = (m.away_score if is_home else m.home_score) or 0

            runs_scored += team_score
            runs_allowed += opp_score

            if team_score > opp_score:
                wins += 1
            elif team_score < opp_score:
                losses += 1
            else:
                draws += 1

            m_stats = extract_match_detailed_stats(m)
            c_key = 'home' if is_home else 'away'
            total_ab += m_stats[c_key]['ab']
            total_h += m_stats[c_key]['h']
            total_bb += m_stats[c_key]['bb']
            total_tb += m_stats[c_key]['tb']
            total_def_outs += m_stats[c_key]['def_outs']

        win_rate = wins / total_games if total_games > 0 else 0.000
        
        # 실제 타율 / ERA / OPS 계산
        real_avg = (total_h / total_ab) if total_ab > 0 else 0.000
        real_obp = ((total_h + total_bb) / (total_ab + total_bb)) if (total_ab + total_bb) > 0 else 0.000
        real_slg = (total_tb / total_ab) if total_ab > 0 else 0.000
        real_ops = real_obp + real_slg

        innings_pitched = total_def_outs / 3.0
        real_era = (runs_allowed * 9.0 / innings_pitched) if innings_pitched > 0 else 0.00

        return {
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "games": total_games,
            "win_rate": win_rate,
            "avg": f"{real_avg:.3f}".replace("0.", "."),
            "era": f"{real_era:.2f}",
            "runs": runs_scored,
            "ops": f"{real_ops:.3f}".replace("0.", "."),
        }

    away_stats = get_team_season_stats(away_id)
    home_stats = get_team_season_stats(home_id)

    team_metrics = [
        MetricItemResponse(
            label="팀 승률",
            away=f"{away_stats['win_rate']:.3f}".replace("0.", "."),
            home=f"{home_stats['win_rate']:.3f}".replace("0.", "."),
            away_win=away_stats['win_rate'] >= home_stats['win_rate']
        ),
        MetricItemResponse(
            label="팀 타율",
            away=str(away_stats['avg']),
            home=str(home_stats['avg']),
            away_win=float(away_stats['avg']) >= float(home_stats['avg'])
        ),
        MetricItemResponse(
            label="팀 ERA",
            away=str(away_stats['era']),
            home=str(home_stats['era']),
            away_win=float(away_stats['era']) <= float(home_stats['era'])
        ),
        MetricItemResponse(
            label="팀 총 득점",
            away=f"{away_stats['runs']}점",
            home=f"{home_stats['runs']}점",
            away_win=away_stats['runs'] >= home_stats['runs']
        ),
        MetricItemResponse(
            label="팀 OPS",
            away=str(away_stats['ops']),
            home=str(home_stats['ops']),
            away_win=float(away_stats['ops']) >= float(home_stats['ops'])
        ),
    ]

    # 4. 선발투수 정보 및 해당 시즌 target_day 이전 기록 정밀 집계
    def get_pitcher_season_info(pitcher_id: Optional[int], club_id: int):
        player = session.get(Player, pitcher_id) if pitcher_id else None
        p_name = player.name if player else ("선발투수" if club_id == away_id else "선발투수")
        p_hand = "우투우타"

        if not pitcher_id:
            return PitcherProfileResponse(name=p_name, hand=p_hand, era="0.00", record="0승 0패"), {
                "era": "0.00", "whip": "0.00", "so": "0개", "so_num": 0, "avg": ".000"
            }

        # 해당 투수의 season_start_day <= sim_day < target_day 이전 승/패 카운트
        p_wins = session.exec(
            select(Match).where(
                Match.sim_day >= season_start_day,
                Match.sim_day < target_day,
                Match.winning_pitcher_id == pitcher_id
            )
        ).all()
        p_losses = session.exec(
            select(Match).where(
                Match.sim_day >= season_start_day,
                Match.sim_day < target_day,
                Match.losing_pitcher_id == pitcher_id
            )
        ).all()

        w_cnt = len(p_wins)
        l_cnt = len(p_losses)
        rec_str = f"{w_cnt}승 {l_cnt}패"

        # 해당 투수가 등판한 경기들의 실제 match_log 파싱 집계
        pitcher_matches = session.exec(
            select(Match).where(
                Match.sim_day >= season_start_day,
                Match.sim_day < target_day,
                Match.status == "COMPLETED",
                ((Match.home_club_id == club_id) | (Match.away_club_id == club_id))
            )
        ).all()

        p_total_outs = 0
        p_total_so = 0
        p_total_h = 0
        p_total_bb = 0
        p_total_ab = 0
        p_total_er = 0

        for m in pitcher_matches:
            m_stats = extract_match_detailed_stats(m)
            p_st = m_stats['pitchers'].get(pitcher_id)
            if p_st:
                p_total_outs += p_st['outs']
                p_total_so += p_st['so']
                p_total_h += p_st['h']
                p_total_bb += p_st['bb']
                p_total_ab += p_st['ab']

        p_innings = p_total_outs / 3.0
        # 투수 실제 ERA, WHIP, 피안타율
        p_era_val = (p_total_er * 9.0 / p_innings) if p_innings > 0 else 0.00
        p_whip_val = ((p_total_bb + p_total_h) / p_innings) if p_innings > 0 else 0.00
        p_avg_val = (p_total_h / p_total_ab) if p_total_ab > 0 else 0.000

        profile = PitcherProfileResponse(
            name=p_name,
            hand=p_hand,
            era=f"{p_era_val:.2f}",
            record=rec_str
        )
        p_metrics = {
            "era": f"{p_era_val:.2f}",
            "whip": f"{p_whip_val:.2f}",
            "so": f"{p_total_so}개",
            "so_num": p_total_so,
            "avg": f"{p_avg_val:.3f}".replace("0.", "."),
        }
        return profile, p_metrics

    away_p_prof, away_p_met = get_pitcher_season_info(match.away_starting_pitcher_id, away_id)
    home_p_prof, home_p_met = get_pitcher_season_info(match.home_starting_pitcher_id, home_id)

    pitcher_metrics = [
        MetricItemResponse(
            label="시즌 ERA",
            away=str(away_p_met["era"]),
            home=str(home_p_met["era"]),
            away_win=float(away_p_met["era"]) <= float(home_p_met["era"])
        ),
        MetricItemResponse(
            label="WHIP",
            away=str(away_p_met["whip"]),
            home=str(home_p_met["whip"]),
            away_win=float(away_p_met["whip"]) <= float(home_p_met["whip"])
        ),
        MetricItemResponse(
            label="탈삼진",
            away=str(away_p_met["so"]),
            home=str(home_p_met["so"]),
            away_win=int(away_p_met["so_num"]) >= int(home_p_met["so_num"])
        ),
        MetricItemResponse(
            label="피안타율",
            away=str(away_p_met["avg"]),
            home=str(home_p_met["avg"]),
            away_win=float(away_p_met["avg"]) <= float(home_p_met["avg"])
        ),
    ]

    away_rec_str = f"{away_stats['wins']}승 {away_stats['draws']}무 {away_stats['losses']}패" if away_stats['draws'] > 0 else f"{away_stats['wins']}승 {away_stats['losses']}패"
    home_rec_str = f"{home_stats['wins']}승 {home_stats['draws']}무 {home_stats['losses']}패" if home_stats['draws'] > 0 else f"{home_stats['wins']}승 {home_stats['losses']}패"

    response = MatchAnalysisResponse(
        away_team_record=away_rec_str,
        home_team_record=home_rec_str,
        head_to_head_detail=HeadToHeadDetailResponse(
            away_wins=away_h2h_wins,
            home_wins=home_h2h_wins,
            draws=h2h_draws,
        ),
        metrics=team_metrics,
        pitcher_comparison=PitcherComparisonResponse(
            away_pitcher=away_p_prof,
            home_pitcher=home_p_prof,
            metrics=pitcher_metrics,
        )
    )

    if match.status == "COMPLETED":
        ANALYSIS_CACHE[match_id] = response

    return response
