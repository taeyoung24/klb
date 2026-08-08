# uv run -m scripts.services.ingame.physics.demo_batting
from datetime import datetime

from src.utils.logger import logger
from src.models import Player, PitchSelectionResult
from src.enums import IngameRole, RosterStatus, IngamePitchType, IngamePitchZone, IngameBattingStrategy
from src.services.ingame.physics import calculate_pitch_physics, calculate_batting_physics


def main():
    logger.info("==================================================================")
    logger.info("       KLB Batting Physics Demo Simulator                       ")
    logger.info("==================================================================")

    # 1. 테스트용 가정 투수 (Power: 850, Control: 750)
    pitcher = Player(
        id=99,
        name="투수 (테스트용)",
        club_id=1,
        uniform_number="1",
        speed=500,
        control=750,
        power=850,
        flexibility=500,
        focus=500,
        roster_status=RosterStatus.ACTIVE,
        position=IngameRole.PITCHER,
        personality=[1],
        birthday=datetime(1995, 1, 1),
        height=185.0,
        weight=85.0,
    )

    # 2. 타자 프로필 샘플 (Slugger / Contact Hitter / Weak Hitter)
    batters = [
        Player(
            id=1,
            name="Choi Power (Slugger / Power 960, Focus 650)",
            club_id=1,
            uniform_number="55",
            speed=400,
            control=500,
            power=960,   # 최상급 장타력 (강력한 타구속도)
            flexibility=500,
            focus=650,   # 보통 집중력
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.THIRD_BASE,
            personality=[1],
            birthday=datetime(1996, 4, 15),
            height=190.0,
            weight=100.0,
        ),
        Player(
            id=2,
            name="Son Contact (Contact Master / Power 620, Focus 950)",
            club_id=1,
            uniform_number="7",
            speed=800,
            control=500,
            power=620,   # 보통 파워
            flexibility=700,
            focus=950,   # 극상의 선구안 & 스윗스폿 정타 능력
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.SHORT_STOP,
            personality=[2],
            birthday=datetime(1999, 7, 22),
            height=178.0,
            weight=75.0,
        ),
        Player(
            id=3,
            name="Kang Weak (Weak Batter / Power 380, Focus 420)",
            club_id=1,
            uniform_number="99",
            speed=450,
            control=500,
            power=380,   # 약한 파워
            flexibility=400,
            focus=420,   # 낮은 정타율 및 잦은 빗맞음
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.CATCHER,
            personality=[3],
            birthday=datetime(2002, 10, 1),
            height=175.0,
            weight=72.0,
        ),
    ]

    # 샘플 투구
    test_pitch_selections = [
        PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_CENTER),
        PitchSelectionResult(pitch_type=IngamePitchType.SLIDER, target_zone=IngamePitchZone.ZONE_LOW_OUTSIDE),
        PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_HIGH_INSIDE),
        PitchSelectionResult(pitch_type=IngamePitchType.CURVEBALL, target_zone=IngamePitchZone.ZONE_LOW_INSIDE),
        PitchSelectionResult(pitch_type=IngamePitchType.CHANGEUP, target_zone=IngamePitchZone.BALL_LOW),
    ]

    for b in batters:
        divider = "=" * 90
        print(f"\n{divider}")
        print(f"[BATTER PROFILE] {b.name} | Power(ExitVel): {b.power} | Focus(SweetSpot): {b.focus}")
        print(f"{divider}")

        fair_count = 0
        total_trials = 10

        for i in range(total_trials):
            pitch_sel = test_pitch_selections[i % len(test_pitch_selections)]
            p_res = calculate_pitch_physics(pitcher, pitch_sel)
            b_res = calculate_batting_physics(b, p_res, IngameBattingStrategy.SWING_FULL)

            if b_res.is_fair_territory:
                fair_count += 1
                territory_str = "[FAIR (IN)] "
            else:
                territory_str = "[FOUL (OUT)]"

            print(
                f"  [{i+1:02d} Hit] Pitch: {p_res.pitch_type.name:<9} | PitchVel: {p_res.pitch_velocity:5.1f}km/h "
                f"| HitVel: {b_res.hit_velocity:5.1f}km/h | LaunchAngle: {b_res.launch_angle:+5.1f}° "
                f"| Backspin: {b_res.backspin_rpm:+6.1f} RPM | SprayAngle: {b_res.spray_angle:+5.1f}° | {territory_str}"
            )


        fair_rate = (fair_count / total_trials) * 100
        logger.info(f"[STATS] {b.name} -> Fair Territory Rate in 10 Hits: {fair_rate:.1f}% ({fair_count}/{total_trials})")

    print(f"\n{"="*90}")
    logger.success("KLB Batting Physics Demo Completed Successfully!")
    print(f"{"="*90}\n")


if __name__ == "__main__":
    main()
