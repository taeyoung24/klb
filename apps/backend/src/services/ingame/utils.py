from datetime import datetime
from src.enums import (
    IngameRole,
    RosterStatus,
)
from src.models import (
    Player,
)

def generate_mock_players(club_id: int) -> tuple[Player, list[Player], list[Player]]:
    """지정된 클럽 ID를 갖는 목 선발 투수 1명, 불펜 투수들, 그리고 목 타자 9명을 생성합니다."""
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
            roster_status=RosterStatus.ACTIVE,
            position=pos,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, i, 1),
            height=180.0,
            weight=78.0
        )
        batters.append(batter)
        
    return starting_pitcher, bullpen_pitchers, batters
