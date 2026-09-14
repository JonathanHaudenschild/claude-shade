#!/usr/bin/env python3
"""SessionStart — teach the model how to behave around placeholders.

Without this, a model that meets `<EMAIL_a1b2c3>` tends to treat it as a
template to fill in, or asks the user for "the real address" — which would undo
the redaction in one turn.
"""

from __future__ import annotations

import os
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


PROXY_NOTE = """\
[shade] A local privacy filter is active, with the egress proxy in front.

Personal data and credentials are replaced before they reach you, with stable
placeholders of the form <LABEL_xxxxxx> — for example <EMAIL_a1b2c3>,
<PERSON_4f9c20>, <IBAN_77b105>. This covers the user's prompt AND the contents
of files and command output.

Crucially, the substitution is a ROUND TRIP: any placeholder you write is
replaced with the real value again before the user sees your reply. On their
screen, <EMAIL_a1b2c3> reads as the actual address.

So do not narrate the redaction. Saying "I only have a placeholder" while
writing that placeholder produces, on the user's screen, a sentence that names
the real value and then claims you cannot see it — which reads as a
contradiction and looks like the filter is broken. It is not.

Just use the placeholder naturally, as if it were the value:
  good:  "I'll add <EMAIL_a1b2c3> to the config."
  bad:   "I see <EMAIL_a1b2c3>, but it's redacted so I can't read it."

Other rules:
- Treat each placeholder as an opaque but stable identifier. The same
  placeholder always refers to the same real value.
- Never guess or reconstruct the value behind one, and never ask the user to
  retype it.
- Keep placeholders verbatim in code and config you write.
"""


DRY_RUN_WARNING = """\
[shade] NOTE: the privacy proxy is running in DRY-RUN. It reports what it would
redact but forwards everything unchanged, so values in this session are NOT
redacted. Do not tell the user their data is being filtered. The prompt hook
remains active and will still refuse a prompt containing credentials or personal
data.
"""


def main(event: dict) -> None:
    engine = engine_for(event)
    if not engine.config.get("enabled", True):
        return
    mode = os.environ.get("SHADE_PROXY_MODE")
    if mode == "dry-run":
        sys.stdout.write(DRY_RUN_WARNING)
        return
    if mode == "active":
        sys.stdout.write(PROXY_NOTE)
        return
    sys.stdout.write(NOTE)


if __name__ == "__main__":
    run(main)
