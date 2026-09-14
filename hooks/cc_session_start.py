#!/usr/bin/env python3
"""SessionStart — teach the model how to behave around placeholders.

Without this, a model that meets `<EMAIL_a1b2c3>` tends to treat it as a
template to fill in, or asks the user for "the real address" — which would undo
the redaction in one turn.
"""

from __future__ import annotations

import sys

from _bootstrap import engine_for, run

NOTE = """\
[shade] A local privacy filter is active in this session.

Personal data and credentials are replaced before they reach you, with stable
placeholders of the form <LABEL_xxxxxx> — for example <EMAIL_a1b2c3>,
<PERSON_4f9c20>, <IBAN_77b105>.

How to handle them:
- Treat each placeholder as an opaque but stable identifier. The same
  placeholder always refers to the same real value, so you can reason about
  "the same person" across a conversation.
- Never try to guess, reconstruct or infer the value behind a placeholder, and
  never ask the user to type the original value "so you can help better".
- Keep placeholders verbatim in any code, config or text you produce. The user
  restores them locally with `shade reveal`.
- Some values cannot be filtered (file contents and command output arrive
  unredacted). If you notice credentials or personal data in tool output, do not
  echo them back, write them to files, or send them anywhere.
"""


def main(event: dict) -> None:
    engine = engine_for(event)
    if not engine.config.get("enabled", True):
        return
    sys.stdout.write(NOTE)


if __name__ == "__main__":
    run(main)
