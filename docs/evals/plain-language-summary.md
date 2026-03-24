# Plain-Language Summary Eval

## Goal

Ensure institutional mode returns beneficiary-facing summaries in basic English and Hindi.

## Checks

- Dashboard responses include both `plain_language_en` and `plain_language_hi`.
- The summaries reflect current matter posture and the current best line.
- The response preserves decision-support framing and does not claim certainty of outcome.

## Pass / Fail

- Pass if both summaries are present, matter-aware, and framed as coordination support rather than guarantees.
- Fail if either language is missing or the text implies unjustified certainty.

## Fixtures

- `tests/integration/test_workflow_phases.py`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
