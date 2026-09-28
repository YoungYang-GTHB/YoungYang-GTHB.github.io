#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_file="${project_root}/templates/resume/public-anonymized.tex"
output_root="${project_root}/public"
build_root="$(mktemp -d)"
cleanup() {
  if [[ -n "${build_root:-}" && -d "${build_root}" && ! -L "${build_root}" && "${build_root}" == /tmp/tmp.* ]]; then
    rm -rf -- "${build_root}"
  fi
}
trap cleanup EXIT

for language in zh en; do
  for track in vla embedded; do
    job_name="resume-${track}-${language}"
    (
      cd "${build_root}"
      xelatex -interaction=nonstopmode -halt-on-error -jobname="${job_name}" \
        "\\def\\ResumeLanguage{${language}}\\def\\ResumeTrack{${track}}\\input{${source_file}}" >/dev/null
    )
    install -m 644 "${build_root}/${job_name}.pdf" "${output_root}/${job_name}.pdf"
  done
done

echo "Anonymized public resume samples rebuilt under public/."
