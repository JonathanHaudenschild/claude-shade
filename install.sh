#!/usr/bin/env bash
# Install shade for the CLI, Claude Code, and/or Codex.
#
#   ./install.sh            # everything
#   ./install.sh cli        # just the `shade` command
#   ./install.sh claude     # just the Claude Code plugin
#   ./install.sh uninstall  # remove the CLI symlink
#
# Codex lives in a separate repo: https://github.com/JonathanHaudenschild/codex-shade

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-all}"
BIN_DIR="${SHADE_BIN_DIR:-$HOME/.local/bin}"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }

require_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 not found on PATH. shade needs it for its hooks." >&2
    exit 1
  fi
  python3 - <<'PY'
import sys
if sys.version_info < (3, 9):
    sys.exit("error: python3 >= 3.9 required, found %s" % sys.version.split()[0])
PY
}

install_cli() {
  say "CLI"
  mkdir -p "$BIN_DIR"
  chmod +x "$ROOT/bin/shade"
  ln -sf "$ROOT/bin/shade" "$BIN_DIR/shade"
  note "linked $BIN_DIR/shade -> $ROOT/bin/shade"
  case ":$PATH:" in
    *":$BIN_DIR:"*) note "$BIN_DIR is already on PATH" ;;
    *) note "add it to PATH:  export PATH=\"$BIN_DIR:\$PATH\"" ;;
  esac
}

install_claude() {
  say "Claude Code plugin"
  if command -v claude >/dev/null 2>&1; then
    note "run these two commands (they are interactive, so they are not run for you):"
  else
    note "claude was not found on PATH; run these once it is installed:"
  fi
  echo
  echo "    claude plugin marketplace add \"$ROOT\""
  echo "    claude plugin install shade@shade"
  echo
  note "or, to try it without installing:  claude --plugin-dir \"$ROOT\""
  note "verify with /shade:status inside a session"
}

uninstall() {
  say "Uninstalling"
  rm -f "$BIN_DIR/shade" && note "removed $BIN_DIR/shade"
  note "for Claude Code:  claude plugin uninstall shade@shade"
}

require_python

case "$TARGET" in
  all)       install_cli; install_claude ;;
  cli)       install_cli ;;
  claude)    install_claude ;;
  uninstall) uninstall ;;
  *) echo "usage: $0 [all|cli|claude|uninstall]" >&2; exit 2 ;;
esac

say "Done"
note "shade status          show the effective configuration"
note "shade scan --file X   check a file without changing it"
note "config lives at ${SHADE_HOME:-$HOME/.shade}/config.json"
