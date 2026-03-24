# Draft Completeness Eval

## Goal

Ensure structured drafts contain the expected sections, visible unresolved placeholders, and verified-authority links.

## Checks

- Petition and list-of-dates generation return the configured section keys.
- Draft responses expose `authorities_used`, `annexures`, and `unresolved_placeholders`.
- Exported markdown preserves the generated title and section structure.
- Redlines compare versioned drafts without dropping section labels.

## Pass / Fail

- Pass if draft generation, export, and redline all succeed and unresolved placeholders remain visible where the record is incomplete.
- Fail if sections are missing, placeholders disappear silently, or authorities are inserted without saved research provenance.

## Fixtures

- `tests/fixtures/sample_matter/petition_note.txt`
- `tests/fixtures/sample_matter/public_law/*`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
