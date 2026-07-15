import random
import calendar
from datetime import datetime
from typing import Optional

from src.enums import RosterStatus, IngameRole
from src.models import Player
from src.utils.str_ext import generate_name

# 주 포지션 9종 정의
PRIMARY_POSITIONS = [
    IngameRole.PITCHER,
    IngameRole.CATCHER,
    IngameRole.FIRST_BASE,
    IngameRole.SECOND_BASE,
    IngameRole.THIRD_BASE,
    IngameRole.SHORT_STOP,
    IngameRole.LEFT_FIELD,
    IngameRole.CENTER_FIELD,
    IngameRole.RIGHT_FIELD,
]

def generate_stats(height: float, weight: float, general: bool = False) -> dict:
    """
    선수의 피지컬 조건에 비례하여 5대 스탯(speed, control, power, flexibility, focus)을 생성합니다.
    general=False (고교 선수)인 경우 스탯 베이스가 낮게 잡힙니다.
    """
    def random_stat():
        if not general:
            # 고교 선수: 평균치 하향 조정
            base = 200 + random.random() * 350 # 200 ~ 550
            variance = (random.random() - 0.5) * 150 # -75 ~ 75
        else:
            # 일반 선수: 기존 레거시 공식
            base = 300 + random.random() * 400 # 300 ~ 700
            variance = (random.random() - 0.5) * 200 # -100 ~ 100
        return int(max(150, min(850, base + variance)))

    size_factor = (height - 175) * 3 + (weight - 75) * 2
    base_power = random_stat()
    power = int(max(150, min(850, base_power + size_factor)))

    weight_factor = (78 - weight) * 3
    base_speed = random_stat()
    speed = int(max(150, min(850, base_speed + weight_factor)))

    return {
        "speed": speed,
        "control": random_stat(),
        "power": power,
        "flexibility": random_stat(),
        "focus": random_stat()
    }

def generate_player(
    club_id: int, 
    position: Optional[IngameRole] = None, 
    general: bool = False,
    current_year: int = 2024
) -> Player:
    """
    지정된 클럽 ID 및 포지션, 그리고 general 조건에 따라 무작위 선수 데이터를 생성합니다.
    """
    # 1. 나이 설정
    if not general:
        # 고교 선수 발탁용: 고졸 신인 연령대 (만 18세~19세)
        age = 18 + random.randint(0, 1)
    else:
        # 초기 시딩용 일반 선수: 19세 ~ 32세 분포
        age_random = random.random()
        if age_random < 0.6:
            age = 23 + random.randint(0, 4)
        elif age_random < 0.85:
            age = 19 + random.randint(0, 3)
        else:
            age = 28 + random.randint(0, 4)

    # 2. 생년월일 설정 (birthday)
    birth_year = current_year - age
    month = random.randint(1, 12)
    _, last_day = calendar.monthrange(birth_year, month)
    day = random.randint(1, last_day)
    birthday = datetime(birth_year, month, day)

    # 3. 포지션 설정
    final_pos = position if position is not None else random.choice(PRIMARY_POSITIONS)

    # 4. 신장 및 체중 (투수 vs 야수)
    is_pitcher = final_pos == IngameRole.PITCHER
    base_height = 178 if is_pitcher else 175
    base_weight = 80 if is_pitcher else 75

    height = float(base_height + int((random.random() - 0.5) * 20))
    weight = float(base_weight + int((random.random() - 0.5) * 20))

    # 5. 스탯 생성
    stats = generate_stats(height, weight, general=general)

    # 6. 인격(personality)
    personality_traits = [random.randint(0, 1000) for _ in range(4)]

    return Player(
        name=generate_name(),
        club_id=club_id,
        speed=stats["speed"],
        control=stats["control"],
        power=stats["power"],
        flexibility=stats["flexibility"],
        focus=stats["focus"],
        roster_status=RosterStatus.ACTIVE,
        position=final_pos,
        personality=personality_traits,
        birthday=birthday,
        height=height,
        weight=weight
    )
