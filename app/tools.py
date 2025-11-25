import json
from datetime import datetime
import numpy as np
import requests
from openai import OpenAI

from config import NEWS_API_KEY
from prompts import (
    CLASSIFY_PROMPT_TEMPLATE,
    PLAN_PROMPT_TEMPLATE,
    JUDGE_PROMPT_TEMPLATE,
    POLICY_SAFETY_PROMPT_TEMPLATE,
)


def get_news(topic: str):
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=ko"
    r = requests.get(url)
    if r.status_code != 200:
        return {"error": "뉴스 정보를 가져올 수 없습니다."}
    arts = r.json().get("articles", [])[:5]
    return {"topic": topic, "headlines": [a["title"] for a in arts]}


def search_korean_law(
    query: str,
    search: int = 1,  # 검색범위 (기본 : 1 법령해석례명) 2 : 본문검색
    inq: str | None = None,  # 질의기관
    rpl: str | None = None,  # 회신기관
    gana: str | None = None,  # 사전식 검색(ga,na,da…,etc)
    itmno: str | None = None,  # 안건번호 13-0217 검색을 원할시 itmno=130217
    regYd: str | None = None,  # 등록일자 검색(20090101~20090130)
    explYd: str | None = None,  # 해석일자 검색(20090101~20090130)
):
    base_url = "http://www.law.go.kr/DRF/lawSearch.do"
    params = {
        "OC": "shsha9292",
        "target": "expc",
        "type": "JSON",
        "query": query,
        "search": search,
    }
    optional_params = {
        "inq": inq,
        "rpl": rpl,
        "gana": gana,
        "itmno": itmno,
        "regYd": regYd,
        "explYd": explYd,
    }
    for key, value in optional_params.items():
        if value is not None:
            params[key] = value
    try:
        r = requests.get(base_url, params=params, timeout=10)
        if r.status_code != 200:
            return {"error": f"HTTP 오류: {r.status_code}", "params": params}
        try:
            data = r.json()
        except ValueError:
            return {"error": "JSON 파싱 실패", "raw": r.text, "params": params}
        return data
    except requests.RequestException as e:
        return {"error": f"요청 중 오류 발생: {e}", "params": params}


def llm_as_a_judge(content, client: OpenAI):
    judge_directive = JUDGE_PROMPT_TEMPLATE
    judge_session = [
        {"role": "system", "content": judge_directive},
        {"role": "user", "content": content},
    ]
    judge_response = client.chat.completions.create(
        model="gpt-4o",
        messages=judge_session,
    )
    return judge_response.choices[0].message.content


def get_current_datetime():
    print("#MCP: Load Datetime")
    from datetime import datetime

    now = datetime.now()
    ampm = "오전" if now.hour < 12 else "오후"
    hour_12 = now.hour if 1 <= now.hour <= 12 else abs(now.hour - 12)
    return f"{now.year}년 {now.month}월 {now.day}일 {ampm} {hour_12}시 {now.minute}분"


def plan_from_user_query(raw_query: str, client: OpenAI):
    prompt = PLAN_PROMPT_TEMPLATE.format(raw_query=raw_query)
    res = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )
    text = res.choices[0].message.content
    try:
        plan = json.loads(text)
    except Exception:
        plan = {"refine_question": raw_query, "intention": "일반질문", "tool_plan": []}
    return plan


def check_policy_and_safety(user_query: str, answer: str, client: OpenAI):
    prompt = POLICY_SAFETY_PROMPT_TEMPLATE.format(user_query=user_query, answer=answer)
    res = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )
    text = res.choices[0].message.content
    try:
        data = json.loads(text)
    except Exception:
        data = {"is_safe": True, "reason": "", "final_answer": answer}
    return data


def classify_query_for_tools(query: str, client: OpenAI):
    prompt = CLASSIFY_PROMPT_TEMPLATE.format(query=query)
    res = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )
    text = res.choices[0].message.content
    try:
        data = json.loads(text)
    except Exception:
        # 파싱 실패 시 보수적으로 tools 사용
        data = {"need_tools": True, "reason": "JSON 파싱 실패, 기본값으로 tools 사용"}
    return data


def search_vector_store(client: OpenAI, query, index, chunks, metadatas, top_k=3):
    q_emb = np.array([get_embedding(query, client)], dtype="float32")
    dist, ids = index.search(q_emb, top_k)
    results = []
    for d, i in zip(dist[0], ids[0]):
        if i == -1:
            continue
        results.append(
            {
                "text": chunks[i],
                "source_file": metadatas[i]["source_file"],
                "score": float(d),
            }
        )
    return results


def get_embedding(text, client: OpenAI):
    res = client.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(res.data[0].embedding, dtype="float32")
