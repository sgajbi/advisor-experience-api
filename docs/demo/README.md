# Advisor Experience API Demo Pack

## Goal

Run a deterministic BFF demo for proposal creation plus approval-chain actions.

## Prerequisites

- DPM running at `http://127.0.0.1:8000`
- BFF running at `http://127.0.0.1:8100`

## Run

```bash
bash docs/demo/scripts/demo-approval-chain.sh
```

The script will:

1. Create proposal draft via BFF.
2. Submit for risk review.
3. Approve risk.
4. Record client consent.
5. Fetch workflow events and approvals.
