from src.models import Player

# --- 일일 체력 회복 밸런스 상수 파라미터 ---
BASE_RECOVERY_REST = 1800       # 경기 미출전/휴식 선수 1일 기본 회복량
BASE_RECOVERY_BATTER = 450      # 당일 경기 출전 야수 1일 기본 회복량
BASE_RECOVERY_PITCHER = 300     # 당일 경기 등판 투수 1일 기본 회복량

AWAY_RECOVERY_RATIO = 0.70      # 원정 경기 체류 시 회복 배율 (기본 70%)


def drain_pitcher_energy(pitcher: Player, is_power_pitch: bool = False) -> int:
    """
    투수의 1구 투구 시 체력(current_energy)을 소진합니다.
    - 기본 소진량: 90 (전력투구 시 115)
    - stamina(지구력 계수 1~1000)가 높을수록 소진 억제 (0.5배 ~ 1.5배)
    """
    base_cost = 115.0 if is_power_pitch else 90.0
    stamina_factor = 1.5 - (pitcher.stamina / 1000.0)
    drain_amount = int(base_cost * max(0.5, min(1.5, stamina_factor)))
    
    pitcher.current_energy = max(0, pitcher.current_energy - drain_amount)
    return drain_amount


def drain_batter_energy(batter: Player, pitch_count_in_pa: int) -> int:
    """
    타자의 1타석(PA) 완료 시 체력(current_energy)을 소진합니다.
    - 기본 소진량: 40 + 투구수당 8
    - stamina(지구력 계수 1~1000) 반영
    """
    base_cost = 40.0 + (pitch_count_in_pa * 8.0)
    stamina_factor = 1.3 - (batter.stamina / 1000.0) * 0.6
    drain_amount = int(base_cost * max(0.5, min(1.3, stamina_factor)))
    
    batter.current_energy = max(0, batter.current_energy - drain_amount)
    return drain_amount


def drain_runner_energy(runner: Player, bases_advanced: int) -> int:
    """
    주자의 베이스 진루/도루/주루 시 체력을 소진합니다.
    """
    base_cost = 40.0 * max(1, bases_advanced)
    stamina_factor = 1.3 - (runner.stamina / 1000.0) * 0.5
    drain_amount = int(base_cost * max(0.5, min(1.3, stamina_factor)))
    
    runner.current_energy = max(0, runner.current_energy - drain_amount)
    return drain_amount


def drain_fielder_energy(fielder: Player, is_difficult_play: bool = False) -> int:
    """
    수비수의 포구/송구 등 수비 행위 시 체력을 소진합니다.
    """
    base_cost = 50.0 if is_difficult_play else 20.0
    stamina_factor = 1.2 - (fielder.stamina / 1000.0) * 0.4
    drain_amount = int(base_cost * max(0.5, min(1.2, stamina_factor)))
    
    fielder.current_energy = max(0, fielder.current_energy - drain_amount)
    return drain_amount


def recover_player_energy_daily(
    player: Player,
    participated: bool = False,
    is_pitcher: bool = False,
    is_away: bool = False,
) -> int:
    """
    매일 자정/일일 마감 시 선수의 체력을 자연 회복합니다.
    - 미출전/휴식 선수: +1800 회복 (4~5일 휴식 시 완충)
    - 출전 타자: +450 회복
    - 등판 투수: +300 회복
    - 원정(Away) 체류 시: 회복량의 70%(AWAY_RECOVERY_RATIO)만 적용
    """
    if not participated:
        base_recovery = BASE_RECOVERY_REST
    elif is_pitcher:
        base_recovery = BASE_RECOVERY_PITCHER
    else:
        base_recovery = BASE_RECOVERY_BATTER

    ratio = AWAY_RECOVERY_RATIO if is_away else 1.0
    recovery_amount = int(base_recovery * ratio)

    prev_energy = player.current_energy
    max_cap = player.max_energy or 10000
    player.current_energy = min(max_cap, player.current_energy + recovery_amount)
    return player.current_energy - prev_energy
