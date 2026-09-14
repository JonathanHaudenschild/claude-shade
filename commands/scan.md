---
name: scan
description: Scan a file or path for personal data and credentials without changing it
argument-hint: <path>
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/shade" scan --file "$ARGUMENTS" 2>&1 || true`

The scan output above lists findings as `line / severity / label / masked
preview`. The previews are masked on purpose — the real values were never
printed.

Report to the user:
- how many findings there are, grouped by label;
- which ones are `secret` severity (those are the urgent ones);
- for any finding that looks like a false positive given the file's purpose,
  suggest the exact command to allowlist it: `shade allow '<term>'`.

If the file is one that should never be opened by an agent at all, suggest
adding a matching glob to `deny_paths` in `~/.shade/config.json`.
