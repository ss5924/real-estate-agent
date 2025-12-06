import streamlit as st
import time
import logging
import json
from datetime import datetime
import os

from src.agent_core import get_response
from components.chat_renderer import render_tool_data_for_display
from src.session_manager import save_new_session_items
from src.config import SESSION_DIR

logger = logging.getLogger(__name__)

TOOL_ICON_MAP = {
    "get_news": ("📰", "#e67e22", "📰 뉴스검색"),
    "search_vector_store": ("📚", "#2ecc71", "📚 문서검색"),
    "search_korean_law": ("⚖️", "#3498db", "⚖️ 법령검색"),
    "get_current_datetime": ("⏰", "#9b59b6", "⏰ 시간확인"),
    "llm_as_a_judge_attempt_1": ("🧪", "#e74c3c", "🧪 자기 평가"),
    "llm_as_a_judge_attempt_2": ("🧪", "#e74c3c", "🧪 자기 평가"),
    "llm_as_a_judge_attempt_3": ("🧪", "#e74c3c", "🧪 자기 평가"),
}


def handle_user_query(
    client, query, directive, index, chunks, metadatas, session_file: str | None
):
    # 사용자 메시지 버블

    _session_file = session_file

    if not _session_file:
        # 새 세션 파일명 생성 (예: session_20251121_103030.jsonl)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(SESSION_DIR, exist_ok=True)
        filename = os.path.join(SESSION_DIR, f"session_{ts}.jsonl")
        _session_file = os.path.join(SESSION_DIR, f"session_{ts}.jsonl")
        st.session_state["session_file"] = filename

    with st.chat_message("user"):
        st.markdown(query)
        logger.info(f"🚀 질문이 입력되었습니다: {query[:50]}...")

    # 에이전트 응답 버블
    # 이 버블 안에서 그려야 함
    with st.chat_message("assistant"):

        # 이 assistant 버블 안에서만 쓰는 placeholder
        status_placeholder = st.empty()
        timer_placeholder = st.empty()

        # core에서 상태 업데이트 요청이 오면 이 버블 안에 표시
        def status_callback(text: str, ph=status_placeholder):
            ph.markdown(text)

        start_time = time.time()

        with st.spinner("💭 Thinking..."):
            reply, tool_results, new_session, previous_session_size = get_response(
                client=client,
                query=query,
                directive=directive,
                index=index,
                chunks=chunks,
                metadatas=metadatas,
                session=st.session_state.get("session", []),
                status_callback=status_callback,
            )

        # 3. 결과 저장 및 출력
        # 최신 세션 session_state에 저장
        st.session_state["session"] = new_session
        # 파일에 세션 히스토리 저장
        save_new_session_items(new_session, previous_session_size, _session_file)

        elapsed = time.time() - start_time

        # ⏱️ 처리 시간 표시
        timer_placeholder.markdown(
            f"""
            <div style="
                display:inline-block;
                background:#f7f7f7;
                color:#666;
                font-size:11px;
                padding:4px 10px;
                border-radius:8px;
                margin:0 0 6px 0;
                max-width:180px;
            ">⏱️ 처리 시간: 약 {elapsed:.1f}초</div>
            """,
            unsafe_allow_html=True,
        )

        for msg in new_session[previous_session_size:]:
            if msg.get("role") == "tool":
                tool_name = msg.get("name", "unknown")
                content = msg.get("content", "")
                try:
                    tool_data = json.loads(content)
                except Exception:
                    tool_data = content
                render_tool_data_for_display(tool_name, tool_data)

        # 최종 답변 출력
        st.markdown(reply)
