#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
private_root="${project_root}/career"
private_data="${private_root}/site/content/resume.yaml"
private_public="${private_root}/site/public"

if [[ ! -f "${private_data}" || ! -d "${private_public}" ]]; then
  echo "Private profile data is unavailable. Initialize the career submodule first." >&2
  exit 1
fi

if [[ -L "${private_public}" ]]; then
  echo "Refusing to copy from a symbolic-link asset root: ${private_public}" >&2
  exit 1
fi

node "${project_root}/scripts/prepare-public-site.mjs" career/site content/resume.public.yaml public

echo "Sanitized personal site prepared locally. Use RESUME_DATA_PATH=content/resume.public.yaml."
