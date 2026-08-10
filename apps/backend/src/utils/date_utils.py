"""
KLB 유니버스 가상 날짜 및 캘린더 날짜 계산 유틸리티 모듈

모든 순수 날짜/시계 연산 함수를 포함하며 서비스 간 순환 참조(Circular Import)를 원천 차단합니다.
"""

import datetime


def sim_day_to_date(sim_day: int, base_year: int = 2026) -> datetime.date:
    """sim_day(1-indexed)를 실제 가상 날짜(datetime.date)로 변환합니다."""
    start_date = datetime.date(base_year, 1, 1)
    return start_date + datetime.timedelta(days=sim_day - 1)


def date_to_sim_day(d_str: str, base_year: int = 2026) -> int:
    """ISO 날짜 문자열(YYYY-MM-DD)을 백엔드 sim_day로 변환합니다."""
    d = datetime.date.fromisoformat(d_str)
    start_date = datetime.date(base_year, 1, 1)
    return (d - start_date).days + 1


def is_third_monday_of_february(target_date: datetime.date) -> bool:
    """해당 날짜가 2월 셋째 주 월요일인지 판별합니다."""
    if target_date.month != 2 or target_date.weekday() != 0:
        return False
    feb_first = datetime.date(target_date.year, 2, 1)
    days_to_monday = (0 - feb_first.weekday() + 7) % 7
    first_monday_day = 1 + days_to_monday
    third_monday_day = first_monday_day + 14
    return target_date.day == third_monday_day


def get_first_monday_of_october(year: int) -> datetime.date:
    """
    매년 10월 첫째 주차 월요일 계산.
    규칙: 목요일이 포함된 달의 주차를 해당 달의 주차로 간주 (ISO 방식).
    10월 1일~7일 사이의 첫 목요일이 속한 주(월~일)의 월요일을 반환합니다.
    """
    for day in range(1, 8):
        d = datetime.date(year, 10, day)
        if d.weekday() == 3:  # 목요일
            return d - datetime.timedelta(days=3)  # 해당 주의 월요일
    # fallback
    return datetime.date(year, 10, 1)
