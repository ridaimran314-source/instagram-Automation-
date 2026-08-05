FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OUTPUT_DIR=/data/renders
ENV FONT_PATH=/usr/share/fonts/truetype/lora/Lora-Bold.ttf

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg fonts-liberation fonts-dejavu-core curl ca-certificates && \
    mkdir -p /usr/share/fonts/truetype/lora /usr/share/fonts/truetype/montserrat /data/renders && \
    curl -fsSL -o /usr/share/fonts/truetype/lora/Lora-Bold.ttf \
      "https://cdn.jsdelivr.net/fontsource/fonts/lora@latest/latin-700-normal.ttf" && \
    curl -fsSL -o /usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf \
      "https://cdn.jsdelivr.net/fontsource/fonts/montserrat@latest/latin-700-normal.ttf" && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY config.py render.py main.py ./

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
