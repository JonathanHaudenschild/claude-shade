#!/usr/bin/env python3
"""PostToolUse — detection only, and honest about it.

Neither Claude Code nor Codex lets a hook rewrite tool output. By the time this
runs, the file contents or command output are already in the model's context.
What this hook can still do is tell the user what landed there and instruct the
model not to propagate it. Prevention happens in `cc_pre_tool.py` via
`deny_paths`; this is the audit trail.
"""

from __future__ import annotations

from _bootstrap import config, deny, emit, engine_for, policy, run

EVENT = "PostToolUse"


def main(event: dict) -> None:
    tool_response = event.get("tool_response")
    if tool_response is None:
        return

    engine = engine_for(event)
    if not engine.config.get("enabled", True):
        return

    tool_name = event.get("tool_name") or ""
    decision = policy.evaluate_tool_output(engine, tool_name, tool_response)
    if decision.action == config.OFF or not decision.findings:
        return

    engine.log(EVENT, config.OUTPUT, decision.action, decision.findings, {"tool": tool_name})

    paths = policy.collect_paths(event.get("tool_input") or {})
    origin = f" (from {paths[0]})" if paths else ""

    if decision.action == config.BLOCK:
        deny(
            f"shade: the output of {tool_name}{origin} contains {decision.reason}. "
            "It is already in context — end this session with /clear if that is not acceptable, "
            "and add the path to deny_paths so the read is refused next time."
        )

    emit(
        EVENT,
        additionalContext=(
            f"[shade] The output of {tool_name}{origin} contains {decision.reason}. "
            "This could not be redacted — tool output is not rewritable. Do not repeat these "
            "values back, do not copy them into files, commands, commit messages or network "
            "requests, and refer to them indirectly if you must mention them at all."
        ),
        systemMessage=f"shade: {tool_name} output contains {decision.reason} — already in context",
    )


if __name__ == "__main__":
    run(main)
