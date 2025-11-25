import streamlit as st
import json
import os
import pandas as pd
import logging

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


def _render_news_result(tool_data):
    st.markdown(f"**📰 {tool_data.get('topic', '뉴스')}**")
    for i, article in enumerate(tool_data.get("headlines", []), 1):
        if isinstance(article, dict) and "title" in article:
            st.markdown(f"- {article['title']}")
        elif isinstance(article, str):
            st.markdown(f"- {article}")
        else:
            st.markdown(f"- {str(article)}")


def _render_document_search_result(tool_data):
    st.markdown("**📚 문서 검색 결과**")

    unique_files = {}

    for i, item in enumerate(tool_data, 1):
        if isinstance(item, dict):
            text = item.get("text", "")
            src = item.get("source_file")
            src_name = os.path.basename(src) if src else ""
            header = f"**Chunk {i}** ({src_name})" if src_name else f"**Chunk {i}**"
        else:
            text = str(item)
            header = f"**Chunk {i}**"

        if len(text) > 300:
            with st.expander(f"{header} (더보기)", expanded=False):
                st.markdown(text)
        else:
            st.markdown(f"{header}\n{text}")

        if isinstance(item, dict):
            sf = item.get("source_file")
            if sf and sf not in unique_files:
                unique_files[sf] = os.path.basename(sf)

    if unique_files:  ## 모두 다운로드로 수정 필요
        st.markdown("##### ⬇️ 이 질문과 관련된 원문 파일 다운로드")
        for path, fname in unique_files.items():
            try:
                with open(path, "rb") as f:
                    file_bytes = f.read()
                st.download_button(
                    label=f"📎 {fname}",
                    data=file_bytes,
                    file_name=fname,
                    mime="application/pdf",
                )
            except Exception as e:
                st.caption(f"파일을 불러올 수 없습니다 ({e}): {fname}")


def render_tool_data_for_display(tool_name: str, tool_data):
    icon, _, _ = TOOL_ICON_MAP.get(tool_name, ("🧩", "#999999", tool_name))

    try:
        if isinstance(tool_data, str):
            processed_data = json.loads(tool_data)
        else:
            processed_data = tool_data
    except json.JSONDecodeError:
        processed_data = tool_data
    except Exception:
        processed_data = tool_data

    with st.expander(f"{icon} Tool Result: {tool_name}", expanded=False):

        # 1) 뉴스 결과
        if isinstance(processed_data, dict) and "headlines" in processed_data:
            _render_news_result(processed_data)

        # 2) 문서 검색 결과 (리스트)
        elif isinstance(processed_data, list):
            _render_document_search_result(processed_data)

        # 3) 기타 도구 결과
        else:
            try:
                if isinstance(processed_data, (dict, list)):
                    st.json(processed_data)
                else:
                    st.markdown(str(processed_data))
            except Exception:
                st.markdown(str(processed_data))


def render_chat_history():
    for msg in st.session_state.get("session", []):
        role = msg.get("role", "")
        content = msg.get("content", "")

        # system 메시지는 화면에 표시 안 함
        if role == "system":
            continue

        # 이전 턴 tool 결과
        if role == "tool":
            try:
                tool_data = json.loads(content)
            except Exception:
                tool_data = content
            tool_name = msg.get("name", "unknown")
            render_tool_data_for_display(tool_name, tool_data)
            continue

        # user / assistant 일반 대화 메시지
        if content:
            with st.chat_message(role):
                st.markdown(content)
