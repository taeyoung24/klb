import random
import math
from sqlmodel import SQLModel
from src.enums import IngamePitchType, IngamePitchZone
from src.models import Player, PitchSelectionResult


class PitchPhysicsResult(SQLModel):
    """
    투수 스탯 기반 물리 투구 연산 결과 DTO
    """
    pitch_type: IngamePitchType
    target_zone: IngamePitchZone
    pitch_velocity: float  # 실측 투구 구속 (km/h)
    spin_rate: int         # 투구 회전수 (Spin Rate, RPM)
    is_strike_zone: bool   # 실제 공의 탄착점이 스트라이크 존 내에 투입되었는지 여부
    actual_location_x: float  # 스트라이크 존 중심 기준 가로 위치 (-1.0 ~ 1.0 내부, |x| > 1.0 볼)
    actual_location_y: float  # 스트라이크 존 중심 기준 세로 위치 (-1.0 ~ 1.0 내부, |y| > 1.0 볼)


# 각 존의 중심 좌표 정의 (x: -1.0 ~ 1.0, y: -1.0 ~ 1.0)
ZONE_COORDINATES: dict[IngamePitchZone, tuple[float, float]] = {
    IngamePitchZone.ZONE_CENTER: (0.0, 0.0),
    IngamePitchZone.ZONE_HIGH_INSIDE: (-0.6, 0.6),
    IngamePitchZone.ZONE_HIGH_OUTSIDE: (0.6, 0.6),
    IngamePitchZone.ZONE_LOW_INSIDE: (-0.6, -0.6),
    IngamePitchZone.ZONE_LOW_OUTSIDE: (0.6, -0.6),
    IngamePitchZone.BALL_HIGH: (0.0, 1.3),
    IngamePitchZone.BALL_LOW: (0.0, -1.3),
    IngamePitchZone.BALL_INSIDE: (-1.3, 0.0),
    IngamePitchZone.BALL_OUTSIDE: (1.3, 0.0),
}

# 구종별 최고 구속 대비 속도 비율
PITCH_SPEED_RATIO: dict[IngamePitchType, float] = {
    IngamePitchType.FASTBALL: 1.00,
    IngamePitchType.SINKER: 0.95,
    IngamePitchType.SLIDER: 0.91,
    IngamePitchType.SPLITTER: 0.89,
    IngamePitchType.CHANGEUP: 0.86,
    IngamePitchType.CURVEBALL: 0.82,
}

# 구종별 기준 평균 회전수 (RPM)
PITCH_BASE_SPIN_RPM: dict[IngamePitchType, int] = {
    IngamePitchType.FASTBALL: 2250,
    IngamePitchType.SLIDER: 2450,
    IngamePitchType.CURVEBALL: 2600,
    IngamePitchType.SINKER: 2100,
    IngamePitchType.CHANGEUP: 1700,
    IngamePitchType.SPLITTER: 1450,
}


def calculate_pitch_physics(
    pitcher: Player,
    pitch_selection: PitchSelectionResult
) -> PitchPhysicsResult:
    """
    투수의 스탯(power, control)과 구종/코스 판단 결과를 입력받아 
    실제 투구 구속(km/h), 회전수(RPM) 및 정밀 2차원 탄착점 물리 위치를 연산합니다.
    """
    power = pitcher.power
    control = pitcher.control

    # 1. 구속 연산 (km/h)
    max_fb_speed = 130.0 + (power / 1000.0) * 32.0
    speed_ratio = PITCH_SPEED_RATIO.get(pitch_selection.pitch_type, 0.90)
    speed_fluctuation = random.uniform(-1.5, 1.5)
    actual_velocity = round(max_fb_speed * speed_ratio + speed_fluctuation, 1)

    # 2. 회전수 연산 (Spin Rate, RPM)
    base_rpm = PITCH_BASE_SPIN_RPM.get(pitch_selection.pitch_type, 2000)
    # 파워/제구 스탯 합산에 따른 회전수 추가 보정 (±300 RPM 범위)
    stat_boost_rpm = int(((power + control) / 2000.0) * 350) - 175
    actual_spin_rate = max(1000, base_rpm + stat_boost_rpm + random.randint(-80, 80))

    # 3. 제구 및 탄착점 연산 (x, y 좌표)
    # TODO: 향후 투수 투구수 누적 및 이닝 진행에 따른 체력(Stamina/Fatigue) 감쇄 물리 수식 추가 예정
    focus = pitcher.focus
    
    # control 수치에 따른 탄착 분산 표준편차 연속 수식 연산 (control 1000 -> sigma 0.32, control 1 -> sigma 1.10)
    sigma = 0.32 + (1.0 - control / 1000.0) * 0.78

    # focus(집중력) 수치에 따른 제구 실투 오차 변동 강화
    focus_wildness = random.gauss(0, (1.0 - focus / 1000.0) * 0.45)




    target_x, target_y = ZONE_COORDINATES.get(
        pitch_selection.target_zone, (0.0, 0.0)
    )

    actual_x = round(random.gauss(target_x + focus_wildness, sigma), 2)
    actual_y = round(random.gauss(target_y + focus_wildness, sigma), 2)

    is_strike = (abs(actual_x) <= 1.0) and (abs(actual_y) <= 1.0)


    return PitchPhysicsResult(
        pitch_type=pitch_selection.pitch_type,
        target_zone=pitch_selection.target_zone,
        pitch_velocity=actual_velocity,
        spin_rate=actual_spin_rate,
        is_strike_zone=is_strike,
        actual_location_x=actual_x,
        actual_location_y=actual_y
    )

