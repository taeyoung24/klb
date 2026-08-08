# uv run -m scripts.simulate_days 365
import sys
import argparse

# Windows 콘솔 인코딩 호환성을 위해 stdout 인코딩 재설정
reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
if callable(reconfigure_stdout):
    reconfigure_stdout(encoding="utf-8")

from sqlmodel import Session, create_engine, select
from settings import DATABASE_URL
from src.models import WorldState
from src.services.core_simulation import step_simulation_day
from src.utils.logger import logger

engine = create_engine(DATABASE_URL)


def main():
    parser = argparse.ArgumentParser(description="KLB N일간 1일 단위 시뮬레이션 스크립트")
    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=90,
        help="시뮬레이션을 진행할 일수 (기본값: 90일, 예: 365)",
    )
    args = parser.parse_args()
    sim_days_count = args.days

    with Session(engine) as session:
        world_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
        if not world_state:
            logger.error("WorldState(id=1)를 찾을 수 없습니다. seed_db.py를 먼저 실행해 주세요.")
            sys.exit(1)

        start_day = world_state.current_sim_day
        end_day = start_day + sim_days_count

        logger.info("=========================================")
        logger.info(f"KLB {sim_days_count}일간 코어 시뮬레이션을 시작합니다. (시작 Sim Day: {start_day} ➔ 목표 Sim Day: {end_day})")
        logger.info("=========================================")

        for i in range(sim_days_count):
            step_simulation_day(session)
            if (i + 1) % 30 == 0:
                cur_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
                cur_day = cur_state.current_sim_day if cur_state else start_day + i + 1
                logger.info(f"  [진행 상황] {i + 1}/{sim_days_count}일 진행 완료 (현재 Sim Day: {cur_day})")
                print('\n')

        final_state = session.exec(select(WorldState).where(WorldState.id == 1)).first()
        final_day = final_state.current_sim_day if final_state else end_day
        logger.success("=========================================")
        logger.success(f"{sim_days_count}일 시뮬레이션이 성공적으로 완료되었습니다! (최종 Sim Day: {final_day})")
        logger.success("=========================================")


if __name__ == "__main__":
    main()
