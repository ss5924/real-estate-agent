import json
from openai import OpenAI
from src.personal_memory import MemoryManager

from src.tools import (
    classify_query_for_tools,
    plan_from_user_query,
    get_news,
    search_vector_store,
    get_current_datetime,
    search_korean_law,
    llm_as_a_judge,
    check_policy_and_safety,
    get_user_summary,
)
from src.agent_constants import TOOLS
from src.agent_utils import init_session, call_llm, update_status
from src.prompts import MEMORY_PROMPT_TEMPLATE


def get_response(
    user_id: str,
    client: OpenAI,
    query: str,
    directive: str | None,
    continuous: bool = True,
    index=None,
    chunks=None,
    metadatas=None,
    session: list | None = None,
    status_callback=None,
):
    if session is None:
        session = []

    previous_session_size = len(session)

    # 세션 초기화 및 준비
    session = init_session(session, directive, continuous)

    # 질의 복잡도 분류
    classify_result = classify_query_for_tools(query, client)
    need_tools = classify_result.get("need_tools", False)

    final_answer = ""
    tool_results = {}

    # 간단한 질의 (Tools 불필요)
    if not need_tools:
        final_answer, tool_results, session = _handle_simple_query(
            client, session, query, directive, classify_result
        )

    # 복잡한 질의 (Tools + Planner + Judge)
    else:
        assert session is not None
        session.append({"role": "user", "content": query})

        # 플래너 단계
        plan, tool_plan = _run_planner_phase(
            client, query, session, status_callback=status_callback
        )

        tool_results = {
            "_planner": plan,
            "_classifier": classify_result,
        }

        # 툴 실행 루프
        draft_answer = _run_tool_loop(
            user_id=user_id,
            client=client,
            session=session,
            tool_plan=tool_plan,
            tool_results=tool_results,
            status_callback=status_callback,
            index=index,
            chunks=chunks,
            metadatas=metadatas,
        )

        # Judge 루프
        final_answer, judge_logs = _run_judge_loop(
            client=client,
            query=query,
            directive=directive,
            session=session,
            first_output=draft_answer,
            tool_results=tool_results,
            status_callback=status_callback,
        )
        tool_results.update(judge_logs)

        update_status(status_callback, "✅ 답변 준비가 완료되었습니다.")

    # 장기 메모리 지능형 업데이트
    if user_id:
        try:
            mm = MemoryManager()
            _update_memory_if_necessary(client, session, user_id, mm)
        except Exception as e:
            # 메모리 저장이 메인 로직을 방해하면 안 되므로 로그만 남기고 패스
            print(f"Memory update failed: {e}")

    return final_answer, tool_results, session, previous_session_size


def _update_memory_if_necessary(
    client: OpenAI, session: list, user_id: str, mm: MemoryManager
):
    recent_messages = []
    # 뒤에서부터 10개 정도만 보되, user나 assistant의 '대화 내용'만 추려냅니다.
    for msg in reversed(session):
        if len(recent_messages) >= 6:  # 최대 6턴만 확인
            break

        # tool 메시지나 tool_calls는 메모리 요약에 굳이 필요 없으므로 제외 (API 에러 방지)
        if msg["role"] in ["user", "assistant"] and msg.get("content"):
            # 순서를 맞추기 위해 앞에 삽입 (reversed로 돌고 있으므로)
            recent_messages.insert(0, {"role": msg["role"], "content": msg["content"]})

    # 내용이 너무 없으면 중단
    if not recent_messages:
        return

    # 시스템 프롬프트
    system_msg = {
        "role": "system",
        "content": MEMORY_PROMPT_TEMPLATE,
    }

    # LLM 호출
    messages = []
    messages.append(system_msg)
    messages.extend(recent_messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content

        if not content:
            raise ValueError("Empty response from LLM")

        result = json.loads(content)

        should_update = result.get("update_needed", False)
        new_memory = result.get("memory_content", "").strip()

        if should_update and new_memory:
            # 기존 메모리 로드
            existing = mm.get_user_summary(user_id) or ""

            if existing:
                combined_memory = f"{existing}\n- {new_memory}"
            else:
                combined_memory = f"- {new_memory}"

            # 저장
            mm.save_user_summary(user_id, combined_memory)
            print(f"📝 [Memory Updated] {new_memory}")
        else:
            # 업데이트 불필요
            pass

    except Exception as e:
        print(f"Error during memory judgement: {e}")


def _handle_simple_query(
    client: OpenAI,
    session,
    query: str,
    directive: str | None,
    classify_result: dict,
):
    session.append({"role": "user", "content": query})
    msg = call_llm(client, session)
    final_answer = msg.content
    session.append({"role": "assistant", "content": final_answer})

    tool_results = {
        "_mode": "simple_answer",
        "_classifier": classify_result,
    }
    return final_answer, tool_results, session


def _run_planner_phase(client: OpenAI, query: str, session, status_callback=None):
    update_status(status_callback, "✏️ 플래너가 질문을 정리하고 있습니다...")

    plan = plan_from_user_query(query, client)
    refined_q = plan.get("refine_question", query)
    intent = plan.get("intention", "")
    tool_plan = plan.get("tool_plan", [])

    user_content = f"[사용자 원문]\n{query}\n\n[정제된 질문]\n{refined_q}"
    if intent:
        user_content += f"\n\n[의도 추론]\n{intent}"

    session.append({"role": "system", "content": user_content})
    session.append(
        {
            "role": "system",
            "content": (
                "다음은 상위 플래너가 추천한 툴 사용 계획입니다. "
                "필요에 따라 유연하게 참고하세요.\n"
                + json.dumps(plan, ensure_ascii=False)
            ),
        }
    )
    return plan, tool_plan


def _execute_tool_call(
    user_id: str,
    func_name: str,
    args: dict,
    client: OpenAI,
    index=None,
    chunks=None,
    metadatas=None,
):
    if func_name == "get_news":
        return get_news(args["topic"])
    if func_name == "search_vector_store" and index is not None:
        return search_vector_store(
            client,
            args["query"],
            index,
            chunks,
            metadatas,
            top_k=args.get("top_k", 3),
        )
    if func_name == "get_current_datetime":
        return get_current_datetime()
    if func_name == "search_korean_law":
        return search_korean_law(**args)
    if func_name == "check_policy_and_safety":
        return check_policy_and_safety(args["user_query"], args["answer"], client)
    if func_name == "get_user_summary":
        return get_user_summary(user_id=user_id)
    return {"error": f"알 수 없는 함수: {func_name}"}


def _run_tool_loop(
    user_id: str,
    client: OpenAI,
    session,
    tool_plan,
    tool_results: dict,
    status_callback=None,
    index=None,
    chunks=None,
    metadatas=None,
):
    planned_steps = len(tool_plan or [])
    base_loops = 1 if planned_steps == 0 else planned_steps
    MAX_TOOL_LOOPS = min(base_loops + 2, 6)

    if planned_steps == 0:
        update_status(
            status_callback, "🧭 플랜 분석 결과, 필요한 경우에만 도구를 사용합니다..."
        )
    else:
        update_status(
            status_callback,
            f"🧭 플랜 분석 결과, 우선 {planned_steps}개의 도구 사용이 추천되었습니다.",
        )

    draft_answer = None
    loop_idx = 0

    while True:
        if loop_idx >= MAX_TOOL_LOOPS:
            break

        update_status(
            status_callback,
            f"🔍 외부 도구를 사용해 자료를 수집하는 중입니다... ({loop_idx+1}/{MAX_TOOL_LOOPS})",
        )

        msg = call_llm(
            client,
            session,
            tools=TOOLS,
            tool_choice="auto",
        )

        # 툴 호출 없이 바로 답변이 오면 루프 종료
        if not getattr(msg, "tool_calls", None):
            draft_answer = msg.content
            session.append({"role": "assistant", "content": draft_answer})
            break

        # 툴 호출 처리
        session.append({"role": "assistant", "tool_calls": msg.tool_calls})

        for t in msg.tool_calls:
            func_name = t.function.name
            args = json.loads(t.function.arguments)

            try:
                result = _execute_tool_call(
                    user_id,
                    func_name,
                    args,
                    client,
                    index=index,
                    chunks=chunks,
                    metadatas=metadatas,
                )
            except Exception as e:
                result = {"error": str(e)}

            tool_results[func_name] = result

            if func_name == "get_user_summary":
                # 개인정보 보호를 위해 get_user_summary 결과는 세션에 저장하지 않음
                continue

            session.append(
                {
                    "role": "tool",
                    "tool_call_id": t.id,
                    "name": func_name,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        loop_idx += 1

    if draft_answer is None:
        update_status(
            status_callback, "🧩 수집한 정보를 바탕으로 답변을 정리하고 있습니다..."
        )
        msg = call_llm(client, session)
        draft_answer = msg.content
        session.append({"role": "assistant", "content": draft_answer})

    return draft_answer


def _run_judge_loop(
    client: OpenAI,
    query: str,
    directive: str | None,
    session,
    first_output: str,
    tool_results: dict,
    status_callback=None,
):
    update_status(status_callback, "🧪 LLM Judge가 답변 품질을 평가하고 있습니다...")

    current_attempt = 1
    max_retries = 3
    output = first_output
    last_judgement = None
    judge_logs = {}

    while current_attempt <= max_retries:
        judge_input_content = json.dumps(
            {
                "user_query": query,
                "system_directive": directive,
                "tool_call_results": tool_results,
                "first_response": output,
            },
            ensure_ascii=False,
        )
        try:
            judgement_str = llm_as_a_judge(judge_input_content, client)
            if not judgement_str:
                raise ValueError("Empty response from LLM")

            judgement = json.loads(judgement_str)

            key = f"llm_as_a_judge_attempt_{current_attempt}"
            judge_logs[key] = judgement
            last_judgement = judgement

            score = judgement.get("score")
            # 4.0 미만 + 재시도 가능하면 재생성
            if (
                isinstance(score, (int, float))
                and score < 4.0
                and current_attempt < max_retries
            ):
                reason = judgement.get("reason", "사유 없음")

                update_status(
                    status_callback,
                    f"🔁 Judge 점수 {score}점 → 답변을 다시 다듬는 중입니다... ({current_attempt}/{max_retries})",
                )

                retry_prompt = (
                    f"당신의 이전 응답이 품질 점수 {score}점을 받았으며, 사유는 다음과 같습니다: '{reason}'\n"
                    f"이 사유를 바탕으로 사용자 질문에 대해 더 정확하고, 시스템 지시문을 더 잘 준수하며, "
                    f"출력 형식([핵심 요약] / [상세 설명] / [출처])을 유지하도록 다시 답변해주세요. "
                    f"필요시 이전에 참조한 도구 호출 결과(tool_call_results)를 다시 활용해도 됩니다."
                )

                session.append({"role": "system", "content": retry_prompt})
                retry_msg = call_llm(client, session)
                output = retry_msg.content
                session.append({"role": "system", "content": output})

                current_attempt += 1
            else:
                break

        except Exception as e:
            key = f"llm_as_a_judge_attempt_{current_attempt}"
            judge_logs[key] = {
                "error": f"Judge 호출 또는 파싱 오류: {e}",
                "original_output": output,
            }
            break

    if last_judgement is not None:
        judge_logs["_judge_last"] = last_judgement

    return output, judge_logs
