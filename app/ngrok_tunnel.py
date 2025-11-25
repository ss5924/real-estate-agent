from pyngrok import ngrok
from pyngrok import conf
import subprocess
import time
import os
import sys

NGROK_BINARY_PATH = "/usr/local/bin/ngrok"

pyngrok_config = conf.get_default()
pyngrok_config.ngrok_path = NGROK_BINARY_PATH


def start_streamlit():
    print("Streamlit 앱 실행합니다.")
    process = subprocess.Popen(
        [
            "streamlit",
            "run",
            "app.py",
            "--server.port",
            "8501",
            "--server.address",
            "0.0.0.0",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
    )
    print(f"Streamlit 백그라운드 실행 중 (PID: {process.pid})")
    return process


def start_ngrok_tunnel():
    print("ngrok 터널을 시작합니다...")

    if not os.path.exists(NGROK_BINARY_PATH):
        print(f"오류: ngrok 실행 파일을 찾을 수 없습니다: {NGROK_BINARY_PATH}")
        sys.exit(1)

    try:
        ngrok.kill()

        if "NGROK_AUTH_TOKEN" not in os.environ:
            print(
                "NGROK_AUTH_TOKEN 환경 변수가 설정되지 않았습니다. ERR_NGROK_4018 오류가 발생합니다."
            )
            sys.exit(1)

        authtoken = os.environ.get("NGROK_AUTH_TOKEN")
        ngrok.set_auth_token(authtoken)

        tunnel = ngrok.connect(8501)
        public_url = tunnel.public_url
        print("-" * 50)
        print(f"🌐 앱 접속 주소: {public_url}")
        print("-" * 50)
        return public_url
    except Exception as e:
        print(f"❌ ngrok 연결 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Streamlit 시작
    streamlit_process = start_streamlit()

    # ngrok 시작
    start_ngrok_tunnel()

    try:
        # 프로세스가 종료되지 않도록 무한 대기
        while True:
            time.sleep(1)
            if streamlit_process.poll() is not None:
                print("Streamlit 프로세스가 종료되었습니다. 컨테이너를 종료합니다.")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\n사용자 요청으로 종료합니다.")
    finally:
        ngrok.kill()
        if "streamlit_process" in locals() and streamlit_process.poll() is None:
            streamlit_process.terminate()
        print("clean up.")
