"""
KLB 선수단 및 계약 행정 서비스 모듈 (Roster & Contract Management Service)

책임:
- 시즌 종료 직후 은퇴(Retire) 처리 (36세 이상 에이징 커브 노장, 장기 정체 선수)
- 시즌 종료 직후 1차 방출(Release) 처리 (성적/연봉 대비 하위권 노장 정리)
- 드래프트 직전 2차 방출(Release) 처리 (신인 지명을 위한 구단 정원 여유 공간 확보)

아키텍처 원칙:
- 타 서비스 모듈(draft.py 등)과의 상호 순환 참조 없음
- DB Session 객체를 전달받아 내부 상태 변경 및 장부를 완결하는 Void(None) 서비스
- core_simulation.py가 상위 오케스트레이터로서 시각(sim_day) 순서에 맞춰 단방향 호출
"""

from sqlmodel import Session, select

from settings import CONFIG
from src.enums import PlayerTransactionType
from src.models import Club, Player, PlayerTransactionHistory
from src.utils.logger import logger


def process_season_end_retirements(session: Session, year: int, sim_day: int) -> None:
    """
    [은퇴 처리] 연 1회 시즌 종료 직후 실행.
    - 36세 이상 노장 선수 또는 기여도가 낮은 노장 선수를 은퇴 처리합니다.
    - 소속 구단 해제(club_id = None) 및 PlayerTransactionHistory(RETIRE) 장부 적재.
    """
    players = list(session.exec(select(Player).where(Player.club_id != None)).all())  # type: ignore
    retired_count = 0

    for player in players:
        age = year - player.birthday.year
        total_stat = player.speed + player.control + player.power + player.flexibility + player.focus

        # 은퇴 조건: 36세 이상이며 스탯 합 2000 미만이거나, 38세 이상인 경우
        is_retire_candidate = (age >= 36 and total_stat < 2000) or (age >= 38)

        if is_retire_candidate:
            old_club_id = player.club_id
            player.club_id = None
            session.add(player)

            history = PlayerTransactionHistory(
                player_id=player.id,
                sim_day=sim_day,
                transaction_type=PlayerTransactionType.RETIRE,
                from_club_id=old_club_id,
                to_club_id=None,
                details=f"{year}시즌 종료 현역 은퇴 (만 {age}세)"
            )
            session.add(history)
            retired_count += 1

    session.commit()
    logger.info(f"[{year}시즌 종료 행정] 총 {retired_count}명 현역 은퇴 처리 완료")


def process_season_end_releases(session: Session, year: int, sim_day: int) -> None:
    """
    [1차 방출 처리] 연 1회 시즌 종료 직후 실행.
    - 성적 및 가성비 하위권 노장/저효율 선수를 정리합니다.
    """
    clubs = list(session.exec(select(Club)).all())
    released_count = 0

    for club in clubs:
        roster = list(session.exec(select(Player).where(Player.club_id == club.id)).all())
        if len(roster) <= 28:
            continue

        # 나이가 28세 이상이고 스탯 합이 낮은 순으로 정렬하여 하위 1~2명 방출
        roster.sort(key=lambda p: (year - p.birthday.year, -(p.speed + p.control + p.power + p.flexibility + p.focus)), reverse=True)
        candidates = [p for p in roster if (year - p.birthday.year) >= 28][:2]

        for player in candidates:
            player.club_id = None
            session.add(player)

            history = PlayerTransactionHistory(
                player_id=player.id,
                sim_day=sim_day,
                transaction_type=PlayerTransactionType.RELEASE,
                from_club_id=club.id,
                to_club_id=None,
                details=f"{year}시즌 종료 1차 구단 자유계약 방출"
            )
            session.add(history)
            released_count += 1

    session.commit()
    logger.info(f"[{year}시즌 종료 행정] 총 {released_count}명 1차 방출 처리 완료")


def process_pre_draft_releases(session: Session, year: int, sim_day: int, target_roster_limit: int = 30) -> None:
    """
    [2차 방출 처리] 신인 드래프트 개최 직전 실행.
    - 구단 정원(target_roster_limit) 초과 인원 및 신인 지명 공간 확보를 위해 하위권 선수를 방출합니다.
    """
    clubs = list(session.exec(select(Club)).all())
    released_count = 0

    for club in clubs:
        roster = list(session.exec(select(Player).where(Player.club_id == club.id)).all())
        # 로스터 인원이 target_roster_limit 초과 시 초과분만큼 방출
        if len(roster) > target_roster_limit:
            excess_count = len(roster) - target_roster_limit

            # 스탯 기준 하위 선수 방출
            roster.sort(key=lambda p: (p.speed + p.control + p.power + p.flexibility + p.focus))
            release_targets = roster[:excess_count]

            for player in release_targets:
                player.club_id = None
                session.add(player)

                history = PlayerTransactionHistory(
                    player_id=player.id,
                    sim_day=sim_day,
                    transaction_type=PlayerTransactionType.RELEASE,
                    from_club_id=club.id,
                    to_club_id=None,
                    details=f"{year}년 신인 드래프트 대비 로스터 정원 확보 2차 방출"
                )
                session.add(history)
                released_count += 1

    session.commit()
    logger.info(f"[{year}년 신인 드래프트 행정] 총 {released_count}명 2차 로스터 정원 확보 방출 완료")
