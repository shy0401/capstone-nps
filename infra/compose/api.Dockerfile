FROM python:3.12.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/apps/api
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-noto-cjk libreoffice-impress && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN useradd --uid 10001 --create-home nps && mkdir -p /app/storage && chown -R nps:nps /app
USER 10001

ARG APP_GIT_SHA=UNKNOWN
ENV APP_GIT_SHA=$APP_GIT_SHA
