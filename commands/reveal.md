---
name: reveal
description: Explain how to restore redacted placeholders back to their real values
---

Explain the following to the user, concisely and in their language.

Restoring placeholders is deliberately **not** something you can do for them.
Un-redacting inside this session would print the real values straight back into
your context — undoing the redaction in a single turn. So `reveal` is a local
command they run themselves, in their own terminal:

```
# a whole file
shade reveal --file answer.md

# or something on the clipboard (macOS)
pbpaste | shade reveal
```

It writes the restored text to a private file with mode 0600 and prints only
the path, never the contents. Add `--stdout` if they explicitly want it printed
in their terminal.

Also tell them:
- Restoration uses `~/.shade/vault.json`, which maps placeholders to originals.
  It is local, `0600`, and pruned after `vault.ttl_days` (30 by default).
- Secrets are **not** stored in the vault by design, so `<AWS_ACCESS_KEY_ID_…>`
  and friends cannot be restored. They are meant to stay gone.
- `shade vault --clear` empties it.
