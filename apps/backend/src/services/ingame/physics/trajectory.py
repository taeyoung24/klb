import math
import random
from enum import StrEnum
from sqlmodel import SQLModel

from src.models import Stadium
from .batting import BattingPhysicsResult


class HitOutcome(StrEnum):
    """타구 최종 궤적 판정 결과"""
    HOME_RUN     = "HOME_RUN"      # 펜스를 넘어간 장외 홈런
    FENCE_HIT    = "FENCE_HIT"     # 펜스를 맞고 튀어나온 타구 (펜스 직격)
    IN_FIELD     = "IN_FIELD"      # 내야/외야 필드 내 착지 타구
    FOUL_OUT     = "FOUL_OUT"      # 관중석 파울 타구


class TrajectoryPhysicsResult(SQLModel):
    """
    타구 궤적 및 비거리, 체류시간, 홈런 판정 결과 DTO
    """
    distance_m: float      # 최종 수평 비거리 (m)
    hang_time_sec: float   # 공중 체류시간 (Hang Time, 초)
    max_height_m: float    # 최고 도달 높이 (m)
    landing_x_m: float     # 홈플레이트 기준 2D 착지 X 좌표 (m, 오른쪽 +, 왼쪽 -)
    landing_y_m: float     # 홈플레이트 기준 2D 착지 Y 좌표 (m, 센터 방향 +)
    outcome: HitOutcome    # 타구 최종 궤적 판정 결과


def calculate_trajectory_physics(
    batting_physics: BattingPhysicsResult,
    stadium: Stadium | None = None,
) -> TrajectoryPhysicsResult:
    """
    타격 물리 결과(타구속도, 발사각, 방위각, 백스핀)와 구장 정보(고도, 펜스)를 입력받아
    공기 저항 및 백스핀 마그누스 양력을 적용한 3차원 포물선 궤적, 체류시간(초), 최종 비거리(m) 및 홈런 판정을 연산합니다.
    """
    v0_kmh = batting_physics.hit_velocity
    launch_angle_deg = batting_physics.launch_angle
    spray_angle_deg = batting_physics.spray_angle
    backspin_rpm = batting_physics.backspin_rpm

    # 1. 초기 속도 성분 분해 (m/s)
    v0_ms = v0_kmh * (1000.0 / 3600.0)
    launch_rad = math.radians(launch_angle_deg)
    spray_rad = math.radians(spray_angle_deg)

    v_xy0 = v0_ms * math.cos(launch_rad)  # 수평 초기 속도
    vz0 = v0_ms * math.sin(launch_rad)    # 수직 초기 속도

    # 2. 백스핀 마그누스 양력(Magnus Lift) 보정 연산
    # 백스핀(rpm > 0) 양력 가속도 상쇄 폭 현실화 (최대 1.8 m/s^2)
    g = 9.81
    if backspin_rpm > 0:
        lift_acceleration = min(1.8, (backspin_rpm / 1000.0) * 0.55)
    else:
        # 톱스핀(땅볼): 아래로 가라앉음
        lift_acceleration = -min(1.5, (abs(backspin_rpm) / 1000.0) * 0.45)

    effective_g = max(7.2, g - lift_acceleration)

    # 3. 체류시간(Hang Time, 초) 및 최고점 높이(m) 연산
    h0 = 1.0
    if vz0 > 0:
        hang_time_sec = (vz0 + math.sqrt(vz0 ** 2 + 2 * effective_g * h0)) / effective_g
        max_height_m = round(h0 + (vz0 ** 2) / (2 * effective_g), 1)
    else:
        # 땅볼 타구
        hang_time_sec = max(0.2, (v0_ms * 0.05))
        max_height_m = h0

    hang_time_sec = round(max(0.2, hang_time_sec), 2)

    # 4. 공기 저항 및 고도(Altitude) 반영 수평 비거리(m) 연산
    altitude = getattr(stadium, "altitude", 0.0) if stadium else 0.0
    altitude_factor = 1.0 + (altitude / 1000.0) * 0.05

    # 공기 저항 항력 계수 (야구공 실측 k = 0.0145)
    k = 0.0145
    raw_distance = (v_xy0 / k) * (1.0 - math.exp(-k * hang_time_sec)) * altitude_factor
    
    # 지면 착지 및 구르는 비거리 최종 보정
    distance_m = round(max(0.5, raw_distance), 1)



    # 5. 2D 착지 평면 좌표 (landing_x_m, landing_y_m) 연산
    landing_x_m = round(distance_m * math.sin(spray_rad), 1)
    landing_y_m = round(distance_m * math.cos(spray_rad), 1)

    # 6. 구장 펜스 및 홈런/펜스직격/파울 판정
    # 구장 펜스 프로필 (방위각에 따른 좌/우/중앙 펜스 거리 및 펜스 높이)
    fence_distance = 120.0 - abs(spray_angle_deg) * 0.45  # 중앙 120m, 좌/우측 99.7m
    fence_height = 3.2  # 표준 펜스 높이 3.2m

    if not batting_physics.is_fair_territory:
        outcome = HitOutcome.FOUL_OUT
    elif distance_m >= fence_distance:
        # 펜스 지점에서의 공의 높이 추정 연산
        time_at_fence = fence_distance / max(1.0, v_xy0)
        height_at_fence = h0 + vz0 * time_at_fence - 0.5 * effective_g * (time_at_fence ** 2)

        if height_at_fence > fence_height:
            outcome = HitOutcome.HOME_RUN
        else:
            outcome = HitOutcome.FENCE_HIT
    else:
        outcome = HitOutcome.IN_FIELD

    return TrajectoryPhysicsResult(
        distance_m=distance_m,
        hang_time_sec=hang_time_sec,
        max_height_m=max_height_m,
        landing_x_m=landing_x_m,
        landing_y_m=landing_y_m,
        outcome=outcome
    )
