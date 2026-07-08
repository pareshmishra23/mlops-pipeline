# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /build

COPY app/requirements.txt .

# Install dependencies in a local user directory to separate build from runtime environment
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production image
FROM python:3.10-slim AS runner

WORKDIR /app

# Setup secure non-root user
RUN groupadd -g 999 appuser && \
    useradd -r -u 999 -g appuser -d /home/appuser -m appuser

# Copy installed libraries from the builder stage
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ /app/app/

# Setup runtime environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Adjust permissions
RUN chown -R appuser:appuser /app /home/appuser

# Switch to non-root user for security
USER appuser

# Expose the API port
EXPOSE 8080

# Start Uvicorn server
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
