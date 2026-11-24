# US Stock Research Agent

An LLM agent that answers US stock research questions from SEC filings, prices and news. Scope, skills and slice plan: [docs/ROADMAP.md](docs/ROADMAP.md).

## Workflow

Work advances in **tracer-bullet slices**: each slice is a thin end-to-end path that can be demoed on its own.

Per slice: `/grill-with-docs` → `/to-spec` → `/to-tickets` → slice branch (`slice-NN-<name>`) → `/implement` → `/code-review` → `/pr` → merge after CI is green → `/retro`.

The developer makes every design decision; present options with their trade-offs and implement the chosen one.

## Coaching

@.learning/COACHING.md

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
