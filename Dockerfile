FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STORYAGENTS_RESULTS_DIR=/app/stories

WORKDIR /app

COPY pyproject.toml README.md ./
COPY storyagents ./storyagents

RUN pip install --no-cache-dir .

RUN mkdir -p /app/stories

EXPOSE 8000

CMD ["storyagents", "serve", "--host", "0.0.0.0", "--port", "8000", "--mode", "standard"]
