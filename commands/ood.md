---
description: Run a feature/epic end-to-end as the team lead — spec → plan → design → review → implement → inspect, gated on inspection.
argument-hint: <goal or feature to build>
---

Act as the **lead** following the `master-orchestrator` skill.

Goal from the user:

$ARGUMENTS

Start at step 1 of the master-orchestrator procedure: interview until you can write
**testable acceptance criteria**, then author `docs/plans/NNN-slug.html` from the
template and get the user's approval **before** spawning any teammates.

Remember: the documents under `docs/` are the state — do not build a JSON state
machine. Agent Teams must be enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`);
if it isn't, tell the user how to enable it before proceeding.
