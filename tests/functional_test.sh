#!/usr/bin/env bash
set -euo pipefail

APP_URL="${APP_URL:-http://localhost:8000}"

health_json="$(curl -fsS "${APP_URL}/health")"
health_status="$(echo "${health_json}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"

if [[ "${health_status}" != "ok" ]]; then
  echo "Functional test failed: health endpoint did not return ok"
  exit 1
fi

first="$(curl -fsS -X POST "${APP_URL}/visits")"
second="$(curl -fsS -X POST "${APP_URL}/visits")"

first_total="$(echo "${first}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["total_visits"])')"
second_total="$(echo "${second}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["total_visits"])')"

if [[ "${second_total}" -le "${first_total}" ]]; then
  echo "Functional test failed: total visits did not increase"
  exit 1
fi

created_product="$(curl -fsS -X POST "${APP_URL}/products" \
  -H "Content-Type: application/json" \
  -d '{"name":"Apple","calories":52,"proteins":0.3,"fats":0.2,"carbs":14}')"

created_name="$(echo "${created_product}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])')"
if [[ "${created_name}" != "Apple" ]]; then
  echo "Functional test failed: product was not created correctly"
  exit 1
fi

products="$(curl -fsS "${APP_URL}/products")"
products_count="$(echo "${products}" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
if [[ "${products_count}" -lt 1 ]]; then
  echo "Functional test failed: products list is empty"
  exit 1
fi

echo "Functional test passed"
