#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Use venv Python when available
if [[ -f "venv/bin/python3" ]]; then
  PYTHON="venv/bin/python3"
else
  PYTHON="python3"
fi

OK=0
FAIL=0
WARN=0

check() {
  local label="$1"
  local result="$2"
  if [[ "$result" == "ok" ]]; then
    echo "  ✓ $label"
    ((OK++)) || true
  else
    echo "  ✗ $label — $result"
    ((FAIL++)) || true
  fi
}

warn() {
  echo "  ~ $1 — $2 (optional)"
  ((WARN++)) || true
}

echo ""
echo "=== KayaFlow Setup Verification ==="
echo "    Python: $($PYTHON --version 2>&1)"
echo ""

# Check .env
[[ -f ".env" ]] && check ".env exists" "ok" || check ".env exists" "missing — copy .env.example"

# Check Python 3.9+
py_minor=$($PYTHON -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
py_major=$($PYTHON -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
if [[ "$py_major" -ge 3 && "$py_minor" -ge 9 ]]; then
  check "Python 3.9+" "ok"
else
  check "Python 3.9+" "$($PYTHON --version 2>&1)"
fi

# Check required packages
for pkg in telegram anthropic PIL dotenv yaml pydantic; do
  result=$($PYTHON -c "import $pkg" 2>&1 && echo "ok" || echo "not installed")
  check "import $pkg" "$result"
done

# Check OCR (optional)
tesseract_check=$(tesseract --version 2>&1 | head -1 || echo "not installed")
if [[ "$tesseract_check" == tesseract* ]]; then
  check "tesseract (OCR)" "ok"
else
  warn "tesseract (OCR)" "not installed"
fi

# Check env vars
if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

[[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && check "TELEGRAM_BOT_TOKEN set" "ok" || warn "TELEGRAM_BOT_TOKEN" "empty (required to run bot)"
[[ -n "${ANTHROPIC_API_KEY:-}" ]] && check "ANTHROPIC_API_KEY set" "ok" || warn "ANTHROPIC_API_KEY" "empty (required to run bot)"

# Check design-memory dirs
for dir in onboarding kyc trust-signals cta-patterns navigation anti-patterns journey-reviews; do
  [[ -d "design-memory/$dir" ]] && check "design-memory/$dir" "ok" || check "design-memory/$dir" "missing"
done

# Check no secrets in git
if git rev-parse --git-dir > /dev/null 2>&1; then
  tracked_env=$(git ls-files .env 2>/dev/null || true)
  if [[ -z "$tracked_env" ]]; then
    check ".env not tracked by git" "ok"
  else
    check ".env not tracked by git" "DANGER: .env is committed"
  fi
fi

echo ""
echo "=== Results: $OK passed, $FAIL failed, $WARN warnings ==="
echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "Core checks passed."
  [[ $WARN -gt 0 ]] && echo "Warnings are optional (OCR, API keys for live mode)."
  echo "Run: bash scripts/run_bot.sh"
else
  echo "Fix failures above before running."
fi
