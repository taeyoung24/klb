from datetime import datetime
from src.enums import (
    IngameRole,
    RosterStatus,
)
from src.models import (
    Player,
)

def generate_mock_players(club_id: int) -> tuple[Player, list[Player]]:
    """지정된 클럽 ID를 갖는 목 투수 1명과 목 타자 9명을 생성합니다."""
    # 투수 생성
    pitcher = Player(
        id=club_id * 1000 + 1,
        name=f"Pitcher_{club_id}",
        club_id=club_id,
        speed=600,
        control=620,
        power=500,
        flexibility=580,
        focus=600,
        roster_status=RosterStatus.ACTIVE,
        position=IngameRole.PITCHER,
        personality=[500, 500, 500, 500],
        birthday=datetime(2000, 1, 1),
        height=185.0,
        weight=82.0
    )
    
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
            speed=550 + i * 15,
            control=500,
            power=500 + i * 20,
            flexibility=530 + i * 10,
            focus=520 + i * 15,
            roster_status=RosterStatus.ACTIVE,
            position=pos,
            personality=[500, 500, 500, 500],
            birthday=datetime(2001, i, 1),
            height=180.0,
            weight=78.0
        )
        batters.append(batter)
        
    return pitcher, batters
