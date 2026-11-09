FROM python:3.12-slim
# Apply available distribution security fixes before creating the runtime user.
# The CI vulnerability gate remains strict, including findings without a fix.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8080 ACOLHE_DB=/tmp/acolhe.db
WORKDIR /srv/acolhe
RUN groupadd --gid 10001 acolhe && useradd --uid 10001 --gid acolhe --no-create-home acolhe
COPY --chown=acolhe:acolhe app ./app
COPY --chown=acolhe:acolhe robot ./robot
COPY --chown=acolhe:acolhe genai ./genai
COPY --chown=acolhe:acolhe vision ./vision
COPY --chown=acolhe:acolhe rpa ./rpa
COPY --chown=acolhe:acolhe big_data/output/summary.json ./big_data/output/summary.json
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=2)" || exit 1
CMD ["python", "-m", "app.server"]

