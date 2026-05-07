#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

OK=0
FAIL=0

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

echo ""
echo "=== KayaFlow Setup Verification ==="
echo ""

# Check .env
[[ -f ".env" ]] && check ".env exists" "ok" || check ".env exists" "missing — copy .env.example"

# Check Python
python_version=$(python3 --version 2>&1 || echo "not found")
[[ "$python_version" == Python\ 3.1* ]] && check "Python 3.10+" "ok" || check "Python 3.10+" "$python_version"

# Check required packages
for pkg in telegram anthropic PIL dotenv yaml pydantic; do
  result=$(python3 -c "import $pkg" 2>&1 && echo "ok" || echo "not installed")
  check "import $pkg" "$result"
done

# Check OCR (optional)
tesseract_check=$(tesseract --version 2>&1 | head -1 || echo "not installed")
if [[ "$tesseract_check" == tesseract* ]]; then
  check "tesseract (OCR)" "ok"
else
  echo "  ~ tesseract (OCR) — not installed (optional)"
fi

# Check env vars loaded
if [[ -f ".env" ]]; then
  source <(grep -v '^#' .env | grep -v '^$' | sed 's/^/export /')
fi

[[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && check "TELEGRAM_BOT_TOKEN set" "ok" || check "TELEGRAM_BOT_TOKEN set" "empty"
[[ -n "${ANTHROPIC_API_KEY:-}" ]] && check "ANTHROPIC_API_KEY set" "ok" || check "ANTHROPIC_API_KEY set" "empty"

# Check design-memory dirs
for dir in onboarding kyc trust-signals cta-patterns navigation anti-patterns journey-reviews; do
  [[ -d "design-memory/$dir" ]] && check "design-memory/$dir" "ok" || check "design-memory/$dir" "missing"
done

echo ""
echo "=== Results: $OK passed, $FAIL failed ==="
echo ""
[[ $FAIL -eq 0 ]] && echo "All checks passed! Run: bash scripts/run_bot.sh" || echo "Fix the issues above before running."
