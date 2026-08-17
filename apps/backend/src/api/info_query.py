import datetime
from typing import Optional, cast, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func, col
from sqlalchemy.orm import joinedload
from src.models import Player
from src.services.common import get_session

router = APIRouter(prefix="/info-query", tags=["InfoQuery"])


class RegionRead(BaseModel):
    id: int
    name: str
    name_ko: str

    class Config:
        from_attributes = True


class HighSchoolRead(BaseModel):
    id: int
    name: str
    name_ko: str

    class Config:
        from_attributes = True


class PlayerListItemRead(BaseModel):
    """선수 조회 목록 테이블 렌더링용 경량 모델 (스탯/성향 등 대용량 데이터 제외)"""
    id: int
    name: str
    club_id: Optional[int] = None
    uniform_number: str
    position: str
    potential: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    birthday: Optional[datetime.datetime] = None
    region_id: Optional[int] = None
    region: Optional[RegionRead] = None
    high_school_id: Optional[int] = None
    high_school: Optional[HighSchoolRead] = None

    class Config:
        from_attributes = True


class PlayerBattingRecord(BaseModel):
    """선수 시즌별/통산 타격 성적 레코드"""
    season: str         # "통산" 또는 "2026"
    avg: str            # 타율 (".000")
    games: int          # 경기수
    ab: int             # 타수
    hits: int           # 안타
    homeruns: int       # 홈런
    rbi: int            # 타점
    so: int             # 삼진
    obp: str            # 출루율 (".000")
    ops: str            # OPS (".000")


class PlayerPitchingRecord(BaseModel):
    """선수 시즌별/통산 투구 성적 레코드"""
    season: str         # "통산" 또는 "2026"
    era: str            # 평균자책점 ("0.00")
    games: int          # 경기수 (등판)
    innings: str        # 이닝 ("0.0")
    wins: int           # 승
    losses: int         # 패
    saves: int          # 세이브
    holds: int          # 홀드
    so: int             # 삼진 (K)
    hits: int           # 피안타
    homeruns: int       # 피홈런
    runs: int           # 실점
    bb: int             # 볼넷
    hbp: int            # 사구
    whip: str           # WHIP ("0.00")


# 이전 버전 호환성을 위한 별칭
PlayerSeasonRecord = PlayerBattingRecord


class PlayerDetailRead(BaseModel):
    """선수 1명 세부 정보 조회용 풀스펙 모델"""
    id: int
    name: str
    club_id: Optional[int] = None
    uniform_number: str
    position: str
    speed: Optional[int] = None
    control: Optional[int] = None
    power: Optional[int] = None
    flexibility: Optional[int] = None
    focus: Optional[int] = None
    stamina: Optional[int] = None
    potential: Optional[int] = None
    current_energy: Optional[int] = None
    max_energy: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    birthday: Optional[datetime.datetime] = None
    personality: Optional[list[int]] = None
    roster_status: Optional[str] = None
    region_id: Optional[int] = None
    region: Optional[RegionRead] = None
    high_school_id: Optional[int] = None
    high_school: Optional[HighSchoolRead] = None
    records: list[PlayerBattingRecord] = []
    batting_records: list[PlayerBattingRecord] = []
    pitching_records: list[PlayerPitchingRecord] = []

    class Config:
        from_attributes = True


class PaginatedPlayersResponse(BaseModel):
    items: list[PlayerListItemRead]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("/players", response_model=PaginatedPlayersResponse)
def get_info_query_players(
    club_id: Optional[int] = Query(None, description="구단 ID"),
    position: Optional[str] = Query(None, description="포지션 코드/이름"),
    name: Optional[str] = Query(None, description="선수명 검색어"),
    sort_by: str = Query("id", description="정렬 기준 필드 (id, name, age, uniform_number, height, weight, potential)"),
    order: str = Query("asc", description="정렬 방향 (asc, desc)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    session: Session = Depends(get_session),
):
    """
    정보조회 전용 선수 목록 검색/페이징/정렬 경량 엔드포인트
    """
    query = (
        select(Player)
        .options(
            joinedload(getattr(Player, "region")),
            joinedload(getattr(Player, "high_school")),
        )
    )

    if club_id is not None:
        query = query.where(Player.club_id == club_id)

    if position is not None and position != "all":
        query = query.where(Player.position == position)

    if name is not None and name.strip() != "":
        search_kw = f"%{name.strip()}%"
        query = query.where(col(Player.name).like(search_kw))

    # Total Count 쿼리
    count_query = select(func.count(col(Player.id)))
    if club_id is not None:
        count_query = count_query.where(Player.club_id == club_id)
    if position is not None and position != "all":
        count_query = count_query.where(Player.position == position)
    if name is not None and name.strip() != "":
        count_query = count_query.where(col(Player.name).like(f"%{name.strip()}%"))

    total_count = session.exec(count_query).one()
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    # 정렬 (Sorting) 로직
    is_desc = order.lower() == "desc"
    if sort_by == "name":
        sort_col = col(Player.name).desc() if is_desc else col(Player.name).asc()
    elif sort_by == "age" or sort_by == "birthday":
        # 나이순: 'age desc'(나이 많은 순) -> 생일이 빠른 순(birthday asc)
        # 'age asc'(나이 어린 순) -> 생일이 늦은 순(birthday desc)
        if sort_by == "age":
            sort_col = col(Player.birthday).asc() if is_desc else col(Player.birthday).desc()
        else:
            sort_col = col(Player.birthday).desc() if is_desc else col(Player.birthday).asc()
    elif sort_by == "uniform_number":
        sort_col = col(Player.uniform_number).desc() if is_desc else col(Player.uniform_number).asc()
    elif sort_by == "height":
        sort_col = col(Player.height).desc() if is_desc else col(Player.height).asc()
    elif sort_by == "weight":
        sort_col = col(Player.weight).desc() if is_desc else col(Player.weight).asc()
    elif sort_by == "potential":
        sort_col = col(Player.potential).desc() if is_desc else col(Player.potential).asc()
    else:
        sort_col = col(Player.id).desc() if is_desc else col(Player.id).asc()

    query = query.order_by(sort_col)

    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    items = session.exec(paginated_query).all()

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
    }


@router.get("/players/{player_id}", response_model=PlayerDetailRead)
def get_info_query_player_detail(
    player_id: int,
    session: Session = Depends(get_session),
):
    """
    선수 단일 세부 정보 (스탯, 성향, 실시간 체력, 생년월일, 통산/시즌별 타격 및 투구 지표) 정밀 조회 엔드포인트
    """
    from settings import CONFIG
    from src.models import Match

    query = (
        select(Player)
        .where(Player.id == player_id)
        .options(
            joinedload(getattr(Player, "region")),
            joinedload(getattr(Player, "high_school")),
        )
    )
    player = session.exec(query).first()
    if not player:
        raise HTTPException(status_code=404, detail="선수를 찾을 수 없습니다.")

    # 1. 해당 선수가 소속된 팀의 완료 경기 목록 조회
    player_matches = []
    if player.club_id:
        match_stmt = select(Match).where(
            Match.status == "COMPLETED",
            ((Match.home_club_id == player.club_id) | (Match.away_club_id == player.club_id))
        ).order_by(Match.sim_day.asc()) # type: ignore
        player_matches = list(session.exec(match_stmt).all())

    # 2. 경기별 match_log를 파싱하여 연도별 타격/투구 기록 집계
    def _get_val(ev: Any, attr: str, default: Any = None) -> Any:
        if isinstance(ev, dict):
            return ev.get(attr, default)
        return getattr(ev, attr, default)

    # year -> dict stats
    yearly_batting: dict[str, dict[str, int]] = {}
    yearly_pitching: dict[str, dict[str, int]] = {}

    for m in player_matches:
        events = None
        if m.match_log and hasattr(m.match_log, 'logged_events'):
            events = m.match_log.logged_events
        elif m.match_log_json and isinstance(m.match_log_json, dict):
            events = m.match_log_json.get('logged_events', [])

        if not events:
            continue

        year_num = CONFIG.base_datetime.year + (max(1, m.sim_day) - 1) // 365
        year_key = str(year_num)

        if year_key not in yearly_batting:
            yearly_batting[year_key] = {
                "games": 0, "ab": 0, "hits": 0, "homeruns": 0, "rbi": 0, "so": 0, "bb": 0, "tb": 0
            }

        if year_key not in yearly_pitching:
            yearly_pitching[year_key] = {
                "games": 0, "outs": 0, "wins": 0, "losses": 0, "saves": 0, "holds": 0,
                "so": 0, "hits": 0, "homeruns": 0, "runs": 0, "bb": 0, "hbp": 0
            }

        batter_participated = False
        pitcher_participated = False
        curr_batter_id = None
        curr_pitcher_id = None
        strikes = 0
        balls = 0

        for ev in events:
            etype = _get_val(ev, 'event_type')
            if etype == 'BATTER_ENTER':
                curr_batter_id = _get_val(ev, 'batter_id')
                curr_pitcher_id = _get_val(ev, 'pitcher_id')
                strikes = 0
                balls = 0
                if curr_batter_id == player_id:
                    batter_participated = True
                if curr_pitcher_id == player_id:
                    pitcher_participated = True

            elif etype == 'PITCH':
                res = _get_val(ev, 'result')
                if res == 'BALL':
                    balls += 1
                    if balls == 4:
                        if curr_batter_id == player_id:
                            yearly_batting[year_key]["bb"] += 1
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["bb"] += 1
                elif res in ('STRIKE', 'STRIKE_LOOKING', 'STRIKE_SWINGING'):
                    strikes += 1
                    if strikes == 3:
                        if curr_batter_id == player_id:
                            yearly_batting[year_key]["ab"] += 1
                            yearly_batting[year_key]["so"] += 1
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["so"] += 1
                            yearly_pitching[year_key]["outs"] += 1
                elif res == 'FOUL':
                    if strikes < 2:
                        strikes += 1
                elif res in ('HIT_BY_PITCH', 'DEAD_BALL', 'HBP'):
                    if curr_pitcher_id == player_id:
                        yearly_pitching[year_key]["hbp"] += 1

            elif etype == 'NOTICE':
                msg = _get_val(ev, 'message', '')
                if '홈런' in str(msg):
                    if curr_batter_id == player_id:
                        yearly_batting[year_key]["ab"] += 1
                        yearly_batting[year_key]["hits"] += 1
                        yearly_batting[year_key]["homeruns"] += 1
                        yearly_batting[year_key]["tb"] += 4
                        yearly_batting[year_key]["rbi"] += 1
                    if curr_pitcher_id == player_id:
                        yearly_pitching[year_key]["hits"] += 1
                        yearly_pitching[year_key]["homeruns"] += 1
                        yearly_pitching[year_key]["runs"] += 1

            elif etype == 'BASE_RUN_RESULT':
                target_base = _get_val(ev, 'target_base')
                res = _get_val(ev, 'result')
                reason = _get_val(ev, 'reason')
                runner_id = _get_val(ev, 'runner_id')

                # 타자 주자의 인플레이 타구 결과 집계
                if runner_id is None or runner_id == curr_batter_id:
                    if res == 'OUT':
                        if curr_batter_id == player_id:
                            yearly_batting[year_key]["ab"] += 1
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["outs"] += 1
                    elif res == 'SAFE' and target_base and 1 <= target_base <= 3 and reason != 'WALK':
                        if curr_batter_id == player_id:
                            yearly_batting[year_key]["ab"] += 1
                            yearly_batting[year_key]["hits"] += 1
                            yearly_batting[year_key]["tb"] += target_base
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["hits"] += 1
                else:
                    # 루상 주자의 진루/아웃 처리 (득점 또는 주루사)
                    if res == 'OUT':
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["outs"] += 1
                    elif res == 'SAFE' and target_base == 4:
                        if curr_pitcher_id == player_id:
                            yearly_pitching[year_key]["runs"] += 1

        if batter_participated:
            yearly_batting[year_key]["games"] += 1

        if pitcher_participated:
            yearly_pitching[year_key]["games"] += 1
            if getattr(m, 'winning_pitcher_id', None) == player_id:
                yearly_pitching[year_key]["wins"] += 1
            if getattr(m, 'losing_pitcher_id', None) == player_id:
                yearly_pitching[year_key]["losses"] += 1
            if getattr(m, 'save_pitcher_id', None) == player_id:
                yearly_pitching[year_key]["saves"] += 1

    # 3. 통산(Career) 및 시즌별 PlayerBattingRecord 생성
    def _calc_batting_row(season_label: str, st: dict[str, int]) -> PlayerBattingRecord:
        ab = st["ab"]
        hits = st["hits"]
        bb = st["bb"]
        tb = st["tb"]
        
        avg_val = (hits / ab) if ab > 0 else 0.000
        obp_val = ((hits + bb) / (ab + bb)) if (ab + bb) > 0 else 0.000
        slg_val = (tb / ab) if ab > 0 else 0.000
        ops_val = obp_val + slg_val

        return PlayerBattingRecord(
            season=season_label,
            avg=f"{avg_val:.3f}".replace("0.", "."),
            games=st["games"],
            ab=ab,
            hits=hits,
            homeruns=st["homeruns"],
            rbi=st["rbi"],
            so=st["so"],
            obp=f"{obp_val:.3f}".replace("0.", "."),
            ops=f"{ops_val:.3f}".replace("0.", "."),
        )

    # 4. 통산(Career) 및 시즌별 PlayerPitchingRecord 생성
    def _calc_pitching_row(season_label: str, st: dict[str, int]) -> PlayerPitchingRecord:
        outs = st["outs"]
        runs = st["runs"]
        hits = st["hits"]
        bb = st["bb"]
        
        inn_full = outs // 3
        inn_rem = outs % 3
        innings_str = f"{inn_full}.{inn_rem}"
        inn_float = inn_full + (inn_rem / 3.0)

        era_val = (runs * 9.0 / inn_float) if inn_float > 0 else 0.00
        whip_val = ((hits + bb) / inn_float) if inn_float > 0 else 0.00

        return PlayerPitchingRecord(
            season=season_label,
            era=f"{era_val:.2f}",
            games=st["games"],
            innings=innings_str,
            wins=st["wins"],
            losses=st["losses"],
            saves=st["saves"],
            holds=st["holds"],
            so=st["so"],
            hits=hits,
            homeruns=st["homeruns"],
            runs=runs,
            bb=bb,
            hbp=st["hbp"],
            whip=f"{whip_val:.2f}",
        )

    # 타격 통산 & 연도별
    batting_records: list[PlayerBattingRecord] = []
    total_batting = {"games": 0, "ab": 0, "hits": 0, "homeruns": 0, "rbi": 0, "so": 0, "bb": 0, "tb": 0}
    for st in yearly_batting.values():
        for k in total_batting:
            total_batting[k] += st[k]

    batting_records.append(_calc_batting_row("통산", total_batting))
    for year_k in sorted(yearly_batting.keys(), reverse=True):
        batting_records.append(_calc_batting_row(f"{year_k}", yearly_batting[year_k]))

    # 투구 통산 & 연도별
    pitching_records: list[PlayerPitchingRecord] = []
    total_pitching = {
        "games": 0, "outs": 0, "wins": 0, "losses": 0, "saves": 0, "holds": 0,
        "so": 0, "hits": 0, "homeruns": 0, "runs": 0, "bb": 0, "hbp": 0
    }
    for st in yearly_pitching.values():
        for k in total_pitching:
            total_pitching[k] += st[k]

    pitching_records.append(_calc_pitching_row("통산", total_pitching))
    for year_k in sorted(yearly_pitching.keys(), reverse=True):
        pitching_records.append(_calc_pitching_row(f"{year_k}", yearly_pitching[year_k]))

    # Pydantic 응답 객체 생성
    resp_dict = player.model_dump()
    resp_dict["region"] = player.region
    resp_dict["high_school"] = player.high_school
    resp_dict["records"] = batting_records
    resp_dict["batting_records"] = batting_records
    resp_dict["pitching_records"] = pitching_records

    return PlayerDetailRead(**resp_dict)



