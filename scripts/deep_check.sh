#!/usr/bin/env bash
set -euo pipefail
# deep_check.sh - 基础环境与功能检查脚本
# 生成基线报告，用于回归比对

OUTDIR="reports"
mkdir -p "$OUTDIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTFILE="$OUTDIR/deep_check_${TIMESTAMP}.txt"

echo "Deep check started at: $(date)" | tee "$OUTFILE"

echo "\n-- Docker containers --" | tee -a "$OUTFILE"
docker ps --format 'table {{.Names}}	{{.Image}}	{{.Status}}	{{.Ports}}' 2>/dev/null | tee -a "$OUTFILE" || true

echo "\n-- Ports (8000 backend, 5173 frontend) --" | tee -a "$OUTFILE"
ss -ltnp | grep -E ':(8000|5173)' || true | tee -a "$OUTFILE"

echo "\n-- Backend health check --" | tee -a "$OUTFILE"
curl -sS http://localhost:8000/health 2>/dev/null | jq . 2>/dev/null || curl -sS http://localhost:8000/health 2>/dev/null | tee -a "$OUTFILE" || echo "No backend response" | tee -a "$OUTFILE"

echo "\n-- Vite dev server check --" | tee -a "$OUTFILE"
if lsof -i :5173 >/dev/null 2>&1; then
  lsof -i :5173 | head -n 20 | tee -a "$OUTFILE"
else
  echo "No process listening on 5173" | tee -a "$OUTFILE"
fi

echo "\n-- Node modules check (frontend) --" | tee -a "$OUTFILE"
if [ -d frontend/node_modules ]; then
  du -sh frontend/node_modules 2>/dev/null | tee -a "$OUTFILE"
else
  echo "frontend node_modules not found" | tee -a "$OUTFILE"
fi

echo "\n-- Database tables quick check --" | tee -a "$OUTFILE"
if docker ps --format '{{.Names}}' | grep -q 'bidding_postgres'; then
  docker exec -it bidding_postgres psql -U postgres -d bidding_db -c "\dt" 2>/dev/null | tee -a "$OUTFILE" || true
else
  echo "Postgres container not detected; attempting psql locally" | tee -a "$OUTFILE"
  psql -c "\dt" 2>/dev/null | tee -a "$OUTFILE" || echo "psql not available or DB not reachable" | tee -a "$OUTFILE"
fi

echo "\n-- Test upload API (no file) --" | tee -a "$OUTFILE"
curl -sS -X POST "http://localhost:8000/api/files/upload" -F "files=@/dev/null" 2>/dev/null | tee -a "$OUTFILE" || echo "upload endpoint not responding or rejected empty upload" | tee -a "$OUTFILE"

echo "\n-- End of deep check: $(date)" | tee -a "$OUTFILE"

echo "Report saved to: $OUTFILE"

exit 0
