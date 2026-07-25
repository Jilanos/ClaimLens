FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

RUN addgroup --system --gid 10001 claimlens \
    && adduser --system --uid 10001 --gid 10001 --no-create-home claimlens \
    && mkdir -p /data \
    && chown -R claimlens:claimlens /app /data

USER claimlens

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"

EXPOSE 8765

CMD ["claimlens", "serve", "--host", "0.0.0.0", "--port", "8765"]
