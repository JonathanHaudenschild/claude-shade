#!/usr/bin/env python3
"""PreToolUse — guard what the agent puts *into* a tool call.

Covers two distinct risks:

* a tool call carrying sensitive data outward (WebFetch, an MCP server, a curl
  command) — redacted or refused according to the surface's policy;
* a read that would pull a credentials file into context — refused by path,
  because once tool output exists there is no way to take it back.
"""

from __future__ import annotations

from _bootstrap import config, emit, engine_for, model_note, policy, run, user_note

EVENT = "PreToolUse"


def main(event: dict) -> None:
    tool_name = event.get("tool_name") or ""
    tool_input = event.get("tool_input")
    if tool_input is None:
        return

    engine = engine_for(event)
    if not engine.config.get("enabled", True):
        return

    decision = policy.evaluate_tool_input(engine, tool_name, tool_input)
    if decision.action == config.OFF:
        return

    surface = policy.classify_tool(tool_name)
    engine.log(EVENT, surface, decision.action, decision.findings, {"tool": tool_name})

    if decision.action == config.BLOCK:
        reason = decision.reason
        if decision.findings:
            reason = (
                f"shade: this {tool_name} call carries {decision.reason}. "
                f"Blocked because the policy for `{surface}` is `block`. "
                "Use a placeholder or an environment variable reference instead of the literal value."
            )
        emit(EVENT, permissionDecision="deny", permissionDecisionReason=reason)

    if decision.action == config.REDACT and decision.rewritten:
        # Deliberately no permissionDecision: the call still goes through the
        # user's normal approval flow, it just carries placeholders now.
        emit(
            EVENT,
            updatedInput=decision.updated,
            additionalContext=model_note(decision),
            systemMessage=user_note(decision, f"{tool_name} input"),
        )

    emit(
        EVENT,
        additionalContext=model_note(decision),
        systemMessage=user_note(decision, f"{tool_name} input"),
    )


if __name__ == "__main__":
    run(main)
