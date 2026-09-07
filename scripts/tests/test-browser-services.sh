#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)"
SERVICE_SCRIPT="$REPO_ROOT/scripts/browser-services.sh"
LEASE_TOOL="$REPO_ROOT/skills/job-hunter/scripts/browser_lease.py"

plan="$($SERVICE_SCRIPT --dry-run --plan-all)"
plain_plan="${plan//\\/}"

if [[ "$plain_plan" == *"/vePFS/"* ]]; then
  printf 'browser service plan contains the retired workspace path\n' >&2
  exit 1
fi
[[ "$plain_plan" == *"--remote-debugging-address=127.0.0.1"* ]]
[[ "$plain_plan" == *"x11vnc -display :99 -nopw -rfbport 5900 -localhost"* ]]
[[ "$plain_plan" == *"127.0.0.1:6080 127.0.0.1:5900"* ]]
[[ "$plain_plan" == *"127.0.0.1:6080:127.0.0.1:6080"* ]]
if [[ "$plain_plan" == *"127.0.0.1:9222:127.0.0.1:9222"* ]]; then
  printf 'browser service plan must not forward raw CDP 9222\n' >&2
  exit 1
fi

lease_test_dir="$(mktemp -d)"
if YY_BROWSER_LEASE_DIR="$lease_test_dir/lease" \
  "$SERVICE_SCRIPT" --dry-run --restart chrome >/dev/null 2>&1; then
  printf 'Chrome restart must require explicit session-loss confirmation\n' >&2
  rmdir "$lease_test_dir"
  exit 1
fi
rmdir "$lease_test_dir"

active_lease_root="$(mktemp -d)"
active_lease_dir="$active_lease_root/lease"
lease_payload="$(python3 "$LEASE_TOOL" --state-dir "$active_lease_dir" acquire \
  --agent test-agent --task-id test-restart-guard --ttl 60)"
lease_id="$(python3 -c \
  'import json,sys; print(json.load(sys.stdin)["lease_id"])' <<<"$lease_payload")"
if YY_BROWSER_LEASE_DIR="$active_lease_dir" \
  "$SERVICE_SCRIPT" --dry-run --restart tunnel >/dev/null 2>&1; then
  printf 'active browser lease must block every restart\n' >&2
  exit 1
fi
python3 "$LEASE_TOOL" --state-dir "$active_lease_dir" release \
  --lease-id "$lease_id" >/dev/null
unlink "$active_lease_dir/browser.lock"
rmdir "$active_lease_dir" "$active_lease_root"

status_test_dir="$(mktemp -d)"
XDG_STATE_HOME="$status_test_dir/state" \
YY_BROWSER_LEASE_DIR="$status_test_dir/lease" \
  "$SERVICE_SCRIPT" --status --no-tunnel >/dev/null
if [[ -e "$status_test_dir/state" || -e "$status_test_dir/lease" ]]; then
  printf 'status mode must not create runtime state\n' >&2
  exit 1
fi
rmdir "$status_test_dir"

printf 'browser-services dry-run invariants passed\n'
