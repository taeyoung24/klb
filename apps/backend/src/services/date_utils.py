"""
KLB 유니버스 가상 날짜 및 캘린더 날짜 계산 유틸리티 모듈

모든 순수 날짜/시계 연산 함수를 포함하며 서비스 간 순환 참조(Circular Import)를 원천 차단합니다.
"""

import datetime
from settings import CONFIG


def sim_day_to_date(sim_day: int) -> datetime.date:
    """sim_day(1-indexed)를 실제 가상 날짜(datetime.date)로 변환합니다."""
    base_year = CONFIG.base_datetime.year
    start_date = datetime.date(base_year, 1, 1)
    return start_date + datetime.timedelta(days=sim_day - 1)


def date_str_to_sim_day(d_str: str) -> int:
    """ISO 날짜 문자열(YYYY-MM-DD)을 백엔드 sim_day로 변환합니다."""
    base_year = CONFIG.base_datetime.year
    d = datetime.date.fromisoformat(d_str)
    start_date = datetime.date(base_year, 1, 1)
    return (d - start_date).days + 1


def date_obj_to_sim_day(d: datetime.date) -> int:
    """datetime.date 객체를 백엔드 sim_day로 변환합니다."""
    base_year = CONFIG.base_datetime.year
    start_date = datetime.date(base_year, 1, 1)
    return (d - start_date).days + 1


def date_to_sim_day(d_str: str) -> int:
    """ISO 날짜 문자열(YYYY-MM-DD)을 백엔드 sim_day로 변환합니다. (date_str_to_sim_day의 별칭)"""
    return date_str_to_sim_day(d_str)
