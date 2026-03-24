# Low-Bandwidth Brief Eval

## Goal

Ensure institutional mode exposes a concise brief that remains usable under constrained connectivity.

## Checks

- Dashboard responses include `low_bandwidth_brief`.
- The brief contains urgency, pending approvals, best line, and fallback line.
- The UI can switch into low-bandwidth mode without needing a different API shape.

## Pass / Fail

- Pass if the dashboard returns a compact brief with actionable matter state.
- Fail if the brief is missing or omits the key institutional coordination fields.

## Fixtures

- `tests/integration/test_workflow_phases.py`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
