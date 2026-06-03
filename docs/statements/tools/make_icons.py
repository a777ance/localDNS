#!/usr/bin/env python3
"""Rasterize the brand SVGs to the PNG sizes the PWA manifest needs.

Run once, or whenever icons/icon.svg changes:
    pip install cairosvg
    python3 tools/make_icons.py

The resulting PNGs are committed to the repo, so the repo itself has NO runtime
dependency on cairosvg — this script is only needed to regenerate them.
"""
import os, cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "..", "icons")


def render(src, out, size):
    cairosvg.svg2png(url=os.path.join(ICONS, src), write_to=os.path.join(ICONS, out),
                     output_width=size, output_height=size)
    print("wrote", out, f"{size}x{size}")


if __name__ == "__main__":
    render("icon.svg", "icon-192.png", 192)
    render("icon.svg", "icon-512.png", 512)
    render("icon.svg", "apple-touch-icon.png", 180)
    render("icon-maskable.svg", "icon-512-maskable.png", 512)
