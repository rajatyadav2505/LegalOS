# Style Pack Fidelity Eval

## Goal

Ensure style packs change drafting tone and framing without breaking provenance or structure.

## Checks

- Style pack creation stores opening phrase, prayer style, and derived voice notes.
- A later draft version reflects the selected style pack in at least one section body.
- The draft remains structured and continues to use verified-authority insertion only.

## Pass / Fail

- Pass if a styled draft differs from the base version in predictable, traceable text and still preserves authority and placeholder rails.
- Fail if styling bypasses structured sections or causes unsupported authority insertion.

## Fixtures

- `tests/fixtures/sample_matter/petition_note.txt`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
