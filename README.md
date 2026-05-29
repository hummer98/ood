# Orchestration-Oriented Development (OOD)

*English | [日本語](README.ja.md)*

**A document-driven orchestration plugin for Claude Code.** Author the plan in
`docs/`, run it with Agent Teams, gate completion on inspection. Flat two-tier
(lead + role teammates), no JSON state machine — *the documents are the state*.

> OOD treats orchestration as the unit of development: you decide intent and
> acceptance criteria, and a team of agents designs, builds, and verifies against
> them. (Yes, the acronym collides with Object-Oriented Design — intentionally
> cheeky.)

Designed for the Opus 4.8 era: large context + native agency + Agent Teams mean
you no longer need a daemon, a finite-state machine, or a task database to
coordinate. You need a clear plan, independent verification, and a way to keep
docs honest.

## How it works

```
lead (you)  ── author plan → spawn teammates → monitor → gate → sync docs
  ├─ architect          design + ADRs        (in-process)
  ├─ design-reviewer    adversarial review    (in-process)
  ├─ implementer ×N     build owned files     (in-process)
  └─ inspector          GO/NOGO vs criteria   (in-process)
```

- **State lives in `docs/`** — `plans/` (the contract), `adr/` (why),
  `specs/` (living spec), `reports/` (completion markers + journal).
- **Docs are HTML & visual** — every OOD document is self-contained HTML, one file
  per doc (no Markdown source), renderable in a c11 browser/markdown surface, and
  leads with **diagrams** (Mermaid / inline SVG) for sequence, flow, and
  architecture instead of walls of text.
- **Inspection is a real gate** — a `TaskCompleted` hook blocks any
  `[gate:inspect]` task until `docs/reports/NNN-inspection.html` says
  `Verdict: GO`. Determinism by file existence, not by prompt.
- **Resume is free** — on interruption the lead re-reads `docs/plans/` +
  `docs/reports/` to see what's done and re-spawns the rest. (Agent Teams doesn't
  restore teammates on `/resume`; with doc-as-state that doesn't matter.)

## Design philosophy

OOD is a *style*, not just a tool — and its choices are recorded as ADRs that are
themselves worked examples of OOD docs (HTML, diagram-first). They render in a
browser / c11 surface or via `raw.githack.com`; on GitHub the `.html` opens as
source.

- [ADR 001 — Documents are the state](docs/adr/001-doc-as-state.html) — why there's no JSON state machine
- [ADR 002 — Flat two-tier](docs/adr/002-flat-two-tier.html) — why no Manager/Conductor tier
- [ADR 003 — Hooks are the only determinism layer](docs/adr/003-hook-as-the-only-determinism.html) — soft prompts vs. hard gates
- [ADR 004 — HTML, diagram-first documents](docs/adr/004-html-diagram-first-docs.html) — the two-audience doctrine
- [ADR 005 — Inspection is an independent, enforced gate](docs/adr/005-inspection-as-adversarial-gate.html) — verifying against generation bias

The throughline: as agents get more capable, the bottleneck shifts from *writing
code* to *deciding intent and verifying it*. OOD invests there — a clear plan,
independent verification, honest docs — and drops the coordination ceremony (state
machines, daemons, tiers) that capable models + Agent Teams make redundant.

## Requirements

- Claude Code with **Agent Teams** enabled:
  ```json
  // settings.json
  { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
  ```
- `python3` (for the completion-gate hook).
- Optional: [c11](https://github.com/Stage-11-Agentics/c11) as the terminal —
  teammates run in-process and are observable in c11's subagent footer/sidebar;
  render `docs/plans/*.html` as a markdown/browser surface for human review.

## Install

From this repo as a marketplace:

```
/plugin marketplace add hummer98/ood
/plugin install ood@ood
```

Then merge `CLAUDE.md.fragment` into your project's `CLAUDE.md` so teammates pick
up the document map, and create the dirs:

```
mkdir -p docs/{plans,adr,specs,reports}
```

## Use

```
/ood add a CSV export to the reports page
```

The lead interviews you into testable acceptance criteria, writes a plan to
`docs/plans/`, asks for approval, then runs the team to GO.

## Scope & limits

- **Depth, not breadth**: one epic at a time with internal parallelism. Many
  concurrent epics needs a coordinator tier this intentionally omits.
- **Parallel writes**: isolation comes from the plan's **file-ownership map**, not
  worktrees (`isolation:"worktree"` silently fails in team mode). Don't let two
  concurrent tasks own the same file.
- **Agent Teams is experimental**; behaviour may change across Claude Code
  versions.

## Components

| path | what |
|---|---|
| `skills/master-orchestrator/` | the lead playbook |
| `skills/doc-sync/` | sync `docs/specs/` from git history (after GO) |
| `agents/` | role teammates: architect, design-reviewer, implementer, inspector |
| `hooks/gate-task-completed.py` | the inspection gate |
| `commands/ood.md` | `/ood <goal>` entry point |
| `templates/` | plan / adr / inspection-report shapes |
| `CLAUDE.md.fragment` | doc-map to merge into your project |

## License

MIT
