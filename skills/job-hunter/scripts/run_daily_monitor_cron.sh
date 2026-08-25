#!/usr/bin/env bash
set -euo pipefail

project_root="/vePFS/tim/workspace/YoungYang/YoungYang-Resume"
output_dir="${project_root}/output/daily-monitor"

mkdir -p "${output_dir}"
cd "${project_root}"

exec /usr/bin/flock -n "${output_dir}/.daily-monitor.lock" \
  /root/miniconda3/bin/python3 skills/job-hunter/scripts/run_daily_monitor.py \
  >>"${output_dir}/scheduler.log" 2>&1
