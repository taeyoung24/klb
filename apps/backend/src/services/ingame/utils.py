from datetime import datetime
from src.enums import (
    IngameRole,
    RosterStatus,
)
from src.models import (
    Player,
    IngameContext,
)


def calculate_pressure_weight(context: IngameContext) -> float:
    """
    인게임 컨텍스트(이닝, BSO 카운트, 루상 주자 상황)를 기반으로 현재 승부의 부담가중치(0.0 ~ 1.0)를 계산합니다.
    - 이닝 가중치: (현재 이닝수 / 9) * 0.2
    - 카운트 가중치: (B + S + O 카운트 총합 / 7) * 0.3
    - 주자 가중치: (루상 주자 수 / 3) * 0.5
    """
    # 1. 이닝 부담 가중치 (이닝이 깊어질수록 증가, 9이닝 기준 최대 0.2)
    inning_val = max(1, context.inning)
    inning_weight = min(1.0, inning_val / 9.0) * 0.2

    # 2. 볼카운트 & 아웃카운트 부담 가중치 (볼3 + 스트2 + 아웃2 = 7 기준 최대 0.3)
    bso_sum = context.scoreboard.balls + context.scoreboard.strikes + context.scoreboard.outs
    bso_weight = min(1.0, bso_sum / 7.0) * 0.3

    # 3. 루상 주자 부담 가중치 (만루 3명 기준 최대 0.5)
    runners_count = sum(1 for r in [context.runner_1b, context.runner_2b, context.runner_3b] if r is not None)
    runners_weight = min(1.0, runners_count / 3.0) * 0.5

    pressure_weight = inning_weight + bso_weight + runners_weight
    return max(0.0, min(1.0, pressure_weight))

def generate_mock_players(club_id: int) -> tuple[Player, list[Player], list[Player], list[Player]]:
    """지정된 클럽 ID를 갖는 목 선발 투수 1명, 불펜 투수들, 목 타자 9명, 그리고 목 벤치 타자들을 생성합니다."""
    # 선발 투수 생성
    starting_pitcher = Player(
        id=club_id * 1000 + 1,
        name=f"선발_{club_id}",
        club_id=club_id,
        uniform_number="01",
        speed=620,
        control=630,
        power=500,
        flexibility=580,
        focus=600,
        stamina=700,
        current_energy=10000,
        max_energy=10000,
        roster_status=RosterStatus.ACTIVE,
        position=IngameRole.PITCHER,
        personality=[500, 500, 500, 500],
        birthday=datetime(2000, 1, 1),
        height=185.0,
        weight=82.0
    )
    
    # 불펜 투수 3명 생성
    bullpen_pitchers = []
    for idx in range(1, 4):
        rp = Player(
            id=club_id * 1000 + 1 + idx,
            name=f"구원_{club_id}_{idx}",
            club_id=club_id,
            uniform_number=f"4{idx}",
            speed=580 + idx * 10,
            control=590 + idx * 5,
            power=500,
            flexibility=570,
            focus=580,
            stamina=550,
            current_energy=10000,
            max_energy=10000,
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.PITCHER,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, 2, idx),
            height=182.0,
            weight=80.0
        )
        bullpen_pitchers.append(rp)

    # 타자 9명 생성
    batters = []
    positions = [
        IngameRole.CATCHER, IngameRole.FIRST_BASE, IngameRole.SECOND_BASE,
        IngameRole.THIRD_BASE, IngameRole.SHORT_STOP, IngameRole.LEFT_FIELD,
        IngameRole.CENTER_FIELD, IngameRole.RIGHT_FIELD, IngameRole.DESIGNATED_HITTER
    ]
    
    for i, pos in enumerate(positions, 1):
        batter = Player(
            id=club_id * 1000 + 10 + i,
            name=f"Batter_{club_id}_{i}",
            club_id=club_id,
            uniform_number=f"{i+10:02d}",
            speed=550 + i * 15,
            control=500,
            power=500 + i * 20,
            flexibility=530 + i * 10,
            focus=520 + i * 15,
            stamina=500,
            current_energy=10000,
            max_energy=10000,
            roster_status=RosterStatus.ACTIVE,
            position=pos,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, i, 1),
            height=180.0,
            weight=78.0
        )
        batters.append(batter)
        
    # 벤치 타자 2명 생성
    bench_batters = []
    for idx in range(1, 3):
        bench = Player(
            id=club_id * 1000 + 30 + idx,
            name=f"Bench_{club_id}_{idx}",
            club_id=club_id,
            uniform_number=f"{idx+50:02d}",
            speed=530 + idx * 20,
            control=500,
            power=520 + idx * 20,
            flexibility=520,
            focus=510,
            stamina=500,
            current_energy=10000,
            max_energy=10000,
            roster_status=RosterStatus.ACTIVE,
            position=IngameRole.LEFT_FIELD if idx == 1 else IngameRole.FIRST_BASE,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, 5, idx),
            height=178.0,
            weight=76.0
        )
        bench_batters.append(bench)

    return starting_pitcher, bullpen_pitchers, batters, bench_batters
