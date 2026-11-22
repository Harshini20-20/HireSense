FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HIRESENSE_DATABASE_URL=sqlite:////app/backend/hiresense.db \
    HIRESENSE_RESUME_STORAGE=/app/backend/storage/resumes \
    HF_HOME=/home/hiresense/.cache/huggingface

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin hiresense \
    && mkdir -p /app/backend/storage/resumes /home/hiresense/.cache/huggingface \
    && chown -R hiresense:hiresense /app/backend/storage /home/hiresense/.cache

COPY --chown=hiresense:hiresense backend ./backend

USER hiresense
EXPOSE 8001

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
