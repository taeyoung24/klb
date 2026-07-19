import datetime
from typing import Optional
from src.enums import MatchStatus
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
                    sim_day=current_day,
                    status=MatchStatus.SCHEDULED
                ))
                
    return matches

def generate_krown_elite_schedule(clubs: list[Club]) -> list[Match]:
    """
    크라운 엘리트 경기 일정 생성하는 함수. 참가 구단인 clubs를 입력받아(16개 구단 기준) Match list를 반환한다.
    모든 팀이 서로 상대 팀과 홈 1경기, 원정 1경기를 완벽히 배분하여 더블 라운드 로빈으로 총 30라운드(30 sim_day) 일정을 빌드한다.
    """
    n = len(clubs)
    if n % 2 != 0:
        raise ValueError("크라운 엘리트 경기 일정 생성에는 짝수 개의 구단이 필요합니다.")
        
    matches = []
    sim_day = 1
    
    # 더블 라운드 로빈이므로 2번 반복
    for iteration in range(2):
        for round_num in range(n - 1):
            for i in range(n // 2):
                home_idx = (round_num + i) % (n - 1)
                away_idx = (round_num + n - 1 - i) % (n - 1)
                if i == 0:
                    away_idx = n - 1
                
                # 첫 번째 세트와 두 번째 세트의 홈/원정을 반대로 배정
                if iteration == 0:
                    if round_num % 2 == 0:
                        home = clubs[home_idx]
                        away = clubs[away_idx]
                    else:
                        home = clubs[away_idx]
                        away = clubs[home_idx]
                else:
                    if round_num % 2 == 0:
                        home = clubs[away_idx]
                        away = clubs[home_idx]
                    else:
                        home = clubs[home_idx]
                        away = clubs[away_idx]
                        
                matches.append(Match(
                    home_club_id=home.id,
                    away_club_id=away.id,
                    sim_day=sim_day,
                    status=MatchStatus.SCHEDULED
                ))
            sim_day += 1
            
    return matches

def generate_knockout_schedule(clubs: list[Club]) -> list[MatchPlaceholder]:
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
    # Bo3이므로 8강전의 시뮬레이션 일자는 1~2일차 예정
    q1 = MatchPlaceholder(round="ROUND_OF_8", sim_day=1, home_club_id=clubs[0].id, away_club_id=clubs[7].id)
    q2 = MatchPlaceholder(round="ROUND_OF_8", sim_day=1, home_club_id=clubs[3].id, away_club_id=clubs[4].id)
    q3 = MatchPlaceholder(round="ROUND_OF_8", sim_day=1, home_club_id=clubs[1].id, away_club_id=clubs[6].id)
    q4 = MatchPlaceholder(round="ROUND_OF_8", sim_day=1, home_club_id=clubs[2].id, away_club_id=clubs[5].id)
    
    placeholders.extend([q1, q2, q3, q4])
    
    # 2. 4강전 플레이스홀더 (2개)
    # 4강 1경기: 8강 1경기(q1) 승자 vs 8강 2경기(q2) 승자
    # 4강 2경기: 8강 3경기(q3) 승자 vs 8강 4경기(q4) 승자
    # Bo5이므로 4강전의 sim_day는 3일차~7일차 예정
    s1 = MatchPlaceholder(round="SEMI_FINAL", sim_day=3)
    s2 = MatchPlaceholder(round="SEMI_FINAL", sim_day=3)
    
    # DB 저장 전 ID 매핑 헬퍼를 위해 임시 인메모리 속성 연결
    setattr(s1, "_home_parent", q1)
    setattr(s1, "_away_parent", q2)
    setattr(s2, "_home_parent", q3)
    setattr(s2, "_away_parent", q4)
    
    placeholders.extend([s1, s2])
    
    # 3. 결승전 플레이스홀더 (1개)
    # 4강 1경기(s1) 승자 vs 4강 2경기(s2) 승자
    # Bo7이므로 결승전의 sim_day는 8일차~14일차 예정
    f = MatchPlaceholder(round="FINAL", sim_day=8)
    
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
