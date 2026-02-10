#!/bin/bash
# RTW Optimizer — session preflight check
# Runs on SessionStart to verify environment is ready.
# Exit 0 = OK (stdout goes to Claude context)
# Exit 2 = blocking error (stderr shown to user)

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ISSUES=()
WARNINGS=()
OK=()

# ── 1. Check uv is installed ──
if command -v uv &>/dev/null; then
  OK+=("uv installed")
else
  ISSUES+=("uv not installed — get it at https://docs.astral.sh/uv/")
fi

# ── 2. Check .venv exists (run uv sync if missing) ──
if [ -d "$PROJECT_DIR/.venv" ]; then
  OK+=(".venv ready")
else
  if command -v uv &>/dev/null; then
    echo "Installing dependencies (first time setup)..." >&2
    (cd "$PROJECT_DIR" && uv sync 2>&1) >&2
    if [ -d "$PROJECT_DIR/.venv" ]; then
      OK+=(".venv created via uv sync")
    else
      ISSUES+=("uv sync failed — run manually: cd $PROJECT_DIR && uv sync")
    fi
  else
    ISSUES+=(".venv missing and uv not available — install uv then run: uv sync")
  fi
fi

# ── 3. Check SERPAPI_API_KEY ──
if [ -n "${SERPAPI_API_KEY:-}" ]; then
  OK+=("SERPAPI_API_KEY set")
  # Persist for this session's Bash commands
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export SERPAPI_API_KEY=\"$SERPAPI_API_KEY\"" >> "$CLAUDE_ENV_FILE"
  fi
else
  # Try to source from .zshrc
  SERPAPI_FROM_RC=$(grep 'SERPAPI_API_KEY' "$HOME/.zshrc" 2>/dev/null | head -1 | sed 's/^export //' | cut -d= -f2 | tr -d '"' | tr -d "'" || true)
  if [ -n "$SERPAPI_FROM_RC" ]; then
    if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
      echo "export SERPAPI_API_KEY=\"$SERPAPI_FROM_RC\"" >> "$CLAUDE_ENV_FILE"
    fi
    OK+=("SERPAPI_API_KEY loaded from .zshrc")
  else
    WARNINGS+=("SERPAPI_API_KEY not set — nonstop checks and SerpAPI searches won't work. Set: export SERPAPI_API_KEY='your-key'")
  fi
fi

# ── 4. Check ExpertFlyer credentials in keyring ──
if security find-generic-password -s "expertflyer.com" >/dev/null 2>&1; then
  OK+=("ExpertFlyer credentials in keyring")
else
  WARNINGS+=("ExpertFlyer not in keyring — D-class checks won't work. Run: python3 -m rtw login expertflyer")
fi

# ── 5. Check Playwright chromium ──
if [ -d "$PROJECT_DIR/.venv" ]; then
  PLAYWRIGHT_BROWSERS="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}"
  if [ -d "$PLAYWRIGHT_BROWSERS" ] && ls "$PLAYWRIGHT_BROWSERS"/chromium-* >/dev/null 2>&1; then
    OK+=("Playwright chromium installed")
  else
    WARNINGS+=("Playwright chromium not installed — ExpertFlyer scraper needs it. Run: uv run playwright install chromium")
  fi
fi

# ── Report results ──
if [ ${#ISSUES[@]} -gt 0 ]; then
  echo "RTW Optimizer setup has blocking issues:" >&2
  for issue in "${ISSUES[@]}"; do
    echo "  ERROR: $issue" >&2
  done
  if [ ${#WARNINGS[@]} -gt 0 ]; then
    for warn in "${WARNINGS[@]}"; do
      echo "  WARN: $warn" >&2
    done
  fi
  echo "" >&2
  echo "Run /rtw-init to fix these issues." >&2
  exit 2
fi

# Non-blocking output — goes to Claude context
echo "RTW preflight: ${#OK[@]} checks passed."
if [ ${#WARNINGS[@]} -gt 0 ]; then
  for warn in "${WARNINGS[@]}"; do
    echo "  WARN: $warn"
  done
  echo "Run /rtw-init to configure missing services."
fi
exit 0
