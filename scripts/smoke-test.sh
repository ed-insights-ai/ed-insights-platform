#!/usr/bin/env bash
set -euo pipefail

# Smoke test for Ed Insights Platform
# Checks that web, API, and data endpoints are responding correctly.

GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

pass=0
fail=0

check() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    printf "${GREEN}PASS${RESET}  %s\n" "$name"
    ((pass++))
  else
    printf "${RED}FAIL${RESET}  %s\n" "$name"
    ((fail++))
  fi
}

# 1. Web frontend returns HTTP 200
check "localhost:3000 returns HTTP 200" \
  curl -sf -o /dev/null http://localhost:3000

# 2. API health endpoint returns {"status":"ok"}
check "localhost:8000/health returns {status:ok}" \
  bash -c 'curl -sf http://localhost:8000/health | grep -q "\"status\":\"ok\""'

# 3. Schools endpoint returns a non-empty JSON array
check "localhost:8000/api/schools returns JSON array (length > 0)" \
  bash -c 'resp=$(curl -sf http://localhost:8000/api/schools) && echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d,list) and len(d)>0"'

echo ""
echo "Results: ${pass} passed, ${fail} failed"
[ "$fail" -eq 0 ] || exit 1
