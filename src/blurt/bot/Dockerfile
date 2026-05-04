FROM python:3.12-slim

ARG APP_VERSION=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

WORKDIR /app

COPY . .
# setuptools-scm needs git history to infer the version, which isn't available
# in the build context. Provide it explicitly; strip leading 'v' (v1.2.3 → 1.2.3).
# Local dev builds pass APP_VERSION=0.0.0.dev0 via docker-compose.override.yml.
RUN SETUPTOOLS_SCM_PRETEND_VERSION="${APP_VERSION#v}" \
    pip install --no-cache-dir .

RUN adduser --disabled-password --gecos "" appuser
USER appuser

CMD ["python", "-m", "blurt.bot.main"]
