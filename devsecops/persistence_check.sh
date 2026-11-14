#!/usr/bin/env bash
# Proves the SQLite DB survives container recreation (compose volume acolhe-data).
# Usage (repo root, Linux/WSL2 + Docker): bash devsecops/persistence_check.sh
set -euo pipefail
cd "$(dirname "$0")/.."
api(){ curl -fsS "http://127.0.0.1:8080$1" "${@:2}"; }
wait_up(){ for i in $(seq 1 40); do api /api/health >/dev/null 2>&1 && return 0; sleep 1; done; echo "app did not start"; exit 1; }
summary(){ api /api/summary | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"sessions={d['sessions']} attempts={d['attempts']}\")"; }

echo "== 1. fresh stack (app + prometheus)"
docker compose --profile monitoring down -v >/dev/null 2>&1 || true
docker compose --profile monitoring up -d --build --quiet-pull 2>&1 | tail -2
wait_up; echo "before: $(summary)"
sid=$(api /api/sessions -H 'Content-Type: application/json' -d '{"language":"es"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
api /api/attempts -H 'Content-Type: application/json' -d "{\"session_id\":\"$sid\",\"lesson_id\":\"casa\",\"option\":0,\"request_id\":\"persist-1\"}" >/dev/null
echo "after answer: $(summary)"
echo "== 2. destroy and recreate containers (volume kept)"
docker compose --profile monitoring down 2>&1 | tail -1
docker compose --profile monitoring up -d 2>&1 | tail -1
wait_up; echo "after recreate: $(summary)"
echo "container id: $(docker compose ps -q app | cut -c1-12)  volume: $(docker volume ls -q | grep acolhe-data)"
echo "read-only rootfs: $(docker inspect -f '{{.HostConfig.ReadonlyRootfs}}' "$(docker compose ps -q app)")  user: $(docker compose exec -T app id -u)"
echo "== 3. prometheus target"
sleep 20
curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22acolhe%22%7D' | python3 -c "import json,sys; r=json.load(sys.stdin)['data']['result']; print('up{job=acolhe} =', r[0]['value'][1] if r else 'no data')"
