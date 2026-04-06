# Memory Grounding Eval

## Goal

Ensure litigant and case memory snapshots contain only source-backed assertions.

## Checks

- every non-trivial section includes source references
- markdown artifacts are consistent with snapshot-table state
- unsupported facts are rejected rather than silently synthesized
- recurring claims, defenses, and contradictions appear only when evidence exists
