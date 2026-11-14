# Official Python image validated by the base evaluation workflow.
FROM python:3.12-alpine@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7
# Keep distribution security fixes current without weakening the CI gate.
RUN apk upgrade --no-cache
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8080 ACOLHE_DB=/data/acolhe.db
WORKDIR /srv/acolhe
# /data is the only writable application path; mount a volume there to persist.
RUN addgroup -g 10001 acolhe && adduser -D -H -u 10001 -G acolhe acolhe \
 && mkdir -p /data && chown 10001:10001 /data && chmod 0700 /data
VOLUME ["/data"]
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

