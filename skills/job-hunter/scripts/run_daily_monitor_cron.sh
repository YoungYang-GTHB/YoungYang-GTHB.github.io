#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../" && pwd)"
output_dir="${project_root}/output/daily-monitor"

mkdir -p "${output_dir}"
cd "${project_root}"

exec /usr/bin/flock -n "${output_dir}/.daily-monitor.lock" \
  /root/miniconda3/bin/python3 skills/job-hunter/scripts/run_daily_monitor.py \
  >>"${output_dir}/scheduler.log" 2>&1
