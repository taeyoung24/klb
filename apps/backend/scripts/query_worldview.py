# uv run -m scripts.query_worldview
# uv run -m scripts.query_worldview --update
import asyncio
import sys

from src.services.worldview import (
    create_session,
    ask_question_async,
    TaskStatus,
)
from src.utils.logger import logger

async def main():
    logger.info("=== KLB 세계관/위키 RAG 폴링 비동기 대화 스크립트 ===")
    
    # 세션 객체 생성
    session = create_session()
    force_update = "--update" in sys.argv

    print("\n" + "=" * 65)
    print(f"💬 KLB 세계관 어시스턴트 '크라운(Krown)'과의 대화 세션 [ID: {session.session_id[:8]}]")
    print("💡 종료하시려면 'exit', 'quit', 또는 'q'를 입력해 주세요.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("❓ 질문을 입력하세요 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 세션을 종료합니다.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "q", "종료"]:
            print("👋 대화를 종료합니다. 이용해 주셔서 감사합니다!")
            break

        # 비동기 질문 요청 태스크 발송 (백그라운드에서 실행)
        task = asyncio.create_task(
            ask_question_async(
                session_id=session.session_id,
                question=user_input,
                force_update=force_update
            )
        )
        
        # 첫 번째 쿼리 이후에는 force_update를 다시 해제
        force_update = False

        # --- 비동기 폴링 (Polling Loop) ---
        last_status_msg = ""
        while not task.done():
            current_msg = f"[상태: {session.status.value}] {session.status_message}"
            if current_msg != last_status_msg:
                print(f"\r\033[K⏳ {current_msg}")
                last_status_msg = current_msg
            await asyncio.sleep(0.2)
        print()  # 개행 추가

        # 태스크 완료 결과 확인
        if session.status == TaskStatus.COMPLETED:
            print(f"\n💬 [크라운의 답변]:\n{session.last_answer}\n")
            print("-" * 65)
        elif session.status == TaskStatus.FAILED:
            print(f"\n❌ [오류 발생]: {session.error_message}\n")
            print("-" * 65)

if __name__ == "__main__":
    asyncio.run(main())
