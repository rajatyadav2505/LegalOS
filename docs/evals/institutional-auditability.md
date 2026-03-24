# Institutional Auditability Eval

## Goal

Ensure institutional mode persists approvals and exposes the relevant audit trail.

## Checks

- Approval requests can be created for draft documents.
- Approval reviews transition state from `pending` to `approved` or `rejected`.
- Dashboard audit events include approval request and review actions.
- Pending approval counts update after review.

## Pass / Fail

- Pass if approval creation, review, and audit visibility all succeed from the matter dashboard.
- Fail if audit events are missing or approval state does not reconcile with the dashboard summary.

## Fixtures

- `tests/integration/test_workflow_phases.py`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
