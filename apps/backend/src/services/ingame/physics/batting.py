import random
import math
from sqlmodel import SQLModel
from src.enums import IngameContactType, IngameBattingStrategy
from src.models import Player, IngameContext
from .pitching import PitchPhysicsResult
from ..utils import calculate_pressure_weight


class BattingPhysicsResult(SQLModel):
    """
    타자 스탯 및 투구 물리에 기반한 타격 임팩트 물리 연산 결과 DTO
    """
    hit_velocity: float    # 타구 발사 속도 (Exit Velocity, km/h)
    launch_angle: float    # 타구 발사 각도 (-90.0° 수직 땅볼 ~ +90.0° 수직 직천구)
    spray_angle: float     # 타구 좌우 방위각 (-90.0° 3루 덕아웃 ~ 0.0° 중앙 ~ +90.0° 1루 덕아웃)
    spin_rate: int         # 총 타구 회전수 (Spin Rate, RPM)
    backspin_rpm: float    # 백스핀/톱스핀 회전수 (양수: 백스핀 ➔ 비거리 양력 가속, 음수: 톱스핀)
    sidespin_rpm: float    # 사이드스핀 회전수 (양수: 오른쪽 휨, 음수: 왼쪽 휨)
    contact_type: IngameContactType

    @property
    def is_fair_territory(self) -> bool:
        """방위각(|spray_angle| <= 45.0°)으로 페어 지역 인플레이 여부 자동 판정"""
        return abs(self.spray_angle) <= 45.0


def calculate_swing_contact_probability(
    batter: Player,
    pitcher: Player,
    pitch_physics: PitchPhysicsResult,
    context: IngameContext | None = None,
) -> float:
    """
    타자와 투수의 스탯 대결(control, power, focus를 통한 상황 부담 억제)과 투구 탄착 오프셋(px, py),
    투수의 구위(구속, 회전수)를 기반으로 배트 스윙 시 공을 맞출 순수 컨택트(Contact) 성공 확률(0.0 ~ 1.0)을 연산합니다.

    - control 대결: 배트 컨트롤/스윙 궤적 제어 vs 투구 로케이션/제구 정밀도 (40%)
    - power 대결: 배트 스피드 vs 구속/구위 (22%)
    - focus 대결: 현재 상황의 '부담가중치'를 억제(1000 - focus)하여 위기/압박 속 멘탈 우위 점유 (22%)
    - energy 대결: 양 선수 간의 잔여 체력 비중 대결 (16%)
    - stuff 보정: 존 중앙이라도 구속 및 회전수가 뛰어난 투구에 대한 헛스윙 유도 보너스
    """
    px = pitch_physics.actual_location_x
    py = pitch_physics.actual_location_y
    offset_dist = math.sqrt(px ** 2 + py ** 2)

    # 1. 상황 부담가중치 연산 및 focus를 통한 부담 억제 대결
    pressure_weight = calculate_pressure_weight(context) if context is not None else 0.0
    batter_pressure = pressure_weight * ((1000.0 - batter.focus) / 1000.0)
    pitcher_pressure = pressure_weight * ((1000.0 - pitcher.focus) / 1000.0)
    diff_pressure = pitcher_pressure - batter_pressure  # 타자가 부담을 덜 느낄수록 양수(우위)

    # 2. 스탯 및 현 체력 1:1 대칭 대결 우위 지수 (-1.0 ~ 1.0)
    diff_control = (batter.control - pitcher.control) / 1000.0
    diff_power = (batter.power - pitcher.power) / 1000.0

    # 양쪽 '현 체력'의 합에 대한 각자의 현체력 비율 대결 (-1.0 ~ 1.0)
    total_energy = max(0, batter.current_energy) + max(0, pitcher.current_energy)
    if total_energy > 0:
        diff_energy = (batter.current_energy - pitcher.current_energy) / total_energy
    else:
        diff_energy = 0.0

    stat_advantage = (
        diff_control * 0.46
        + diff_power * 0.25
        + diff_pressure * 0.25
        + diff_energy * 0.04
    )

    # 3. 투수 구위(구속, 회전수)에 의한 헛스윙 유도 페널티 (Stuff Bonus)
    # 기준 구속 142km/h, 기준 회전수 2150 RPM 대비 초과분에 따른 위력 감쇄
    vel_effect = (pitch_physics.pitch_velocity - 142.0) / 100.0
    spin_effect = (pitch_physics.spin_rate - 2150.0) / 3000.0
    pitch_stuff_penalty = max(-0.06, min(0.12, (vel_effect * 0.55 + spin_effect * 0.45) * 0.18))

    # 4. 존 중심 오프셋 및 구위 반영 기본 컨택트 기준치
    base_contact = 0.90 - ((offset_dist ** 1.3) * 0.24) - pitch_stuff_penalty

    # 5. 최종 컨택트 확률 산출 (0.10 ~ 0.96 범위 클램핑)
    p_contact = base_contact + (stat_advantage * 0.30)
    return max(0.10, min(0.96, p_contact))


def calculate_batting_physics(
    batter: Player,
    pitch_physics: PitchPhysicsResult,
    batting_strategy: IngameBattingStrategy = IngameBattingStrategy.SWING_FULL,
    pitcher: Player | None = None,
) -> BattingPhysicsResult:
    """
    타자의 스탯(power, focus)과 투구 물리(구속, 탄착점, 회전수), 투수 스탯(focus, control)을 입력받아
    배트 임팩트 순간의 타구 속도(km/h), 발사 각도(도), 방위각(도) 및 백스핀/사이드스핀(RPM)을 연산합니다.
    """
    power = batter.power
    focus = batter.focus

    # 1. 최고 타구 발사 속도 (Exit Velocity) 기본치 연산
    pitch_velocity_boost = pitch_physics.pitch_velocity * 0.12
    max_exit_velocity = 95.0 + (power / 1000.0) * 60.0 + pitch_velocity_boost

    # 2. 스윗스폿(Sweet Spot) 임팩트 품질 및 투수 구위/멘탈 억제 연산
    px = pitch_physics.actual_location_x
    py = pitch_physics.actual_location_y
    offset_dist = math.sqrt(px ** 2 + py ** 2)

    # 투수 스탯(focus, control)에 따른 정타 억제력
    pitcher_focus = pitcher.focus if pitcher is not None else 500.0
    pitcher_control = pitcher.control if pitcher is not None else 500.0
    pitcher_suppression = (pitcher_focus * 0.6 + pitcher_control * 0.4) / 1000.0

    # 구위(회전수/구속) 및 타자 focus에 따른 임팩트 품질 감쇄
    stuff_factor = max(0.85, min(1.20, (pitch_physics.spin_rate / 2200.0) * 0.5 + (pitch_physics.pitch_velocity / 142.0) * 0.5))
    focus_factor = max(0.15, 1.25 - (focus / 1000.0) * 0.85)
    impact_penalty = min(0.85, offset_dist * 0.45 * focus_factor * stuff_factor + (pitcher_suppression * 0.08))
    sweet_spot_quality = max(0.15, 0.95 - impact_penalty + random.uniform(-0.08, 0.08))

    actual_hit_velocity = round(max_exit_velocity * sweet_spot_quality, 1)

    # 3. 번트(BUNT) 특수 처리
    if batting_strategy == IngameBattingStrategy.BUNT:
        actual_hit_velocity = round(random.uniform(45.0, 75.0), 1)
        launch_angle = round(random.uniform(-10.0, 15.0), 1)
        spray_angle = round(random.uniform(-40.0, 40.0), 1)
        return BattingPhysicsResult(
            hit_velocity=actual_hit_velocity,
            launch_angle=launch_angle,
            spray_angle=spray_angle,
            spin_rate=800,
            backspin_rpm=200.0,
            sidespin_rpm=50.0,
            contact_type=IngameContactType.BUNT
        )

    # 4. 발사 각도 (Launch Angle: -90.0° ~ +90.0°) 연산
    pitcher_noise_boost = (pitcher_suppression * 4.0) if pitcher is not None else 0.0
    base_launch_angle = 15.0 - (py * 12.0)
    angle_noise_sigma = max(8.0, 35.0 - (focus / 1000.0) * 22.0 + pitcher_noise_boost)
    launch_angle = round(random.gauss(base_launch_angle, angle_noise_sigma), 1)
    launch_angle = max(-90.0, min(90.0, launch_angle))

    # 5. 좌우 방위각 (Spray Angle: -90.0° ~ +90.0°) 연산
    base_spray_angle = px * 20.0
    spray_noise_sigma = max(10.0, 45.0 - (focus / 1000.0) * 28.0 + pitcher_noise_boost)
    spray_angle = round(random.gauss(base_spray_angle, spray_noise_sigma), 1)
    spray_angle = max(-90.0, min(90.0, spray_angle))

    # 6. 타구 회전수 (Spin Rate, Backspin, Sidespin RPM) 삼각함수 연속 수식 연산
    if launch_angle >= 0.0:
        angle_rad = math.radians(min(60.0, launch_angle))
        backspin_rpm = round(2100.0 * math.sin(angle_rad * 2.0) * (sweet_spot_quality ** 1.2) + random.uniform(-100, 100), 1)
    else:
        backspin_rpm = round(-600.0 + (launch_angle * 20.0) - random.uniform(50, 200), 1)

    sidespin_rpm = round((spray_angle * 18.0) + random.uniform(-150, 150), 1)
    total_spin_rate = int(math.sqrt(backspin_rpm ** 2 + sidespin_rpm ** 2))

    # 7. 타구 접촉 타입 (Contact Type) 판정
    if abs(spray_angle) > 45.0:
        contact_type = IngameContactType.FOUL
    else:
        contact_type = IngameContactType.CONTACT_IN_PLAY

    return BattingPhysicsResult(
        hit_velocity=actual_hit_velocity,
        launch_angle=launch_angle,
        spray_angle=spray_angle,
        spin_rate=total_spin_rate,
        backspin_rpm=backspin_rpm,
        sidespin_rpm=sidespin_rpm,
        contact_type=contact_type
    )
