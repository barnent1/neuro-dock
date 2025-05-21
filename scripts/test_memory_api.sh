#!/bin/bash
# Test Memory API endpoints
API_URL="http://localhost:4000/api"
PASS=0
FAIL=0

echo "[TEST] GET /api/memories"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/memories")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

MEM_CONTENT="Memory test $(date +%s)"
echo "[TEST] POST /api/memories"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"content": "'$MEM_CONTENT'", "type": "normal", "source": "test-script"}' "$API_URL/memories")
code=$(echo "$resp" | tail -n1)
mem_id=$(echo "$resp" | grep -o '"id": *"[^"]*"' | head -1 | cut -d '"' -f4)
if [[ "$code" == "200" && -n "$mem_id" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /api/memories/$mem_id"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/memories/$mem_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] DELETE /api/memories/$mem_id"
resp=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/memories/$mem_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
