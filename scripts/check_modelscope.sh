#!/usr/bin/env bash
# Check whether this machine can reach ModelScope for embedding model download.
#
# Prof-Finder downloads Qwen/Qwen3-Embedding-0.6B from ModelScope (www.modelscope.cn).
# Requires: curl (macOS/Linux usually have it preinstalled).
#
# Usage:
#   bash scripts/check_modelscope.sh
#   ./scripts/check_modelscope.sh
#
# Exit code 0 = all checks passed; 1 = at least one check failed.

set -u

MODELSCOPE_HOST="www.modelscope.cn"
MODELSCOPE_BASE="https://${MODELSCOPE_HOST}"
MODEL_ID="Qwen/Qwen3-Embedding-0.6B"
TIMEOUT=15

PASSED=0
TOTAL=4

pass() {
  printf '[PASS] %s: %s\n' "$1" "$2"
  PASSED=$((PASSED + 1))
}

fail() {
  printf '[FAIL] %s: %s\n' "$1" "$2"
}

proxy_info() {
  local parts=()
  local key val
  for key in HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY http_proxy https_proxy all_proxy no_proxy; do
    val="${!key:-}"
    if [[ -n "$val" ]]; then
      parts+=("${key}=${val}")
    fi
  done
  if ((${#parts[@]} == 0)); then
    echo "(none)"
  else
    local IFS=', '
    echo "${parts[*]}"
  fi
}

require_curl() {
  if ! command -v curl >/dev/null 2>&1; then
    echo "Error: curl is required but not found in PATH." >&2
    echo "Install curl, or run: python scripts/check_modelscope.py" >&2
    exit 2
  fi
}

resolve_dns() {
  local host="$1"
  if command -v dig >/dev/null 2>&1; then
    dig +time="${TIMEOUT}" +tries=1 +short "$host" A 2>/dev/null | sed '/^$/d'
    return
  fi
  if command -v getent >/dev/null 2>&1; then
    getent ahosts "$host" 2>/dev/null | awk '{print $1}' | sort -u
    return
  fi
  if command -v nslookup >/dev/null 2>&1; then
    nslookup "$host" 2>/dev/null | awk '/^Address: / {print $2}' | tail -n +2
    return
  fi
  if command -v host >/dev/null 2>&1; then
    host "$host" 2>/dev/null | awk '/has address/ {print $4}'
    return
  fi
  echo ""
}

check_dns() {
  local addrs
  addrs="$(resolve_dns "$MODELSCOPE_HOST" | paste -sd ', ' -)"
  if [[ -n "$addrs" ]]; then
    pass "DNS" "${MODELSCOPE_HOST} -> ${addrs}"
  else
    fail "DNS" "cannot resolve ${MODELSCOPE_HOST} (need dig, getent, nslookup, or host)"
  fi
}

check_https() {
  local code
  code="$(curl -sS --max-time "$TIMEOUT" -o /dev/null -w '%{http_code}' "${MODELSCOPE_BASE}/" 2>&1)" || {
    fail "HTTPS" "$code"
    return
  }
  if [[ "$code" =~ ^[23] ]]; then
    pass "HTTPS" "HTTP ${code} from ${MODELSCOPE_BASE}/"
  else
    fail "HTTPS" "HTTP ${code} from ${MODELSCOPE_BASE}/"
  fi
}

check_model_api() {
  local url="${MODELSCOPE_BASE}/api/v1/models/${MODEL_ID}"
  local tmp http_code body model_name

  tmp="$(mktemp)"
  http_code="$(curl -sS --max-time "$TIMEOUT" -o "$tmp" -w '%{http_code}' "$url" 2>&1)" || {
    rm -f "$tmp"
    fail "Model API" "$http_code"
    return
  }

  if [[ "$http_code" != "200" ]]; then
    rm -f "$tmp"
    fail "Model API" "HTTP ${http_code} for ${url}"
    return
  fi

  body="$(<"$tmp")"
  rm -f "$tmp"

  if ! grep -q '"Code"[[:space:]]*:[[:space:]]*200' <<<"$body"; then
    fail "Model API" "unexpected response (Code != 200)"
    return
  fi

  model_name="$(grep -o '"Name":"Qwen3[^"]*"' <<<"$body" | head -n1 | cut -d'"' -f4)"
  if [[ -z "$model_name" ]]; then
    model_name="$(grep -o '"ChineseName":"[^"]*"' <<<"$body" | head -n1 | cut -d'"' -f4)"
  fi

  if [[ -n "$model_name" ]]; then
    pass "Model API" "${MODEL_ID} reachable (${model_name})"
  else
    fail "Model API" "${MODEL_ID} API responded but model name not found"
  fi
}

check_file_download() {
  local url="${MODELSCOPE_BASE}/api/v1/models/${MODEL_ID}/repo?Revision=master&FilePath=config.json"
  local headers http_code content_range total

  headers="$(curl -sS --max-time "$TIMEOUT" -H 'Range: bytes=0-0' -D - -o /dev/null "$url" 2>&1)" || {
    fail "File download" "$headers"
    return
  }

  http_code="$(sed -n 's/^HTTP\/[^[:space:]]*[[:space:]]\([0-9][0-9][0-9]\).*/\1/p' <<<"$headers" | tail -n1)"
  if [[ "$http_code" != "200" && "$http_code" != "206" ]]; then
    fail "File download" "HTTP ${http_code:-unknown} for repo file"
    return
  fi

  content_range="$(grep -i '^Content-Range:' <<<"$headers" | tail -n1 | sed 's/^[Cc]ontent-[Rr]ange:[[:space:]]*//' | tr -d '\r')"
  total="${content_range##*/}"
  if [[ -n "$total" && "$total" != "$content_range" ]]; then
    pass "File download" "partial download OK (config.json, ${total} bytes total)"
  else
    pass "File download" "partial download OK (config.json)"
  fi
}

main() {
  require_curl

  echo "ModelScope connectivity check (Prof-Finder embedding model)"
  echo "Target model: ${MODEL_ID}"
  echo "Proxy env: $(proxy_info)"
  echo

  check_dns
  check_https
  check_model_api
  check_file_download

  echo
  if [[ "$PASSED" -eq "$TOTAL" ]]; then
    echo "Result: OK (${PASSED}/${TOTAL}) — this machine should be able to download the embedding model."
    exit 0
  fi

  echo "Result: FAILED (${PASSED}/${TOTAL}) — ModelScope is not fully reachable from this machine."
  echo "Tips:"
  echo "  - Ensure general internet access (ModelScope is a domestic CN service; VPN is usually not required)."
  echo "  - Check firewall / corporate proxy settings."
  echo "  - If behind a proxy, set HTTPS_PROXY and retry."
  exit 1
}

main "$@"
