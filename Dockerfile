# syntax=docker/dockerfile:1

# ---- Base build stage ----
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.2
WORKDIR /app

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy pyproject and lock file
COPY pyproject.toml poetry.lock* ./

# Install dependencies in a virtualenv inside /venv
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy actual source code
COPY src ./src

# ---- Final image stage ----
FROM python:3.11-slim

WORKDIR /app

# Copy only what we need from build stage
COPY --from=builder /app /app

# Optional: system dependencies for pypandoc (may depend on your OS)
RUN apt-get update && \
    apt-get install -y pandoc texlive-xetex && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set default command
CMD ["python", "src/remarkable_ai/main.py"]
