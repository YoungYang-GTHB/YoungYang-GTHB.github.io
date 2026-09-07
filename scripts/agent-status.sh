#!/usr/bin/env bash
# Read-only handoff diagnostic. It intentionally does not start, stop, or mutate services.
set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
CAREER_ROOT="$REPO_ROOT/career"

section() {
  printf '\n[%s]\n' "$1"
}

section "repository"
printf 'root: %s\n' "$REPO_ROOT"
git -C "$REPO_ROOT" status --short --branch
git -C "$REPO_ROOT" submodule status || true
if git -C "$CAREER_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '\ncareer:\n'
  git -C "$CAREER_ROOT" status --short --branch
else
  printf 'career: unavailable; run git submodule update --init --recursive\n'
fi

section "local services"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp 2>/dev/null | awk 'NR == 1 || /:(3000|5900|6080|8765|9222)[[:space:]]/'
else
  printf 'ss is unavailable\n'
fi

section "browser targets"
if command -v curl >/dev/null 2>&1 && curl -fsS --max-time 2 http://127.0.0.1:9222/json/version >/dev/null 2>&1; then
  python3 - <<'PY'
import json
from urllib.request import urlopen
from urllib.parse import urlsplit, urlunsplit


def redact_url(value):
    """Keep navigation context without printing tokens or form identifiers."""
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return "(invalid-url)"
    if not parsed.scheme:
        return "(non-url)"
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))

with urlopen("http://127.0.0.1:9222/json/list", timeout=2) as response:
    targets = json.load(response)
pages = [item for item in targets if item.get("type") == "page"]
print(f"CDP ready: {len(pages)} page target(s)")
for item in pages[:8]:
    title = (item.get("title") or "(untitled)").replace("\n", " ")[:80]
    url = redact_url(item.get("url"))[:120]
    print(f"- {title}: {url}")
if len(pages) > 8:
    print(f"- ... {len(pages) - 8} more")
PY
else
  printf 'CDP unavailable on 127.0.0.1:9222\n'
fi

section "tmux"
if command -v tmux >/dev/null 2>&1; then
  tmux list-sessions 2>/dev/null | awk '/^yy-/' || printf 'no yy-* sessions\n'
else
  printf 'tmux is unavailable\n'
fi

section "job ledger"
if [ -f "$CAREER_ROOT/求职投递/2027届/data/applications.yaml" ]; then
  python3 "$REPO_ROOT/skills/job-hunter/scripts/jobctl.py" status || true
  if python3 "$REPO_ROOT/skills/job-hunter/scripts/jobctl.py" validate; then
    printf 'validation: passed\n'
  else
    printf 'validation: FAILED; repair before changing application state\n'
  fi
else
  printf 'private ledger unavailable\n'
fi

section "next commands"
printf '%s\n' \
  "Read: $CAREER_ROOT/AGENT_HANDOFF.md" \
  "Applications: python3 skills/job-hunter/scripts/jobctl.py monitor-due --kind apply --brief --date YYYY-MM-DD" \
  "Process: python3 skills/job-hunter/scripts/jobctl.py monitor-due --kind process --brief --date YYYY-MM-DD" \
  "Queue: python3 skills/job-hunter/scripts/jobqueue.py status" \
  "Browser: ./scripts/browser-services.sh --status" \
  "Build site: ./scripts/prepare-private-site.sh && RESUME_DATA_PATH=content/resume.public.yaml npm run build" \
  "Build resumes: ./scripts/build-private-resumes.sh"
