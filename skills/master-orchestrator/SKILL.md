---
name: master-orchestrator
description: >
  Use to run a feature/epic end-to-end as the team lead: dialogue the spec into a
  plan, run design -> review -> implement -> inspect with an Agent Team, and gate
  completion on inspection. Triggers: "/ood", "オーケストレーション", "計画して実装",
  "plan and build this", "run this as a team", "spec to implementation".
  The plan and reports under docs/ are the state; do not build a JSON state machine.
---

# master-orchestrator — the lead playbook

You are the **lead** of a flat, two-tier team:

```
lead (you)  ── authors the plan, spawns teammates, monitors, gates, integrates
  ├─ architect          (in-process teammate)
  ├─ design-reviewer    (in-process teammate)
  ├─ implementer ×N     (in-process teammate)
  └─ inspector          (in-process teammate)
```

There is **no Manager and no Conductor tier** — you are both. There is **no JSON
state machine**: the documents under `docs/` are the durable state. Agent Teams'
own task list is ephemeral coordination state you never hand-maintain.

## Documents are the state

| dir | role | who writes |
|---|---|---|
| `docs/plans/NNN-slug.html` | the contract: intent, **acceptance criteria**, task breakdown, **file-ownership map**. The program counter. | you (lead) |
| `docs/adr/NNN-slug.html` | decisions & why (AI-read: terse, link-dense) | you / architect |
| `docs/specs/*.html` | living spec, synced to reality | doc-sync, after GO |
| `docs/reports/NNN-*.html` | completion markers & journal, incl. `NNN-inspection.html` with `<h2>Verdict: GO|NOGO</h2>` | inspector etc. |

**All OOD documents are HTML by default** — self-contained, renderable in a c11
browser/markdown surface. One file per doc; no Markdown source to keep in sync.
Keep AI-read docs (`adr`, `specs`) lean: semantic HTML, minimal styling, terse
prose — teammates load them into context.

**Visualize by default — diagrams over walls of text.** Every doc should lead
with a diagram where one aids understanding:
- **sequence diagram** for interactions / message flow,
- **flowchart** for process & branching logic,
- **architecture / component diagram** for structure,
- **state diagram** for lifecycles, **ER/class** for data.

Use **Mermaid** (`<pre class="mermaid">…</pre>`; the bootstrap is in the
templates) as the default; use **inline SVG** for precise, static figures or when
the doc must render fully offline (Mermaid loads from CDN). Prose supports the
diagram, not the reverse.

Templates live at `${CLAUDE_PLUGIN_ROOT}/templates/` (`plan.html`, `adr.html`,
`inspection-report.html`). Copy and fill — don't invent ad-hoc shapes; the gate
hook greps the inspection report for the text `Verdict: GO`
(heading `<h2>Verdict: GO</h2>`).

## Procedure

### 1. Spec dialogue → plan
Interview the user until you can write **testable acceptance criteria**. Then
write `docs/plans/NNN-slug.html` from the template, including:
- intent & scope, acceptance criteria (each must be checkable),
- a task breakdown, and a **file-ownership map** (which task owns which files —
  this is how parallel teammates avoid collisions; see Limits below),
- mark every task that must pass inspection with the token `[gate:inspect]` and
  reference the plan as `plan:NNN`.
Record consequential decisions as ADRs in `docs/adr/`.
The plan is authored directly as HTML (the standard OOD document format), so it
opens as a c11 markdown/browser surface for human review with no extra step.

### 2. Human approval gate
Present the plan and get the user's approval before spawning anyone. If they have
plan mode available, use it. Do not start implementation on an unapproved plan.

### 3. Create the team
Agent Teams is required. If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is not enabled,
stop and tell the user to set it in settings.json. Create one team. On c11,
teammates run **in-process** (split panes need tmux/iTerm2); you observe them via
c11's subagent footer/sidebar — that's expected, not a problem.

Derive the shared task list **from the plan** (the plan is the source of truth;
the task list is a disposable projection you rebuild on every (re)start).

### 4. Spawn teammates with curated context
Teammates do **not** inherit your conversation. In each spawn prompt include:
- which plan/section/ADRs to read (by path),
- the teammate's **owned files** from the file-ownership map,
- its role (use the matching agent type: `architect`, `design-reviewer`,
  `implementer`, `inspector`),
- the `plan:NNN` reference and, for implementation tasks, `[gate:inspect]`.

Spawn order that works well: architect (if design is non-trivial) →
design-reviewer challenges the design → implementer(s) build → inspector verifies.
Reviewer and implementer can run concurrently and message each other directly.

### 5. Monitor
Messages arrive automatically (native mailbox); you don't poll. Keep your own
context **thin** — you are a monitor, not an archive. Push detail into the docs.
If a teammate stops on an error, steer it or spawn a replacement.

### 6. Inspection gate (enforced)
The inspector verifies the implementation against the plan's acceptance criteria
and writes `docs/reports/NNN-inspection.html` with `<h2>Verdict: GO</h2>` or `NOGO` plus
findings. The `TaskCompleted` hook **blocks** any `[gate:inspect]` task from
completing until a `Verdict: GO` report exists. On NOGO, feed the findings back to
the implementer and loop. Escalate to the user after repeated NOGO (no infinite
loops).

### 7. Sync & close
After GO, invoke the **doc-sync** skill to update `docs/specs/` from git history.
Write a short closing report to `docs/reports/NNN-summary.html`. Then clean up the
team (always via the lead).

### 8. Resume
If your session is interrupted, **re-read `docs/plans/` and `docs/reports/`**:
tasks with a report are done, tasks without one are outstanding. Re-create the
team and re-spawn teammates for the remaining work. Agent Teams does not restore
teammates on `/resume` — that's fine, because the docs are the truth.

## Limits (state them; don't pretend otherwise)
- **Depth, not breadth.** One epic at a time with internal parallelism. Many
  concurrent epics is out of scope (would need a coordinator tier).
- **Parallel writes.** `isolation:"worktree"` silently fails when combined with a
  team, so isolation comes from the **file-ownership map**, not worktrees. If two
  tasks must touch the same files, serialize them or split the files.
- **Skills/MCP for teammates** load from project/user settings, not from a
  subagent definition's frontmatter — keep the OOD plugin installed at
  project/user scope so teammates can reach doc-sync.
