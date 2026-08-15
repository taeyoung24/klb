# uv run -m scripts.services.ingame.physics.demo_pitching
from datetime import datetime

from src.utils.logger import logger
from src.models import Player, PitchSelectionResult
from src.enums import IngameRole, RosterStatus, IngamePitchType, IngamePitchZone
from src.services.ingame.physics import calculate_pitch_physics


def main():
    logger.info("==================================================================")
    logger.info("       KLB Pitching Physics Demo Simulator                      ")
    logger.info("==================================================================")

    # 1. 샘플 투수 프로필 정의 (Power: 구속, Control: 제구력)
    pitchers = [
        Player(
            id=1,
            name="Kim Fire (Fireballer & High Control)",
            club_id=1,
            uniform_number="11",
            speed=500,
            control=880,  # 제구 상급 (탄착군 정밀)
            power=920,    # 구속 상급 (155km+ 직구)
            flexibility=600,
            focus=700,
            stamina=500,
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.PITCHER,
            personality=[1, 2],
            birthday=datetime(1998, 5, 20),
            height=188.0,
            weight=90.0,
        ),
        Player(
            id=2,
            name="Park Flame (Wild Fireballer)",
            club_id=1,
            uniform_number="45",
            speed=500,
            control=320,  # 제구 난조 (탄착군 산포도 큼)
            power=960,    # 최정상급 구속 (160km+)
            flexibility=500,
            focus=500,
            stamina=500,
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.PITCHER,
            personality=[3, 4],
            birthday=datetime(2001, 8, 12),
            height=192.0,
            weight=95.0,
        ),
        Player(
            id=3,
            name="Lee Crafty (Control Master)",
            club_id=1,
            uniform_number="21",
            speed=500,
            control=940,  # 최상급 제구 (탄착군 극도로 정밀)
            power=420,    # 둔한 구속 (140km대 직구)
            flexibility=800,
            focus=850,
            stamina=500,
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.PITCHER,
            personality=[1, 5],
            birthday=datetime(1992, 11, 3),
            height=178.0,
            weight=78.0,
        ),
    ]

    # 테스트할 구종 및 조준 존 샘플
    test_selections = [
        PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_CENTER),
        PitchSelectionResult(pitch_type=IngamePitchType.SLIDER, target_zone=IngamePitchZone.ZONE_LOW_OUTSIDE),
        PitchSelectionResult(pitch_type=IngamePitchType.SPLITTER, target_zone=IngamePitchZone.BALL_LOW),
        PitchSelectionResult(pitch_type=IngamePitchType.CURVEBALL, target_zone=IngamePitchZone.ZONE_HIGH_INSIDE),
        PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_LOW_INSIDE),
    ]

    for p in pitchers:
        divider = "=" * 80
        print(f"\n{divider}")
        print(f"[PITCHER PROFILE] {p.name} | Power(Speed): {p.power} | Control(Accuracy): {p.control}")
        print(f"{divider}")

        strike_count = 0
        total_trials = 10

        for i in range(total_trials):
            sel = test_selections[i % len(test_selections)]
            res = calculate_pitch_physics(p, sel)
            
            if res.is_strike_zone:
                strike_count += 1
                status_str = "[STRIKE (IN)] "
            else:
                status_str = "[BALL (OUT)]   "

            print(
                f"  [{i+1:02d} Pitch] Pitch: {res.pitch_type.name:<9} | Zone: {res.target_zone.name:<17} "
                f"| Velocity: {res.pitch_velocity:5.1f} km/h | SpinRate: {res.spin_rate:4d} RPM | Coords: (X:{res.actual_location_x:+4.2f}, Y:{res.actual_location_y:+4.2f}) | {status_str}"
            )


        strike_rate = (strike_count / total_trials) * 100
        logger.info(f"[STATS] {p.name} -> Strike Rate in 10 Pitches: {strike_rate:.1f}% ({strike_count}/{total_trials})")

    print(f"\n{"="*80}")
    logger.success("KLB Pitching Physics Demo Completed Successfully!")
    print(f"{"="*80}\n")


if __name__ == "__main__":
    main()
