import os
import sys
import subprocess
import time
from pyngrok import ngrok, conf

# Dockerfile에서 설치한 ngrok 경로 (일반적인 리눅스 경로)
# 만약 경로에 없으면 pyngrok가 PATH에서 찾도록 설정합니다.
NGROK_BINARY_PATH = "/usr/local/bin/ngrok"

if os.path.exists(NGROK_BINARY_PATH):
    pyngrok_config = conf.get_default()
    pyngrok_config.ngrok_path = NGROK_BINARY_PATH
else:
    print(
        f"⚠️ 경고: {NGROK_BINARY_PATH}에서 ngrok을 찾을 수 없습니다. 시스템 PATH를 사용합니다."
    )


def start_streamlit():
    print("🚀 Streamlit 앱을 백그라운드에서 실행합니다...")

    # [수정 포인트] 파일 경로를 'app/app.py'로 변경했습니다.
    # WORKDIR가 /project이므로, app 폴더 안의 app.py를 지정해야 합니다.
    script_path = os.path.join("project", "main.py")

    if not os.path.exists(script_path):
        print(f"❌ 오류: 실행할 파일을 찾을 수 없습니다: {script_path}")
        print(f"현재 위치: {os.getcwd()}")
        print(f"파일 목록: {os.listdir('.')}")
        sys.exit(1)

    cmd = [
        "streamlit",
        "run",
        script_path,  # app/app.py
        "--server.port",
        "8501",
        "--server.address",
        "0.0.0.0",  # 도커 외부 접속 허용
        "--server.headless",
        "true",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=sys.stdout,  # 도커 로그로 바로 출력
        stderr=sys.stderr,
        text=True,
    )
    print(f"✅ Streamlit 실행 중 (PID: {process.pid})")
    return process


def start_ngrok_tunnel():
    print("🔗 ngrok 터널을 시작합니다...")

    # 환경 변수 체크 (docker-compose에서 주입됨)
    authtoken = os.environ.get("NGROK_AUTH_TOKEN")
    if not authtoken:
        print("❌ 오류: NGROK_AUTH_TOKEN 환경 변수가 없습니다.")
        print(
            "👉 .env 파일을 확인하거나 docker-compose.yml의 env_file 설정을 확인하세요."
        )
        sys.exit(1)

    try:
        # 기존 세션 정리
        ngrok.kill()

        # 토큰 설정
        ngrok.set_auth_token(authtoken)

        # 터널 생성 (포트 8501)
        tunnel = ngrok.connect("8501")
        public_url = tunnel.public_url

        print("\n" + "=" * 60)
        print(f"🌐  앱 접속 주소 (Public URL): {public_url}")
        print("=" * 60 + "\n")

        return public_url
    except Exception as e:
        print(f"❌ ngrok 연결 오류: {e}")
        # ngrok 오류는 치명적이므로 프로세스 종료
        sys.exit(1)


if __name__ == "__main__":
    # 1. Streamlit 시작
    streamlit_process = start_streamlit()

    # Streamlit이 완전히 뜰 때까지 잠시 대기 (안정성)
    time.sleep(3)

    # 2. ngrok 시작
    start_ngrok_tunnel()

    try:
        # 프로세스 모니터링
        print("👀 프로세스 모니터링 중... (종료하려면 Ctrl+C)")
        while True:
            time.sleep(2)
            # Streamlit이 죽었는지 확인
            if streamlit_process.poll() is not None:
                print("⚠️ 경고: Streamlit 프로세스가 예상치 못하게 종료되었습니다.")
                sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 컨테이너를 종료합니다.")
    finally:
        print("🧹 리소스 정리 중...")
        ngrok.kill()
        if "streamlit_process" in locals() and streamlit_process.poll() is None:
            streamlit_process.terminate()
