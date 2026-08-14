"""
KLB 신인 드래프트 (Rookie Draft) 서비스 모듈

특징:
- 리그별 독립적(League-by-League) 패스(PASS)제 무제한 라운드 드래프트 진행
- 1년 차(최초 시즌)에는 무작위 추첨, 2년 차부터는 전년도 정규시즌 승률 전면 역순 지명
- 각 구단 AI의 스탯 + 포지션 보강 가중치 기반 지명 로직
- 지명 결과는 Player 및 PlayerTransactionHistory 장부에 적재
"""

import random
from typing import Any, Optional
from sqlmodel import Session, select, asc, desc, col

from settings import CONFIG
from src.enums import IngameRole, PlayerTransactionType
from src.models import League, Club, Player, HighSchool, DailyClubStanding, PlayerTransactionHistory
from src.services.generation_utils import generate_player
from src.utils.logger import logger


def generate_draft_prospect_pool(session: Session, league_id: int, year: int) -> list[Player]:
    """
    해당 리그의 소속 연고지 고등학교들을 순회하며 메모리 상에서 지명 후보 신인 선수(Player) 인스턴스 풀을 생성합니다.
    - DB에는 미리 저장하지 않으며, 실제 지명(Pick)이 확정된 선수만 DB에 영구 적재됩니다.
    - 야구 전문고(is_specialized=True): 학교당 5명 생성
    - 일반고(is_specialized=False): 약 20% 확률로 학교당 1명 생성
    """
    league_clubs = list(session.exec(select(Club).where(Club.league_id == league_id)).all())
    if not league_clubs:
        raise ValueError(f"ID가 {league_id}인 리그에 속한 구단이 존재하지 않습니다.")

    # 리그 연고지 내 고등학교 조회
    league_region_ids = [c.region_id for c in league_clubs]
    league_high_schools = list(session.exec(
        select(HighSchool).where(col(HighSchool.region_id).in_(league_region_ids))
    ).all())

    if not league_high_schools:
        league_high_schools = list(session.exec(select(HighSchool)).all())

    if not league_high_schools:
        raise RuntimeError("드래프트 후보를 생성할 고등학교(HighSchool) 데이터가 DB에 전혀 존재하지 않습니다.")

    prospects: list[Player] = []

    # 고등학교 목록을 순회하며 메모리 상에 신인 선수 인스턴스 생성 (DB 저장 안 함)
    for hs in league_high_schools:
        if hs.is_specialized:
            # 야구 전문고: 매년 학교당 8~15명의 신인 생성
            count = random.randint(8, 15)
        else:
            # 일반고: 매년 학교당 1~3명의 신인 생성
            count = random.randint(1, 3)

        for _ in range(count):
            player = generate_player(
                region_id=hs.region_id,
                high_school_id=hs.id,
                club_id=None,  # 지명 전 무소속
                position=None, # 무작위 포지션
                general=False, # 고졸 신인 (만 18~19세)
                current_year=year
            )
            prospects.append(player)

    return prospects


def determine_draft_order(session: Session, league_id: int, year: int) -> list[int]:
    """
    해당 리그 10개 구단의 지명 순서를 결정합니다.
    - 2년 차부터: 전년도 정규시즌 최종 순위/승률 역순 (하위 팀이 1순위)
    - 최초 시즌 기록 없음 - 무작위 추첨(random.shuffle)
    """
    clubs = list(session.exec(select(Club).where(Club.league_id == league_id)).all())
    if not clubs:
        raise ValueError(f"ID가 {league_id}인 리그에 속한 구단이 없습니다.")

    club_ids = [c.id for c in clubs]

    # 전년도 시즌 최종 순위 기록 조회 (전년도 sim_day 기준)
    # 정규시즌 마지막 날 스냅샷
    prev_standings = list(session.exec(
        select(DailyClubStanding)
        .where(DailyClubStanding.league_id == league_id)
        .where(col(DailyClubStanding.is_postseason) == False)
        .order_by(desc(DailyClubStanding.sim_day), desc(DailyClubStanding.rank))
    ).all())

    # 전년도 순위가 10개 구단 모두 온전히 존재하는지 확인
    if prev_standings and len(prev_standings) >= len(clubs):
        # 최신 sim_day의 순위 역순 (rank가 큰 팀 = 하위 팀부터)
        latest_sim_day = prev_standings[0].sim_day
        latest_standings = [s for s in prev_standings if s.sim_day == latest_sim_day]
        latest_standings.sort(key=lambda s: s.rank, reverse=True)  # 10위 -> 1위 순
        return [s.club_id for s in latest_standings]

    # 최초 시즌 또는 성적 기록이 없을 경우: 무작위 지명 순서
    draft_order = list(club_ids)
    random.shuffle(draft_order)
    return draft_order


def evaluate_prospect_for_club(club: Club, prospect: Player, club_roster: list[Player]) -> float:
    """
    구단 관점에서 특정 신인 지명 후보의 가치 점수(Score)를 계산합니다.
    - 기본 점수: 5대 스탯 합산
    - 포지션 가중치: 구단 현 로스터 내 해당 포지션 인원 빈곤도 보정
    """
    # TODO: 추후 고교 리그 공식 성적, 스카우팅 리포트 및 NN AI 지표 반영 예정 (Antigravity)
    base_score = float(prospect.speed + prospect.control + prospect.power + prospect.flexibility + prospect.focus)

    # 포지션별 현 로스터 인원 파악
    pos_count = sum(1 for p in club_roster if p.position == prospect.position)

    # 포지션 가중치 보정 (투수 및 부족한 포지션 우선 고려)
    position_bonus = 0.0
    if prospect.position == IngameRole.PITCHER:
        if pos_count < 14:
            position_bonus += (14 - pos_count) * 25.0
    else:
        if pos_count < 2:
            position_bonus += (2 - pos_count) * 40.0

    return base_score + position_bonus


def run_league_rookie_draft(session: Session, league_id: int, year: int, sim_day: int) -> None:
    """
    1개 리그의 패스(PASS)제 무제한 라운드 신인 드래프트를 실행합니다.
    """
    league = session.get(League, league_id)
    if not league:
        raise ValueError(f"ID가 {league_id}인 리그를 찾을 수 없습니다.")

    draft_order: list[int] = determine_draft_order(session, league_id, year)
    prospects: list[Player] = generate_draft_prospect_pool(session, league_id, year)

    # 구단별 로스터 상태 사전 로드
    roster_map: dict[int, list[Player]] = {}
    club_map: dict[int, Club] = {}
    for cid in draft_order:
        c = session.get(Club, cid)
        if c:
            club_map[cid] = c
            roster_map[cid] = list(session.exec(select(Player).where(Player.club_id == cid)).all())

    passed_clubs: set[int] = set()
    draft_history_records: list[dict[str, Any]] = []

    round_num = 1
    overall_pick = 0

    logger.info(f"[{league.name_ko}] {year}년 신인 드래프트 시작 (후보: {len(prospects)}명, 지명 순서 구단 수: {len(draft_order)}개)")

    while len(passed_clubs) < len(draft_order) and len(prospects) > 0:
        picks_in_this_round = 0

        for club_id in draft_order:
            if club_id in passed_clubs:
                continue

            club = club_map[club_id]
            current_roster = roster_map[club_id]

            # 패스(PASS) 조건: 로스터가 40명 이상이거나 남은 지명 후보가 없는 경우
            if len(current_roster) >= 45 or not prospects:
                passed_clubs.add(club_id)
                logger.debug(f"  [{club.name_ko}] {round_num}라운드 지명 포기 (PASS)")
                continue

            # 남아있는 후보 중 구단 기준 최고의 선수 선택
            best_prospect: Optional[Player] = None
            best_score: float = -1.0

            for prospect in prospects:
                score = evaluate_prospect_for_club(club, prospect, current_roster)
                if score > best_score:
                    best_score = score
                    best_prospect = prospect

            # 일정 수준 미달이거나 후보가 없을 시 패스
            if best_prospect is None:
                passed_clubs.add(club_id)
                continue

            # 지명 확정 처리
            overall_pick += 1
            picks_in_this_round += 1

            best_prospect.club_id = club_id
            session.add(best_prospect)
            session.flush()

            # 사무국 이적/지명 장부 작성
            history = PlayerTransactionHistory(
                player_id=best_prospect.id,
                sim_day=sim_day,
                transaction_type=PlayerTransactionType.DRAFT,
                from_club_id=None,
                to_club_id=club_id,
                draft_round=round_num,
                draft_overall_pick=overall_pick,
                details=f"{year}년 {league.name_ko} 신인 드래프트 {round_num}라운드 (전체 {overall_pick}순위) 지명"
            )
            session.add(history)

            prospects.remove(best_prospect)
            current_roster.append(best_prospect)

        if picks_in_this_round == 0:
            # 해당 라운드에 지명한 구단이 하나도 없으면 전 구단 패스로 판단 종료
            break

        round_num += 1

    session.commit()
    logger.info(f"[{league.name_ko}] {year}년 신인 드래프트 완주 (총 {round_num - 1}라운드, 총 {overall_pick}명 지명 완료)")


def run_all_rookie_drafts(session: Session, year: int, sim_day: int) -> None:
    """
    유니버스 내 4개 리그 전체의 신인 드래프트를 순차적으로 실행하는 메인 서비스 함수.
    """
    leagues = list(session.exec(select(League)).all())

    for league in leagues:
        run_league_rookie_draft(session, league.id, year, sim_day)
