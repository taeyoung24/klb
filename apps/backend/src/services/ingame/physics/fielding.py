import math
import random
from sqlmodel import SQLModel
from src.enums import IngameRole, IngameFieldingAction
from src.models import Player
from .trajectory import TrajectoryPhysicsResult, HitOutcome


# 수비 야수 9개 포지션별 수비 2D 기본 위치 (홈플레이트 기준 m: x, y)
FIELDER_BASE_POSITIONS: dict[IngameRole, tuple[float, float]] = {
    IngameRole.CATCHER: (0.0, 1.5),
    IngameRole.PITCHER: (0.0, 18.44),
    IngameRole.FIRST_BASE: (18.0, 20.0),
    IngameRole.SECOND_BASE: (10.0, 38.0),
    IngameRole.THIRD_BASE: (-18.0, 20.0),
    IngameRole.SHORT_STOP: (-10.0, 38.0),
    IngameRole.LEFT_FIELD: (-38.0, 75.0),
    IngameRole.CENTER_FIELD: (0.0, 90.0),
    IngameRole.RIGHT_FIELD: (38.0, 75.0),
}

# 목표 베이스별 2D 좌표 (m)
BASE_POSITIONS: dict[int, tuple[float, float]] = {
    0: (0.0, 0.0),      # 홈 (Home)
    1: (19.4, 19.4),    # 1루
    2: (0.0, 38.8),     # 2루
    3: (-19.4, 19.4),   # 3루
}


class FieldingPhysicsResult(SQLModel):
    """
    야수 수비 물리 연산 결과 DTO
    """
    fielder: Player                      # 타구를 담당한 수비 야수
    is_caught_in_air: bool               # 공중 뜬공 직접 포구 아웃 여부
    fielding_action: IngameFieldingAction # 포구 동작 결과 (CATCH, ERROR, DROP 등)
    fumble_delay_sec: float              # 포구 더듬음/낙구 실책으로 발생한 추가 수비 지연시간 (초)
    reach_time_sec: float                # 야수가 타구 지점에 도달하는 데 걸린 시간 (초)
    throw_time_sec: float                # 포구 후 목표 베이스 송구 도달 완료 총 시간 (초)


def calculate_fielding_physics(
    defense_lineup: list[Player],
    trajectory_physics: TrajectoryPhysicsResult,
    target_base: int = 1,
) -> FieldingPhysicsResult:
    """
    타구 궤적 결과(착지 좌표, 체류시간)와 수비 라인업을 입력받아
    가장 가깝고 적합한 수비 야수를 선정한 뒤,
    1) 타구 지점 도달시간 (reach_time_sec)
    2) 포구 성공/더듬기(Fumble)/실책(Error) 여부 및 지연시간
    3) 목표 베이스 송구 완류시간 (throw_time_sec)을 정밀 연산합니다.
    """
    landing_x = trajectory_physics.landing_x_m
    landing_y = trajectory_physics.landing_y_m
    hang_time = trajectory_physics.hang_time_sec

    # 1. 9명 수비 라인업 중 타구 지점과 가장 가까운 야수 선발
    best_fielder: Player | None = None
    min_reach_time = 999.0

    for fielder in defense_lineup:
        pos_xy = FIELDER_BASE_POSITIONS.get(fielder.position, (0.0, 30.0))
        dist_to_ball = math.sqrt((landing_x - pos_xy[0]) ** 2 + (landing_y - pos_xy[1]) ** 2)

        # flexibility(유연성/반응속도) 및 speed(주력) 스탯 반영 연속 수식
        react_time = 0.30 + (1.0 - fielder.flexibility / 1000.0) * 0.40
        run_speed_ms = 4.8 + (fielder.speed / 1000.0) * 2.6
        reach_time = round(react_time + (dist_to_ball / run_speed_ms), 2)

        if reach_time < min_reach_time:
            min_reach_time = reach_time
            best_fielder = fielder

    if best_fielder is None:
        best_fielder = defense_lineup[0]
        min_reach_time = 2.5

    # 2. 공중 포구 (Fly Out) vs 지면 포구 및 포구 더듬기/실책 연산
    is_caught_in_air = False
    fumble_delay_sec = 0.0
    fielding_action = IngameFieldingAction.CATCH

    # 장외 홈런이나 관중석 파울인 경우
    if trajectory_physics.outcome == HitOutcome.HOME_RUN:
        return FieldingPhysicsResult(
            fielder=best_fielder,
            is_caught_in_air=False,
            fielding_action=IngameFieldingAction.DROP,
            fumble_delay_sec=0.0,
            reach_time_sec=min_reach_time,
            throw_time_sec=99.0
        )

    # 타구 체류시간 이내에 야수가 여유있게 도착한 경우 (공중 포구 성공 후보: 0.15초 이상 여유 margin)
    if min_reach_time <= (hang_time - 0.15):
        # focus & flexibility 스탯으로 포구 에러 확률 계산
        error_prob = max(0.01, 0.15 - (best_fielder.focus / 1000.0) * 0.12 - (best_fielder.flexibility / 1000.0) * 0.02)
        if random.random() < error_prob:
            # 뜬공 낙구 실책 (Drop Error)
            fielding_action = IngameFieldingAction.ERROR
            fumble_delay_sec = round(random.uniform(1.8, 3.2), 2)  # 공 빠뜨려 주워오는데 2초+ 소요
            is_caught_in_air = False
        else:
            # 공중 포구 완벽 성공 (Fly Out)
            fielding_action = IngameFieldingAction.FLY_CATCH
            is_caught_in_air = True
            fumble_delay_sec = 0.0

    else:
        # 공이 지면에 먼저 바운드된 후 잡는 경우 (땅볼 / 바운드 안타 포구)
        is_caught_in_air = False
        # 바운드 공 포구 시 더듬기(Fumble) 확률 계산
        fumble_prob = max(0.03, 0.28 - (best_fielder.focus / 1000.0) * 0.22)
        if random.random() < fumble_prob:
            # 포구 더듬기 (Bobble/Fumble) 발생
            fielding_action = IngameFieldingAction.ERROR
            fumble_delay_sec = round(random.uniform(0.7, 1.6), 2)  # 더듬거리느라 1초 내외 추가 지연
        else:
            fielding_action = IngameFieldingAction.GROUND_CATCH
            fumble_delay_sec = 0.0

    # 3. 송구 도달 시간 (throw_time_sec) 연산
    # 포구 지점(landing_x, landing_y)에서 목표 베이스(target_base)까지의 거리 (m)
    target_pos = BASE_POSITIONS.get(target_base, (19.4, 19.4))
    throw_dist = math.sqrt((landing_x - target_pos[0]) ** 2 + (landing_y - target_pos[1]) ** 2)

    # 야수의 송구 구속 (power: 1~1000 -> 105 ~ 155 km/h)
    throw_speed_kmh = 105.0 + (best_fielder.power / 1000.0) * 50.0
    throw_speed_ms = throw_speed_kmh * (1000.0 / 3600.0)

    # 포구 후 송구 릴리즈 타임 (control 스탯이 높을수록 민첩한 릴리즈)
    release_time = max(0.35, 0.90 - (best_fielder.control / 1000.0) * 0.45)
    throw_flight_time = throw_dist / throw_speed_ms

    # 최종 총 수비 완료 시간 (야수 이동시간 + 더듬기 지연 + 릴리즈 타임 + 송구 비행시간)
    total_throw_time = round(min_reach_time + fumble_delay_sec + release_time + throw_flight_time, 2)

    return FieldingPhysicsResult(
        fielder=best_fielder,
        is_caught_in_air=is_caught_in_air,
        fielding_action=fielding_action,
        fumble_delay_sec=fumble_delay_sec,
        reach_time_sec=min_reach_time,
        throw_time_sec=total_throw_time
    )
