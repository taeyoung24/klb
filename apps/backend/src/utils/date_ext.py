"""
KLB 확장 캘린더/날짜 계산 유틸리티 모듈
"""

import datetime


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
