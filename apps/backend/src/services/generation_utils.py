import random
import calendar
from datetime import datetime
from typing import Optional

from src.enums import RosterStatus, IngameRole, TurfType
from src.models import Player, Stadium, HighSchool
from src.utils.str_ext import generate_name

# 고등학교 인덱스 카운터
_high_school_counter = 1

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
    선수의 6대 스탯(speed, control, power, flexibility, focus, stamina)을 생성합니다.
    - 스탯 총합: 정규분포를 따르며 general=False(고교)일 때 전체 총합 분포가 낮습니다.
    - 개별 스탯: 총합 내에서 생 랜덤(Uniform) 가중치 비율로 분배됩니다.
    """
    # 1. 정규분포로 스탯 총합(면적) 결정
    if not general:
        # 고교 선수: 총합 평균 2220 (개별 평균 370), 표준편차 240
        mean_total, std_total = 2220.0, 240.0
        min_total, max_total = 1200, 3100
    else:
        # 일반 선수: 총합 평균 3000 (개별 평균 500), 표준편차 300
        mean_total, std_total = 3000.0, 300.0
        min_total, max_total = 1800, 4200

    total_stat = int(max(min_total, min(max_total, random.gauss(mean_total, std_total))))

    # 2. 피지컬 조건에 따른 성향 보정치 + 생 랜덤 가중치 (0.5 ~ 1.5)
    size_factor = (height - 175) * 0.01 + (weight - 75) * 0.01
    weight_factor = (78 - weight) * 0.01

    w_power = max(0.1, random.uniform(0.5, 1.5) + size_factor)
    w_speed = max(0.1, random.uniform(0.5, 1.5) + weight_factor)
    w_control = random.uniform(0.5, 1.5)
    w_flexibility = random.uniform(0.5, 1.5)
    w_focus = random.uniform(0.5, 1.5)
    w_stamina = random.uniform(0.5, 1.5)

    weights = [w_speed, w_control, w_power, w_flexibility, w_focus, w_stamina]
    total_weight = sum(weights)

    # 3. 비율 기반 스탯 분배
    raw_values = [w / total_weight * total_stat for w in weights]
    stat_values = [int(round(v)) for v in raw_values]

    # 최소/최대 스탯 안전범위 지정 (100 ~ 950)
    for i in range(6):
        stat_values[i] = max(100, min(950, stat_values[i]))

    # 정수화 및 클램핑에 따른 합계 차이 보정 (총합이 정확히 total_stat이 되도록)
    diff = total_stat - sum(stat_values)
    while diff != 0:
        idx = random.randint(0, 5)
        if diff > 0 and stat_values[idx] < 950:
            stat_values[idx] += 1
            diff -= 1
        elif diff < 0 and stat_values[idx] > 100:
            stat_values[idx] -= 1
            diff += 1

    return {
        "speed": stat_values[0],
        "control": stat_values[1],
        "power": stat_values[2],
        "flexibility": stat_values[3],
        "focus": stat_values[4],
        "stamina": stat_values[5]
    }

def generate_player(
    region_id: int,
    high_school_id: int,
    club_id: Optional[int] = None, 
    position: Optional[IngameRole] = None, 
    general: bool = False,
    current_year: int = 2024
) -> Player:
    """
    지정된 클럽 ID, 출신 지역 ID, 출신 고등학교 ID 및 포지션, general 조건에 따라 무작위 선수 데이터를 생성합니다.
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

    # 7. 등번호 생성 ("00" ~ "99")
    # TODO: 구단 내 등번호 중복 방지 및 고유 등번호 재할당 검증 로직 구현 필요 (26. 8. 3. Antigravity)
    uniform_number = f"{random.randint(0, 99):02d}"

    return Player(
        name=generate_name(),
        club_id=club_id,
        region_id=region_id,
        high_school_id=high_school_id,
        uniform_number=uniform_number,
        speed=stats["speed"],
        control=stats["control"],
        power=stats["power"],
        flexibility=stats["flexibility"],
        focus=stats["focus"],
        stamina=stats["stamina"],
        roster_status=RosterStatus.ACTIVE,
        position=final_pos,
        personality=personality_traits,
        birthday=birthday,
        height=height,
        weight=weight
    )

def generate_fence_profile(
    left_dist: float = 98.0,
    center_dist: float = 120.0,
    right_dist: float = 98.0,
    left_height: float = 2.5,
    center_height: float = 2.5,
    right_height: float = 2.5
) -> list[dict[str, float]]:
    """
    구장의 극좌표계 기반 외야 펜스 기하 프로필 데이터를 생성합니다.
    """
    left_center_dist = round((left_dist + center_dist) / 2 + random.uniform(1.0, 3.0), 1)
    right_center_dist = round((right_dist + center_dist) / 2 + random.uniform(1.0, 3.0), 1)

    return [
        {"angle": -45.0, "dist": round(left_dist, 1), "height": round(left_height, 1)},
        {"angle": -22.5, "dist": left_center_dist, "height": round((left_height + center_height) / 2, 1)},
        {"angle": 0.0, "dist": round(center_dist, 1), "height": round(center_height, 1)},
        {"angle": 22.5, "dist": right_center_dist, "height": round((right_height + center_height) / 2, 1)},
        {"angle": 45.0, "dist": round(right_dist, 1), "height": round(right_height, 1)},
    ]

def generate_stadium(name: str, name_ko: str, region_id: int) -> Stadium:
    """
    구장 이름(영어, 한글) 및 지역 ID를 기반으로 코어 시뮬레이터 물리 엔진용 구장 객체를 생성합니다.
    """
    is_dome = random.random() < 0.15
    capacity = random.randint(15, 45) * 1000
    turf_type = random.choices(
        [TurfType.NATURAL, TurfType.ARTIFICIAL, TurfType.HYBRID],
        weights=[0.7, 0.2, 0.1]
    )[0]
    altitude = round(random.uniform(5.0, 150.0), 1)

    left_dist = random.uniform(95.0, 102.0)
    center_dist = random.uniform(117.0, 125.0)
    right_dist = random.uniform(95.0, 102.0)

    left_height = random.uniform(2.0, 4.5)
    center_height = random.uniform(2.0, 3.5)
    right_height = random.uniform(2.0, 4.5)

    fence_profile = generate_fence_profile(
        left_dist=left_dist,
        center_dist=center_dist,
        right_dist=right_dist,
        left_height=left_height,
        center_height=center_height,
        right_height=right_height
    )
    curvature = round(random.uniform(0.3, 0.8), 2)

    return Stadium(
        name=name,
        name_ko=name_ko,
        region_id=region_id,
        is_dome=is_dome,
        capacity=capacity,
        turf_type=turf_type,
        altitude=altitude,
        fence_profile=fence_profile,
        curvature=curvature
    )


def generate_high_school(region_id: int) -> HighSchool:
    """
    고등학교 모델 객체를 생성합니다.
    이름은 전역 카운터(_high_school_counter)를 사용하여 '고등학교#1', '고등학교#2' 형태로 부여되며,
    야구 전문고 여부 및 학생 수용량이 무작위로 할당됩니다.
    """
    global _high_school_counter
    hs_index = _high_school_counter
    _high_school_counter += 1

    is_specialized = random.random() < 0.04
    capacity = random.randint(30, 150) * 10

    return HighSchool(
        name=f"HighSchool #{hs_index}",
        name_ko=f"고등학교#{hs_index}",
        is_specialized=is_specialized,
        capacity=capacity,
        region_id=region_id
    )
