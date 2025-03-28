# syntax=docker/dockerfile:1

# ---- Base build stage ----
FROM python:3.12-slim AS builder


# Optional: system dependencies for pypandoc (may depend on your OS)
RUN apt-get update && \
    apt-get install -y pandoc texlive-xetex && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


ENV POETRY_VERSION=2.1.1
WORKDIR /app

# Install Poetry
RUN pip install "poetry==2.1.1"

# Copy pyproject and lock file
COPY ./ ./

# Install dependencies in a virtualenv inside /venv
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi


# Set default command
CMD ["python", "src/remarkable_ai/main.py"]
