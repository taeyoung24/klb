from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List

from src.services.worldview import (
    create_session,
    get_session,
    ask_question_async,
    WorldviewSession,
    TaskStatus,
)

router = APIRouter(prefix="/worldview", tags=["worldview"])


class AskRequest(BaseModel):
    question: str = Field(description="세계관/위키 관련 질문", examples=["KLB 4대 리그에 대해 설명해줘"])
    force_update: bool = Field(default=False, description="FAISS 인덱스를 새로 강제 재구축할지 여부")
    max_hops: int = Field(default=5, ge=1, le=10, description="멀티홉 검색 최대 수행 횟수 제한 (기본값: 5)")


class ChatMessageResponse(BaseModel):
    role: str
    content: str


class SessionResponse(BaseModel):
    session_id: str
    status: TaskStatus
    status_message: str
    last_question: Optional[str] = None
    last_answer: Optional[str] = None
    compressed_summary: Optional[str] = None
    error_message: Optional[str] = None
    history: List[ChatMessageResponse] = []


@router.post("/session", response_model=SessionResponse, summary="새로운 세계관 챗 세션 생성")
def create_new_worldview_session():
    """
    새로운 세계관 챗 세션을 생성하고 초기 상태를 반환합니다.
    """
    session = create_session()
    return session


@router.get("/session/{session_id}", response_model=SessionResponse, summary="챗 세션 상태 및 이력 조회 (폴링용)")
def get_worldview_session_status(session_id: str):
    """
    세션 ID로 현재 비동기 처리 상태(status, status_message) 및 대화 이력을 조회합니다.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")
    return session


@router.post("/session/{session_id}/ask", response_model=SessionResponse, summary="세션에 비동기 질문 요청")
async def ask_worldview_question(session_id: str, request: AskRequest, background_tasks: BackgroundTasks):
    """
    세션에 질문을 제출합니다. 백그라운드 태스크로 처리가 시작되며,
    클라이언트는 GET /session/{session_id}를 폴링하여 완료 여부를 확인합니다.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"세션을 찾을 수 없습니다: {session_id}")

    # 백그라운드에서 비동기 RAG 체인 실행
    background_tasks.add_task(
        ask_question_async,
        session_id=session_id,
        question=request.question,
        force_update=request.force_update,
        max_hops=request.max_hops,
    )

    return session


@router.post("/ask", response_model=SessionResponse, summary="단발성 1회 질문 처리 (세션 자동 생성)")
async def ask_single_question(request: AskRequest):
    """
    임시 세션을 생성하여 질문을 처리하고 결과를 반환하는 헬퍼 동기/비동기 엔드포인트입니다.
    """
    session = create_session()
    await ask_question_async(
        session_id=session.session_id,
        question=request.question,
        force_update=request.force_update,
        max_hops=request.max_hops,
    )
    return session
