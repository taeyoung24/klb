# uv run -m scripts.run_single_match [--live] [--update-interval 0.1] [--speed 1.0]
import argparse
import sys
import time
import unicodedata
from typing import Any

# Windows 콘솔 인코딩 호환성을 위해 stdout 인코딩 재설정
reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
if callable(reconfigure_stdout):
    reconfigure_stdout(encoding="utf-8")

from src.models import (
    Match,
    Player,
    IngameNoticeEvent,
    IngameGameStateEvent,
    IngameBatterEnterEvent,
    IngamePitchStartEvent,
    IngamePitchEvent,
    IngameBatContactEvent,
    IngameFieldingActionEvent,
    IngameThrowActionEvent,
    IngameBaseRunStartEvent,
    IngameBaseRunResultEvent,
)
from src.services.ingame import run_match, get_scoreboard, select_starting_lineup
from src.utils.logger import logger


def get_player_display_name(player_id: int, player_map: dict[int, Player]) -> str:
    """선수 ID를 등번호와 선수 이름 포맷으로 변환합니다."""
    player = player_map.get(player_id)
    if player:
        return f"#{player.uniform_number} {player.name}"
    return f"선수 #{player_id}"



def get_display_width(text: str) -> int:
    """문자열의 실제 터미널 표시 너비를 계산한다 (전각/한글 2칸, 반각 1칸)."""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ("F", "W", "A"):
            width += 2
        else:
            width += 1
    return width


def pad_east_asian(text: str, target_width: int, align: str = "<") -> str:
    """동아시아 전각 문자를 고려하여 패딩된 고정 너비 문자열을 반환한다."""
    current_width = get_display_width(text)
    padding_needed = max(0, target_width - current_width)
    if align == "<":
        return text + " " * padding_needed
    elif align == ">":
        return " " * padding_needed + text
    elif align == "^":
        left_pad = padding_needed // 2
        right_pad = padding_needed - left_pad
        return " " * left_pad + text + " " * right_pad
    return text


def clear_console():
    """터미널 화면을 깨끗하게 비우고 커서를 맨 위로 이동한다."""
    sys.stdout.write("\033[H\033[J")
    sys.stdout.flush()


def format_bso(count: int, max_count: int) -> str:
    """볼/스트라이크/아웃 카운트를 기호(●/○)로 포맷팅한다."""
    filled = "●" * min(count, max_count)
    empty = "○" * (max_count - min(count, max_count))
    return f"{filled}{empty}"


def render_live_view(
    match: Match,
    sim_time: float,
    inning: int,
    is_top: bool,
    away_score: int,
    home_score: int,
    balls: int,
    strikes: int,
    outs: int,
    runners: dict[int, bool],
    recent_logs: list[str],
):
    """동아시아 문자 폭 계산을 적용하여 정밀하게 터미널 전광판을 렌더링한다."""
    clear_console()
    top_bottom_str = f"{inning:2d}회 {"초 (원정 공격)" if is_top else "말 (홈 공격)"}"
    
    r1 = "●" if runners.get(1) else "○"
    r2 = "●" if runners.get(2) else "○"
    r3 = "●" if runners.get(3) else "○"

    padded_progress = pad_east_asian(top_bottom_str, 20, "<")
    bso_str = f"B: {format_bso(balls, 3)}  |  S: {format_bso(strikes, 2)}  |  O: {format_bso(outs, 2)}"

    divider = "=" * 68
    sub_divider = "-" * 68

    print(divider)
    print(f" [KLB LIVE MATCH SIMULATION] - [Match #{match.id}]")
    print(divider)
    print(f" [스코어] 원정(Club {match.away_club_id:<2d})  {away_score:2d}  :  {home_score:2d}  홈(Club {match.home_club_id:<2d})")
    print(sub_divider)
    print(f" [진  행] {padded_progress} | 상대시간: {sim_time:6.1f}초")
    print(f" [카운트] {bso_str}")
    print(sub_divider)
    print(f" [루  상]        [2루: {r2}]")
    print(f"          [3루: {r3}]        [1루: {r1}]")
    print(divider)
    print(" [최근 이벤트 브로드캐스트]")
    for log in recent_logs[-5:]:
        padded_log = pad_east_asian(log, 64, "<")
        print(f"  > {padded_log}")
    print(divider)


def play_live_simulation(match: Match, update_interval: float = 0.1, speed: float = 1.0):
    """
    실제 게임 시간 흐름(sim_timestamp)에 맞추어 경기를 진행하며,
    update_interval 간격으로 CLI 화면을 부드럽게 갱신한다.
    """
    if not match.match_log or not match.match_log.logged_events:
        logger.error("재생할 인스트럭션 이벤트가 없습니다.")
        return

    events = match.match_log.logged_events
    if not events:
        return

    # 상대시간 기준 이벤트 순서 정렬
    sorted_events = sorted(events, key=lambda x: x.sim_timestamp)
    max_sim_time = sorted_events[-1].sim_timestamp
    total_events = len(sorted_events)

    # 선수 ID -> 선수 객체 매핑 맵 생성
    player_map: dict[int, Player] = {}
    for club_id in (match.away_club_id, match.home_club_id):
        if club_id is not None:
            pitcher, batters = select_starting_lineup(club_id)
            if pitcher and pitcher.id:
                player_map[pitcher.id] = pitcher
            for batter in batters:
                if batter and batter.id:
                    player_map[batter.id] = batter

    # 라이브 상태 변수 초기화
    inning = 1
    is_top = True
    away_score = 0
    home_score = 0
    balls = 0
    strikes = 0
    outs = 0
    runners = {1: False, 2: False, 3: False}
    recent_logs: list[str] = ["시뮬레이션 재생을 시작한다."]

    event_idx = 0
    start_real_time = time.time()

    while True:
        # 실제 경과 시간 계산 및 현재 게임 타임라인 결정
        real_elapsed = time.time() - start_real_time
        current_sim_time = real_elapsed * speed

        # 현재 게임 타임라인(current_sim_time) 이하의 미처리 이벤트 연속 반영
        while event_idx < total_events and sorted_events[event_idx].sim_timestamp <= current_sim_time:
            evt = sorted_events[event_idx]

            if isinstance(evt, IngameNoticeEvent):
                recent_logs.append(f"[공지] {evt.message}")

            elif isinstance(evt, IngameGameStateEvent):
                inning = evt.inning
                is_top = evt.is_top
                away_score = evt.away_score
                home_score = evt.home_score
                state_val = evt.state_type.value if hasattr(evt.state_type, "value") else evt.state_type
                recent_logs.append(f"[게임상태] {state_val} (이닝: {inning}회 {'초' if is_top else '말'})")
                balls, strikes, outs = 0, 0, 0
                runners = {1: False, 2: False, 3: False}

            elif isinstance(evt, IngameBatterEnterEvent):
                balls, strikes = 0, 0
                batter_str = get_player_display_name(evt.batter_id, player_map)
                pitcher_str = get_player_display_name(evt.pitcher_id, player_map)
                recent_logs.append(f"[타석] 타자 {batter_str} 등장 (투수 {pitcher_str})")

            elif isinstance(evt, IngamePitchStartEvent):
                p_type = evt.pitch_type.value if hasattr(evt.pitch_type, "value") else str(evt.pitch_type)
                pitcher_str = get_player_display_name(evt.pitcher_id, player_map)
                recent_logs.append(f"[투구준비] 투수 {pitcher_str} -> {p_type} 투구 준비")

            elif isinstance(evt, IngamePitchEvent):
                p_res = evt.result.value if hasattr(evt.result, "value") else str(evt.result)
                res_str = p_res.upper()
                if "STRIKE" in res_str:
                    strikes += 1
                elif "BALL" in res_str:
                    balls += 1
                elif "FOUL" in res_str:
                    if strikes < 2:
                        strikes += 1
                recent_logs.append(f"[투구결과] {p_res} (B:{balls}, S:{strikes})")

            elif isinstance(evt, IngameBatContactEvent):
                c_type = evt.contact_type.value if hasattr(evt.contact_type, "value") else str(evt.contact_type)
                recent_logs.append(f"[타격] {c_type} (속도: {evt.hit_velocity:.1f}km/h, 각도: {evt.launch_angle:.1f}°)")

            elif isinstance(evt, IngameFieldingActionEvent):
                act_type = evt.action_type.value if hasattr(evt.action_type, "value") else str(evt.action_type)
                fielder_str = get_player_display_name(evt.fielder_id, player_map)
                recent_logs.append(f"[수비] 야수 {fielder_str} - {act_type}")

            elif isinstance(evt, IngameThrowActionEvent):
                succ_str = "정송구" if evt.is_successful else "악송구/에러"
                thrower_str = get_player_display_name(evt.thrower_id, player_map)
                recent_logs.append(f"[송구] 야수 {thrower_str} -> {evt.target_base}루 ({succ_str})")

            elif isinstance(evt, IngameBaseRunStartEvent):
                runner_str = get_player_display_name(evt.runner_id, player_map)
                recent_logs.append(f"[주루출발] 주자 {runner_str} ({evt.start_base}루 -> {evt.target_base}루)")

            elif isinstance(evt, IngameBaseRunResultEvent):
                run_res = evt.result.value if hasattr(evt.result, "value") else str(evt.result)
                res_upper = run_res.upper()
                runner_str = get_player_display_name(evt.runner_id, player_map)

                if "OUT" in res_upper:
                    outs += 1
                    for b in range(1, 4):
                        if evt.target_base == b:
                            runners[b] = False
                elif "SAFE" in res_upper or "ADVANCE" in res_upper or "HOME" in res_upper:
                    if evt.target_base in [1, 2, 3]:
                        runners[evt.target_base] = True
                    elif evt.target_base == 4:
                        if is_top:
                            away_score += 1
                        else:
                            home_score += 1
                recent_logs.append(f"[주루결과] 주자 {runner_str} -> {evt.target_base}루 {run_res}")

            event_idx += 1

        # CLI 화면 업데이트 렌더링
        render_live_view(
            match=match,
            sim_time=min(current_sim_time, max_sim_time),
            inning=inning,
            is_top=is_top,
            away_score=away_score,
            home_score=home_score,
            balls=balls,
            strikes=strikes,
            outs=outs,
            runners=runners,
            recent_logs=recent_logs,
        )

        # 모든 이벤트가 처리되었고 최종 경기 시간까지 경과한 경우 종료
        if event_idx >= total_events and current_sim_time >= max_sim_time:
            break

        # 설정된 CLI 화면 갱신 주기(update_interval) 대기
        time.sleep(update_interval)

    print("\n라이브 중계 시뮬레이션 재생이 완료되었다!")


def main():
    parser = argparse.ArgumentParser(description="KLB 단일 경기 시뮬레이션 테스트 스크립트")
    parser.add_argument(
        "--live",
        action="store_true",
        help="시뮬레이션 이벤트를 시간 순서대로 터미널 전광판으로 실시간 중계 렌더링한다.",
    )
    parser.add_argument(
        "--update-interval",
        type=float,
        default=0.1,
        help="--live 모드 실행 시 CLI 전광판 화면 갱신 간격 (초 단위, 기본값: 0.1)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="--live 모드 실행 시 게임 시뮬레이션 재생 배속 (기본값: 1.0배속)",
    )
    args = parser.parse_args()

    logger.info("단일 경기 인스트럭션 시뮬레이션을 시작한다...")

    # 단일 테스트용 Match 객체 생성
    match = Match(
        id=999,
        sim_day=1,
        away_club_id=1,
        home_club_id=2,
        stadium_id=1,
        limit_extra_innings=True,
    )

    # 경기 시뮬레이션 실행
    run_match(match)

    logger.success("경기가 성공적으로 완료되었다!")
    logger.info(
        f"[경기 결과] 원정(Club {match.away_club_id}) {match.away_score} : {match.home_score} 홈(Club {match.home_club_id})"
    )
    logger.info(
        f"[투수 결과] 승리투수: {match.winning_pitcher_id}, 패전투수: {match.losing_pitcher_id}, 세이브투수: {match.save_pitcher_id}"
    )

    if not match.match_log:
        logger.error("Match log가 생성되지 않았다.")
        return

    # 전광판(Scoreboard) 정보 계산 및 출력
    scoreboard = get_scoreboard(match.match_log)
    logger.info("=================== Scoreboard Summary ===================")
    logger.info(f"진행 이닝: {scoreboard.current_inning}회 (is_top: {scoreboard.is_top})")
    logger.info(f"원정팀 이닝별 득점: {scoreboard.away_innings} -> 총 R:{scoreboard.away_r}, H:{scoreboard.away_h}, E:{scoreboard.away_e}, B:{scoreboard.away_b}")
    logger.info(f"홈  팀 이닝별 득점: {scoreboard.home_innings} -> 총 R:{scoreboard.home_r}, H:{scoreboard.home_h}, E:{scoreboard.home_e}, B:{scoreboard.home_b}")
    logger.info("==========================================================")

    # 이벤트 로그 정보 출력
    events = match.match_log.logged_events
    logger.info(f"총 생성된 인스트럭션 이벤트 개수: {len(events)}개")
    
    # 이벤트 타입별 카운트 수집 및 요약
    event_counts: dict[str, int] = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

    logger.info("================ Event Breakdown ================")
    for evt_type, count in event_counts.items():
        logger.info(f"  - {evt_type}: {count}개")
    logger.info("=================================================")

    # 샘플 이벤트 5개 출력
    logger.info("이벤트 샘플 (최초 5개):")
    for idx, event in enumerate(events[:5]):
        logger.info(f"  [{idx + 1}] {event.model_dump_json()}")

    # --live 옵션 지정 시 실시간 재생 렌더링 수행
    if args.live:
        logger.info(f"라이브 중계 렌더링을 시작한다... (화면 갱신: {args.update_interval}초, 재생 배속: {args.speed}배속)")
        time.sleep(1.5)
        play_live_simulation(match, update_interval=args.update_interval, speed=args.speed)


if __name__ == "__main__":
    main()
