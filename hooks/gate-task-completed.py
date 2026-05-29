#!/usr/bin/env python3
"""
OOD (Orchestration-Oriented Development) — TaskCompleted gate.

Blocks completion of a *gated* Agent Teams task until a matching inspection
report with `Verdict: GO` exists under docs/reports/.

This is the determinism backbone of OOD: the "don't finish without
inspection" rule is enforced by file existence, not by prompt suggestion.
No JSON state machine — the report file *is* the gate.

Convention (set by the master-orchestrator skill when it creates tasks):
  - A task that must pass inspection carries the token  [gate:inspect]
    in its name or description.
  - The plan it belongs to is referenced as  plan:NNN  (e.g. plan:001).
  - The inspector writes  docs/reports/NNN-inspection.html  containing
    `<h2>Verdict: GO</h2>`  (or NOGO). OOD documents are HTML by default;
    legacy `.md` reports are also accepted.

Behaviour:
  - Task is not gated            -> allow  (exit 0)
  - Gated + matching GO report   -> allow  (exit 0)
  - Gated + no GO report         -> BLOCK  (exit 2, feedback on stderr)
  - Anything unparseable / bug   -> allow  (exit 0) but warn on stderr
    (never wedge the workflow because the hook itself failed)

Hook contract: exit code 2 prevents the task from completing and feeds
stderr back to the lead. See Claude Code hooks docs (TaskCompleted).
"""
import json
import os
import re
import sys
from pathlib import Path

GATE_TOKEN = "[gate:inspect]"
VERDICT_GO = re.compile(r"verdict\s*[:\-]?\s*go\b", re.IGNORECASE)
PLAN_REF = re.compile(r"plan:([A-Za-z0-9][\w.-]*)", re.IGNORECASE)


def warn(msg: str) -> None:
    print(f"ood gate: {msg}", file=sys.stderr)


def read_event() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def task_text(event: dict) -> str:
    """Collect every plausible text field the task data might live under."""
    parts = []
    for key in ("task", "tool_input", "data", "payload"):
        v = event.get(key)
        if isinstance(v, dict):
            for k in ("name", "title", "description", "content", "body", "text"):
                if isinstance(v.get(k), str):
                    parts.append(v[k])
        elif isinstance(v, str):
            parts.append(v)
    for k in ("name", "title", "description", "content", "text"):
        if isinstance(event.get(k), str):
            parts.append(event[k])
    if not parts:
        # last resort: stringify the whole event so token detection still works
        parts.append(json.dumps(event, ensure_ascii=False))
    return "\n".join(parts)


def project_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def go_report_exists(plan_id: str | None, reports_dir: Path) -> bool:
    if not reports_dir.is_dir():
        return False
    # OOD docs are HTML by default; accept legacy .md too.
    exts = ("html", "md")
    candidates: list[Path] = []
    if plan_id:
        for ext in exts:
            candidates += reports_dir.glob(f"*{plan_id}*inspection*.{ext}")
        if not candidates:
            for ext in exts:
                candidates += reports_dir.glob(f"{plan_id}*.{ext}")
    else:
        # no plan id resolvable: fall back to any inspection report
        for ext in exts:
            candidates += reports_dir.glob(f"*inspection*.{ext}")
    for f in candidates:
        try:
            if VERDICT_GO.search(f.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def main() -> int:
    try:
        event = read_event()
    except Exception as e:  # noqa: BLE001 - never wedge on parse failure
        warn(f"could not parse hook input ({e}); allowing.")
        return 0

    text = task_text(event)

    # Not a gated task -> nothing to enforce.
    if GATE_TOKEN not in text:
        return 0

    m = PLAN_REF.search(text)
    plan_id = m.group(1) if m else None
    reports = project_dir() / "docs" / "reports"

    if go_report_exists(plan_id, reports):
        return 0

    where = f"docs/reports/{plan_id}-inspection.html" if plan_id \
        else "docs/reports/<plan>-inspection.html"
    print(
        "BLOCKED by OOD: this task is marked [gate:inspect] but no "
        f"inspection report with `Verdict: GO` was found ({where}).\n"
        "Spawn/await the inspector to verify against the plan's acceptance "
        "criteria and write the GO/NOGO report, then retry completion.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
