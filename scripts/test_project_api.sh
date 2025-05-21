#!/bin/bash
# Test Project API endpoints
API_URL="http://localhost:4000/api"
PASS=0
FAIL=0

echo "[TEST] GET /api/projects"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/projects")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

PROJ_NAME="Project test $(date +%s)"
echo "[TEST] POST /api/projects"
resp=$(curl -s -w "\n%{http_code}" -H "Content-Type: application/json" -d '{"name": "'$PROJ_NAME'", "description": "Test project"}' "$API_URL/projects")
code=$(echo "$resp" | tail -n1)
proj_id=$(echo "$resp" | grep -o '"id": *"[^"]*"' | head -1 | cut -d '"' -f4)
if [[ "$code" == "200" && -n "$proj_id" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] GET /api/projects/$proj_id"
resp=$(curl -s -w "\n%{http_code}" "$API_URL/projects/$proj_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "[TEST] DELETE /api/projects/$proj_id"
resp=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/projects/$proj_id")
code=$(echo "$resp" | tail -n1)
if [[ "$code" == "200" ]]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi

echo "Tests passed: $PASS"
echo "Tests failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then exit 0; else exit 1; fi
