#!/bin/bash
# Test Task API endpoints
API_URL="http://localhost:4000/api"
PASS=0
FAIL=0

echo "[TEST] GET /api/tasks"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/tasks")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

TASK_TITLE="Task test $(date +%s)"
echo "[TEST] POST /api/tasks"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"title": "'$TASK_TITLE'", "description": "Test task", "priority": 2}' "$API_URL/tasks")
code=$(echo "$resp" | tail -n1)
task_id=$(echo "$resp" | grep -o '"id": *"[^"]*"' | head -1 | cut -d '"' -f4)
if [[ "$code" == "200" && -n "$task_id" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /api/tasks/$task_id"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/tasks/$task_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] DELETE /api/tasks/$task_id"
resp=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/tasks/$task_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
