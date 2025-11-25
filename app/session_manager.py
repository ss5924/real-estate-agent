import os
import json
import streamlit as st
import time
import logging
from datetime import datetime
from rag_pipeline import build_index_from_folder

logger = logging.getLogger(__name__)


def initialize_rag_index(client, data_directory):
    index = st.session_state.get("index", None)
    chunks = st.session_state.get("chunks", None)
    metadatas = st.session_state.get("metadatas", None)

    if "index" not in st.session_state:
        logger.info("RAG 인덱스 로드 중...")
        with st.spinner("📚 임베딩된 문서를 불러오는 중입니다..."):
            start_time = time.time()
            try:
                index, chunks, metadatas = build_index_from_folder(
                    data_directory, client
                )
                st.session_state["index"] = index
                st.session_state["chunks"] = chunks
                st.session_state["metadatas"] = metadatas
                logger.info(
                    f"RAG 인덱스 로드 완료. 시간: {time.time() - start_time:.2f}초"
                )
            except Exception as e:
                st.error(f"RAG 인덱스 로드 실패: {e}")
                logger.error(f"RAG 인덱스 로드 실패: {e}")

    return index, chunks, metadatas


def load_session_from_file(filepath):
    session = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                session.append(json.loads(line))
    except FileNotFoundError:
        return []
    return session


def save_new_session_items(session, previous_size, filepath):
    new_items = session[previous_size:]
    with open(filepath, "a", encoding="utf-8") as f:
        for msg in new_items:
            serializable = make_json_safe(msg)
            f.write(json.dumps(serializable, ensure_ascii=False) + "\n")


def make_json_safe(obj):
    # OpenAI / Pydantic 객체 → dict
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()

    # dict인 경우: 재귀 처리
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}

    # list/tuple인 경우
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(v) for v in obj]

    # JSON 기본 타입
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj

    # 그 외 특이한 타입은 문자열로
    return str(obj)


def list_log_sessions(log_dir: str = "sessions"):
    if not os.path.isdir(log_dir):
        return []

    all_session_metadatas = []
    for fname in os.listdir(log_dir):
        if not fname.endswith(".jsonl"):
            continue

        fpath = os.path.join(log_dir, fname)
        try:
            stat = os.stat(fpath)
            created_at = datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            with open(fpath, "r", encoding="utf-8") as f:
                msg_count = sum(1 for line in f if line.strip())
        except Exception as e:
            logger.warning(f"세션 파일 메타정보 읽기 실패: {fpath} / {e}")
            created_at = ""
            msg_count = 0

        all_session_metadatas.append(
            {
                "id": fpath,
                "title": os.path.splitext(fname)[0],
                "created_at": created_at,
                "message_count": msg_count,
                "filepath": fpath,
            }
        )

    all_session_metadatas.sort(key=lambda x: x["filepath"], reverse=True)
    return all_session_metadatas
