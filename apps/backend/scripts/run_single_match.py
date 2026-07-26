# uv run -m scripts.run_single_match
from src.models import Match
from src.services.ingame import run_match, get_scoreboard
from src.utils.logger import logger


def main():
    logger.info("단일 경기 인스트럭션 시뮬레이션을 시작합니다...")

    # 단일 테스트용 Match 객체 생성
    match = Match(
        id=999,
        sim_day=1,
        away_club_id=1,
        home_club_id=2,
        limit_extra_innings=True,
    )

    # 경기 시뮬레이션 실행
    run_match(match)

    logger.success("경기가 성공적으로 완료되었습니다!")
    logger.info(
        f"[경기 결과] 원정(Club {match.away_club_id}) {match.away_score} : {match.home_score} 홈(Club {match.home_club_id})"
    )

    if not match.match_log:
        logger.error("Match log가 생성되지 않았습니다.")
        return

    # 전광판(Scoreboard) 정보 계산 및 출력
    scoreboard = get_scoreboard(match.match_log)
    logger.info("=================== Scoreboard Summary ===================")
    logger.info(f"진행 이닝: {scoreboard.current_inning}회 (is_top: {scoreboard.is_top})")
    logger.info(f"원정팀 이닝별 득점: {scoreboard.away_innings} -> 총 R:{scoreboard.away_r}, H:{scoreboard.away_h}, E:{scoreboard.away_e}, B:{scoreboard.away_b}")
    logger.info(f"홈  팀 이닝별 득점: {scoreboard.home_innings} -> 총 R:{scoreboard.home_r}, H:{scoreboard.home_h}, E:{scoreboard.home_e}, B:{scoreboard.home_b}")
    logger.info("==========================================================")

    # 이벤트 로그 정보 출력
    events = match.match_log.logged_events
    logger.info(f"총 생성된 인스트럭션 이벤트 개수: {len(events)}개")
    
    # 이벤트 타입별 카운트 수집 및 요약
    event_counts: dict[str, int] = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

    logger.info("================ Event Breakdown ================")
    for evt_type, count in event_counts.items():
        logger.info(f"  - {evt_type}: {count}개")
    logger.info("=================================================")

    # 샘플 이벤트 5개 출력
    logger.info("이벤트 샘플 (최초 5개):")
    for idx, event in enumerate(events[:5]):
        logger.info(f"  [{idx + 1}] {event.model_dump_json()}")


if __name__ == "__main__":
    main()
