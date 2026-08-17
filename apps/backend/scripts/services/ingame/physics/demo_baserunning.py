# uv run -m scripts.services.ingame.physics.demo_baserunning
from datetime import datetime

from src.utils.logger import logger
from src.models import Player
from src.enums import IngameRole, RosterStatus, IngameFieldingAction
from src.services.ingame.physics import (
    FieldingPhysicsResult,
    calculate_baserunning_physics,
)


def create_runner(name: str, speed: int, focus: int, flexibility: int, stamina: int = 500) -> Player:
    return Player(
        id=1, name=name, club_id=1, uniform_number="7", speed=speed, control=500, power=500,
        flexibility=flexibility, focus=focus, stamina=stamina, roster_status=RosterStatus.ACTIVE,
        position=IngameRole.CENTER_FIELD, personality=[1], birthday=datetime(1998, 1, 1),
        height=180.0, weight=75.0
    )


def main():
    logger.info("==================================================================")
    logger.info("       KLB BaseRunning & Sprint Physics Demo Simulator           ")
    logger.info("==================================================================")

    runners = [
        ("Lee Speed (Supersonic Runner)", create_runner("Lee Speed", speed=980, focus=900, flexibility=850)),
        ("Park Average (Average Runner)", create_runner("Park Average", speed=650, focus=600, flexibility=600)),
        ("Kim Heavy (Heavy Batter)", create_runner("Kim Heavy", speed=380, focus=400, flexibility=350)),
    ]

    # 수비 가상 시나리오 (1루 송구, 2루 중계, 3루 중계 완류시간)
    mock_fielders = [
        ("Scenario 1: Infield Grounder to 1B (Throw Time: 4.10s)", 1, FieldingPhysicsResult(
            fielder=create_runner("Fielder", 700, 700, 700), is_caught_in_air=False,
            fielding_action=IngameFieldingAction.CATCH, fumble_delay_sec=0.0, reach_time_sec=1.8, throw_time_sec=4.10
        )),
        ("Scenario 2: Deep Line Drive to 2B (Throw Time: 7.60s)", 2, FieldingPhysicsResult(
            fielder=create_runner("Fielder", 700, 700, 700), is_caught_in_air=False,
            fielding_action=IngameFieldingAction.CATCH, fumble_delay_sec=0.0, reach_time_sec=4.2, throw_time_sec=7.60
        )),
        ("Scenario 3: Deep Corner Hit to 3B (Throw Time: 10.50s)", 3, FieldingPhysicsResult(
            fielder=create_runner("Fielder", 700, 700, 700), is_caught_in_air=False,
            fielding_action=IngameFieldingAction.CATCH, fumble_delay_sec=0.0, reach_time_sec=6.0, throw_time_sec=10.50
        )),
    ]

    for scn_label, target_base, f_res in mock_fielders:
        divider = "=" * 95
        print(f"\n{divider}")
        print(f"[{scn_label}] Target Base: {target_base}B")
        print(f"{divider}")

        for r_label, runner in runners:
            b_res = calculate_baserunning_physics(runner, start_base=0, target_base=target_base, fielding_physics=f_res)

            if b_res.is_safe:
                status_str = f"[SAFE!] (Margin: +{b_res.safe_margin_sec:.2f}s)"
            else:
                status_str = f"[OUT!]  (Margin: {b_res.safe_margin_sec:.2f}s)"


            print(
                f"  Runner: {r_label:<32} | Speed: {runner.speed:3d} | BaseReachTime: {b_res.runner_reach_time_sec:4.2f}s "
                f"| ThrowTime: {f_res.throw_time_sec:4.2f}s | Result: {status_str}"
            )

    print(f"\n{"="*95}")
    logger.info("KLB BaseRunning & Sprint Physics Demo Completed Successfully!")
    print(f"{"="*95}\n")


if __name__ == "__main__":
    main()
