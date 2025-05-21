#!/bin/bash
# Test MCP API endpoints
API_URL="http://localhost:4000/neuro-dock"
PASS=0
FAIL=0

echo "[TEST] POST /neuro-dock/memory (store memory)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"content": "MCP memory test", "type": "normal", "source": "test-script"}' "$API_URL/memory")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] POST /neuro-dock/task (create task)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"title": "MCP task test", "description": "Test task", "priority": 2}' "$API_URL/task")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] POST /neuro-dock/context (query context)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"query": "test", "max_memories": 3}' "$API_URL/context")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] POST /neuro-dock/editor-context (editor context)"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"query": "test", "max_memories": 3}' "$API_URL/editor-context")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /neuro-dock/tools (tool discovery)"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/tools")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /neuro-dock/config (config)"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/config")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
