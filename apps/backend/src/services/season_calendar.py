import datetime
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Session, select, asc

from src.models import Match, MatchPlaceholder, WorldState
from src.enums import MatchStage
from src.utils.date_utils import sim_day_to_date, get_first_monday_of_october


class CalendarEvent(BaseModel):
    date: str  # YYYY-MM-DD
    sim_day: int
    label: str
    event_type: str  # SEASON_EVENT, ELITE_LEAGUE, POSTSEASON, DRAFT, SEASON_END 등 UI 카테고리용


# ==============================================================================
# 정규시즌 전/후반기 구분 설정 (상수)
# 추후 '인터리그(Interleague)' 이벤트 매치 추가 시 전반기 종료 및 후반기 시작 사이에
# 인터리그 일정이 삽입되도록 이 상수 및 관련 로직을 수정하면 됩니다.
# ==============================================================================
SPLIT_SERIES_INDEX = 24  # 총 48개 시리즈 중 전반기 24개 시리즈 (시리즈 Index 0~23)

CALENDAR_EVENTS_CACHE: dict[tuple[int, int], list[CalendarEvent]] = {}


def get_season_calendar_events(session: Session, year: int) -> list[CalendarEvent]:
    """
    특정 연도(year) 및 현재 current_sim_day에 해당하는 모든 시즌 캘린더 주요 이벤트를 생성/반환합니다.
    """
    world_state = session.get(WorldState, 1)
    current_sim_day = world_state.current_sim_day if world_state else 1

    cache_key = (year, current_sim_day)
    if cache_key in CALENDAR_EVENTS_CACHE:
        return CALENDAR_EVENTS_CACHE[cache_key]

    events: list[CalendarEvent] = []
    
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    
    # 1. 해당 연도의 sim_day 범위를 구함 (2026년 기준 1-indexed)
    jan_1_sim_day = (start_date - datetime.date(2026, 1, 1)).days + 1
    dec_31_sim_day = (end_date - datetime.date(2026, 1, 1)).days + 1

    # 2. 10월 첫째 주차 월요일 -> 신인 드래프트
    draft_date = get_first_monday_of_october(year)
    draft_sim_day = (draft_date - datetime.date(2026, 1, 1)).days + 1
    events.append(CalendarEvent(
        date=draft_date.strftime("%Y-%m-%d"),
        sim_day=draft_sim_day,
        label="신인 드래프트",
        event_type="DRAFT"
    ))

    # 3. 정규시즌 매치 조회 및 개막/전반기/후반기/종료 라벨 생성 (스칼라 sim_day 쿼리로 경량화)
    reg_sim_days = session.exec(
        select(Match.sim_day)
        .where(Match.stage == MatchStage.REGULAR)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
        .order_by(asc(Match.sim_day))
    ).all()

    if reg_sim_days:
        reg_days = sorted(list(set(reg_sim_days)))
        
        # 3-1. 정규시즌 개막
        opening_day = reg_days[0]
        opening_date = sim_day_to_date(opening_day, base_year=2026)
        events.append(CalendarEvent(
            date=opening_date.strftime("%Y-%m-%d"),
            sim_day=opening_day,
            label="정규시즌 개막",
            event_type="SEASON_EVENT"
        ))

        # 3-2. 정규시즌 종료
        reg_end_day = reg_days[-1]
        reg_end_date = sim_day_to_date(reg_end_day, base_year=2026)
        events.append(CalendarEvent(
            date=reg_end_date.strftime("%Y-%m-%d"),
            sim_day=reg_end_day,
            label="정규시즌 종료",
            event_type="SEASON_EVENT"
        ))

        # 3-3. 전반기 종료 및 후반기 시작 (24번째 시리즈 기준)
        # 매주 2개 시리즈(주중/주말), 12주차 = 24시리즈. 각 시리즈 3일 (총 72경기일)
        if len(reg_days) >= 72:
            first_half_end_day = reg_days[71]  # 24시리즈 마감일 (72번째 경기일)
            second_half_start_day = reg_days[72]  # 25시리즈 시작일 (73번째 경기일)

            fh_end_date = sim_day_to_date(first_half_end_day, base_year=2026)
            sh_start_date = sim_day_to_date(second_half_start_day, base_year=2026)

            events.append(CalendarEvent(
                date=fh_end_date.strftime("%Y-%m-%d"),
                sim_day=first_half_end_day,
                label="RS 전반기 종료",
                event_type="SEASON_EVENT"
            ))

            events.append(CalendarEvent(
                date=sh_start_date.strftime("%Y-%m-%d"),
                sim_day=second_half_start_day,
                label="RS 후반기 시작",
                event_type="SEASON_EVENT"
            ))

    # 4. 크라운 정예리그 (EL: Elite League) (스칼라 sim_day 쿼리로 경량화)
    elite_sim_days = session.exec(
        select(Match.sim_day)
        .where(Match.stage == MatchStage.ELITE)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
        .order_by(asc(Match.sim_day))
    ).all()

    if elite_sim_days:
        elite_days = sorted(list(set(elite_sim_days)))
        
        # PS 개막 (EL 첫째 날)
        el_start_day = elite_days[0]
        el_start_date = sim_day_to_date(el_start_day, base_year=2026)
        events.append(CalendarEvent(
            date=el_start_date.strftime("%Y-%m-%d"),
            sim_day=el_start_day,
            label="PS 개막",
            event_type="POSTSEASON"
        ))

        # EL {n}일차
        for idx, day in enumerate(elite_days, start=1):
            d_date = sim_day_to_date(day, base_year=2026)
            events.append(CalendarEvent(
                date=d_date.strftime("%Y-%m-%d"),
                sim_day=day,
                label=f"EL {idx}일차",
                event_type="ELITE_LEAGUE"
            ))

        # EL 종료 (EL 마지막 날)
        el_end_day = elite_days[-1]
        el_end_date = sim_day_to_date(el_end_day, base_year=2026)
        events.append(CalendarEvent(
            date=el_end_date.strftime("%Y-%m-%d"),
            sim_day=el_end_day,
            label="EL 종료",
            event_type="ELITE_LEAGUE"
        ))

    # 5. 녹아웃 토너먼트 (PS 8강/4강/KS) - MatchPlaceholder 시작일 및 KNOCKOUT 경기일 기반 일자별 라벨링
    ko_sim_days = session.exec(
        select(Match.sim_day)
        .where(Match.stage == MatchStage.KNOCKOUT)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
        .order_by(asc(Match.sim_day))
    ).all()

    placeholders = session.exec(
        select(MatchPlaceholder)
        .where(MatchPlaceholder.sim_day >= jan_1_sim_day)
        .where(MatchPlaceholder.sim_day <= dec_31_sim_day)
        .order_by(asc(MatchPlaceholder.sim_day))
    ).all()

    # 라운드별 시작 sim_day 파악
    q_start = min([p.sim_day for p in placeholders if p.round == "ROUND_OF_8"], default=None)
    s_start = min([p.sim_day for p in placeholders if p.round == "SEMI_FINAL"], default=None)
    f_start = min([p.sim_day for p in placeholders if p.round == "FINAL"], default=None)

    # 8강 라운드 일자 수집 (치러진 경기는 실제 Match.sim_day, 미래 경기는 예정일)
    if q_start:
        q_end = (s_start - 1) if s_start else (q_start + 2)
        q_days_set = set()
        # 과거/현재 치러진 8강 경기
        for d in ko_sim_days:
            if q_start <= d <= q_end and d <= current_sim_day:
                q_days_set.add(d)
        # 미래 예정 8강 경기일 (Placeholder 기준 Bo3 기본 예정: q_start, q_start + 1)
        for d in [q_start, q_start + 1]:
            if d > current_sim_day and d <= q_end:
                q_days_set.add(d)

        q_days = sorted(list(q_days_set))
        for idx, day in enumerate(q_days, start=1):
            d_date = sim_day_to_date(day, base_year=2026)
            events.append(CalendarEvent(
                date=d_date.strftime("%Y-%m-%d"),
                sim_day=day,
                label=f"PS 8강 {idx}차전",
                event_type="POSTSEASON"
            ))

    # 4강 라운드 일자 수집
    if s_start:
        s_end = (f_start - 1) if f_start else (s_start + 6)
        s_days_set = set()
        # 과거/현재 치러진 4강 경기
        for d in ko_sim_days:
            if s_start <= d <= s_end and d <= current_sim_day:
                s_days_set.add(d)
        # 미래 예정 4강 경기일 (Placeholder 기준 Bo5 기본 5일 예정)
        for d in [s_start, s_start + 1, s_start + 2, s_start + 3, s_start + 4]:
            if d > current_sim_day and d <= s_end:
                s_days_set.add(d)

        s_days = sorted(list(s_days_set))
        for idx, day in enumerate(s_days, start=1):
            d_date = sim_day_to_date(day, base_year=2026)
            events.append(CalendarEvent(
                date=d_date.strftime("%Y-%m-%d"),
                sim_day=day,
                label=f"PS 4강 {idx}차전",
                event_type="POSTSEASON"
            ))

    # 결승 라운드 일자 수집 (KROWN SERIES)
    if f_start:
        f_days_set = set()
        # 과거/현재 치러진 결승 경기
        for d in ko_sim_days:
            if d >= f_start and d <= current_sim_day:
                f_days_set.add(d)
        # 미래 예정 결승 경기일 (Placeholder 기준 Bo7 기본 예정: 3경 경기 후 1일 휴식 패턴)
        for d in [f_start, f_start + 1, f_start + 2, f_start + 4, f_start + 5, f_start + 6, f_start + 7]:
            if d > current_sim_day:
                f_days_set.add(d)

        f_days = sorted(list(f_days_set))
        for idx, day in enumerate(f_days, start=1):
            d_date = sim_day_to_date(day, base_year=2026)
            events.append(CalendarEvent(
                date=d_date.strftime("%Y-%m-%d"),
                sim_day=day,
                label=f"KS {idx}차전",
                event_type="POSTSEASON"
            ))

    # 6. {YYYY} 시즌 종료 (KNOCKOUT 실제/예정 경기 포함 최댓값 산출)
    all_season_sim_days: list[int] = []
    if reg_sim_days:
        all_season_sim_days.extend(reg_sim_days)
    if elite_sim_days:
        all_season_sim_days.extend(elite_sim_days)
    if ko_sim_days:
        all_season_sim_days.extend(ko_sim_days)
    for p in placeholders:
        all_season_sim_days.append(p.sim_day)
    if f_start:
        all_season_sim_days.append(f_start + 7)

    last_season_day: Optional[int] = max(all_season_sim_days) if all_season_sim_days else None

    if last_season_day:
        season_end_date = sim_day_to_date(last_season_day, base_year=2026)
        events.append(CalendarEvent(
            date=season_end_date.strftime("%Y-%m-%d"),
            sim_day=last_season_day,
            label=f"{year} 시즌 종료",
            event_type="SEASON_END"
        ))

    # 7. 경기 없는 날 (NO_MATCH) 처리
    # 경기가 치러지는 모든 날짜(정규시즌, EL, 녹아웃) + 주요 행사일의 종합 집합
    all_busy_days = set()
    if reg_sim_days:
        all_busy_days.update(reg_sim_days)
    if elite_sim_days:
        all_busy_days.update(elite_sim_days)
    if ko_sim_days:
        all_busy_days.update(ko_sim_days)
    for e in events:
        all_busy_days.add(e.sim_day)

    if reg_sim_days and last_season_day:
        season_first_day = reg_days[0]
        for s_day in range(season_first_day, last_season_day + 1):
            if s_day not in all_busy_days:
                s_date = sim_day_to_date(s_day, base_year=2026)
                events.append(CalendarEvent(
                    date=s_date.strftime("%Y-%m-%d"),
                    sim_day=s_day,
                    label="경기 없는 날",
                    event_type="NO_MATCH"
                ))

    CALENDAR_EVENTS_CACHE[cache_key] = events
    return events
