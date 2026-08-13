from typing import Optional, cast, Any
from fastapi import APIRouter, Depends, Query
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


class PlayerDetailRead(BaseModel):
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
    height: Optional[float] = None
    weight: Optional[float] = None
    region_id: Optional[int] = None
    region: Optional[RegionRead] = None
    high_school_id: Optional[int] = None
    high_school: Optional[HighSchoolRead] = None

    class Config:
        from_attributes = True


class PaginatedPlayersResponse(BaseModel):
    items: list[PlayerDetailRead]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("/players", response_model=PaginatedPlayersResponse)
def get_info_query_players(
    club_id: Optional[int] = Query(None, description="구단 ID"),
    position: Optional[str] = Query(None, description="포지션 코드/이름"),
    name: Optional[str] = Query(None, description="선수명 검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    session: Session = Depends(get_session),
):
    """
    정보조회 전용 선수 기본 정보 및 연관 데이터(지역, 고교) DB 쿼리/검색/페이징 엔드포인트
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
