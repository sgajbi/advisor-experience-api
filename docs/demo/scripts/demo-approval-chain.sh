#!/usr/bin/env bash
set -euo pipefail

BFF_BASE_URL="${BFF_BASE_URL:-http://127.0.0.1:8100}"
IDEM="demo-bff-approval-chain-1"

create_response=$(curl -sS -X POST "${BFF_BASE_URL}/api/v1/proposals" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: ${IDEM}" \
  --data @docs/demo/payloads/proposal-create.json)

proposal_id=$(printf '%s' "$create_response" | python -c "import json,sys; print(json.load(sys.stdin)['data']['proposal']['proposal_id'])")

echo "proposal_id=${proposal_id}"

curl -sS -X POST "${BFF_BASE_URL}/api/v1/proposals/${proposal_id}/submit" \
  -H "Content-Type: application/json" \
  -d '{"actor_id":"advisor_demo_1","expected_state":"DRAFT","review_type":"RISK"}' >/dev/null

curl -sS -X POST "${BFF_BASE_URL}/api/v1/proposals/${proposal_id}/approve-risk" \
  -H "Content-Type: application/json" \
  -d '{"actor_id":"risk_demo_1","expected_state":"RISK_REVIEW","details":{"comment":"approved"}}' >/dev/null

curl -sS -X POST "${BFF_BASE_URL}/api/v1/proposals/${proposal_id}/record-client-consent" \
  -H "Content-Type: application/json" \
  -d '{"actor_id":"advisor_demo_1","expected_state":"AWAITING_CLIENT_CONSENT","details":{"channel":"IN_PERSON"}}' >/dev/null

echo "workflow events:"
curl -sS "${BFF_BASE_URL}/api/v1/proposals/${proposal_id}/workflow-events"

echo "approvals:"
curl -sS "${BFF_BASE_URL}/api/v1/proposals/${proposal_id}/approvals"

echo
echo "demo completed"
