import random
import math
from sqlmodel import SQLModel
from src.enums import IngameContactType, IngameBattingStrategy
from src.models import Player
from .pitching import PitchPhysicsResult


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
    pitch_physics: PitchPhysicsResult,
) -> float:
    """
    타자의 focus, flexibility 스탯과 투구 3D 탄착점 오프셋 거리(px, py)를 기반으로
    배트 스윙 시 공을 맞출 컨택트(Contact) 성공 확률을 연산합니다.
    
    - 존 중심(d=0) 근처 공: ~90% 쉽게 맞춤
    - 존 바깥(d>1.2) 볼존 공: 타자 focus/flexibility 커버리지 스탯에 따라 헛스윙률 자연 연출
    """
    px = pitch_physics.actual_location_x
    py = pitch_physics.actual_location_y
    offset_dist = math.sqrt(px ** 2 + py ** 2)

    # 타자의 focus, flexibility 스탯 커버리지 능력이 높을수록 어려운 공의 실효 오프셋 감축
    coverage_ability = (batter.focus * 0.6 + batter.flexibility * 0.4) / 1000.0
    effective_offset = offset_dist * (1.35 - coverage_ability * 0.70)

    # 중심 탄착 오프셋 기반 컨택트 확률 (0.15 ~ 0.95)
    p_contact = max(0.15, min(0.95, 0.92 - (effective_offset * 0.45)))
    return p_contact


def calculate_batting_physics(
    batter: Player,
    pitch_physics: PitchPhysicsResult,
    batting_strategy: IngameBattingStrategy = IngameBattingStrategy.SWING_FULL,
) -> BattingPhysicsResult:
    """
    타자의 스탯(power, focus)과 투구 물리(구속, 탄착점, 투구 회전수)를 입력받아
    배트 임팩트 순간의 타구 속도(km/h), 발사 각도(도), 방위각(도) 및 백스핀/사이드스핀(RPM)을 연산합니다.
    """
    power = batter.power
    focus = batter.focus

    # 1. 최고 타구 발사 속도 (Exit Velocity) 기본치 연산
    pitch_velocity_boost = pitch_physics.pitch_velocity * 0.12
    max_exit_velocity = 95.0 + (power / 1000.0) * 60.0 + pitch_velocity_boost

    # 2. 스윗스폿(Sweet Spot) 임팩트 품질 연산
    px = pitch_physics.actual_location_x
    py = pitch_physics.actual_location_y
    offset_dist = math.sqrt(px ** 2 + py ** 2)

    # focus(집중력)가 낮을수록 탄착점 중심 오프셋에 따른 정타 감쇄율 대폭 증가
    focus_factor = max(0.15, 1.25 - (focus / 1000.0) * 0.85)
    impact_penalty = min(0.80, offset_dist * 0.48 * focus_factor)
    sweet_spot_quality = max(0.18, 0.95 - impact_penalty + random.uniform(-0.10, 0.10))

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
    base_launch_angle = 15.0 - (py * 12.0)
    angle_noise_sigma = max(8.0, 35.0 - (focus / 1000.0) * 22.0)
    launch_angle = round(random.gauss(base_launch_angle, angle_noise_sigma), 1)
    launch_angle = max(-90.0, min(90.0, launch_angle))

    # 5. 좌우 방위각 (Spray Angle: -90.0° ~ +90.0°) 연산
    base_spray_angle = px * 20.0
    spray_noise_sigma = max(10.0, 45.0 - (focus / 1000.0) * 28.0)
    spray_angle = round(random.gauss(base_spray_angle, spray_noise_sigma), 1)
    spray_angle = max(-90.0, min(90.0, spray_angle))

    # 6. 타구 회전수 (Spin Rate, Backspin, Sidespin RPM) 삼각함수 연속 수식 연산
    # 발사각(launch_angle) 및 스윗스폿 임팩트 품질(sweet_spot_quality)에 따른 삼각함수 곡선 백스핀 연산
    if launch_angle >= 0.0:
        angle_rad = math.radians(min(60.0, launch_angle))
        # sin(2 * angle_rad) 곡선에 의해 발사각 20°~30° 부근에서 매끄러운 3D 백스핀 양력 최고치 형성
        backspin_rpm = round(2100.0 * math.sin(angle_rad * 2.0) * (sweet_spot_quality ** 1.2) + random.uniform(-100, 100), 1)
    else:
        # 땅볼 (< 0°): 톱스핀 (음수 RPM)
        backspin_rpm = round(-600.0 + (launch_angle * 20.0) - random.uniform(50, 200), 1)

    # 사이드스핀: 방위각 및 밀어치기/당겨치기 스핀 오차
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
