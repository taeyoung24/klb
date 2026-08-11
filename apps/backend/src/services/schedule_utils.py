import datetime
from typing import Optional, Union
from sqlmodel import Session, select
from src.enums import MatchStatus, MatchStage
from src.models import Match, Club, MatchPlaceholder


def generate_regular_schedule(clubs: list[Club], year: int, base_sim_day: int) -> list[Match]:
    """
    정규시즌 경기 일정 생성하는 함수. 참가 구단인 clubs를 입력받아(10개 구단 기준) Match list를 반환한다.
    매주 7일 주기 중 화~목(주중 3연전), 금~일(주말 3연전) 경기를 편성하고 월요일은 휴식일로 비워둔다.
    총 48개 3연전 시리즈(총 144경기, 전체 168 sim_day)를 균등한 홈/원정 밸런스로 생성한다.
    """
    n = len(clubs)
    if n != 10:
        raise ValueError("정규시즌 일정 생성에는 정확히 10개의 구단이 필요합니다.")

    # 3월 첫 번째 화요일의 글로벌 sim_day 계산
    jan_first = datetime.date(year, 1, 1)
    march_first = datetime.date(year, 3, 1)
    # 화요일 = 1 (월=0, 화=1, 수=2...)
    days_to_tuesday = (1 - march_first.weekday() + 7) % 7
    first_tuesday = march_first + datetime.timedelta(days=days_to_tuesday)

    # 1월 1일 대비 첫 화요일까지 경과된 날짜
    days_elapsed = (first_tuesday - jan_first).days
    start_sim_day = base_sim_day + days_elapsed

        
    # 1. 48개 시리즈 대진 매칭 조합 생성
    def get_round_robin_matchings():
        round_matchings = []
        for round_num in range(n - 1):
            round_matches = []
            for i in range(n // 2):
                home_idx = (round_num + i) % (n - 1)
                away_idx = (round_num + n - 1 - i) % (n - 1)
                if i == 0:
                    away_idx = n - 1
                round_matches.append((home_idx, away_idx))
            round_matchings.append(round_matches)
        return round_matchings

    base_round_robin = get_round_robin_matchings()
    
    series_list = []
    
    # 4회 완주 (36개 시리즈) -> 짝수 iteration 대칭으로 홈/원정 완벽 분배
    for iteration in range(4):
        flip = (iteration % 2 == 1)
        for round_num in range(9):
            series_list.append((base_round_robin[round_num], flip))
            
    # 남은 12개 시리즈 -> 6개 고유 라운드(0~5)를 선정해 한 번은 flip=False, 한 번은 flip=True로 2회 편성하여 대칭성 확보
    # 전반 6개 시리즈 (flip=False)
    for round_num in range(6):
        series_list.append((base_round_robin[round_num], False))
    # 후반 6개 시리즈 (flip=True)
    for round_num in range(6):
        series_list.append((base_round_robin[round_num], True))
        
    # 2. 48개 시리즈에 대해 경기 일정 생성
    matches = []
    for series_idx, (matchings, flip) in enumerate(series_list):
        # 주차 및 요일 결정
        week = series_idx // 2
        is_weekend = series_idx % 2
        
        if is_weekend == 0:
            # 주중 3연전 (화, 수, 목): 화요일부터 시작
            sim_day_start = start_sim_day + week * 7
        else:
            # 주말 3연전 (금, 토, 일): 금요일부터 시작 (화요일로부터 3일 뒤)
            sim_day_start = start_sim_day + week * 7 + 3
            
        for home_idx, away_idx in matchings:
            if not flip:
                home_club = clubs[home_idx]
                away_club = clubs[away_idx]
            else:
                home_club = clubs[away_idx]
                away_club = clubs[home_idx]
                
            # 3연전 매치 생성
            for day_offset in range(3):
                current_day = sim_day_start + day_offset
                matches.append(Match(
                    home_club_id=home_club.id,
                    away_club_id=away_club.id,
                    stadium_id=home_club.home_stadium_id,
                    sim_day=current_day,
                    status=MatchStatus.SCHEDULED,
                    stage=MatchStage.REGULAR,
                    limit_extra_innings=True
                ))
                
    return matches

def generate_krown_elite_schedule(clubs: list[Club], base_sim_day: int) -> list[Match]:
    """
    크라운 정예리그 경기 일정 생성하는 함수. 참가 구단인 clubs를 입력받아(16개 구단 기준) Match list를 반환한다.
    모든 팀이 서로 상대 팀과 홈 1경기, 원정 1경기를 배분하여 더블 라운드 로빈으로 총 15개 2연전 시리즈(총 30경기일) 일정을 빌드한다.
    경기 일정은 수/목, 토/일 요일에만 매핑되도록 생성한다.
    """
    n = len(clubs)
    if n != 16:
        raise ValueError("크라운 정예리그 일정 생성에는 정확히 16개의 구단이 필요합니다.")

    # 1. 15개 라운드의 싱글 라운드 로빈 대진 매칭 생성
    def get_round_robin_matchings():
        round_matchings = []
        for round_num in range(n - 1): # 15라운드
            round_matches = []
            for i in range(n // 2): # 8경기
                home_idx = (round_num + i) % (n - 1)
                away_idx = (round_num + n - 1 - i) % (n - 1)
                if i == 0:
                    away_idx = n - 1
                round_matches.append((home_idx, away_idx))
            round_matchings.append(round_matches)
        return round_matchings

    base_round_robin = get_round_robin_matchings()
    
    # 2. 날짜 탐색 헬퍼 함수 정의
    def is_valid_day(day: int) -> bool:
        # 2026-01-01 (sim_day=1)은 목요일(3)이므로
        # weekday: 0=월, 1=화, 2=수, 3=목, 4=금, 5=토, 6=일
        weekday = (3 + (day - 1)) % 7
        return weekday in [2, 3, 5, 6]

    def get_next_valid_day(current_day: int) -> int:
        day = current_day + 1
        while not is_valid_day(day):
            day += 1
        return day

    # 시작일 보정 (base_sim_day가 수/목/토/일이 아니면 가장 가까운 경기일로 밀어줌)
    start_day = base_sim_day
    while not is_valid_day(start_day):
        start_day += 1

    matches = []
    current_game_day = start_day

    # 3. 15개 라운드 매칭에 대해 2연전 시리즈 매칭 진행
    for series_idx, matchings in enumerate(base_round_robin):
        if series_idx > 0:
            # 다음 시리즈 시작일 (수요일 또는 토요일) 찾기
            current_game_day = get_next_valid_day(current_game_day)
            
        day1 = current_game_day
        day2 = get_next_valid_day(day1)
        
        # 다음 루프를 위해 현재 경기일을 day2로 업데이트
        current_game_day = day2

        for home_idx, away_idx in matchings:
            club_a = clubs[home_idx]
            club_b = clubs[away_idx]
            
            # 1차전: club_a 홈 (경기일: day1)
            matches.append(Match(
                home_club_id=club_a.id,
                away_club_id=club_b.id,
                stadium_id=club_a.home_stadium_id,
                sim_day=day1,
                status=MatchStatus.SCHEDULED,
                stage=MatchStage.ELITE,
                limit_extra_innings=True
            ))
            # 2차전: club_b 홈 (경기일: day2)
            matches.append(Match(
                home_club_id=club_b.id,
                away_club_id=club_a.id,
                stadium_id=club_b.home_stadium_id,
                sim_day=day2,
                status=MatchStatus.SCHEDULED,
                stage=MatchStage.ELITE,
                limit_extra_innings=True
            ))

    # 매치들을 sim_day 순서대로 정렬하여 반환
    matches.sort(key=lambda x: x.sim_day)
    return matches

def generate_knockout_schedule(clubs: list[Club], base_sim_day: int) -> list[MatchPlaceholder]:
    """
    토너먼트 경기 일정 대진 스케줄러(8개 구단 기준).
    정예리그 최종 순위(#1 ~ #8) 대로 구단들이 전달된다고 가정합니다.
    출력 결과로 부모-자식 트리 관계가 엮인 MatchPlaceholder list를 반환합니다.
    """
    if len(clubs) != 8:
        raise ValueError("토너먼트 일정 생성에는 정확히 8개의 구단이 필요합니다.")
        
    placeholders = []
    
    # 1. 8강전 플레이스홀더 (4개)
    # 대진 매칭: #1 vs #8 (q1), #4 vs #5 (q2), #2 vs #7 (q3), #3 vs #6 (q4)
    # Bo3이므로 8강전의 시뮬레이션 일자는 base_sim_day ~ base_sim_day + 1일차 예정
    q1 = MatchPlaceholder(round="ROUND_OF_8", sim_day=base_sim_day, home_club_id=clubs[0].id, away_club_id=clubs[7].id, limit_extra_innings=False)
    q2 = MatchPlaceholder(round="ROUND_OF_8", sim_day=base_sim_day, home_club_id=clubs[3].id, away_club_id=clubs[4].id, limit_extra_innings=False)
    q3 = MatchPlaceholder(round="ROUND_OF_8", sim_day=base_sim_day, home_club_id=clubs[1].id, away_club_id=clubs[6].id, limit_extra_innings=False)
    q4 = MatchPlaceholder(round="ROUND_OF_8", sim_day=base_sim_day, home_club_id=clubs[2].id, away_club_id=clubs[5].id, limit_extra_innings=False)
    
    placeholders.extend([q1, q2, q3, q4])
    
    # 2. 4강전 플레이스홀더 (2개)
    # 4강 1경기: 8강 1경기(q1) 승자 vs 8강 2경기(q2) 승자
    # 4강 2경기: 8강 3경기(q3) 승자 vs 8강 4경기(q4) 승자
    # Bo5이므로 4강전의 sim_day는 base_sim_day + 3 ~ base_sim_day + 9일차 예정 (중간 휴식일 포함)
    s1 = MatchPlaceholder(round="SEMI_FINAL", sim_day=base_sim_day + 3, limit_extra_innings=False)
    s2 = MatchPlaceholder(round="SEMI_FINAL", sim_day=base_sim_day + 3, limit_extra_innings=False)
    
    # DB 저장 전 ID 매핑 헬퍼를 위해 임시 인메모리 속성 연결
    setattr(s1, "_home_parent", q1)
    setattr(s1, "_away_parent", q2)
    setattr(s2, "_home_parent", q3)
    setattr(s2, "_away_parent", q4)
    
    placeholders.extend([s1, s2])
    
    # 3. 결승전 플레이스홀더 (1개)
    # 4강 1경기(s1) 승자 vs 4강 2경기(s2) 승자
    # Bo7이므로 결승전의 sim_day는 base_sim_day + 11 ~ base_sim_day + 19일차 예정 (3일 경기 후 1일 휴식 패턴)
    f = MatchPlaceholder(round="FINAL", sim_day=base_sim_day + 11, limit_extra_innings=False)
    
    setattr(f, "_home_parent", s1)
    setattr(f, "_away_parent", s2)
    
    placeholders.append(f)
    
    return placeholders

def save_knockout_placeholders(session, placeholders: list[MatchPlaceholder]) -> list[MatchPlaceholder]:
    """
    인메모리 객체 참조(_home_parent, _away_parent)를 이용해 
    외래 키 ID(home_parent_id, away_parent_id)를 설정하고 데이터베이스에 일괄 저장 및 영속화하는 헬퍼 함수.
    """
    # 1. 8강 플레이스홀더 저장 (부모가 없으므로 바로 저장 가능)
    q_nodes = [p for p in placeholders if p.round == "ROUND_OF_8"]
    for q in q_nodes:
        session.add(q)
    session.flush() # ID를 생성받기 위해 flush 실행
    
    # 2. 4강 플레이스홀더 저장 (8강 노드의 ID를 참조하여 외래 키 설정)
    s_nodes = [p for p in placeholders if p.round == "SEMI_FINAL"]
    for s in s_nodes:
        home_parent = getattr(s, "_home_parent", None)
        away_parent = getattr(s, "_away_parent", None)
        if home_parent is not None:
            s.home_parent_id = home_parent.id
        if away_parent is not None:
            s.away_parent_id = away_parent.id
        session.add(s)
    session.flush() # 4강 노드 ID 생성을 위해 flush 실행
    
    # 3. 결승 플레이스홀더 저장 (4강 노드의 ID를 참조하여 외래 키 설정)
    f_nodes = [p for p in placeholders if p.round == "FINAL"]
    for f in f_nodes:
        home_parent = getattr(f, "_home_parent", None)
        away_parent = getattr(f, "_away_parent", None)
        if home_parent is not None:
            f.home_parent_id = home_parent.id
        if away_parent is not None:
            f.away_parent_id = away_parent.id
        session.add(f)
    session.flush()
    
    return placeholders


def generate_tiebreaker_schedule(
    home_club: Union[Club, int], 
    away_club: Union[Club, int], 
    sim_day: int,
    stadium_id: Optional[int] = None
) -> Match:
    """
    정규리그 타이브레이크 단판 순위결정전 경기 일정 객체를 생성하는 함수.
    타이브레이크 경기는 끝장 승부이므로 limit_extra_innings=False(연장 무제한)가 적용됩니다.
    """
    home_club_id: int = home_club.id if isinstance(home_club, Club) else home_club
    away_club_id: int = away_club.id if isinstance(away_club, Club) else away_club
    
    final_stadium_id: Optional[int] = stadium_id
    if final_stadium_id is None and isinstance(home_club, Club):
        final_stadium_id = home_club.home_stadium_id

    return Match(
        home_club_id=home_club_id,
        away_club_id=away_club_id,
        stadium_id=final_stadium_id,
        sim_day=sim_day,
        status=MatchStatus.SCHEDULED,
        stage=MatchStage.TIEBREAKER,
        limit_extra_innings=False,
    )


def update_knockout_placeholders_realtime(session: Session) -> bool:
    """
    매 경기 시뮬레이션 직후 실행되어, 녹아웃(8강/4강/결승)의 승자가 조기 확정된 부모 매치가 있을 때
    연관된 자식 MatchPlaceholder의 home_club_id / away_club_id를 매일 실시간 갱신합니다.
    """
    placeholders = session.exec(select(MatchPlaceholder)).all()
    if not placeholders:
        return False

    q_nodes = sorted([p for p in placeholders if p.round == "ROUND_OF_8"], key=lambda x: x.id)
    s_nodes = sorted([p for p in placeholders if p.round == "SEMI_FINAL"], key=lambda x: x.id)
    f_nodes = [p for p in placeholders if p.round == "FINAL"]
    f_node = f_nodes[0] if f_nodes else None

    # 모든 녹아웃 완료 매치 기록 가져오기
    ko_matches = session.exec(
        select(Match)
        .where(Match.stage == MatchStage.KNOCKOUT)
        .where(Match.status == MatchStatus.COMPLETED)
    ).all()

    updated = False

    # 승자 판정 헬퍼
    def get_series_winner(c1_id: Optional[int], c2_id: Optional[int], required_wins: int, is_bo3_advantage: bool = False) -> Optional[int]:
        if not c1_id or not c2_id:
            return None
        c1_wins = 1 if is_bo3_advantage else 0
        c2_wins = 0
        for m in ko_matches:
            h = m.home_club_id
            a = m.away_club_id
            if (h == c1_id and a == c2_id) or (h == c2_id and a == c1_id):
                h_score = m.home_score if m.home_score is not None else 0
                a_score = m.away_score if m.away_score is not None else 0
                if h_score != a_score:
                    winner = h if h_score > a_score else a
                    if winner == c1_id:
                        c1_wins += 1
                    else:
                        c2_wins += 1
        if c1_wins >= required_wins:
            return c1_id
        if c2_wins >= required_wins:
            return c2_id
        return None

    # 1. 8강 ➔ 4강 Placeholder 실시간 갱신 (Bo3, 2승 선취)
    if len(q_nodes) >= 4 and len(s_nodes) >= 2:
        q1_winner = get_series_winner(q_nodes[0].home_club_id, q_nodes[0].away_club_id, required_wins=2, is_bo3_advantage=True)
        q2_winner = get_series_winner(q_nodes[1].home_club_id, q_nodes[1].away_club_id, required_wins=2, is_bo3_advantage=True)
        q3_winner = get_series_winner(q_nodes[2].home_club_id, q_nodes[2].away_club_id, required_wins=2, is_bo3_advantage=True)
        q4_winner = get_series_winner(q_nodes[3].home_club_id, q_nodes[3].away_club_id, required_wins=2, is_bo3_advantage=True)

        if q1_winner and s_nodes[0].home_club_id != q1_winner:
            s_nodes[0].home_club_id = q1_winner
            session.add(s_nodes[0])
            updated = True
        if q2_winner and s_nodes[0].away_club_id != q2_winner:
            s_nodes[0].away_club_id = q2_winner
            session.add(s_nodes[0])
            updated = True
        if q3_winner and s_nodes[1].home_club_id != q3_winner:
            s_nodes[1].home_club_id = q3_winner
            session.add(s_nodes[1])
            updated = True
        if q4_winner and s_nodes[1].away_club_id != q4_winner:
            s_nodes[1].away_club_id = q4_winner
            session.add(s_nodes[1])
            updated = True

    # 2. 4강 ➔ 결승 Placeholder 실시간 갱신 (Bo5, 3승 선취)
    if len(s_nodes) >= 2 and f_node:
        s1_winner = get_series_winner(s_nodes[0].home_club_id, s_nodes[0].away_club_id, required_wins=3, is_bo3_advantage=False)
        s2_winner = get_series_winner(s_nodes[1].home_club_id, s_nodes[1].away_club_id, required_wins=3, is_bo3_advantage=False)

        if s1_winner and f_node.home_club_id != s1_winner:
            f_node.home_club_id = s1_winner
            session.add(f_node)
            updated = True
        if s2_winner and f_node.away_club_id != s2_winner:
            f_node.away_club_id = s2_winner
            session.add(f_node)
            updated = True

    if updated:
        session.commit()

    return updated

