from typing import Optional, Any
from sqlmodel import Session, select
from src.enums import IngameRole, RosterStatus
from src.models import Player
from src.services.common import engine
from .decisions import BaseDecisionEngine, RuleBasedDecisionEngine
from .utils import generate_mock_players


def _pick_best_pitcher(pitchers: list[Player], decision_engine: Optional[BaseDecisionEngine] = None) -> Player:
    """
    투수들 중 선발 투수를 선택합니다 (Decision Engine에 위임).
    """
    engine_inst = decision_engine or RuleBasedDecisionEngine()
    return engine_inst.decide_starting_pitcher(pitchers)


def _build_batting_order(batters: list[Player], decision_engine: Optional[BaseDecisionEngine] = None) -> list[Player]:
    """
    야수/타자들 중 9명의 선발 라인업 및 타순을 결정합니다 (Decision Engine에 위임).
    """
    engine_inst = decision_engine or RuleBasedDecisionEngine()
    return engine_inst.decide_batting_order(batters)


def select_team_roster_for_match(
    club_id: int,
    session: Optional[Session] = None,
    manager_strategy: Optional[Any] = None,
    decision_engine: Optional[BaseDecisionEngine] = None,
    preloaded_roster: Optional[list[Player]] = None,
) -> tuple[Player, list[Player], list[Player], list[Player]]:
    """
    구단의 ACTIVE 로스터 선수 목록에서 선발 투수(1명), 불펜 투수진, 선발 타순(9명), 벤치 타자들을 결정/추출합니다.
    감독 의사결정(선발 투수, 타순)은 decision_engine(기본 RuleBasedDecisionEngine)에 위임됩니다.
    preloaded_roster가 제공되면 DB 쿼리를 생략하고 즉시 사용합니다.
    """
    db_players: list[Player] = []

    if preloaded_roster is not None:
        db_players = preloaded_roster
    else:
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

    engine_inst = decision_engine or RuleBasedDecisionEngine()

    # 3. 선수 수 검증
    if len(pitchers) >= 1 and len(batters) >= 9:
        starting_pitcher = engine_inst.decide_starting_pitcher(pitchers)
        bullpen = [p for p in pitchers if p.id != starting_pitcher.id]
        starting_batters = engine_inst.decide_batting_order(batters)
        used_batter_ids = {b.id for b in starting_batters if b.id}
        bench_batters = [b for b in batters if b.id not in used_batter_ids]
        return starting_pitcher, bullpen, starting_batters, bench_batters

    # 4. DB 선수 데이터가 부족할 경우 fallback
    return generate_mock_players(club_id)


def select_starting_lineup(
    club_id: int,
    session: Optional[Session] = None,
    manager_strategy: Optional[Any] = None,
    decision_engine: Optional[BaseDecisionEngine] = None,
) -> tuple[Player, list[Player]]:
    sp, _, batters, _ = select_team_roster_for_match(
        club_id,
        session=session,
        manager_strategy=manager_strategy,
        decision_engine=decision_engine,
    )
    return sp, batters
