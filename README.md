# shade

A local privacy filter for coding agents. It finds personal data, credentials
and API tokens in what you type and in what the agent does, and replaces them
with stable placeholders — **before** anything is sent to the model.

A Claude Code plugin: hooks plus `/shade:*` commands.

> **Using Codex too?** The same engine ships as
> [**codex-shade**](https://github.com/JonathanHaudenschild/codex-shade),
> a standalone repo with the Codex lifecycle hooks. The two are independent —
> install either, or both. `shade/` is vendored identically in each.

No services, no Docker, no network calls, no dependencies beyond Python 3.9+.
Everything runs on your machine, and the key used to generate placeholders never
leaves it.

```
you type:   Bitte mail an erika.mustermann@example.de, IBAN DE89 3704 0044 0532 0130 00
model sees: Bitte mail an <EMAIL_97029f>, IBAN <IBAN_924945>
```

---

## 1. What it can and cannot do

This is the part worth reading before you trust it with anything.

A hook can only act where its host lets it act, and **a hook cannot tell whether
the host honoured its output** — an unknown field is ignored in silence. So the
capabilities below were verified against the host binaries themselves, not taken
from a documentation page. The honest picture:

| Channel | What shade does | Guarantee |
|---|---|---|
| What you type | **blocked**, with the clean text handed back to paste | prevented |
| Tool input (WebFetch, MCP, Bash, …) | rewritten (`updatedInput`) or refused | prevented |
| Reading a credentials file | refused by path before it opens | prevented |
| File contents / command output | **detected, not removed** | warning only |
| What the model writes back | not touched | out of scope |

**Claude Code cannot rewrite a submitted prompt.** Its own embedded hook
reference is explicit — `updatedInput` is "PreToolUse only" — and the 2.1.x
binary contains no prompt-rewrite field at all; `UserPromptSubmit` offers
`decision: "block"` and `additionalContext`. Codex documents the same limit, so
codex-shade behaves identically. A `redact` policy on the prompt surface
therefore degrades to `block`: shade refuses the prompt and hands you the
cleaned text to paste. Nothing is let through silently, but the substitution is
yours to make, not the tool's.

Run `shade doctor` to see what your own installation actually enforces.

The fourth row is the other real limitation. Once `Read` or `Bash` has run, its
output is in the model's context and no hook can take it back — neither host
offers an `updatedOutput`. `shade` responds to that in two ways: it refuses reads
of sensitive paths *before* they happen (`deny_paths`), and when something slips
through anyway it tells you what landed in context and instructs the model not
to propagate it.

So: **shade substantially reduces what leaves your machine. It is not a
guarantee that nothing sensitive ever reaches the model.** Treat it as a seatbelt,
not as permission to drive into a wall — the rules about what you may paste into
an AI tool still apply.

Two more things it deliberately does not do:

* **It does not find names on its own.** No NLP model ships with it. Names are
  matched from a list you maintain (`shade name "Erika Mustermann"`). A regex
  cannot tell a person from a variable, and pretending otherwise would be worse
  than being explicit.
* **It does not protect you from yourself in another window.** It only sees what
  passes through Claude Code.

---

## 2. Install

```bash
git clone <this repo> claude-shade
cd claude-shade
./install.sh            # or: ./install.sh cli | claude
```

`install.sh` is safe to re-run. It never installs the Claude Code plugin for you
— it prints the two commands, because they are interactive.

### Claude Code

```bash
claude plugin marketplace add /path/to/claude-shade
claude plugin install shade@shade
```

Try it without installing first:

```bash
claude --plugin-dir /path/to/claude-shade
```

Then in a session: `/shade:status`.

### Codex CLI

Codex lives in its own repo — clone
[codex-shade](https://github.com/JonathanHaudenschild/codex-shade) and run
`python3 install.py`. It writes `~/.codex/hooks.json` and shares this engine, this
config file (`~/.shade/config.json`) and this vault, so names, allowlists and
placeholders carry across both tools.

### The CLI on its own

```bash
./install.sh cli        # links ~/.local/bin/shade
shade scan --file notes.md
```

---

## 3. Configuration

Layers, later wins:

1. built-in defaults (`shade/config.py`)
2. `~/.shade/config.json` — your settings
3. `$SHADE_CONFIG` — an explicit path
4. `<project>/.shade.json` — per-repo, safe to commit
5. `SHADE_*` environment variables

Copy `shade.example.json` to `~/.shade/config.json` and edit. `shade status`
shows what is actually in force.

### Policies

Six *surfaces*, three *severities*, four *actions*.

| Surface | What it covers |
|---|---|
| `prompt` | what you type |
| `egress` | WebFetch, WebSearch, MCP tools, subagents — anything leaving the machine |
| `shell` | Bash (and Codex `shell`, if you also run codex-shade) |
| `local_write` | Write, Edit, `apply_patch` |
| `local_read` | Read, Grep, Glob |
| `output` | tool results (detection only) |

| Severity | Meaning |
|---|---|
| `secret` | credentials, keys, tokens. Leaking one is an incident |
| `pii` | personal data under GDPR Art. 4 |
| `special` | special categories under GDPR Art. 9 |

| Action | Effect |
|---|---|
| `redact` | replace with a placeholder and continue |
| `block` | refuse the prompt or the tool call |
| `warn` | allow, but tell you and tell the model to be careful |
| `off` | ignore |

Defaults:

```
prompt        secret=block   pii=block   special=warn
egress        secret=block   pii=redact  special=warn
shell         secret=block   pii=warn    special=warn
local_write   secret=warn    pii=warn    special=off
local_read    secret=warn    pii=off     special=off
output        secret=warn    pii=warn    special=off
```

Three defaults are load-bearing and worth understanding:

* **`prompt` blocks rather than redacts.** Not a preference — no host exposes a
  prompt-rewrite field. `redact` there degrades to `block` automatically.

* **`local_write` never redacts.** Rewriting a `Write` or `Edit` payload would
  put `<EMAIL_97029f>` into your actual source file. Redaction is disabled on
  disk-bound fields entirely, not merely discouraged.
* **`shell` blocks rather than redacts secrets.** Rewriting a command string
  would produce a broken command that fails in a confusing way. Refusing is
  clearer, and the fix — use `$GITHUB_TOKEN` instead of the literal — is the
  right fix anyway.

Quick overrides without editing anything:

```bash
SHADE_PROMPT_POLICY=warn    claude    # let it through with a warning instead
SHADE_EGRESS_POLICY=block   claude    # nothing sensitive goes outward, ever
SHADE_ENABLED=0             claude    # off for one session
```

### deny_paths

Globs whose contents must never be opened by the agent. A leading `!` re-allows.
These are enforced at `PreToolUse`, so the file is never read in the first place
— the only genuinely reliable protection for file contents.

Defaults cover `.env*` (but not `.env.example`), `*.pem`, `*.key`, `*.p12`,
`~/.ssh/**`, `.aws/credentials`, `.npmrc`, `.netrc`, `.git-credentials`,
`service-account*.json`, `*.sqlite`, `*.dump`.

```bash
shade check-path .env .env.example src/app.py
```

---

## 4. What it detects

**Credentials** — PEM/OpenSSH/PGP private keys, AWS access key IDs and secret
keys, GitHub (classic + fine-grained) and GitLab tokens, Anthropic, OpenAI,
Google, Slack, Stripe, HuggingFace, npm and SendGrid keys, JWTs, Slack/Discord
webhooks, passwords inside connection strings, `Authorization:` headers, secrets
in URL query parameters, and a generic `key = value` detector gated on entropy.

**Personal data** — email addresses, IBANs (mod-97 checked), BICs, credit cards
(Luhn checked), German Steuer-ID (ISO 7064 MOD 11,10 checked), German
Sozialversicherungsnummer (check digit verified), US SSN, phone numbers, public
IPv4/IPv6, MAC addresses, dates of birth, German street addresses and postal
codes, and any name on your list.

**Special categories (GDPR Art. 9)** — a configurable DE/EN vocabulary covering
health, disability, union membership, religion, political affiliation, sexual
orientation and ethnic origin. Policy defaults to `warn`, because matching such a
word does not by itself mean a person has been identified.

Checksums and boundaries are the reason this can run unattended: an IBAN-shaped string that
fails mod-97 is not redacted, a 16-digit number that fails Luhn is not a card,
and RFC1918 addresses are ignored entirely because `192.168.0.1` is not personal
data and redacting it would only train you to ignore the warnings. Numeric
detectors also refuse to match inside a longer number or inside a decimal
fraction, which is what stops a table of geo coordinates reading as a wall of
credit cards.

Measured on real repositories: a 26-file application produced zero findings; a
9 MB database dump produced ~2,800, all of them genuine contact data.

Off by default because they are noisy: `bic`, `ipv6`, `de_postal_address`,
`de_plz_city`. Turn any detector on or off by name:

```json
{ "detectors": { "de_postal_address": true, "ipv4": false } }
```

---

## 5. Placeholders and the vault

A redacted value becomes `<LABEL_xxxxxx>`, where the suffix is
`HMAC-SHA256(local key, label + value)` truncated to six hex characters.

That design buys two things at once. The placeholder is **stable** — the same
person is `<PERSON_4f9c20>` in every session, so the model can still follow "the
same person" through a conversation and tell two people apart. And it is
**opaque** — the key lives in `~/.shade/key` (mode 0600) and never leaves the
machine, so the placeholder discloses nothing.

`~/.shade/vault.json` (0600) maps placeholders back to originals so you can
restore a model's answer locally:

```bash
shade reveal --file answer.md          # writes a 0600 file, prints only the path
pbpaste | shade reveal --stdout        # prints, if you ask explicitly
```

`reveal` writes to a file rather than printing by default. If an agent ever runs
it, printing would put every original value straight back into the context.

**Secrets are not stored in the vault.** A leaked API key should not be copied
into a second file on disk so it can be un-redacted later; it is meant to stay
gone. Change that with `vault.store_severities` if you disagree.

Entries older than `vault.ttl_days` (30) are pruned. `shade vault --clear` empties
it.

`~/.shade/audit.jsonl` records what was caught — categories and masked previews,
never raw values. `shade log --tail 20`.

---

## 6. Commands

In Claude Code:

| Command | Does |
|---|---|
| `/shade:status` | effective config, active detectors, vault size |
| `/shade:scan <path>` | scan a file without changing it |
| `/shade:name <name…>` | add names that must always be pseudonymised |
| `/shade:allow <term…>` | mark a false positive so it stops being redacted |
| `/shade:reveal` | explains how to restore placeholders yourself |

Plus `shade doctor` in the terminal — it probes the host binaries for the hook
fields they actually implement, checks the plugin loaded, and runs three live
hook invocations end to end.

In the terminal:

```
shade scan [--file F] [--json]      report findings, exit 1 if any
shade redact [--file F] [--severity secret|pii|special]
shade reveal [--file F] [--stdout] [-o OUT]
shade status
shade name NAME...   [--remove]
shade allow TERM...  [--remove]
shade check-path PATH...
shade classify TOOL...
shade doctor
shade vault [--clear]
shade log [--tail N]
```

`scan` and `redact` read stdin when given no text, so they compose:

```bash
git diff | shade scan
cat draft.md | shade redact > draft.clean.md
```

---

## 7. Tuning it

Expect to spend ten minutes on this once, then never again.

**Add the names you work with.** This is the single highest-value step, and
nothing else can do it for you:

```bash
shade name "Erika Mustermann" "Projekt Nordlicht"
```

Use full names. A short entry like `Berg` would match inside ordinary German
prose and turn your transcript into noise.

**Clear false positives as they appear.** A test IBAN in a fixture, a
documentation IP, a public support address:

```bash
shade allow "support@example.de" "DE89370400440532013000"
```

Allowlisted values are sent in full, every time, with no further checks — so put
test data there, never a real key.

**Keep your own domain readable, if you want to.** Internal team addresses are
still personal data, but you may prefer them legible:

```json
{ "allow_email_domains": ["example.de"] }
```

**Check what a policy actually does** before committing to it:

```bash
echo '{"hook_event_name":"PreToolUse","tool_name":"WebFetch","tool_input":{"prompt":"mail ada@example.com"}}' \
  | python3 hooks/cc_pre_tool.py
```

---

## 8. Troubleshooting

**`Status: ✘ failed to load — Duplicate hooks file detected`.** `hooks/hooks.json`
and `commands/` are discovered automatically; naming them in `plugin.json` makes
the plugin load them twice and fail outright. The manifest here deliberately
declares neither.

**A hook claims something it did not do.** Run `shade doctor`. It reports which
hook fields your host binary actually implements, so a capability that quietly
disappears in an update shows up as a `NO` rather than as a false reassurance.

**Nothing seems to happen.** Hooks are registered at session start; restart the
session after installing or changing them. `shade log --tail 20` shows whether
the hooks ran at all.

**Edits to this checkout have no effect.** `claude plugin install` copies the
plugin into `~/.claude/plugins/cache/shade/shade/<version>/`, and *that copy* is
what runs — `claude plugin list` can report `enabled` while a stale copy is
loaded. After changing anything here, bump `version` in `plugin.json` and run:

```bash
claude plugin marketplace update shade
claude plugin update shade@shade      # then restart the session
```

`shade doctor` compares the installed copy against this checkout and says
`STALE` when they have drifted.

---

## 9. Failure behaviour

Hooks **fail open**. If a hook crashes, times out, or receives something it does
not understand, it exits 0 and the session continues unfiltered. The alternative
— failing closed — would mean a bad regex could lock you out of your own tools.

That is a deliberate trade and you should know which way it points. Set
`SHADE_DEBUG=1` to see tracebacks instead of silence.

---

## 9. Notes for Users

This tool helps with the privacy rules on AI use; it does not replace them.

It reduces accidental exposure of the categories the guidance names —
credentials and tokens, personal data, financial data with a personal
reference, Art. 9 special categories. It cannot judge whether a strategy paper
is confidential, whether a procurement is still running, or whether a research
result has been published. Those remain human decisions, and *"if in doubt, do
not enter it"* still stands.

A caught secret is still a secret that existed in a prompt. If a real credential
is blocked, rotate it - a block means it did
not reach the model, not that it was never at risk.

---

## 11. Development

```bash
python3 -m unittest discover -s tests -v
```

41 tests, no dependencies. The check-digit validators are tested against
published worked examples rather than against themselves, and two tests pin
precision regressions found by running the scanner over real repositories: a
credit-card pattern that joined adjacent SQL timestamps into one candidate, and
numeric detectors that matched inside the fractional part of a geo coordinate.

```
shade/          engine: detectors, validators, vault, policy, CLI
                — vendored identically in codex-shade; change it in one repo,
                  then run that repo's tools/sync-engine.sh
hooks/          Claude Code hook scripts + hooks.json
commands/       Claude Code /shade:* commands
bin/shade       CLI entry point
```

Adding a detector: append a `Detector` to `shade/detectors.py`. Give it a
validator if the format has a checksum — precision is what makes automatic
redaction tolerable, and a noisy detector gets switched off, which protects
nobody.

## Licence

MIT.

## See also

* [**codex-shade**](https://github.com/JonathanHaudenschild/codex-shade) — the
  same engine with Codex CLI hooks instead of a Claude Code plugin.
