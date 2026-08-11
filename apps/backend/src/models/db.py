from datetime import datetime
from typing import Any, Optional
from sqlmodel import SQLModel, Field, JSON, Relationship
from sqlalchemy import Column
from sqlalchemy.types import TypeDecorator

from src.enums import (
    MatchStatus,
    MatchStage,
    IngameRole,
    PlayerTransactionType,
)
from .base import Stadium, Club, Player
from .ingame import IngameInstructionLog


class IngameInstructionLogType(TypeDecorator):
    """Pydantic IngameInstructionLog 모델을 데이터베이스 JSON 컬럼과 자동으로 매핑하는 커스텀 타입"""
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        model_cls = globals().get("IngameInstructionLog") or IngameInstructionLog
        if model_cls:
            return model_cls.model_validate(value)
        return value


class DailyClubStanding(SQLModel, table=True):
    """
    매일의 정규 시즌 및 포스트시즌(정예리그) 리그 순위 스냅샷 장부 (통합 단일 테이블).
    """
    id: int         = Field(default=None, primary_key=True)
    sim_day: int    = Field(index=True)
    league_id: int  = Field(foreign_key="league.id")
    club_id: int    = Field(foreign_key="club.id")
    is_postseason: bool = Field(default=False, index=True)
    
    rank: int
    win_rate: float
    games_back: int
    wins: int
    draws: int
    losses: int
    games_played: int
    streak: int
    batting_average: float
    era: float


class Match(SQLModel, table=True):
    """
    매치 일정과 결과를 모두 포괄하는 통합 매치 장부.
    시즌 시작 시 SCHEDULED로 생성되고, 시뮬레이션 종료 시 COMPLETED로 전환
    """
    id: int              = Field(default=None, primary_key=True)
    away_club_id: int    = Field(foreign_key="club.id")
    home_club_id: int    = Field(foreign_key="club.id")
    stadium_id: Optional[int] = Field(default=None, foreign_key="stadium.id")
    sim_day: int         = Field(index=True)
    status: MatchStatus  = Field(default=MatchStatus.SCHEDULED, index=True)
    stage: MatchStage    = Field(default=MatchStage.REGULAR, index=True)
    limit_extra_innings: bool = Field()
    
    # 경기 예정이거나 취소 상태일 때는 Null(None) 허용
    home_score: Optional[int] = Field(default=None)
    away_score: Optional[int] = Field(default=None)
    
    # 끝난 매치에 대한 raw 레벨 가공 JSON 인스트럭션 로그 (Data-Driven Playback)
    match_log_json: Optional[dict[str, Any]] = Field(default=None, sa_type=JSON)
    
    # 구조화된 인게임 로그 객체 컬럼 (Pydantic 모델 타입으로 자동 직렬화/역직렬화)
    match_log: Optional[IngameInstructionLog] = Field(
        default=None,
        sa_column=Column(IngameInstructionLogType)
    )

    # 선발 투수 예고/기록 ID
    away_starting_pitcher_id: Optional[int] = Field(default=None, foreign_key="player.id")
    home_starting_pitcher_id: Optional[int] = Field(default=None, foreign_key="player.id")

    # 승/패/세 투수 ID 기록
    winning_pitcher_id: Optional[int] = Field(default=None, foreign_key="player.id")
    losing_pitcher_id: Optional[int] = Field(default=None, foreign_key="player.id")
    save_pitcher_id: Optional[int] = Field(default=None, foreign_key="player.id")

    stadium: Optional[Stadium] = Relationship()


class MatchLineup(SQLModel, table=True):
    """
    경기별 팀 선발/출전 라인업 장부 테이블
    """
    id: int = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="match.id", index=True)
    club_id: int = Field(foreign_key="club.id", index=True)
    player_id: int = Field(foreign_key="player.id")
    
    position: IngameRole
    batting_order: Optional[int] = Field(default=None)
    is_starter: bool = Field(default=True)


class MatchPlaceholder(SQLModel, table=True):
    """
    토너먼트(녹아웃) 대진 스키마를 표현하는 플레이스홀더 테이블.
    """
    id: int = Field(default=None, primary_key=True)
    round: str  # "ROUND_OF_8", "SEMI_FINAL", "FINAL"
    sim_day: int  # 경기가 치러질 예정 시뮬레이션 일자
    limit_extra_innings: bool = Field()
    
    # 8강처럼 최초 구단이 고정된 경우에만 값을 가짐
    home_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    away_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    
    # 대진 트리 상에서 이 노드의 홈/어웨이 팀의 승자가 결정될 이전 플레이스홀더 매치
    home_parent_id: Optional[int] = Field(default=None, foreign_key="matchplaceholder.id")
    away_parent_id: Optional[int] = Field(default=None, foreign_key="matchplaceholder.id")

    # 이 플레이스홀더를 통해 실제로 생성된 경기 ID (추적 용도)
    actual_match_id: Optional[int] = Field(default=None, foreign_key="match.id")


class NewsAgency(SQLModel, table=True):
    """
    뉴스 언론사/보도매체 정보를 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(index=True)
    description: str = Field(default="")
    lore: str = Field(default="")

    articles: list["Article"] = Relationship(back_populates="news_agency")


class Article(SQLModel, table=True):
    """
    리그 주요 뉴스, 경기 리뷰, 인터뷰, 하이라이트 소식을 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str
    category: str = Field(default="리뷰", index=True)
    sim_day: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    likes: int = Field(default=0)
    
    match_id: Optional[int] = Field(default=None, foreign_key="match.id")
    club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    image_url: Optional[str] = Field(default=None)

    # 뉴스사 외래키 및 관계
    news_agency_id: Optional[int] = Field(default=None, foreign_key="newsagency.id")
    news_agency: Optional[NewsAgency] = Relationship(back_populates="articles")

    # 기사 댓글 목록 관계
    comments: list["ArticleComment"] = Relationship(
        back_populates="article",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ArticleComment(SQLModel, table=True):
    """
    기사에 작성된 댓글 정보를 저장하는 모델
    """
    id: int = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id", index=True)
    author_name: str = Field(default="익명팬")
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    likes: int = Field(default=0)
    dislikes: int = Field(default=0)

    article: Article = Relationship(back_populates="comments")


class PlayerTransactionHistory(SQLModel, table=True):
    """
    사무국 선수 계약, 지명, 이적 행정 일지 장부
    """
    id: int = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True)
    sim_day: int = Field(index=True)

    transaction_type: PlayerTransactionType = Field(index=True)

    from_club_id: Optional[int] = Field(default=None, foreign_key="club.id")
    to_club_id: Optional[int] = Field(default=None, foreign_key="club.id")

    draft_round: Optional[int] = Field(default=None)
    draft_overall_pick: Optional[int] = Field(default=None)

    details: Optional[str] = Field(default=None)
