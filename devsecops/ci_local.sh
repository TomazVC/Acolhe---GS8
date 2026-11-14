#!/usr/bin/env bash
# Mirror of .github/workflows/devsecops.yml "test-and-build" job, same tool images/versions.
# Usage (Linux/WSL2 with Docker, repo root): bash devsecops/ci_local.sh
# Note: gitleaks runs in "dir" mode when there is no .git history (e.g. zip checkout).
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=acolhe:local
step(){ printf '\n=== %s ===\n' "$*"; }

step "Python tests (host)";     python3 -B -m unittest discover 2>&1 | tail -3
step "Gitleaks 8.24.2"
if [ -d .git ]; then mode="detect --source=/repo"; else mode="dir /repo"; fi
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:v8.24.2 $mode --no-banner --redact --exit-code=1
step "Semgrep 1.111.0"
docker run --rm -v "$PWD:/src" semgrep/semgrep:1.111.0 semgrep scan --config /src/devsecops/semgrep.yml --error --metrics=off --quiet /src/app /src/robot /src/rpa /src/big_data
step "Build image";              docker build -q --pull -t "$TAG" .
step "Tests inside runtime image"
docker run --rm -v "$PWD:/source:ro" -w /source "$TAG" python -B -m unittest discover 2>&1 | tail -3
step "Smoke HTTP + SQLite + non-root"
docker rm -f acolhe-runtime-test >/dev/null 2>&1 || true
docker run -d --name acolhe-runtime-test -p 127.0.0.1:18080:8080 "$TAG" >/dev/null
trap 'docker rm -f acolhe-runtime-test >/dev/null 2>&1 || true' EXIT
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:18080/api/health >/dev/null 2>&1 && break; sleep 1; done
for p in / /logo.png /api/lessons /api/summary /api/gold /metrics; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:18080$p"); echo "GET $p -> $code"; [ "$code" = 200 ]
done
docker exec acolhe-runtime-test python -c "import os,sqlite3; assert os.getuid()==10001; c=sqlite3.connect('/data/smoke.db'); c.execute('CREATE TABLE s(i)'); c.execute('INSERT INTO s VALUES(1)'); c.commit(); print('uid', os.getuid(), 'sqlite on /data ok')"
echo "healthcheck: $(docker inspect -f '{{.State.Health.Status}}' acolhe-runtime-test 2>/dev/null || echo n/a)"
step "Trivy 0.60.0 image (HIGH,CRITICAL blocks)"
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.60.0 image --quiet --exit-code 1 --severity HIGH,CRITICAL "$TAG"
step "Trivy 0.60.0 IaC (HIGH,CRITICAL blocks)"
docker run --rm -v "$PWD:/src" aquasec/trivy:0.60.0 config --quiet --exit-code 1 --severity HIGH,CRITICAL --skip-files /src/devsecops/Dockerfile.candidate /src
step "ALL GATES PASSED"
