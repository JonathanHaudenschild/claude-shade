---
name: allow
description: Mark a term as a false positive so shade stops redacting it
argument-hint: "<term> [<term> ...]"
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/shade" allow $ARGUMENTS`

Allowlisted terms are matched literally and case-insensitively, and are skipped
by every detector.

Confirm what was added. Then warn the user if any of the terms look like they
might be genuinely sensitive rather than a false positive — an allowlisted value
is sent to the model in full, every time, with no further checks. Good
candidates are things like a public support address, a documentation IP, or a
test IBAN; a real key is not one.
