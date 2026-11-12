
FROM python:3.12-slim

# PYTHONUNBUFFERED=1 — логи выводятся сразу, без буферизации
# PYTHONDONTWRITEBYTECODE=1 — не создаются .pyc файлы
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --default-timeout=1000 --upgrade pip && \
    pip install --default-timeout=1000 --no-cache-dir .

COPY . .

# Создаём непривилегированного пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    mkdir -p /app/data && chown -R appuser:appuser /app

EXPOSE 8000

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]