# uv run -m scripts.services.ingame.physics.demo_trajectory
from datetime import datetime

from src.utils.logger import logger
from src.models import Stadium, Player, PitchSelectionResult
from src.enums import IngameRole, RosterStatus, IngamePitchType, IngamePitchZone, IngameBattingStrategy, TurfType
from src.services.ingame.physics import (
    calculate_pitch_physics,
    calculate_batting_physics,
    calculate_trajectory_physics,
)


def main():
    logger.info("==================================================================")
    logger.info("       KLB Trajectory & Distance Physics Demo Simulator           ")
    logger.info("==================================================================")

    # 1. 샘플 구장 정보 (잠실구장 스타일)
    stadium = Stadium(
        id=1,
        name="Jamsil Stadium",
        name_ko="Seoul Jamsil Stadium",
        is_dome=False,
        capacity=25000,
        turf_type=TurfType.NATURAL,
        altitude=35.0,  # 해발 35m
        curvature=0.5,
    )

    # 2. 테스트 투수 및 타자
    pitcher = Player(
        id=10, name="Pitcher (152km/h)", club_id=1, uniform_number="1", speed=500, control=750, power=850,
        flexibility=500, focus=500, stamina=500, roster_status=RosterStatus.ACTIVE, position=IngameRole.PITCHER,
        personality=[1], birthday=datetime(1995, 1, 1), height=185.0, weight=85.0
    )

    batters = [
        ("Choi Power (Slugger / Power 960)", Player(
            id=1, name="Choi Power", club_id=1, uniform_number="55", speed=400, control=500, power=960,
            flexibility=500, focus=700, stamina=500, roster_status=RosterStatus.ACTIVE, position=IngameRole.THIRD_BASE,
            personality=[1], birthday=datetime(1996, 4, 15), height=190.0, weight=100.0
        )),
        ("Son Contact (Contact Master / Power 650)", Player(
            id=2, name="Son Contact", club_id=1, uniform_number="7", speed=800, control=500, power=650,
            flexibility=700, focus=950, stamina=500, roster_status=RosterStatus.ACTIVE, position=IngameRole.SHORT_STOP,
            personality=[2], birthday=datetime(1999, 7, 22), height=178.0, weight=75.0
        )),
        ("Kang Weak (Weak Batter / Power 380)", Player(
            id=3, name="Kang Weak", club_id=1, uniform_number="99", speed=450, control=500, power=380,
            flexibility=400, focus=420, stamina=500, roster_status=RosterStatus.ACTIVE, position=IngameRole.CATCHER,
            personality=[3], birthday=datetime(2002, 10, 1), height=175.0, weight=72.0
        )),
    ]

    pitch_sel = PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_CENTER)

    for b_label, batter in batters:
        divider = "=" * 95
        print(f"\n{divider}")
        print(f"[BATTER] {b_label} | Stadium: {stadium.name_ko} (Altitude: {stadium.altitude}m)")
        print(f"{divider}")

        homerun_count = 0
        total_trials = 10

        for i in range(total_trials):
            p_res = calculate_pitch_physics(pitcher, pitch_sel)
            b_res = calculate_batting_physics(batter, p_res, IngameBattingStrategy.SWING_FULL)
            t_res = calculate_trajectory_physics(b_res, stadium)

            if t_res.outcome == "HOME_RUN":
                homerun_count += 1
                outcome_str = "[HOME RUN!!]    "
            elif t_res.outcome == "FENCE_HIT":
                outcome_str = "[FENCE HIT!]    "
            elif t_res.outcome == "FOUL_OUT":
                outcome_str = "[FOUL OUT]      "
            else:
                outcome_str = "[IN FIELD LAND] "

            print(
                f"  [{i+1:02d} Hit] Velocity: {b_res.hit_velocity:5.1f}km/h | LaunchAngle: {b_res.launch_angle:+5.1f}deg "
                f"| Backspin: {b_res.backspin_rpm:+6.1f}RPM | Distance: {t_res.distance_m:5.1f}m | HangTime: {t_res.hang_time_sec:4.2f}s "
                f"| MaxHeight: {t_res.max_height_m:4.1f}m | Coords: ({t_res.landing_x_m:+5.1f}m, {t_res.landing_y_m:+5.1f}m) | {outcome_str}"
            )

        hr_rate = (homerun_count / total_trials) * 100
        logger.info(f"[STATS] {b_label} -> Home Run Rate in 10 Hits: {hr_rate:.1f}% ({homerun_count}/{total_trials})")

    print(f"\n{"="*95}")
    logger.info("KLB Trajectory & Distance Physics Demo Completed Successfully!")
    print(f"{"="*95}\n")


if __name__ == "__main__":
    main()
