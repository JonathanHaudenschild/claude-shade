"""Shared plumbing for the Claude Code hook scripts.

Two rules govern everything in here:

1. **Fail open, never fail loud.** A crash in a hook must not break the user's
   session. Every entry point is wrapped and exits 0 on an unexpected error.
2. **Never echo a raw finding.** Messages sent back to the host describe
   *categories* (``EMAIL×2, IBAN``), never values — otherwise the warning would
   leak the very data the hook just caught.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shade import config, policy  # noqa: E402
from shade.engine import Engine  # noqa: E402


def read_event() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def emit(event_name: str, **fields: Any) -> None:
    """Print a Claude Code hook response and exit 0."""
    specific = {"hookEventName": event_name}
    top_level: dict[str, Any] = {}
    for key, value in fields.items():
        if value in (None, ""):
            continue
        if key in ("continue", "suppressOutput", "stopReason"):
            top_level[key] = value
        else:
            specific[key] = value
    payload = dict(top_level)
    if len(specific) > 1:
        payload["hookSpecificOutput"] = specific
    if payload:
        sys.stdout.write(json.dumps(payload))
    raise SystemExit(0)


def deny(message: str) -> None:
    """Refuse the action. Exit 2 puts the message in front of the user."""
    sys.stderr.write(message + "\n")
    raise SystemExit(2)


def engine_for(event: dict) -> Engine:
    return Engine(cwd=event.get("cwd") or os.getcwd())


def user_note(decision: policy.Decision, surface: str) -> str:
    """User-facing status line.

    `redacted` is only ever claimed when the host actually accepted a rewrite —
    i.e. `updatedInput` on PreToolUse. Announcing a redaction that did not
    happen is the worst failure a privacy tool can have, so `warn` says plainly
    that nothing was removed.
    """
    if decision.action == config.REDACT and decision.rewritten:
        return f"shade: redacted {decision.reason} in {surface}"
    if decision.action == config.BLOCK:
        return f"shade: blocked {surface} — contains {decision.reason}"
    return f"shade: {decision.reason} in {surface} was NOT removed (policy: {decision.action})"


def model_note(decision: policy.Decision) -> str:
    if decision.action == config.REDACT:
        return (
            f"[shade] Sensitive values ({decision.reason}) were replaced with placeholders "
            "of the form <LABEL_xxxxxx> before this reached you. Treat each placeholder as an "
            "opaque, stable identifier: the same placeholder always means the same real value. "
            "Do not guess, reconstruct, or ask the user to repeat the original values, and keep "
            "the placeholders intact in any code or text you produce."
        )
    return (
        f"[shade] Sensitive values ({decision.reason}) are present here and were not removed. "
        "Do not copy them into files, commands, commit messages, or network requests."
    )


def run(entry: Callable[[dict], None]) -> None:
    event = read_event()
    try:
        entry(event)
    except SystemExit:
        raise
    except Exception:
        if os.environ.get("SHADE_DEBUG"):
            traceback.print_exc(file=sys.stderr)
        raise SystemExit(0)
    raise SystemExit(0)
