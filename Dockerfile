FROM python:3.14.5-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends --yes make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock requirements-dev.lock ./
RUN python -m pip install --no-cache-dir --requirement requirements-dev.lock

COPY pyproject.toml Makefile README.md LICENSE .env.example ./
COPY src ./src
COPY tests ./tests
COPY docs ./docs
COPY extensions ./extensions

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "sunny_devfix.app:app", "--host", "0.0.0.0", "--port", "8000"]
