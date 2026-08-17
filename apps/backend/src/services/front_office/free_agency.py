"""
KLB 자유계약선수(FA) 및 미계약 선수 영입 엔진 모듈 (Free Agency Service)

책임:
- 방출/드래프트 미지명 등으로 무소속(club_id=None) 상태인 선수들의 FA 시장 영입 처리
- 구단별 로스터 결원(30명 정원 미만) 및 취약 포지션 보강 계약 체결
- PlayerTransactionHistory(FA) 장부 적재
"""

import datetime
import random
from typing import Optional
from sqlmodel import Session, select

from src.enums import RosterStatus, PlayerTransactionType
from src.models import Club, Player, PlayerTransactionHistory
from src.services.front_office.valuation import (
    evaluate_player_value,
    calculate_team_depth_and_needs,
)
from src.utils.logger import logger


def process_daily_fa_market(
    session: Session,
    year: int,
    sim_day: int,
    current_date: datetime.date,
    is_postseason_ended: bool = False
) -> list[dict]:
    """
    [일일 FA 시장] 매일 09:00 시점에 실행되어 무소속 우수 선수와 구단 간 입단 계약을 진행합니다.
    """
    m = current_date.month

    # 1. FA 시장 활성화 확률 체크
    # 스토브리그(11~2월): 8% 확률, 정규시즌(3~7월): 2% 확률
    if m in [11, 12, 1, 2]:
        prob = 0.08
    elif 3 <= m <= 7:
        prob = 0.02
    else:
        prob = 0.0

    if random.random() > prob:
        return []

    # 2. 영입 가능한 무소속 선수(FA) 목록 조회 (스탯 상위 50명)
    fa_pool = list(session.exec(
        select(Player)
        .where(Player.club_id == None)  # type: ignore
        .where(Player.roster_status == RosterStatus.ACTIVE)
    ).all())

    if not fa_pool:
        return []

    # 스탯 총합 높은 순 정렬
    fa_pool.sort(
        key=lambda p: (p.speed + p.control + p.power + p.flexibility + p.focus + p.stamina),
        reverse=True
    )

    # 3. 로스터 정원(30명)에 여유가 있는 구단 목록 조회
    clubs = list(session.exec(select(Club)).all())
    random.shuffle(clubs)

    signed_results = []

    for club in clubs:
        roster = list(session.exec(select(Player).where(Player.club_id == club.id)).all())
        if len(roster) >= 30:  # 정원 꽉 참
            continue

        _, needs, _ = calculate_team_depth_and_needs(roster, year)

        # 결핍 포지션에 맞는 FA 선수 우선 탐색
        target_fa = None
        for candidate in fa_pool[:30]:  # 상위 30명 중 탐색
            if candidate.position in needs:
                target_fa = candidate
                break

        # 결핍 포지션이 없더라도 로스터가 27명 이하로 많이 부족하면 가치 상위 FA 영입
        if not target_fa and len(roster) <= 27 and fa_pool:
            target_fa = fa_pool[0]

        if target_fa:
            # 계약 체결
            target_fa.club_id = club.id
            session.add(target_fa)
            fa_pool.remove(target_fa)

            date_str = current_date.strftime("%Y년 %m월 %d일")
            history = PlayerTransactionHistory(
                player_id=target_fa.id,
                sim_day=sim_day,
                transaction_type=PlayerTransactionType.FA,
                from_club_id=None,
                to_club_id=club.id,
                details=f"[{date_str}] {club.name_ko} 자유계약(FA) 입단 영입 ({target_fa.position})"
            )
            session.add(history)
            session.commit()

            signed_results.append({
                "sim_day": sim_day,
                "date": current_date.strftime("%Y-%m-%d"),
                "club": club.name_ko,
                "player": f"{target_fa.name}({target_fa.position})"
            })

            logger.info(
                f"📝 [FA 계약 체결] {current_date.strftime('%m/%d')} (Sim Day {sim_day}) "
                f"{club.name_ko} ➔ {target_fa.name}({target_fa.position}) 영입"
            )

            # 하루 최대 1건 처리 후 분산
            return signed_results

    return signed_results
