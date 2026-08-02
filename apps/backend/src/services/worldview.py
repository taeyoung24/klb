import asyncio
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List, cast
from pydantic import SecretStr

from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough

from settings import OPENROUTER_API_KEY
from src.utils.logger import logger

API_KEY = SecretStr(OPENROUTER_API_KEY)
BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {
    "HTTP-Referer": "https://klb.dispace/",
    "X-Title": "KLB",
}
FALLBACK_MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-31b-it",
]
INDEX_PATH = "./outputs/faiss_index_store"

# 프로젝트 루트의 docs/wiki 경로 정밀 계산 (worldview.py -> services -> src -> backend -> apps -> 프로젝트 루트)
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[4]
WIKI_DIR = (PROJECT_ROOT / "docs" / "wiki").resolve()


class TaskStatus(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    INDEXING = "INDEXING"
    COMPRESSING = "COMPRESSING"
    SEARCHING = "SEARCHING"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class WorldviewSession:
    session_id: str
    status: TaskStatus = TaskStatus.IDLE
    status_message: str = "대기 중"
    history: List[ChatMessage] = field(default_factory=list)
    compressed_summary: str = ""  # 3쌍 이전 대화들의 압축 요약본
    last_question: Optional[str] = None
    last_answer: Optional[str] = None
    error_message: Optional[str] = None

    def update_status(self, status: TaskStatus, message: str):
        self.status = status
        self.status_message = message
        logger.info(f"[Session {self.session_id[:8]}] [{status.value}] {message}")


# 전역 세션 저장소 및 체인 객체
_sessions: Dict[str, WorldviewSession] = {}
current_vectorstore = None
_chain_lock = asyncio.Lock()

llm_fallbacks = [
    ChatOpenAI(
        model=model_name,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0.1,
        default_headers=HEADERS,
    ) for model_name in FALLBACK_MODELS
]

llm = llm_fallbacks[0]
if len(llm_fallbacks) > 1:
    llm = llm.with_fallbacks(llm_fallbacks[1:])

embeddings = OpenAIEmbeddings(
    model="openai/text-embedding-3-small",
    api_key=API_KEY,
    base_url=BASE_URL,
    default_headers=HEADERS,
)


def load_wiki_markdown_documents() -> list[Document]:
    if not WIKI_DIR.exists():
        logger.error(f"위키 경로가 존재하지 않습니다: {WIKI_DIR}")
        return []

    documents: list[Document] = []
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )

    md_files = [p for p in WIKI_DIR.rglob("*.md") if ".obsidian" not in p.parts]

    for file_path in md_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                continue

            rel_path = file_path.relative_to(WIKI_DIR)
            header_splits = markdown_splitter.split_text(content)

            for doc in header_splits:
                doc.metadata["source_file"] = str(rel_path)
                documents.append(doc)

        except Exception as e:
            logger.warning(f"마크다운 파일 로드 실패 ({file_path}): {e}")

    logger.info(f"총 {len(md_files)}개의 마크다운 파일에서 {len(documents)}개 소단원 로드 완료")
    return documents


async def _get_or_create_vectorstore(force_update=False, session: Optional[WorldviewSession] = None):
    global current_vectorstore
    current_embeddings = embeddings

    if session:
        session.update_status(TaskStatus.INITIALIZING, "FAISS 위키 벡터스토어 확인 중...")

    if not force_update and current_vectorstore is not None:
        return current_vectorstore

    if not force_update and os.path.exists(INDEX_PATH):
        try:
            if session:
                session.update_status(TaskStatus.INITIALIZING, "기존 FAISS 위키 인덱스 로딩 중...")
            current_vectorstore = await asyncio.to_thread(
                FAISS.load_local,
                folder_path=INDEX_PATH,
                embeddings=current_embeddings,
                allow_dangerous_deserialization=True
            )
            return current_vectorstore
        except Exception as e:
            logger.warning(f"인덱스 로드 실패 (새로 생성): {e}")

    # 새로 생성해야 하는 경우
    if session:
        session.update_status(TaskStatus.INDEXING, "docs/wiki 문서 스캔 및 인덱싱 중...")

    if not os.path.exists(INDEX_PATH):
        os.makedirs(INDEX_PATH, exist_ok=True)

    md_docs = load_wiki_markdown_documents()

    chunk_size = 1200
    chunk_overlap = 300
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    splits = text_splitter.split_documents(md_docs)
    if session:
        session.update_status(TaskStatus.INDEXING, f"{len(splits)}개 위키 청크 FAISS 인덱싱 중...")

    def _create_and_save_index():
        try:
            vs = FAISS.from_documents(documents=splits, embedding=current_embeddings)
            vs.save_local(INDEX_PATH)
            return vs
        except Exception as e:
            logger.error(f"FAISS 생성/저장 실패: {e}")
            raise e

    current_vectorstore = await asyncio.to_thread(_create_and_save_index)
    return current_vectorstore


async def initialize_chain(session: Optional[WorldviewSession] = None):
    async with _chain_lock:
        await _get_or_create_vectorstore(force_update=False, session=session)


async def update_chain(session: Optional[WorldviewSession] = None):
    async with _chain_lock:
        await _get_or_create_vectorstore(force_update=True, session=session)


# --- 대화 히스토리 슬라이딩 윈도우 & LLM 압축 요약 헬퍼 ---

async def _process_history_and_get_pairs(session: WorldviewSession) -> tuple[str, list[tuple[ChatMessage, ChatMessage]]]:
    """
    대화 히스토리를 (User, Assistant) 짝(Pair) 단위로 분석합니다.
    - 최근 3쌍 (최대 6개 메시지): 개별 ("human", "ai") 메시지 롤 튜플 리스트로 반환.
    - 3쌍 이전의 오래된 메시지: LLM으로 요약(Compressing)하여 summary에 저장.
    """
    history = session.history
    pairs: list[tuple[ChatMessage, ChatMessage]] = []
    i = 0
    while i < len(history) - 1:
        if history[i].role == "user" and history[i+1].role == "assistant":
            pairs.append((history[i], history[i+1]))
            i += 2
        else:
            i += 1

    if len(pairs) <= 3:
        recent_pairs = pairs
        older_pairs = []
    else:
        recent_pairs = pairs[-3:]
        older_pairs = pairs[:-3]

    if older_pairs:
        session.update_status(TaskStatus.COMPRESSING, "3쌍 이전의 오래된 대화 내용을 핵심 요약 압축 중...")
        
        older_text_blocks = []
        for q, a in older_pairs:
            older_text_blocks.append(f"Q: {q.content}\nA: {a.content}")
        
        older_text = "\n\n".join(older_text_blocks)
        
        compress_prompt = f"""다음은 사용자와 KLB 세계관 어시스턴트의 이전 오래된 대화 내용입니다. 
주요 세계관 설정, 등장 구단, 언급된 인물/장소가 손실되지 않도록 2-3문장의 배경 맥락으로 핵심만 깔끔하게 요약해 주세요.

[이전 오래된 대화]
{older_text}"""
        
        try:
            summary_res = await llm.ainvoke(compress_prompt)
            session.compressed_summary = str(summary_res.content).strip()
        except Exception as e:
            logger.warning(f"대화 압축 요약 중 예외 발생: {e}")

    summary_context_str = session.compressed_summary if session.compressed_summary else "없음"
    return summary_context_str, recent_pairs


# --- 세션 관리 API ---

def create_session() -> WorldviewSession:
    session_id = str(uuid.uuid4())
    session = WorldviewSession(session_id=session_id)
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[WorldviewSession]:
    return _sessions.get(session_id)


async def ask_question_async(session_id: str, question: str, force_update: bool = False):
    session = get_session(session_id)
    if not session:
        raise ValueError(f"존재하지 않는 세션입니다: {session_id}")

    session.last_question = question
    session.error_message = None

    try:
        # 1. 벡터스토어 확보
        vectorstore = await _get_or_create_vectorstore(force_update=force_update, session=session)

        # 2. 대화 히스토리 분할 & 3쌍 이전 대화 LLM 요약 압축
        summary_context_str, recent_pairs = await _process_history_and_get_pairs(session)

        # 3. 위키 관련 문서 검색 (MultiQueryRetriever)
        session.update_status(TaskStatus.SEARCHING, "위키 문서에서 관련 정보를 검색 중입니다...")

        base_retriever = vectorstore.as_retriever(search_kwargs={"k": 7})
        multi_query_template = """당신은 Krown League Baseball(KLB) 세계관 검색 어시스턴트입니다.
사용자의 질문과 이전 대화 흐름을 함께 분석하여, 벡터 데이터베이스에서 관련 세계관/리그/구단 위키 문서를 잘 검색할 수 있도록 3개의 다른 검색 질문으로 변환하세요.
각 질문은 반드시 줄바꿈으로만 구분해야 합니다.

질문: {question}"""

        multi_query_prompt = PromptTemplate(input_variables=["question"], template=multi_query_template)
        retriever = MultiQueryRetriever.from_llm(
            retriever=base_retriever,
            llm=cast(BaseLanguageModel, llm),
            prompt=multi_query_prompt
        )

        docs = await retriever.ainvoke(question)

        formatted_docs = []
        for d in docs:
            source = d.metadata.get("source_file", "unknown")
            headers = " > ".join([v for k, v in d.metadata.items() if "Header" in k])
            location_info = f"[출처: {source}" + (f" | 위치: {headers}]" if headers else "]")
            formatted_docs.append(f"{location_info}\n{d.page_content}")
        context_str = "\n\n---\n\n".join(formatted_docs)

        # 4. LLM 메시지 롤 구조화 (ChatPromptTemplate from_messages 튜플 배열 생성)
        session.update_status(TaskStatus.GENERATING, "LLM이 구조화된 대화 턴과 위키 문서를 기반으로 답변을 생성하고 있습니다...")

        system_instruction = f"""당신은 Krown League Baseball(KLB) 세계관 및 위키에 대해 깊은 지식을 가진 전문 어시스턴트 '크라운(Krown)'입니다.
제공된 [이전 대화 요약 맥락], [최근 대화 턴], [KLB 위키 문서 발췌문]을 함께 고려하여 사용자의 질문에 친절하고 명확하게 한국어로 답변해 주세요.

[지침]
1. 발췌문(context)과 이전 대화 맥락을 고려하여 연관된 세계관 질문에 일관성 있게 답변하세요.
2. 발췌문에 없는 완전히 새로운 정보는 함부로 픽션이나 허구를 덧붙이지 말고 '제공된 위키 문서에서 해당 정보를 찾을 수 없다'고 솔직히 대답하세요.
3. 이전 대화 턴에서 지칭하는 대명사(예: '그 팀은?', '거기 위치는?')가 있다면 이전 대화 턴을 바탕으로 추론하여 파악하세요.

[이전 오래된 대화 요약 맥락 (3쌍 이전 내용)]
{summary_context_str}"""

        # 메세지 배열 구조화: System ➔ 최근 3쌍의 ("human", content), ("ai", content) ➔ 현재 질문+Context ("human")
        message_tuples: list[tuple[str, str]] = [("system", system_instruction)]

        for q_msg, a_msg in recent_pairs:
            message_tuples.append(("human", q_msg.content))
            message_tuples.append(("ai", a_msg.content))

        current_human_prompt = f"""[KLB 위키 문서 발췌문]
{context_str}

[현재 질문]
{question}"""

        message_tuples.append(("human", current_human_prompt))

        prompt_template = ChatPromptTemplate.from_messages(message_tuples)
        chain = prompt_template | llm

        response = await chain.ainvoke({})
        answer_text = str(response.content)

        # 5. 세션 히스토리에 현재 질문과 답변 기록 추가
        session.history.append(ChatMessage(role="user", content=question))
        session.history.append(ChatMessage(role="assistant", content=answer_text))

        session.last_answer = answer_text
        session.update_status(TaskStatus.COMPLETED, "답변 생성이 완료되었습니다.")

    except Exception as e:
        session.error_message = str(e)
        session.update_status(TaskStatus.FAILED, f"오류 발생: {e}")
        logger.error(f"ask_question_async 에러: {e}")