FROM python:3.13-slim

WORKDIR /project

COPY requirements.txt ngrok_tunnel.py .

# 1. Python 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 2. ngrok 설치에 필요한 도구 설치
RUN apt-get update \
    && apt-get install -y wget unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 3. ngrok 다운로드 & 설치 (동작하는 URL 사용)
#   - 공식 문서 기준: ngrok-v3-stable-linux-amd64.tgz 사용
ENV NGROK_VERSION=v3-stable
ENV NGROK_ARCH=linux-amd64
ENV NGROK_BASE_URL="https://bin.equinox.io/c/bNyj1mQVY4c"

RUN wget "${NGROK_BASE_URL}/ngrok-${NGROK_VERSION}-${NGROK_ARCH}.tgz" -O /tmp/ngrok.tgz \
    && tar xvzf /tmp/ngrok.tgz -C /usr/local/bin \
    && rm /tmp/ngrok.tgz \
    && chmod +x /usr/local/bin/ngrok

# 앱 코드 복사
COPY . .

# 기본 실행 명령 (ngrok_tunnel.py 실행)
CMD ["python", "ngrok_tunnel.py"]
