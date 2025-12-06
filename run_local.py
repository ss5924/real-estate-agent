import os
import sys
import subprocess
import time
from pyngrok import ngrok
from dotenv import load_dotenv
from app.src.config import ENV_PATH, APP_DIR, SESSION_DIR


print("🔄 환경 설정 로드 중...")
print(f"📁 앱 디렉토리: {APP_DIR}")
print(f"📁 세션 디렉토리: {SESSION_DIR}")


if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print(f"📄 .env 파일을 로드했습니다: {ENV_PATH}")
else:
    print(f"⚠️ 경고: {ENV_PATH} 경로에서 .env 파일을 찾을 수 없습니다.")


def start_streamlit():
    print("🚀 Streamlit 앱을 실행합니다...")

    log_file = open("server_logs.txt", "w", encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "main.py",
        "--server.port",
        "8501",
        "--server.address",
        "localhost",
        "--server.headless",
        "true",
    ]

    process = subprocess.Popen(
        cmd,
        cwd=APP_DIR,
        stdout=None,  # log_file,
        stderr=None,  # log_file,
        text=True,
    )
    print(f"✅ Streamlit 백그라운드 실행 중 (PID: {process.pid})")
    return process


def start_ngrok_tunnel():
    print("🔗 ngrok 터널을 시작합니다...")

    authtoken = os.environ.get("NGROK_AUTH_TOKEN")

    if not authtoken:
        print("❌ 오류: 'NGROK_AUTH_TOKEN'을 찾을 수 없습니다.")
        print(f"👉 {ENV_PATH} 파일 안에 토큰이 올바르게 들어있는지 확인해주세요.")
        sys.exit(1)

    try:
        ngrok.set_auth_token(authtoken)
        ngrok.kill()  # 기존 좀비 프로세스 정리

        tunnel = ngrok.connect("8501")
        public_url = tunnel.public_url

        print("-" * 60)
        print(f"🌐 외부 접속 주소: {public_url}")
        print(f"🏠 로컬 접속 주소: http://localhost:8501")
        print("-" * 60)
        return public_url

    except Exception as e:
        print(f"❌ ngrok 연결 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # main.py 존재 확인
    if not os.path.exists(APP_DIR + "/main.py"):
        print(f"❌ 오류: {APP_DIR} 폴더 안에 'main.py'가 없습니다.")
        sys.exit(1)

    streamlit_process = start_streamlit()

    # Streamlit이 켜질 때까지 잠시 대기
    time.sleep(3)

    start_ngrok_tunnel()

    try:
        print("\n✋ 실행을 멈추려면 Ctrl+C를 누르세요.")
        while True:
            time.sleep(1)
            # 프로세스가 죽었는지 체크
            if streamlit_process.poll() is not None:
                print("⚠️ Streamlit 프로세스가 종료되었습니다.")
                _, stderr = streamlit_process.communicate()
                print("--- 에러 로그 ---")
                print(stderr)
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 종료합니다.")
    finally:
        ngrok.kill()
        if "streamlit_process" in locals() and streamlit_process.poll() is None:
            streamlit_process.terminate()
