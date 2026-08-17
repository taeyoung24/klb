# uv run -m scripts.services.ingame.physics.demo_fielding
from datetime import datetime

from src.utils.logger import logger
from src.models import Stadium, Player, PitchSelectionResult
from src.enums import IngameRole, RosterStatus, IngamePitchType, IngamePitchZone, IngameBattingStrategy, TurfType
from src.services.ingame.physics import (
    calculate_pitch_physics,
    calculate_batting_physics,
    calculate_trajectory_physics,
    calculate_fielding_physics,
)


def create_defense_lineup(team_name: str, base_stat: int) -> list[Player]:
    """테스트용 9인 수비 라인업 생성"""
    roles = [
        IngameRole.PITCHER, IngameRole.CATCHER, IngameRole.FIRST_BASE, IngameRole.SECOND_BASE,
        IngameRole.THIRD_BASE, IngameRole.SHORT_STOP, IngameRole.LEFT_FIELD, IngameRole.CENTER_FIELD, IngameRole.RIGHT_FIELD
    ]
    lineup = []
    for i, role in enumerate(roles):
        p = Player(
            id=100 + i if base_stat > 600 else 200 + i,
            name=f"{team_name} {role.name}",
            club_id=1,
            uniform_number=str(i + 1),
            speed=base_stat,
            control=base_stat,
            power=base_stat,
            flexibility=base_stat,
            focus=base_stat,
            stamina=base_stat,
            roster_status=RosterStatus.ACTIVE,
            position=role,
            personality=[1],
            birthday=datetime(1997, 1, 1),
            height=182.0,
            weight=80.0,
        )
        lineup.append(p)
    return lineup


def main():
    logger.info("==================================================================")
    logger.info("       KLB Fielding & Defense Physics Demo Simulator              ")
    logger.info("==================================================================")

    gold_glove_team = create_defense_lineup("GoldGlove", 900)
    clumsy_team = create_defense_lineup("ClumsyDef", 400)

    # 테스트 타자 및 투수
    pitcher = gold_glove_team[0]
    batter = Player(
        id=1, name="Batter", club_id=2, uniform_number="55", speed=600, control=500, power=850,
        flexibility=500, focus=750, stamina=500, roster_status=RosterStatus.ACTIVE, position=IngameRole.THIRD_BASE,
        personality=[1], birthday=datetime(1996, 4, 15), height=188.0, weight=92.0
    )

    stadium = Stadium(
        id=1, name="Jamsil", name_ko="Jamsil", is_dome=False, capacity=25000,
        turf_type=TurfType.NATURAL, altitude=35.0, curvature=0.5
    )

    pitch_sel = PitchSelectionResult(pitch_type=IngamePitchType.FASTBALL, target_zone=IngamePitchZone.ZONE_CENTER)

    for team_name, lineup in [("Gold Glove Team (Stat: 900)", gold_glove_team), ("Clumsy Team (Stat: 400)", clumsy_team)]:
        divider = "=" * 95
        print(f"\n{divider}")
        print(f"[DEFENSE LINEUP] {team_name}")
        print(f"{divider}")

        caught_count = 0
        total_trials = 10

        for i in range(total_trials):
            p_res = calculate_pitch_physics(pitcher, pitch_sel)
            b_res = calculate_batting_physics(batter, p_res, IngameBattingStrategy.SWING_FULL)
            t_res = calculate_trajectory_physics(b_res, stadium)
            f_res = calculate_fielding_physics(lineup, t_res, target_base=1)

            if f_res.is_caught_in_air:
                caught_count += 1
                status_str = "[FLY OUT CATCH]  "
            elif f_res.fumble_delay_sec > 0:
                status_str = f"[BOBBLE/ERROR +{f_res.fumble_delay_sec:.1f}s]"
            else:
                status_str = "[GROUND CATCH]   "

            print(
                f"  [{i+1:02d} Defense] Fielder: {f_res.fielder.position.name:<13} | BallCoords: ({t_res.landing_x_m:+5.1f}m, {t_res.landing_y_m:+5.1f}m) "
                f"| HangTime: {t_res.hang_time_sec:4.2f}s | ReachTime: {f_res.reach_time_sec:4.2f}s | ThrowTime1B: {f_res.throw_time_sec:4.2f}s | {status_str}"
            )

        flyout_rate = (caught_count / total_trials) * 100
        logger.info(f"[STATS] {team_name} -> Fly Out Catch Rate in 10 Hits: {flyout_rate:.1f}% ({caught_count}/{total_trials})")

    print(f"\n{"="*95}")
    logger.info("KLB Fielding & Defense Physics Demo Completed Successfully!")
    print(f"{"="*95}\n")


if __name__ == "__main__":
    main()
