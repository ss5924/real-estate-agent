import base64
import glob
import io
import json
import os
from datetime import datetime, timedelta

import faiss
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image
from openai import OpenAI


@st.cache_resource(show_spinner=True)
def build_index_from_folder(folder_path: str, _client: OpenAI):
    pdf_files = glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True)
    all_chunks = []
    metadatas = []
    for path in pdf_files:
        with open(path, "rb") as f:
            file_bytes = f.read()
        text = extract_text_from_pdf(file_bytes)
        file_chunks = chunk_text(text)
        for ch in file_chunks:
            all_chunks.append(ch)
            metadatas.append(
                {
                    "source_file": path,
                }
            )
    embeddings = np.array(
        [get_embedding(ch, _client) for ch in all_chunks], dtype="float32"
    )
    dim = embeddings.shape[1]
    base_index = faiss.IndexFlatL2(dim)
    index = faiss.IndexIDMap(base_index)
    ids = np.arange(len(all_chunks)).astype("int64")
    index.add_with_ids(embeddings, ids)
    return index, all_chunks, metadatas


@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_bytes: bytes):
    api_key = "up_3Q55AJgytJeBuO4GZmR3OXSLjkhMy"
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
    index.add(embeddings)
    return index
