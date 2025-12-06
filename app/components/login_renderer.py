from datetime import datetime, timedelta
import streamlit as st
import re


def render_login(cookie_manager):
    # 이미 로그인된 경우 중단
    if st.session_state.get("logged_in"):
        return

    st.markdown(
        """
        <style>
            /* 전체 배경 및 폰트 조정 (선택사항) */
            .stApp {
                background-color: #f8f9fa;
            }
            
            /* 로그인 카드 컨테이너 스타일 */
            .login-container {
                background-color: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.08);
                text-align: center;
                border-top: 5px solid #2d5a27; /* 상단 포인트 컬러 */
            }
            
            /* 제목 스타일 */
            .login-title {
                color: #2d5a27;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            
            /* 설명 텍스트 */
            .login-desc {
                color: #6c757d;
                font-size: 14px;
                margin-bottom: 30px;
            }

            /* 로그인 버튼 스타일 커스터마이징 (Streamlit 기본 버튼 덮어쓰기) */
            div[data-testid="stFormSubmitButton"] > button {
                background-color: #2d5a27 !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 10px 20px !important;
                font-weight: bold !important;
                transition: all 0.3s ease !important;
            }
            
            /* 버튼 호버 효과 */
            div[data-testid="stFormSubmitButton"] > button:hover {
                background-color: #1e3d1b !important; /* 좀 더 진한 녹색 */
                box-shadow: 0 4px 10px rgba(45, 90, 39, 0.3) !important;
                transform: translateY(-2px);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown(
            """
            <div class="login-container">
                <div class="login-title">집사부 Login</div>
                <div class="login-desc">집사부에 오신 것을 환영합니다.<br>로그인해 주세요.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 폼 내부 디자인
        with st.form("login_form", clear_on_submit=False):
            # 아이콘 느낌을 위해 이모지 사용 가능
            st.markdown("###### 👤 아이디")
            user_id = st.text_input(
                "아이디",
                placeholder="영문, 숫자만 입력",
                key="login_user_id",
                label_visibility="collapsed",  # 라벨 숨김 (위의 마크다운으로 대체)
            )

            st.markdown("###### 🔒 비밀번호")
            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="••••••••",
                key="login_password",
                label_visibility="collapsed",
            )

            st.markdown(
                "<div style='height: 10px'></div>", unsafe_allow_html=True
            )  # 간격

            remember = st.checkbox("로그인 상태 유지", value=False)

            st.markdown(
                "<div style='height: 15px'></div>", unsafe_allow_html=True
            )  # 간격

            # 버튼 (CSS로 디자인됨)
            submitted = st.form_submit_button(
                "로그인 시작하기", use_container_width=True
            )

            if submitted:
                # --- 유효성 검사 (Validation) ---
                if not user_id or not password:
                    st.error("⚠️ 아이디와 비밀번호를 모두 입력해 주세요.")

                # 정규표현식: ^(시작) [a-zA-Z0-9] (영문대소문자+숫자) + (1개 이상) $(끝)
                elif not re.match(r"^[a-zA-Z0-9]+$", user_id):
                    st.error(
                        "⚠️ 아이디는 영문과 숫자만 사용할 수 있습니다 (특수문자 불가)."
                    )

                elif not re.match(r"^[a-zA-Z0-9]+$", password):
                    st.error("⚠️ 비밀번호는 영문과 숫자만 사용할 수 있습니다.")

                else:
                    # 검사 통과 시 로그인 처리
                    st.session_state["user_id"] = user_id
                    st.session_state["logged_in"] = True
                    if remember:
                        st.session_state["remember"] = True
                        # expires_at을 설정하여 30일 뒤 만료되게 설정
                        expires = datetime.now() + timedelta(days=30)
                        cookie_manager.set("files_user_id", user_id, expires_at=expires)

                    st.success(f"✅ 환영합니다, {user_id}님!")
                    st.rerun()
