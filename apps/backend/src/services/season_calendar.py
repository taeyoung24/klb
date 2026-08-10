import datetime
from typing import Optional
from pydantic import BaseModel
from sqlmodel import Session, select, asc

from src.models import Match, MatchPlaceholder
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


def get_season_calendar_events(session: Session, year: int) -> list[CalendarEvent]:
    """
    특정 연도(year)에 해당하는 모든 시즌 캘린더 주요 이벤트를 생성/반환합니다.
    """
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

    # 3. 정규시즌 매치 조회 및 개막/전반기/후반기/종료 라벨 생성
    reg_matches = session.exec(
        select(Match)
        .where(Match.stage == MatchStage.REGULAR)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
        .order_by(asc(Match.sim_day))
    ).all()

    if reg_matches:
        reg_days = sorted(list(set(m.sim_day for m in reg_matches)))
        
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

    # 4. 크라운 정예리그 (EL: Elite League)
    elite_matches = session.exec(
        select(Match)
        .where(Match.stage == MatchStage.ELITE)
        .where(Match.sim_day >= jan_1_sim_day)
        .where(Match.sim_day <= dec_31_sim_day)
        .order_by(asc(Match.sim_day))
    ).all()

    if elite_matches:
        elite_days = sorted(list(set(m.sim_day for m in elite_matches)))
        
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

    # 5. 녹아웃 토너먼트 (PS 8강/4강/KS) - MatchPlaceholder 및 Match 기반
    placeholders = session.exec(
        select(MatchPlaceholder)
        .where(MatchPlaceholder.sim_day >= jan_1_sim_day)
        .where(MatchPlaceholder.sim_day <= dec_31_sim_day)
        .order_by(asc(MatchPlaceholder.sim_day))
    ).all()

    round_days_map: dict[str, list[int]] = {
        "ROUND_OF_8": [],
        "SEMI_FINAL": [],
        "FINAL": []
    }

    for p in placeholders:
        if p.round in round_days_map and p.sim_day not in round_days_map[p.round]:
            round_days_map[p.round].append(p.sim_day)

    # 8강 라벨
    for idx, day in enumerate(sorted(round_days_map["ROUND_OF_8"]), start=1):
        d_date = sim_day_to_date(day, base_year=2026)
        events.append(CalendarEvent(
            date=d_date.strftime("%Y-%m-%d"),
            sim_day=day,
            label=f"PS 8강 {idx}차전",
            event_type="POSTSEASON"
        ))

    # 4강 라벨
    for idx, day in enumerate(sorted(round_days_map["SEMI_FINAL"]), start=1):
        d_date = sim_day_to_date(day, base_year=2026)
        events.append(CalendarEvent(
            date=d_date.strftime("%Y-%m-%d"),
            sim_day=day,
            label=f"PS 4강 {idx}차전",
            event_type="POSTSEASON"
        ))

    # 결승(KS) 라벨
    final_days = sorted(round_days_map["FINAL"])
    for idx, day in enumerate(final_days, start=1):
        d_date = sim_day_to_date(day, base_year=2026)
        events.append(CalendarEvent(
            date=d_date.strftime("%Y-%m-%d"),
            sim_day=day,
            label=f"KS {idx}차전",
            event_type="POSTSEASON"
        ))

    # 6. {YYYY} 시즌 종료
    last_season_day: Optional[int] = None
    if final_days:
        last_season_day = final_days[-1]
    elif elite_matches:
        last_season_day = max(m.sim_day for m in elite_matches)
    elif reg_matches:
        last_season_day = max(m.sim_day for m in reg_matches)

    if last_season_day:
        season_end_date = sim_day_to_date(last_season_day, base_year=2026)
        events.append(CalendarEvent(
            date=season_end_date.strftime("%Y-%m-%d"),
            sim_day=last_season_day,
            label=f"{year} 시즌 종료",
            event_type="SEASON_END"
        ))

    # 7. 경기 없는 날 (NO_MATCH) 처리
    all_scheduled_days = set()
    if reg_matches:
        all_scheduled_days.update(m.sim_day for m in reg_matches)
    if elite_matches:
        all_scheduled_days.update(m.sim_day for m in elite_matches)
    for p in placeholders:
        all_scheduled_days.add(p.sim_day)

    if reg_matches and last_season_day:
        season_first_day = reg_days[0]
        for s_day in range(season_first_day, last_season_day + 1):
            if s_day not in all_scheduled_days:
                s_date = sim_day_to_date(s_day, base_year=2026)
                events.append(CalendarEvent(
                    date=s_date.strftime("%Y-%m-%d"),
                    sim_day=s_day,
                    label="경기 없는 날",
                    event_type="NO_MATCH"
                ))

    return events
