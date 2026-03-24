# Strategy Boundedness Eval

## Goal

Ensure the strategy engine stays within bounded scenario templates and remains clearly labeled as decision support.

## Checks

- Strategy workspace returns best, fallback, and risk lines with rationales.
- Issue cards expose attack, defense, bench questions, and rebuttal cards.
- Scenario branches are drawn from the versioned prompt asset rather than uncontrolled generation.
- The response carries a decision-support label.

## Pass / Fail

- Pass if the workspace is reproducible from the same record and every output is labeled as bounded decision support.
- Fail if the workflow emits open-ended swarm behavior or omits the decision-support labeling.

## Fixtures

- `packages/prompts/strategy/scenario_templates.json`
- `tests/fixtures/sample_matter/*`

## Verification

- `./.venv/bin/pytest tests/integration/test_workflow_phases.py -q`
