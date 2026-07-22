# ---------- Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY app/requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Runtime ----------
FROM python:3.11-slim

WORKDIR /app

RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser -d /home/appuser -m appuser

COPY --from=builder /install /usr/local
COPY app/ /app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]