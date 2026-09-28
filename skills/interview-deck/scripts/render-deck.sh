#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: render-deck.sh <deck.pptx>" >&2
  exit 2
fi

deck_path="$(realpath "$1")"
if [[ ! -f "$deck_path" ]]; then
  echo "Deck not found: $deck_path" >&2
  exit 1
fi

deck_dir="$(dirname "$deck_path")"
deck_base="$(basename "$deck_path" .pptx)"
render_dir="$deck_dir/${deck_base}-render"
profile_dir="$(mktemp -d /tmp/interview-deck-lo-XXXXXX)"
trap 'rm -rf "$profile_dir"' EXIT

mkdir -p "$render_dir"
libreoffice --headless --nologo --nodefault --nolockcheck \
  "-env:UserInstallation=file://$profile_dir" \
  --convert-to pdf --outdir "$render_dir" "$deck_path"

pdf_path="$render_dir/$deck_base.pdf"
if [[ ! -f "$pdf_path" ]]; then
  echo "LibreOffice did not produce $pdf_path" >&2
  exit 1
fi

pdftoppm -png -r 144 "$pdf_path" "$render_dir/slide" >/dev/null 2>&1
python3 "$(dirname "$0")/contact-sheet.py" "$render_dir" "$render_dir/contact-sheet.png"

expected="$(unzip -Z1 "$deck_path" 'ppt/slides/slide*.xml' | wc -l | tr -d ' ')"
actual="$(pdfinfo "$pdf_path" | awk '/^Pages:/ {print $2}')"
if [[ "$expected" != "$actual" ]]; then
  echo "Slide/page mismatch: PPTX=$expected PDF=$actual" >&2
  exit 1
fi

echo "Rendered $actual pages to $render_dir"
