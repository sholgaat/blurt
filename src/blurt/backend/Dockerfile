FROM python:3.12-slim

ARG APP_VERSION=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY . .
# setuptools-scm needs git history to infer the version, which isn't available
# in the build context. Provide it explicitly; strip leading 'v' (v1.2.3 → 1.2.3).
# Local dev builds pass APP_VERSION=0.0.0.dev0 via docker-compose.override.yml.
RUN SETUPTOOLS_SCM_PRETEND_VERSION="${APP_VERSION#v}" \
    pip install --no-cache-dir .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn ${UVICORN_APP:-blurt.backend.main:app} --host 0.0.0.0 --port 8000"]
