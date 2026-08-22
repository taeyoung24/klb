"""
KLB 구단 프런트(단장 AI) 선수 가치 평가 및 구단 뎁스 분석 모듈 (Valuation & Depth Analysis)

책임:
- 선수의 현재 기량, 잠재력(미래 가치), 나이, 포지션 희소성을 종합한 시장 가치 산정
- 구단별 포지션 뎁스 분석 및 결핍(Need) / 잉여(Surplus) 포지션 도출
- 순위표 및 시즌 국면에 따른 구단 전략 모드(WIN_NOW, REBUILDING, BALANCED) 판별
"""

from typing import Optional
from sqlmodel import Session, select
from src.enums import IngameRole
from src.models import Club, Player, DailyClubStanding


# 포지션별 기본 희소성/중요도 가중치 (수비 부담 및 이닝 소화 가치)
POSITION_WEIGHTS: dict[IngameRole, float] = {
    IngameRole.PITCHER: 1.25,      # 투수: 현대 야구의 핵심 자원
    IngameRole.CATCHER: 1.20,      # 포수: 수비 밸류 및 희소 포지션
    IngameRole.SHORT_STOP: 1.15,   # 유격수: 센터라인 핵심
    IngameRole.SECOND_BASE: 1.05,  # 2루수
    IngameRole.CENTER_FIELD: 1.10, # 중견수
    IngameRole.THIRD_BASE: 1.00,   # 3루수
    IngameRole.FIRST_BASE: 0.95,   # 1루수
    IngameRole.LEFT_FIELD: 0.95,   # 좌익수
    IngameRole.RIGHT_FIELD: 1.00,  # 우익수
    IngameRole.DESIGNATED_HITTER: 0.90,
    IngameRole.PINCH_HITTER: 0.80,
    IngameRole.PINCH_RUNNER: 0.80,
}

# 기본 필수 주전 포지션 목록
CORE_POSITIONS: list[IngameRole] = [
    IngameRole.PITCHER,
    IngameRole.CATCHER,
    IngameRole.FIRST_BASE,
    IngameRole.SECOND_BASE,
    IngameRole.THIRD_BASE,
    IngameRole.SHORT_STOP,
    IngameRole.LEFT_FIELD,
    IngameRole.CENTER_FIELD,
    IngameRole.RIGHT_FIELD,
]


def evaluate_player_value(player: Player, year: int, strategy_mode: str = "BALANCED") -> float:
    """
    선수의 종합 트레이드 시장 가치(Trade Value)를 계산합니다.

    1. 현재 기량 (Current Value): 6대 스탯 합산 (6 ~ 6000)
    2. 미래 가치 (Future Value): 잠재력(potential) * 잔여 성장 기대 연수
    3. 전략 모드(WIN_NOW / REBUILDING / BALANCED)에 따른 가중치 적용
    4. 포지션 희소성 가중치 곱연산
    """
    age = max(18, year - player.birthday.year)
    total_stat = (
        player.speed + player.control + player.power +
        player.flexibility + player.focus + player.stamina
    )

    current_val = float(total_stat)

    # 30세 이하인 경우 남은 성장/전성기 잔여 연수에 따른 미래 가치 가산
    remaining_prime_years = max(0, 30 - age)
    potential_factor = getattr(player, "potential", 500) / 1000.0
    future_val = potential_factor * remaining_prime_years * 150.0  # 최대 약 1800점 가산

    # 구단 전략 모드에 따른 가중치
    if strategy_mode == "WIN_NOW":
        base_value = (current_val * 1.25) + (future_val * 0.40)
    elif strategy_mode == "REBUILDING":
        base_value = (current_val * 0.70) + (future_val * 1.60)
    else:  # BALANCED
        base_value = (current_val * 1.00) + (future_val * 1.00)

    # 포지션 가중치 적용
    pos_weight = POSITION_WEIGHTS.get(player.position, 1.0)
    final_value = base_value * pos_weight

    return round(final_value, 1)


def calculate_team_depth_and_needs(
    roster: list[Player],
    year: int
) -> tuple[dict[IngameRole, float], list[IngameRole], list[IngameRole]]:
    """
    구단 로스터의 포지션별 뎁스 점수를 평가하고,
    보강이 시급한 결핍 포지션(Needs)과 자원이 넘치는 잉여 포지션(Surplus)을 판별합니다.

    Returns:
        (depth_scores_by_pos, needs_positions, surplus_positions)
    """
    players_by_pos: dict[IngameRole, list[Player]] = {pos: [] for pos in CORE_POSITIONS}

    for p in roster:
        if p.position in players_by_pos:
            players_by_pos[p.position].append(p)

    depth_scores: dict[IngameRole, float] = {}

    for pos, players in players_by_pos.items():
        if not players:
            depth_scores[pos] = 0.0
            continue

        # 해당 포지션 선수들을 스탯 총합 높은 순 정렬
        sorted_players = sorted(
            players,
            key=lambda x: (x.speed + x.control + x.power + x.flexibility + x.focus + x.stamina),
            reverse=True
        )

        if pos == IngameRole.PITCHER:
            # 투수는 최소 선발 5명 + 불펜 5명 = 상위 10명의 가중 평균
            top_pitchers = sorted_players[:10]
            score = sum((p.speed + p.control + p.power + p.flexibility + p.focus + p.stamina) for p in top_pitchers) / max(1, len(top_pitchers))
            # 투수 인원 부족 시 감점
            if len(players) < 12:
                score *= (len(players) / 12.0)
        else:
            # 야수는 주전(1위) 70% + 백업(2위) 30% 비중
            starter_stat = (sorted_players[0].speed + sorted_players[0].control + sorted_players[0].power +
                            sorted_players[0].flexibility + sorted_players[0].focus + sorted_players[0].stamina)
            backup_stat = (
                (sorted_players[1].speed + sorted_players[1].control + sorted_players[1].power +
                 sorted_players[1].flexibility + sorted_players[1].focus + sorted_players[1].stamina)
                if len(sorted_players) > 1 else starter_stat * 0.6
            )
            score = starter_stat * 0.7 + backup_stat * 0.3

        depth_scores[pos] = round(score, 1)

    # 전체 포지션 평균 점수 산출
    avg_score = sum(depth_scores.values()) / max(1, len(depth_scores))

    # 결핍 포지션: 평균 대비 15% 이상 낮거나, 주전 점수가 2600점 미만인 포지션
    needs: list[IngameRole] = []
    # 잉여 포지션: 인원이 넉넉하고 평균 대비 15% 이상 우수한 포지션
    surplus: list[IngameRole] = []

    for pos, score in depth_scores.items():
        pos_count = len(players_by_pos[pos])
        if pos == IngameRole.PITCHER:
            if score < avg_score * 0.90 or pos_count < 11:
                needs.append(pos)
            elif score > avg_score * 1.10 and pos_count >= 14:
                surplus.append(pos)
        else:
            if score < avg_score * 0.85 or pos_count < 2:
                needs.append(pos)
            elif score > avg_score * 1.15 and pos_count >= 3:
                surplus.append(pos)

    return depth_scores, needs, surplus


def determine_club_strategy(
    club_id: int,
    session: Session,
    sim_day: int,
    is_in_season: bool = False
) -> str:
    """
    현재 구단의 시즌 전략 모드(WIN_NOW / REBUILDING / BALANCED)를 판별합니다.
    - 정규시즌 중: 순위표 승률 및 순위 기반
    - 오프시즌: BALANCED (기본)
    """
    if not is_in_season:
        return "BALANCED"

    # 당일 최신 순위표 조회
    standing = session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.club_id == club_id)
        .where(DailyClubStanding.sim_day == sim_day)
        .where(DailyClubStanding.is_postseason == False)
    ).first()

    if not standing or standing.games_played < 20:
        return "BALANCED"

    # 승률 0.550 이상이거나 3위 이내: 우승 도전(WIN_NOW)
    if standing.win_rate >= 0.550 or standing.rank <= 3:
        return "WIN_NOW"

    # 승률 0.420 이하이거나 8위 이하: 리빌딩(REBUILDING)
    if standing.win_rate <= 0.420 or standing.rank >= 8:
        return "REBUILDING"

    return "BALANCED"
