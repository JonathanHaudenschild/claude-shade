---
name: status
description: Show shade's effective configuration, active detectors and vault size
allowed-tools: Bash(python3:*)
---

!`python3 "${CLAUDE_PLUGIN_ROOT}/bin/shade" status`

Summarise the output above for the user in a few lines: whether shade is
enabled, which policy applies to each surface, and how many entries the vault
holds. If any surface is set to `off`, point that out and say what it means in
practice. Do not invent settings that are not in the output.
