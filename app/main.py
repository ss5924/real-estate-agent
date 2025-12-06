import streamlit as st
from openai import OpenAI
import logging

from src.config import RAG_DATA_DIR, OPENAI_API_KEY
from src.prompts import SYSTEM_PROMPT
from src.rag_pipeline import build_index_from_folder
from components.ui_components import render_header, render_sidebar
from src.session_manager import initialize_rag_index, load_session_from_file
from components.chat_renderer import render_chat_history
from src.response_handler import handle_user_query

logger = logging.getLogger(__name__)


client = OpenAI(api_key=OPENAI_API_KEY)
st.set_page_config(page_title="집사부", layout="wide")

# 세션 초기화
session_file = st.session_state.get("session_file")
# 세션 로드: 파일이 있을 때만 로드
if session_file:
    previous_session = load_session_from_file(session_file)
else:
    previous_session = []
st.session_state["session"] = previous_session

# UI 렌더링
render_header()
render_sidebar()

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
        session_file=session_file,
    )
