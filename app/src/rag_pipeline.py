import glob
import os
import faiss
import numpy as np
import requests
import streamlit as st

from openai import OpenAI

from src.config import UPSTAGE_API_KEY


@st.cache_resource(show_spinner=True)
def build_index_from_folder(folder_path: str, _client: OpenAI):
    # 파일 탐색 및 텍스트 청킹
    pdf_files = glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True)
    all_chunks = []
    metadatas = []

    for path in pdf_files:
        try:
            with open(path, "rb") as f:
                file_bytes = f.read()
            text = extract_text_from_pdf(file_bytes)

            # 텍스트가 비어있으면 건너뜀
            if not text:
                continue

            file_chunks = chunk_text(text)
            for ch in file_chunks:
                all_chunks.append(ch)
                metadatas.append({"source_file": path})
        except Exception as e:
            print(f"파일 처리 중 에러 발생 ({path}): {e}")
            continue

    # 청크가 하나도 없으면 여기서 종료 (빈값 리턴)
    if not all_chunks:
        print("경고: 처리할 텍스트 청크가 없습니다.")
        return None, [], []

    # 임베딩 생성
    try:
        # 리스트 컴프리헨션으로 임베딩 생성
        embeddings_list = [get_embedding(ch, _client) for ch in all_chunks]

        # FAISS 호환성을 위한 Numpy 변환 및 메모리 정렬
        embeddings = np.array(embeddings_list, dtype="float32")
        embeddings = np.ascontiguousarray(embeddings)
    except Exception as e:
        print(f"임베딩 생성 중 에러: {e}")
        return None, [], []

    # FAISS 인덱스 생성
    # 데이터가 있으면 차원(dimension)을 구함
    dim = embeddings.shape[1]

    # L2(유클리드 거리) 기반 인덱스 생성
    index = faiss.IndexFlatL2(dim)

    # 0부터 순차적 ID 자동 부여
    index.add(embeddings)  # type: ignore

    return index, all_chunks, metadatas


@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_bytes: bytes):
    api_key = UPSTAGE_API_KEY
    url = "https://api.upstage.ai/v1/document-digitization"
    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"document": ("document.pdf", file_bytes, "application/pdf")}
    data = {"model": "ocr"}
    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()
    pages = result.get("pages", [])
    texts = [p.get("text", "").strip() for p in pages if p.get("text")]
    if not texts:
        for p in pages:
            words = [w.get("text", "") for w in p.get("words", [])]
            texts.append(" ".join(words))
    full_text = "\n\n".join(texts)
    return full_text


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    step = chunk_size - overlap
    length = len(text)
    while start < length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += step
    return chunks


def get_embedding(text, client: OpenAI):
    res = client.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(res.data[0].embedding, dtype="float32")


def build_faiss_index(chunks, client: OpenAI):
    embeddings = np.array([get_embedding(ch, client) for ch in chunks]).astype(
        "float32"
    )
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)  # type: ignore
    return index
