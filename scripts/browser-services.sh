#!/usr/bin/env bash
# Conservatively deploy the local recruitment-browser services.
# Default behaviour only starts missing services. Restarting is always explicit.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
FORM_FILLER_DIR="$REPO_ROOT/tools/form-filler"
LEASE_TOOL="$REPO_ROOT/skills/job-hunter/scripts/browser_lease.py"

STATE_ROOT="${XDG_STATE_HOME:-/root/.local/state}/youngyang-services"
BROWSER_PROFILE_DIR="${YY_BROWSER_PROFILE_DIR:-/root/.config/youngyang-browser/chrome-profile}"
LEASE_STATE_DIR="${YY_BROWSER_LEASE_DIR:-/root/.local/state/youngyang-browser}"
TUNNEL_TARGET="${YY_TUNNEL_TARGET:-dev-machine}"
DISPLAY_NUMBER="${YY_DISPLAY:-:99}"

ACTION="ensure"
RESTART_SERVICE=""
DRY_RUN=0
PLAN_ALL=0
ENABLE_TUNNEL=1
CONFIRM_SESSION_LOSS=0
MAINTENANCE_LEASE_ID=""

usage() {
  cat <<'EOF'
Usage: scripts/browser-services.sh [options]

Default: diagnose services and start only missing components.

Options:
  --status                    Diagnose only; do not start anything.
  --restart SERVICE           Explicitly restart one of:
                              chrome, tunnel, novnc, vnc, openbox, display, all
  --confirm-session-loss      Required when restarting Chrome/Xvfb or all services.
  --dry-run                   Print commands without executing them.
  --plan-all                  With --dry-run, print the complete clean-start plan.
  --no-tunnel                 Do not diagnose or start the noVNC SSH tunnel.
  -h, --help                  Show this help.

Security invariants:
  - Chrome CDP listens only on 127.0.0.1:9222 and is never SSH-forwarded.
  - x11vnc/noVNC listen only on localhost.
  - The SSH tunnel forwards only noVNC 6080.
  - An active browser lease blocks every restart.
EOF
}

while (($#)); do
  case "$1" in
    --status)
      ACTION="status"
      shift
      ;;
    --restart)
      if (($# < 2)); then
        printf 'error: --restart requires a service name\n' >&2
        exit 2
      fi
      ACTION="restart"
      RESTART_SERVICE="$2"
      shift 2
      ;;
    --confirm-session-loss)
      CONFIRM_SESSION_LOSS=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --plan-all)
      PLAN_ALL=1
      shift
      ;;
    --no-tunnel)
      ENABLE_TUNNEL=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$RESTART_SERVICE" in
  ""|chrome|tunnel|novnc|vnc|openbox|display|all) ;;
  *)
    printf 'error: unsupported restart service: %s\n' "$RESTART_SERVICE" >&2
    exit 2
    ;;
esac

if ((PLAN_ALL)) && ((DRY_RUN == 0)); then
  printf 'error: --plan-all is only valid with --dry-run\n' >&2
  exit 2
fi

if [[ ! -d "$FORM_FILLER_DIR" || ! -f "$LEASE_TOOL" ]]; then
  printf 'error: repository layout is incomplete under %s\n' "$REPO_ROOT" >&2
  exit 2
fi

for required_command in awk curl pgrep python3 ss tmux tr; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'error: required command is unavailable: %s\n' "$required_command" >&2
    exit 2
  fi
done

if ((DRY_RUN == 0)) && [[ "$ACTION" != "status" ]]; then
  mkdir -p "$STATE_ROOT"
  chmod 700 "$STATE_ROOT"
fi

log() {
  printf '[browser-services] %s\n' "$*"
}

run_command() {
  if ((DRY_RUN)); then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

command_string() {
  local rendered=""
  local item
  for item in "$@"; do
    printf -v rendered '%s %q' "$rendered" "$item"
  done
  printf '%s' "${rendered# }"
}

start_tmux_service() {
  local session_name="$1"
  local working_dir="$2"
  local log_file="$3"
  shift 3
  local service_command
  service_command="$(command_string "$@")"
  printf -v service_command '%s >>%q 2>&1' "$service_command" "$log_file"
  run_command tmux new-session -d -s "$session_name" -c "$working_dir" "$service_command"
}

localhost_port_listening() {
  local port="$1"
  ss -H -ltn 2>/dev/null | awk -v port="$port" '
    $4 == "127.0.0.1:" port || $4 == "[::1]:" port { found=1 }
    END { exit !found }
  '
}

port_has_nonlocal_listener() {
  local port="$1"
  ss -H -ltn 2>/dev/null | awk -v wanted=":${port}" '
    $4 ~ wanted "$" && $4 !~ /^(127\.0\.0\.1|\[::1\]):/ { found=1 }
    END { exit !found }
  '
}

process_matches() {
  local pattern="$1"
  pgrep -f -- "$pattern" >/dev/null 2>&1
}

chrome_ready() {
  curl -fsS --max-time 2 http://127.0.0.1:9222/json/version >/dev/null 2>&1
}

find_primary_chrome_pid() {
  local proc_path pid command_line
  for proc_path in /proc/[0-9]*/cmdline; do
    [[ -r "$proc_path" ]] || continue
    pid="${proc_path#/proc/}"
    pid="${pid%/cmdline}"
    command_line="$(tr '\0' ' ' < "$proc_path" 2>/dev/null || true)"
    if [[ "$command_line" == *"--user-data-dir=$BROWSER_PROFILE_DIR"* \
      && "$command_line" == *"--remote-debugging-port=9222"* \
      && "$command_line" != *"--type="* ]]; then
      printf '%s\n' "$pid"
      return 0
    fi
  done
  return 1
}

browser_lease_active_readonly() {
  python3 - "$LEASE_STATE_DIR/ownership.json" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file() or path.is_symlink():
    raise SystemExit(1)
try:
    owner = json.loads(path.read_text(encoding="utf-8"))
    expires = datetime.fromisoformat(str(owner.get("expires_at", "")).replace("Z", "+00:00"))
except (OSError, ValueError, json.JSONDecodeError):
    raise SystemExit(1)
raise SystemExit(0 if expires.astimezone(timezone.utc) > datetime.now(timezone.utc) else 1)
PY
}

release_maintenance_lease() {
  if [[ -n "$MAINTENANCE_LEASE_ID" ]]; then
    python3 "$LEASE_TOOL" --state-dir "$LEASE_STATE_DIR" release \
      --lease-id "$MAINTENANCE_LEASE_ID" >/dev/null 2>&1 || true
    MAINTENANCE_LEASE_ID=""
  fi
}

acquire_maintenance_lease() {
  local payload=""
  if ! payload="$(python3 "$LEASE_TOOL" --state-dir "$LEASE_STATE_DIR" acquire \
    --agent browser-services \
    --task-id "restart-$RESTART_SERVICE" \
    --mode service-restart \
    --ttl 600)"; then
    printf 'error: active browser lease detected; release it before any restart\n' >&2
    python3 "$LEASE_TOOL" --state-dir "$LEASE_STATE_DIR" status >&2 || true
    exit 3
  fi
  MAINTENANCE_LEASE_ID="$(python3 -c \
    'import json,sys; print(json.load(sys.stdin).get("lease_id", ""))' <<<"$payload")"
  if [[ -z "$MAINTENANCE_LEASE_ID" ]]; then
    printf 'error: failed to acquire a valid maintenance lease\n' >&2
    exit 3
  fi
  trap release_maintenance_lease EXIT
}

refuse_unsafe_restart() {
  if ((DRY_RUN)); then
    if browser_lease_active_readonly; then
      printf 'error: active browser lease detected; release it before any restart\n' >&2
      exit 3
    fi
  else
    acquire_maintenance_lease
  fi
  if [[ "$RESTART_SERVICE" == "chrome" || "$RESTART_SERVICE" == "display" \
    || "$RESTART_SERVICE" == "all" ]] \
    && ((CONFIRM_SESSION_LOSS == 0)); then
    printf 'error: Chrome/Xvfb restart can lose live form state; add --confirm-session-loss explicitly\n' >&2
    exit 3
  fi
  if [[ "$RESTART_SERVICE" == "display" ]] && find_primary_chrome_pid >/dev/null; then
    printf 'error: Chrome is still running; restart display safely with --restart all instead\n' >&2
    exit 3
  fi
}

stop_tmux_session() {
  local session_name="$1"
  if tmux has-session -t "$session_name" 2>/dev/null; then
    run_command tmux kill-session -t "$session_name"
  fi
}

stop_primary_chrome() {
  local pid=""
  pid="$(find_primary_chrome_pid || true)"
  if [[ -z "$pid" || ! "$pid" =~ ^[0-9]+$ ]]; then
    log "no validated primary Chrome process to stop"
    return 0
  fi
  local command_line
  command_line="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
  if [[ "$command_line" != *"--user-data-dir=$BROWSER_PROFILE_DIR"* \
    || "$command_line" != *"--remote-debugging-port=9222"* ]]; then
    printf 'error: refusing to stop unvalidated Chrome PID %s\n' "$pid" >&2
    exit 3
  fi
  run_command kill -TERM "$pid"
  if ((DRY_RUN)); then
    return 0
  fi
  local attempt
  for attempt in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
    sleep 0.25
  done
  printf 'error: Chrome PID %s did not stop after SIGTERM; no stronger signal was sent\n' "$pid" >&2
  exit 3
}

restart_requested() {
  local service="$1"
  [[ "$ACTION" == "restart" && ("$RESTART_SERVICE" == "$service" || "$RESTART_SERVICE" == "all") ]]
}

if [[ "$ACTION" == "restart" ]]; then
  refuse_unsafe_restart
  if restart_requested chrome; then
    stop_primary_chrome
    stop_tmux_session yy-chrome
  fi
  restart_requested tunnel && stop_tmux_session yy-tunnel
  restart_requested novnc && stop_tmux_session yy-novnc
  restart_requested vnc && stop_tmux_session yy-vnc
  restart_requested openbox && stop_tmux_session yy-openbox
  restart_requested display && stop_tmux_session yy-display
fi

for protected_port in 5900 6080 9222; do
  if port_has_nonlocal_listener "$protected_port"; then
    printf 'error: port %s has a non-localhost listener; refusing to continue\n' \
      "$protected_port" >&2
    exit 3
  fi
done

force_missing() {
  local service="$1"
  ((PLAN_ALL)) || restart_requested "$service"
}

if force_missing display || ! process_matches "^Xvfb ${DISPLAY_NUMBER}([[:space:]]|$)"; then
  if [[ "$ACTION" == "status" ]]; then
    log "display missing: Xvfb $DISPLAY_NUMBER"
  else
    log "starting Xvfb on $DISPLAY_NUMBER"
    start_tmux_service yy-display "$REPO_ROOT" "$STATE_ROOT/xvfb.log" \
      Xvfb "$DISPLAY_NUMBER" -screen 0 1600x1000x24 -nolisten tcp
  fi
else
  log "display ready: $DISPLAY_NUMBER"
fi

if force_missing openbox || ! process_matches "openbox( --startup|$)|openbox-session"; then
  if [[ "$ACTION" == "status" ]]; then
    log "openbox missing"
  else
    log "starting openbox"
    start_tmux_service yy-openbox "$REPO_ROOT" "$STATE_ROOT/openbox.log" \
      env DISPLAY="$DISPLAY_NUMBER" openbox-session
  fi
else
  log "openbox ready"
fi

if force_missing vnc || ! localhost_port_listening 5900; then
  if [[ "$ACTION" == "status" ]]; then
    log "x11vnc missing on localhost:5900"
  else
    log "starting x11vnc on localhost:5900"
    start_tmux_service yy-vnc "$REPO_ROOT" "$STATE_ROOT/x11vnc.log" \
      x11vnc -display "$DISPLAY_NUMBER" -nopw -rfbport 5900 -localhost -forever -noxdamage
  fi
else
  log "x11vnc ready on localhost:5900"
fi

if force_missing novnc || ! localhost_port_listening 6080; then
  if [[ "$ACTION" == "status" ]]; then
    log "noVNC missing on localhost:6080"
  else
    log "starting noVNC on localhost:6080"
    start_tmux_service yy-novnc "$REPO_ROOT" "$STATE_ROOT/novnc.log" \
      websockify --web=/usr/share/novnc/ 127.0.0.1:6080 127.0.0.1:5900
  fi
else
  log "noVNC ready on localhost:6080"
fi

if force_missing chrome || ! chrome_ready; then
  existing_chrome_pid="$(find_primary_chrome_pid || true)"
  if [[ -n "$existing_chrome_pid" ]] && ! restart_requested chrome && ((PLAN_ALL == 0)); then
    printf 'error: Chrome profile process exists but CDP is unavailable; refusing to start a second instance\n' >&2
    printf '       diagnose it or use explicit --restart chrome --confirm-session-loss\n' >&2
    exit 3
  fi
  if [[ "$ACTION" == "status" ]]; then
    log "Chrome CDP missing on localhost:9222"
  else
    chrome_binary="$(command -v google-chrome-stable || command -v google-chrome || command -v chromium || true)"
    if [[ -z "$chrome_binary" ]]; then
      printf 'error: no Chrome/Chromium binary found\n' >&2
      exit 2
    fi
    chrome_args=(
      "$chrome_binary"
      --disable-dev-shm-usage
      --no-first-run
      --no-default-browser-check
      --no-proxy-server
      --window-size=1600,1000
      "--user-data-dir=$BROWSER_PROFILE_DIR"
      --remote-debugging-address=127.0.0.1
      --remote-debugging-port=9222
      "--load-extension=$FORM_FILLER_DIR"
      about:blank
    )
    if [[ "$(id -u)" == "0" ]]; then
      chrome_args=("$chrome_binary" --no-sandbox "${chrome_args[@]:1}")
    fi
    if ((DRY_RUN == 0)); then
      mkdir -p "$BROWSER_PROFILE_DIR"
    fi
    log "starting Chrome with repository extension: $FORM_FILLER_DIR"
    start_tmux_service yy-chrome "$REPO_ROOT" "$STATE_ROOT/chrome.log" \
      env DISPLAY="$DISPLAY_NUMBER" "${chrome_args[@]}"
  fi
else
  log "Chrome CDP ready on localhost:9222"
fi

if ((ENABLE_TUNNEL)); then
  tunnel_pattern="autossh .*127\.0\.0\.1:6080:127\.0\.0\.1:6080"
  if force_missing tunnel || ! process_matches "$tunnel_pattern"; then
    if [[ "$ACTION" == "status" ]]; then
      log "noVNC tunnel missing"
    else
      log "starting SSH reverse tunnel for noVNC only"
      start_tmux_service yy-tunnel "$REPO_ROOT" "$STATE_ROOT/tunnel.log" \
        autossh -M 0 -N \
        -o BatchMode=yes \
        -o ExitOnForwardFailure=yes \
        -o ServerAliveInterval=20 \
        -o ServerAliveCountMax=3 \
        -R 127.0.0.1:6080:127.0.0.1:6080 \
        "$TUNNEL_TARGET"
    fi
  else
    log "noVNC tunnel process ready"
    if process_matches "autossh .*127\.0\.0\.1:9222:127\.0\.0\.1:9222"; then
      log "WARNING: legacy tunnel still forwards raw CDP 9222; use explicit --restart tunnel"
    fi
  fi
fi

if [[ -n "$MAINTENANCE_LEASE_ID" ]]; then
  log "browser lease: held by this service restart"
elif browser_lease_active_readonly; then
  log "browser lease: active"
else
  log "browser lease: free or expired"
fi
