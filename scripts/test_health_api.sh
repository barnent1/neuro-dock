#!/bin/bash
# Test Health/Utility API endpoints
API_URL="http://localhost:4000"
PASS=0
FAIL=0

echo "[TEST] GET /health"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/health")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /api/tools (REST tool discovery)"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/api/tools")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
