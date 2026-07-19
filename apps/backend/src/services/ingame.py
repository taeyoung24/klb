import random
from settings import CONFIG
from src.enums import MatchStatus, IngameEventType, IngameGameState
from src.models import Match, IngameInstructionLog, IngameGameStateEvent

def run_match(match: Match):
    """
    단일 매치를 시뮬레이션.
    임시로 랜덤값과 최소한의 상태 전이 이벤트를 기록하는 아주 단순한 형태로 매치 결과를 업데이트합니다.
    """
    # 1. 경기 결과 결정 (랜덤 스코어링)
    match.home_score = random.randint(0, 12)
    match.away_score = random.randint(0, 12)
    match.status = MatchStatus.COMPLETED
    
    # 2. 아주 단순한 대본(이벤트 로그) 생성
    # 경기 시작 이벤트 (1회초 0:0)
    start_event = IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=0.0,
        state_type=IngameGameState.MATCH_START,
        inning=1,
        is_top=True,
        home_score=0,
        away_score=0
    )
    
    # 경기 종료 이벤트 (9회말 최종 스코어)
    end_event = IngameGameStateEvent(
        event_type=IngameEventType.GAME_STATE,
        sim_timestamp=3600.0,  # 가상의 경기 시간 (1시간)
        state_type=IngameGameState.MATCH_END,
        inning=9,
        is_top=False,
        home_score=match.home_score,
        away_score=match.away_score
    )
    
    # 3. 매치 인스턴스에 대본 할당
    match.match_log = IngameInstructionLog(
        simulation_version=CONFIG.simulation_version,
        logged_events=[start_event, end_event]
    )

