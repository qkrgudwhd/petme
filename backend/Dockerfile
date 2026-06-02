# PetMe-Moji Backend — FastAPI + rembg + Pillow
# Render free tier (512MB RAM)에 충분히 들어가도록 slim 베이스 사용

FROM python:3.12-slim

# rembg ONNX 런타임이 필요로 하는 시스템 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
        fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# rembg 모델을 미리 다운로드 (첫 호출 지연 방지)
RUN python -c "from rembg import new_session; new_session('u2net')"

COPY app ./app
# 한글 합성용 NanumGothic을 Windows 폰트 대신 fallback로 추가
COPY app ./app
RUN mkdir -p app/storage/uploads app/storage/outputs

# Render는 PORT 환경변수를 주입함
ENV PORT=8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
