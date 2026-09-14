---
name: name
description: Add names (colleagues, clients, project code names) that must always be pseudonymised
argument-hint: "<name> [<name> ...]"
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/shade" name $ARGUMENTS`

Person names are the one category no regex can find on its own. This list is how
shade learns them: every entry is replaced with a stable `<PERSON_xxxxxx>`
placeholder from the next prompt onwards, case-insensitively, on word
boundaries.

Confirm what was added and how many names are now configured. Remind the user
that short or common words make poor entries — `Berg` would match
`Bergmann-Straße` fragments and ordinary German prose, whereas a full name does
not. The list lives in `~/.shade/config.json` and never leaves the machine.
