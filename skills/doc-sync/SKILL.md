---
name: doc-sync
description: >
  Use after work lands (after an inspection GO) to sync docs/specs with the
  implementation. Triggers: "docs を同期", "仕様書更新", "sync docs", "update specs",
  or invoked by master-orchestrator at close. Input is git history + docs/plans
  only — no external state files.
---

# doc-sync — keep docs/specs aligned to reality

Sync `docs/specs/*.html` to the current implementation. The spec follows the code
(living spec), not the other way around. Inputs are **git history and
`docs/plans/`** — nothing else. No JSON state, no task database.

## Procedure

### 1. Find the spec baseline
```bash
git log -1 --format="%H %ai %s" -- docs/specs/
```
Record the hash as `<base>` (if `docs/specs/` doesn't exist yet, use the repo
root commit and plan to create specs from scratch).

### 2. Collect implementation changes since the baseline
```bash
git log --oneline <base>..HEAD -- ':!docs'
git diff --name-only <base>..HEAD -- ':!docs'
```
For commits whose intent is unclear, read the relevant `docs/plans/NNN-*.html` to
recover the "what & why".

### 3. Reconcile each spec file
For every file under `docs/specs/` (and any new area that now needs one), compare
against the collected changes and the plan's acceptance criteria. `docs/specs`
records **what the system does and why**, not internal code detail.

### 4. Output by mode
| mode | behaviour |
|---|---|
| `--dry-run` | print a diff report only; change nothing |
| (default) | present the diff, update after user confirms |
| `--auto` | update without confirmation |

Report shape:
```
## docs/specs sync report
baseline: <hash> <date>
commits considered: N
- docs/specs/<file>.html : <what changes>
- (new) docs/specs/<file>.html : <why needed>
- unchanged: <files>
```

## Rules
- Don't restate code; capture behaviour and intent.
- Remove descriptions of deleted features.
- Preserve existing voice and structure; no gratuitous reformatting.
- If a change's intent is unrecoverable, list it as "要確認 / needs review" rather
  than guessing.
