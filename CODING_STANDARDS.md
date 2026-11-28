# Coding Standards

Judgement calls a reviewer checks against the diff. Anything a tool can enforce belongs in ruff, the tests or CI instead.

## Comments

- Comment only the non-obvious *why*: a gotcha, a constraint, a deliberate deviation the code cannot show. A comment that restates the code is a finding.

## LLM-facing text

- MCP tool docstrings and `Field(description=...)` are prompts the LLM reads. Every tool and every parameter has one, written for a model that sees nothing else.

## Rules live in code

- Express rules through names, types, Pydantic validation and tests.
- Guard real invariants with explicit checks that raise, not `assert` (skipped under `python -O`).
- A rule that spans fields ("google-cloud: needs a key file") is visible in the types where it is used. A value typed `X | None` that the code treats as always present is a finding, even when a validator guarantees it.

## Failures

- Every failure a user can cause or meet (bad settings, bad key file, LLM or auth errors) ends in one readable `stock-agent: ...` line on stderr and a deliberate exit code: 2 for setup, 1 for a failed run. A traceback reaching the user is a finding.
- Error text quotes only what helps the user act: a variable name, a path, the provider's first message line. It never echoes a secret's value or a whole provider response body.

## Language

- Repo text (code, comments, docs, issues, PRs) is in English. Prompt examples that show the model a non-English answer are the exception.
