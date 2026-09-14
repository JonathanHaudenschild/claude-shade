#!/usr/bin/env python3
"""UserPromptSubmit — the one place where redaction is airtight.

Claude Code lets this hook replace the prompt outright, so whatever the user
typed is rewritten before a single byte is sent upstream.
"""

from __future__ import annotations

import re

from _bootstrap import config, deny, emit, engine_for, model_note, policy, run, user_note

# `/shade:allow support@example.org` must reach the CLI intact — redacting the
# argument would allowlist a placeholder instead of the value the user named.
SELF_COMMAND = re.compile(r"^\s*/shade[:\-]?", re.IGNORECASE)

EVENT = "UserPromptSubmit"


def main(event: dict) -> None:
    prompt = event.get("prompt") or ""
    if not prompt.strip() or SELF_COMMAND.match(prompt):
        return

    engine = engine_for(event)
    if not engine.config.get("enabled", True):
        return

    decision = policy.evaluate_text(engine, config.PROMPT, prompt)
    if decision.action == config.OFF or not decision.findings:
        return

    engine.log(EVENT, config.PROMPT, decision.action, decision.findings)

    if decision.action == config.BLOCK:
        message = f"shade blocked this prompt: it contains {decision.reason}.\nNothing was sent."
        if decision.rewritten:
            message += (
                "\n\nA hook cannot rewrite a prompt in place, only refuse it. "
                "Here is the same message with the sensitive parts replaced — "
                "send this instead:\n\n"
                f"{decision.updated}\n"
            )
        else:
            message += "\nRun `shade redact 'your text'` and send the result instead."
        deny(message)

    # warn: the prompt goes through unchanged. Say exactly that — claiming a
    # redaction the host never applied would be worse than saying nothing.
    emit(
        EVENT,
        additionalContext=model_note(decision),
        systemMessage=f"shade: {decision.reason} in your prompt was NOT removed (policy: warn)",
    )


if __name__ == "__main__":
    run(main)
