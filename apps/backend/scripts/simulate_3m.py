import sys

# Windows 콘솔 인코딩 호환성을 위해 stdout 인코딩 재설정
reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
if callable(reconfigure_stdout):
    reconfigure_stdout(encoding="utf-8")

from sqlmodel import Session, create_engine, select
from settings import DATABASE_URL
from src.models import WorldState, Match
from src.enums import MatchStatus
from src.services.ingame import run_match
from src.utils.logger import logger
from src.services.standing import update_daily_standings

engine = create_engine(DATABASE_URL)

def main():
    with Session(engine) as session:
        # 1. 현재 WorldState 조회
        world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
        if not world_state:
            logger.error("WorldState(id=1)를 찾을 수 없습니다. seed_db.py를 먼저 실행해 주세요.")
            sys.exit(1)

        start_day = world_state.current_sim_day
        # 세 달치 (약 90일) 일수 지정
        sim_duration_days = 90
        end_day = start_day + sim_duration_days
        
        logger.info(f"3개월 시뮬레이션을 시작합니다. (시작 Sim Day: {start_day} ➔ 목표 Sim Day: {end_day})")

        for day in range(start_day, end_day):
            logger.info(f"[Sim Day {day}] 경기 시뮬레이션 진행 중...")
            
            # 해당 날짜에 예정된(SCHEDULED) 경기 조회
            matches = session.exec(
                select(Match)
                .where(Match.sim_day == day)
                .where(Match.status == MatchStatus.SCHEDULED)
            ).all()

            if not matches:
                logger.info(f"  ➔ [Sim Day {day}] 예정된 경기가 없습니다.")
            else:
                for match in matches:
                    run_match(match, session=session)
                    session.add(match)
                    logger.info(
                        f"  ➔ Match ID {match.id}: "
                        f"Away(Club {match.away_club_id}) {match.away_score} vs "
                        f"Home(Club {match.home_club_id}) {match.home_score}"
                    )

            # 오늘 경기 결과를 토대로 구단별 누적 순위 및 기록 스냅샷 생성
            update_daily_standings(session, day)

            # 하루가 끝나면 WorldState의 시뮬레이션 날짜를 다음 날로 갱신
            world_state.current_sim_day = day + 1
            session.add(world_state)
            
            # 하루 단위로 커밋하여 영속화
            session.commit()
            
        logger.success(f"3개월 시뮬레이션이 성공적으로 완료되었습니다! (최종 Sim Day: {world_state.current_sim_day})")

if __name__ == "__main__":
    main()
