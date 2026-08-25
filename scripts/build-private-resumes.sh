#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_root="${project_root}/career/resumes/sources"
asset_root="${project_root}/career/resumes/assets"
output_root="${project_root}/career/site/public"
template_root="${project_root}/templates/resume"

for source_name in main main-en main-embedded main-embedded-en; do
  [[ -f "${source_root}/${source_name}.tex" ]] || {
    echo "Missing private resume source: ${source_name}.tex" >&2
    exit 1
  }
done
[[ -f "${asset_root}/photo.jpg" ]] || { echo "Missing private resume photo." >&2; exit 1; }

build_root="$(mktemp -d)"
cleanup() {
  if [[ -n "${build_root:-}" && -d "${build_root}" && ! -L "${build_root}" && "${build_root}" == /tmp/tmp.* ]]; then
    rm -rf -- "${build_root}"
  fi
}
trap cleanup EXIT

cp "${template_root}/resume-photo.cls" "${build_root}/"
cp -a "${template_root}/fontawesome5" "${build_root}/"
cp "${asset_root}/photo.jpg" "${build_root}/photo.jpg"
cp "${source_root}/"*.tex "${build_root}/"

for source_name in main main-en main-embedded main-embedded-en; do
  (cd "${build_root}" && xelatex -interaction=nonstopmode -halt-on-error "${source_name}.tex" >/dev/null)
  (cd "${build_root}" && xelatex -interaction=nonstopmode -halt-on-error "${source_name}.tex" >/dev/null)
done

mkdir -p "${output_root}"
cp "${build_root}/main.pdf" "${output_root}/resume-vla-zh.pdf"
cp "${build_root}/main-en.pdf" "${output_root}/resume-vla-en.pdf"
cp "${build_root}/main-embedded.pdf" "${output_root}/resume-embedded-zh.pdf"
cp "${build_root}/main-embedded-en.pdf" "${output_root}/resume-embedded-en.pdf"
cp "${output_root}/resume-vla-zh.pdf" "${output_root}/resume.pdf"
cp "${output_root}/resume-vla-en.pdf" "${output_root}/resume-en.pdf"
cp "${output_root}/resume-embedded-zh.pdf" "${output_root}/resume-embedded.pdf"

echo "Private resume PDFs rebuilt under career/site/public/."
