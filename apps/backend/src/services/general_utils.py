import math


def aging_curve(x: float) -> float:
    """
    나이(x)에 따른 선수 스탯 연간 표준 가중계수 f(x)를 반환합니다.

    f(x) = 85 * exp(-((x-22)^2)/37) - 30 / (1 + exp(-0.20*(x-30)))

    - 전 구간 무한 미분가능(C∞) 초월함수
    - 양음 전환점: x ≈ 30 (f(30) ≈ 0)
    - 최대값: +80 (x ≈ 22)
    - 점근 최솟값: -30 (x → ∞)

    Args:
        x: 선수의 만 나이 (0 이상 실수)

    Returns:
        해당 나이의 스탯 변화 기대 가중계수 (양수: 성장, 음수: 쇠퇴)
    """
    gaussian_term = 85.0 * math.exp(-((x - 22.0) ** 2) / 37.0)
    logistic_term = 30.0 / (1.0 + math.exp(-0.20 * (x - 30.0)))
    return gaussian_term - logistic_term


def calculate_stat_delta(age: float, potential: int) -> int:
    """
    나이와 잠재력(potential)을 기반으로 단일 스탯의 연간 스텝업/다운 변화량을 계산합니다.
    """
    fx = aging_curve(age)
    pot_factor = 1.0 + (potential / 1000.0)

    val_a = fx
    val_b = fx * pot_factor
    min_val = min(val_a, val_b)
    max_val = max(val_a, val_b)

    import random
    delta = int(round(random.uniform(min_val, max_val)))
    return delta


def apply_player_aging_progression(player, current_year: int) -> dict[str, int]:
    """
    오프시즌 연도 전환 시점에 1명의 선수 6대 스탯에 영구 스텝업/다운을 적용합니다.
    (스탯 범위: 1 ~ 1000 클램핑)
    """
    age = float(current_year - player.birthday.year)
    potential = getattr(player, "potential", 500)

    stat_keys = ["speed", "control", "power", "flexibility", "focus", "stamina"]
    changes = {}

    for key in stat_keys:
        old_val = getattr(player, key)
        delta = calculate_stat_delta(age, potential)
        new_val = max(1, min(1000, old_val + delta))
        setattr(player, key, new_val)
        changes[key] = delta

    return changes

