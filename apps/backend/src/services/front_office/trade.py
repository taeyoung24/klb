"""
KLB 구단 간 트레이드(Trade) 엔진 모듈

책임:
- 트레이드 가능 기간(인시즌 윈도우 & 스토브리그 윈도우) 판별 및 일일 트리거 확률 제어
- 구단별 쿨다운(Cooldown) 및 잉여/결핍 포지션 상호 부합 여부 탐색
- 1:1 선수 가치 교환 공식 검증 및 트레이드 장부(PlayerTransactionHistory) 적재
"""

import datetime
import random
from dataclasses import dataclass
from typing import Optional
from sqlmodel import Session, select, desc

from src.enums import IngameRole, PlayerTransactionType
from src.models import Club, Player, PlayerTransactionHistory
from src.services.front_office.valuation import (
    evaluate_player_value,
    calculate_team_depth_and_needs,
    determine_club_strategy,
    CORE_POSITIONS
)
from src.utils.logger import logger


@dataclass
class ClubTradeProfile:
    club: Club
    roster: list[Player]
    strategy: str
    needs: list[IngameRole]
    surplus: list[IngameRole]


def get_daily_trade_probability(current_date: datetime.date, is_postseason_ended: bool) -> float:
    """
    현재 날짜가 트레이드 가능 기간인지 판별하고, 해당 일자의 트레이드 시장 성사 확률을 반환합니다.

    1. 인시즌 윈도우 (개막 3월 ~ 7월 31일):
       - 평상시 (3~6월, 7월 중순 이전): 약 2.5% 일일 확률
       - 마감일 임박 주간 (7월 25일 ~ 7월 31일): 15% ~ 25% 급상승
    2. 트레이드 금지 기간 (8월 1일 ~ 결승전 종료):
       - 0.0% (규정상 트레이드 전면 금지)
    3. 스토브리그 윈도우 (시즌 종료 후 ~ 2월 중순):
       - 평상시: 약 3.0% 일일 확률
       - 윈터미팅 주간 (12월 10일 ~ 12월 20일): 15% ~ 20% 상승
    """
    m = current_date.month
    d = current_date.day

    # 1. 인시즌 윈도우: 3월 ~ 7월 31일
    if 3 <= m <= 7:
        if m == 7 and d >= 25:
            return 0.20  # 트레이드 마감일 임박 주간 (20%)
        return 0.025  # 인시즌 일상 확률 (2.5%)

    # 2. 트레이드 금지 기간: 8월, 9월, 10월 중 결승 종료 전
    if 8 <= m <= 10 and not is_postseason_ended:
        return 0.0  # 트레이드 Freeze

    # 3. 스토브리그 윈도우: 시즌 종료 후 (10월 말~12월) 및 이듬해 1~2월
    if m == 12 and 10 <= d <= 20:
        return 0.15  # 윈터미팅 집중 기간 (15%)
    elif m in [11, 12, 1, 2]:
        return 0.035  # 스토브리그 일상 확률 (3.5%)

    return 0.0


def check_club_trade_cooldown(club_id: int, session: Session, current_sim_day: int, cooldown_days: int = 25) -> bool:
    """
    해당 구단이 최근 cooldown_days 이내에 트레이드를 진행했는지 확인합니다.
    True: 쿨다운 중 (트레이드 불가), False: 트레이드 가능
    """
    recent_trade = session.exec(
        select(PlayerTransactionHistory)
        .where(
            (PlayerTransactionHistory.from_club_id == club_id) |
            (PlayerTransactionHistory.to_club_id == club_id)
        )
        .where(PlayerTransactionHistory.transaction_type == PlayerTransactionType.TRADE)
        .where(PlayerTransactionHistory.sim_day >= current_sim_day - cooldown_days)
    ).first()

    return recent_trade is not None


def process_daily_trade_market(
    session: Session,
    year: int,
    sim_day: int,
    current_date: datetime.date,
    is_postseason_ended: bool = False
) -> list[dict]:
    """
    [일일 트레이드 시장] 매일 09:00 시점에 실행되어 구단 간 자율 상호 협의 트레이드를 타진합니다.
    """
    # 1. 오늘 트레이드 시장 활성화 확률 체크
    prob = get_daily_trade_probability(current_date, is_postseason_ended)
    if prob <= 0.0 or random.random() > prob:
        return []

    is_in_season = (3 <= current_date.month <= 7)

    # 2. 모든 구단 정보 및 로스터 수집
    clubs = list(session.exec(select(Club)).all())
    if len(clubs) < 2:
        return []

    # 쿨다운 중이 아닌 후보 구단들 선별
    active_clubs = [c for c in clubs if not check_club_trade_cooldown(c.id, session, sim_day)]
    if len(active_clubs) < 2:
        return []

    # 구단별 분석 정보 캐싱: ClubTradeProfile
    club_profiles: list[ClubTradeProfile] = []
    for club in active_clubs:
        roster = list(session.exec(select(Player).where(Player.club_id == club.id)).all())
        if len(roster) < 25:
            continue
        strategy = determine_club_strategy(club.id, session, sim_day, is_in_season)
        _, needs, surplus = calculate_team_depth_and_needs(roster, year)
        club_profiles.append(ClubTradeProfile(
            club=club,
            roster=roster,
            strategy=strategy,
            needs=needs,
            surplus=surplus
        ))

    # 무작위로 구단 쌍을 섞어서 탐색
    random.shuffle(club_profiles)
    successful_trades = []

    for i in range(len(club_profiles)):
        for j in range(i + 1, len(club_profiles)):
            prof_a = club_profiles[i]
            prof_b = club_profiles[j]

            club_a, club_b = prof_a.club, prof_b.club

            # 상호 니즈 교차 검증: A의 잉여가 B의 결핍에 부합하고, B의 잉여가 A의 결핍에 부합하는지
            match_a_to_b = any(pos in prof_b.needs for pos in prof_a.surplus)
            match_b_to_a = any(pos in prof_a.needs for pos in prof_b.surplus)

            # 완벽 교차가 아니더라도, 최소 한쪽의 결핍을 채워주고 상대는 가치 균형을 맞추는 경우도 허용
            candidate_players_a = [
                p for p in prof_a.roster
                if p.position in prof_b.needs or (not prof_b.needs and p.position in prof_a.surplus)
            ]
            candidate_players_b = [
                p for p in prof_b.roster
                if p.position in prof_a.needs or (not prof_a.needs and p.position in prof_b.surplus)
            ]

            if not candidate_players_a or not candidate_players_b:
                continue

            # 양 구단의 선수들 중 가치가 가장 잘 맞는 1:1 매칭 탐색
            best_pair = None
            min_value_diff_ratio = 999.0

            for pa in candidate_players_a:
                val_a = evaluate_player_value(pa, year, prof_b.strategy)
                for pb in candidate_players_b:
                    val_b = evaluate_player_value(pb, year, prof_a.strategy)

                    max_v = max(val_a, val_b)
                    if max_v < 1000:
                        continue

                    diff_ratio = abs(val_a - val_b) / max_v

                    # 가치 차이가 20% 이내인 경우 최적 후보로 등록
                    if diff_ratio <= 0.20 and diff_ratio < min_value_diff_ratio:
                        min_value_diff_ratio = diff_ratio
                        best_pair = (pa, pb, val_a, val_b)

            # 트레이드 성사 처리
            if best_pair:
                player_a, player_b, val_a, val_b = best_pair

                # 1. 소속 구단 교체
                player_a.club_id = club_b.id
                player_b.club_id = club_a.id
                session.add(player_a)
                session.add(player_b)

                # 2. 트랜잭션 장부(PlayerTransactionHistory) 기록
                date_str = current_date.strftime("%Y년 %m월 %d일")
                history_a = PlayerTransactionHistory(
                    player_id=player_a.id,
                    sim_day=sim_day,
                    transaction_type=PlayerTransactionType.TRADE,
                    from_club_id=club_a.id,
                    to_club_id=club_b.id,
                    details=f"[{date_str}] {club_a.name_ko} ↔ {club_b.name_ko} 1:1 맞트레이드 (상대: {player_b.name})"
                )
                history_b = PlayerTransactionHistory(
                    player_id=player_b.id,
                    sim_day=sim_day,
                    transaction_type=PlayerTransactionType.TRADE,
                    from_club_id=club_b.id,
                    to_club_id=club_a.id,
                    details=f"[{date_str}] {club_b.name_ko} ↔ {club_a.name_ko} 1:1 맞트레이드 (상대: {player_a.name})"
                )
                session.add(history_a)
                session.add(history_b)
                session.commit()

                trade_info = {
                    "sim_day": sim_day,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "club_a": club_a.name_ko,
                    "player_a": f"{player_a.name}({player_a.position})",
                    "club_b": club_b.name_ko,
                    "player_b": f"{player_b.name}({player_b.position})"
                }
                successful_trades.append(trade_info)

                logger.info(
                    f"🤝 [트레이드 성사] {current_date.strftime('%m/%d')} (Sim Day {sim_day}) "
                    f"{club_a.name_ko}({player_a.name}, {player_a.position}) ↔ "
                    f"{club_b.name_ko}({player_b.name}, {player_b.position})"
                )

                # 하루에 최대 1건의 대형 트레이드만 처리 후 리턴 (자연스러운 분산)
                return successful_trades

    return successful_trades
