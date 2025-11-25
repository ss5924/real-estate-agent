import streamlit as st
import logging

from session_manager import list_log_sessions

logger = logging.getLogger(__name__)


def render_header():
    st.markdown(
        """
        <div style="padding: 25px 20px; border-radius: 12px;">
            <div style="font-size: 1.2em; color: #2d5a27; font-style: italic; font-weight: 500;">
                "부동산 상담 AI Agent"
            </div>
            <div style="margin-top: 10px; font-size: 2.4em; font-weight: 700; color: #1e4d2b;">
                부린이를 위한 '집사부'
            </div>
            <div style="width: 80px; height: 4px; background: #2d5a27; margin-top: 12px;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_session_list(current_session_file: str | None = None):
    """sessions 폴더 기준으로 대화 세션 목록 렌더링"""
    sessions = list_log_sessions("sessions")

    st.markdown("#### 💬 대화 세션")

    if not sessions:
        st.caption("아직 저장된 상담이 없습니다.")
        return

    st.markdown(
        """
        <style>
        div.stButton > button {
            width: 100%;
            text-align: left;
            justify-content: flex-start;
            white-space: pre-line;
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 0.92rem;
        }
        div.stButton > button[kind="primary"] {
            background-color: #2d5a27 !important;
            border-color: #2d5a27 !important;
            color: white !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #336b33 !important;
            border-color: #336b33 !important;
            color: white !important;
        }
        div.stButton > button {
            width: 100%;
            text-align: left;
            justify-content: flex-start;
            white-space: pre-line;   /* \\n 줄바꿈 */
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    current_id = current_session_file or st.session_state.get("session_file")

    for s in sessions:
        is_active = s["filepath"] == current_id

        title = s.get("title", "제목 없음")
        # created_at = s.get("created_at", "")
        # msg_count = s.get("message_count", 0)

        label = f"{title}\n"

        # 🔹 활성 세션: primary 버튼 → 자동으로 다른 색/스타일 적용
        # 🔹 비활성 세션: secondary 버튼
        if is_active:
            clicked = st.button(
                label,
                key=f"session_select_{s['filepath']}",
                use_container_width=True,
                type="primary",  # ✅ 현재 세션 강조
            )
        else:
            clicked = st.button(
                label,
                key=f"session_select_{s['filepath']}",
                use_container_width=True,
                type="secondary",  # 기본 스타일
            )

        if clicked:
            st.session_state["session_file"] = s["filepath"]
            st.rerun()


def render_sidebar(current_session_file: str | None = None):
    with st.sidebar:
        st.markdown(
            """
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:8px 4px 16px 4px;
            ">
                <div style="
                    width:34px;
                    height:34px;
                    border-radius:50%;
                    background:linear-gradient(135deg, #16a085, #2ecc71);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:20px;
                ">🤖</div>
                <div style="display:flex; flex-direction:column;">
                    <span style="font-weight:700; font-size:16px;">집사부 에이전트</span>
                    <span style="font-size:11px; color:#888;">
                        부린이를 위한 부동산 상담
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 🔄 새 상담 시작 버튼
        new_session_btn = st.button("새 상담 시작하기", use_container_width=True)
        if new_session_btn:
            # 메모리 대화 초기화
            st.session_state["session"] = []
            # 다음 발화부터 새 파일을 만들도록 기존 session_file 제거
            st.session_state.pop("session_file", None)
            st.rerun()

        st.divider()

        # 💬 로그 폴더 기준 대화 세션 목록
        _render_session_list(current_session_file)

        st.divider()

        # 📚 지식 베이스 상태
        st.markdown("#### 📚 지식 베이스 상태")
        if "index" in st.session_state and st.session_state.get("chunks"):
            num_chunks = len(st.session_state["chunks"])
            st.markdown(f"- 사전 임베딩 문서 청크 수: **{num_chunks}**개")
            st.caption("사전 로드된 부동산 자료를 기반으로 답변을 보완합니다.")
        else:
            st.markdown("- 사전 임베딩 문서가 아직 준비되지 않았습니다.")
            st.caption("앱이 시작되면 자동으로 문서를 불러옵니다.")

        st.divider()

        # ℹ️ 에이전트 안내
        with st.expander("ℹ️ 에이전트 안내", expanded=True):
            st.markdown(
                """
                - 기본적으로 **개념 설명·상담** 위주로 도와드립니다.
                - 법령·세법·규제 등은 최대한 정확히 설명하지만,
                  **최종 의사결정 전에는 전문가 상담**을 권장드립니다.
                """
            )

        st.markdown(
            """
            <div style="margin-top:24px; font-size:11px; color:#888;">
                ⚖️ 법률·세무 자문이 아닌,
                정보 제공용 AI 상담입니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
