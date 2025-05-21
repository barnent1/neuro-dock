#!/bin/bash
# Test Context/Knowledge Graph API endpoints
API_URL="http://localhost:4000/api"
PASS=0
FAIL=0

echo "[TEST] POST /api/context (query context)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"query": "test", "max_memories": 3}' "$API_URL/context")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] POST /api/memory/search-nodes (search nodes)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"query": "test"}' "$API_URL/memory/search-nodes")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] POST /api/memory/episode (add episode)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"content": "Episode test", "type": "episode", "source": "test-script"}' "$API_URL/memory/episode")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
