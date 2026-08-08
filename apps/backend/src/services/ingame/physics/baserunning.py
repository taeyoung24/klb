import math
from sqlmodel import SQLModel
from src.models import Player
from .fielding import FieldingPhysicsResult


class BaseRunningPhysicsResult(SQLModel):
    """
    주자 주루 물리 연산 결과 DTO
    """
    runner: Player                # 주루를 수행한 주자 / 타자
    start_base: int               # 출발 베이스 (0: 홈/타석, 1: 1루, 2: 2루, 3: 3루)
    target_base: int              # 목표 베이스 (1: 1루, 2: 2루, 3: 3루, 4: 홈)
    runner_reach_time_sec: float  # 주자가 목표 베이스에 도달하는 데 걸린 시간 (초)
    is_safe: bool                 # 목표 베이스 세이프 판정 여부
    safe_margin_sec: float        # 세이프/아웃 여유 시간 (초, t_throw - t_runner. 양수: 세이프, 음수: 아웃)


def calculate_baserunning_physics(
    runner: Player,
    start_base: int,
    target_base: int,
    fielding_physics: FieldingPhysicsResult | None = None,
) -> BaseRunningPhysicsResult:
    """
    주자의 스탯(speed, focus, flexibility)과 수비 완류 결과(fielding_physics)를 입력받아
    1) 목표 베이스 주루 도달 시간 (runner_reach_time_sec)
    2) 수비 송구 시간과의 비교를 통한 최종 세이프 / 아웃 및 마진 시간(sec)을 연산합니다.
    """
    speed = runner.speed
    focus = runner.focus
    flexibility = runner.flexibility

    # 1. 이동 목표 거리 (m, 각 베이스 간 27.4m)
    num_bases = max(1, target_base - start_base)
    distance_m = num_bases * 27.4

    # 2. 타구 판단 순발력 스타트 지연 (focus 스탯 반영)
    start_delay_sec = max(0.10, 0.45 - (focus / 1000.0) * 0.30)

    # 3. 2베이스 이상 연속 주루 시 턴오버 코너링 지연 (flexibility 스탯 반영)
    if num_bases > 1:
        cornering_delay_sec = (num_bases - 1) * max(0.18, 0.48 - (flexibility / 1000.0) * 0.28)
    else:
        cornering_delay_sec = 0.0

    # 4. 최고 주행 속도 연산 (speed: 1~1000 -> 6.8 m/s ~ 10.0 m/s)
    max_run_speed_ms = 6.8 + (speed / 1000.0) * 3.2

    # 5. 가속 가산 구간 포함 순수 주행 시간
    run_time_sec = (distance_m / max_run_speed_ms) + 0.25

    # 6. 최종 주자 목표 베이스 도달 총 시간 (초)
    runner_reach_time_sec = round(start_delay_sec + run_time_sec + cornering_delay_sec, 2)

    # 7. 세이프 / 아웃 판정 및 마진 계산
    if fielding_physics is not None:
        # 공중 뜬공 포구로 즉시 아웃된 경우
        if fielding_physics.is_caught_in_air:
            is_safe = False
            safe_margin_sec = -9.9
        else:
            throw_time = fielding_physics.throw_time_sec
            safe_margin_sec = round(throw_time - runner_reach_time_sec, 2)
            is_safe = safe_margin_sec > 0.0
    else:
        is_safe = True
        safe_margin_sec = 0.0

    return BaseRunningPhysicsResult(
        runner=runner,
        start_base=start_base,
        target_base=target_base,
        runner_reach_time_sec=runner_reach_time_sec,
        is_safe=is_safe,
        safe_margin_sec=safe_margin_sec
    )




