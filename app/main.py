import streamlit as st
from openai import OpenAI
import logging

from src.config import RAG_DATA_DIR, OPENAI_API_KEY
from src.prompts import SYSTEM_PROMPT
from components.ui_components import render_header, render_sidebar
from components.login_renderer import render_login
from src.session_manager import initialize_rag_index, load_session_from_file
from components.chat_renderer import render_chat_history
from src.response_handler import handle_user_query
from src.cache_manager import get_manager

logger = logging.getLogger(__name__)

# 기본 설정
client = OpenAI(api_key=OPENAI_API_KEY)
st.set_page_config(page_title="집사부", layout="wide")

# 쿠키 매니저 로드
cookie_manager = get_manager()

# 아직 세션상으로는 로그인이 안 된 상태라면, 쿠키를 뒤져봅니다.
if not st.session_state.get("logged_in"):
    try:
        # 쿠키 동기화를 위해 전체 가져오기 시도
        cookies = cookie_manager.get_all()

        # 저장해둔 키('files_user_id') 확인
        cookie_user_id = cookie_manager.get("files_user_id")

        if cookie_user_id:
            st.session_state["user_id"] = cookie_user_id
            st.session_state["logged_in"] = True
            st.session_state["remember"] = True

            # 토스트 메시지로 가볍게 알림
            st.toast(f"🍪 {cookie_user_id}님으로 자동 로그인되었습니다!", icon="✅")
            st.rerun()  # 상태 반영을 위해 새로고침
    except Exception as e:
        logger.error(f"Cookie reading error: {e}")

# 여전히 로그인이 안 된 상태라면 -> 로그인 폼을 보여주고 멈춥니다.
if not st.session_state.get("logged_in"):
    render_login(cookie_manager=cookie_manager)
    st.stop()  # 여기서 멈춰야 아래 메인 로직이 실행 안 됨


user_id = st.session_state["user_id"]

# 세션 초기화
session_file = st.session_state.get("session_file")

# 세션 파일이 있으면 로드, 없으면 빈 리스트(새 대화)
if session_file:
    previous_session = load_session_from_file(session_file)
else:
    previous_session = []

st.session_state["session"] = previous_session

# UI 렌더링
render_header()
# 사이드바에도 cookie_manager 전달 (로그아웃 버튼용)
render_sidebar(
    user_id=user_id, cookie_manager=cookie_manager, current_session_file=session_file
)

# RAG 인덱스 로드
index, chunks, metadatas = initialize_rag_index(client, RAG_DATA_DIR)

# 기존 대화 렌더링
render_chat_history()

# 사용자 입력 + 응답 처리
if query := st.chat_input("질문을 입력해 주세요."):
    handle_user_query(
        client=client,
        query=query,
        directive=SYSTEM_PROMPT,
        index=index,
        chunks=chunks,
        metadatas=metadatas,
        user_id=user_id,
        session_file=session_file,
    )
