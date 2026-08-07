from typing import Optional, Any
from sqlmodel import Session, select
from src.enums import IngameRole, RosterStatus
from src.models import Player
from src.services.common import engine
from .utils import generate_mock_players


def _pick_best_pitcher(pitchers: list[Player]) -> Player:
    """
    투수들 중 선발 투수를 선택합니다.
    (기본 전략: 제구력, 구속 등 종합 능력치가 높은 투수 선택)
    """
    # control + speed 종합이 가장 높은 투수 선택
    return max(pitchers, key=lambda p: p.control + p.speed)


def _build_batting_order(batters: list[Player]) -> list[Player]:
    """
    야수/타자들 중 9명의 선발 라인업 및 타순을 결정합니다.
    (기본 전략: 각 주요 포지션별 최선선수 선택 후 능력치 순으로 타순 배치)
    """
    # 필수 포지션 9개
    target_positions = [
        IngameRole.CATCHER,
        IngameRole.FIRST_BASE,
        IngameRole.SECOND_BASE,
        IngameRole.THIRD_BASE,
        IngameRole.SHORT_STOP,
        IngameRole.LEFT_FIELD,
        IngameRole.CENTER_FIELD,
        IngameRole.RIGHT_FIELD,
        IngameRole.DESIGNATED_HITTER,
    ]

    selected_batters: list[Player] = []
    used_player_ids = set()

    # 1. 각 포지션별 가장 능력이 뛰어난 선수 1명씩 우선 배치
    for pos in target_positions:
        candidates = [
            p for p in batters
            if p.position == pos and p.id not in used_player_ids
        ]
        if candidates:
            # power + speed + focus 종합 높은 선수 선택
            best_player = max(candidates, key=lambda p: p.power + p.speed + p.focus)
            selected_batters.append(best_player)
            if best_player.id:
                used_player_ids.add(best_player.id)

    # 2. 남은 자리가 있다면 남은 타자 중 종합 능력치순으로 채움
    remaining = [p for p in batters if p.id not in used_player_ids]
    remaining.sort(key=lambda p: p.power + p.speed + p.focus, reverse=True)
    
    while len(selected_batters) < 9 and remaining:
        player = remaining.pop(0)
        selected_batters.append(player)
        if player.id:
            used_player_ids.add(player.id)

    return selected_batters[:9]


def select_team_roster_for_match(
    club_id: int,
    session: Optional[Session] = None,
    manager_strategy: Optional[Any] = None,
) -> tuple[Player, list[Player], list[Player]]:
    """
    구단의 ACTIVE 로스터 선수 목록에서 선발 투수(1명), 불펜 투수진, 그리고 선발 타순(9명)을 결정/추출합니다.
    """
    db_players: list[Player] = []

    # 1. DB 세션이 제공되었거나 engine을 통한 DB 선수 조회
    local_session = session
    should_close = False
    if local_session is None:
        try:
            local_session = Session(engine)
            should_close = True
        except Exception:
            local_session = None

    if local_session:
        try:
            statement = select(Player).where(
                Player.club_id == club_id,
                Player.roster_status == RosterStatus.ACTIVE,
            )
            db_players = list(local_session.exec(statement).all())
        except Exception:
            db_players = []
        finally:
            if should_close:
                local_session.close()

    # 2. 선수 분류
    pitchers = [p for p in db_players if p.position == IngameRole.PITCHER]
    batters = [p for p in db_players if p.position != IngameRole.PITCHER]

    # 3. 선수 수 검증
    if len(pitchers) >= 1 and len(batters) >= 9:
        starting_pitcher = _pick_best_pitcher(pitchers)
        bullpen = [p for p in pitchers if p.id != starting_pitcher.id]
        starting_batters = _build_batting_order(batters)
        return starting_pitcher, bullpen, starting_batters

    # 4. DB 선수 데이터가 부족할 경우 fallback
    return generate_mock_players(club_id)


def select_starting_lineup(
    club_id: int,
    session: Optional[Session] = None,
    manager_strategy: Optional[Any] = None,
) -> tuple[Player, list[Player]]:
    sp, _, batters = select_team_roster_for_match(club_id, session, manager_strategy)
    return sp, batters
