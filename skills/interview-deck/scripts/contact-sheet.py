#!/usr/bin/env python3

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(description="Build a numbered contact sheet from rendered slide PNGs")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, default=3)
    args = parser.parse_args()

    files = sorted(args.input_dir.glob("slide-*.png"))
    if not files:
        raise SystemExit(f"No slide-*.png files in {args.input_dir}")

    thumb_w, thumb_h, label_h, gap = 640, 360, 34, 18
    rows = math.ceil(len(files) / args.columns)
    canvas = Image.new("RGB", (
        args.columns * thumb_w + (args.columns + 1) * gap,
        rows * (thumb_h + label_h) + (rows + 1) * gap,
    ), "#D8DEE8")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    resample = getattr(Image, "Resampling", Image).LANCZOS

    for index, file_path in enumerate(files):
        image = Image.open(file_path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), resample)
        col, row = index % args.columns, index // args.columns
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        canvas.paste(image, (x, y))
        draw.text((x, y + thumb_h + 8), f"{index + 1:02d}  {file_path.name}", fill="#10233E", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, quality=92)
    print(args.output)


if __name__ == "__main__":
    main()
