"""One-off helper: turn the GitHub avatar into data/portrait.txt (ASCII art).

Run locally when the avatar changes (needs Pillow):
    ../../.venv/bin/python scripts/make_portrait.py avatar.png
The renderer only reads data/portrait.txt, so the daily Action needs no Pillow.
"""
import sys
from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps

COLS, ROWS = 64, 34          # mono cell is ~0.6 wide, so 64x34 keeps the face square-ish
RAMP = " .:-=+*#%@"          # dark -> bright (cards are dark, bright pixels get dense glyphs)


def background_mask(im):
    """Flood-fill the maroon studio backdrop from the borders."""
    w, h = im.size
    px = im.load()
    def is_bg(x, y):
        r, g, b = px[x, y]
        return r - g >= 12 and max(r, g, b) < 80
    seen = [[False] * h for _ in range(w)]
    q = deque((x, y) for x in range(w) for y in (0, h - 1))
    q.extend((x, y) for y in range(h) for x in (0, w - 1))
    while q:
        x, y = q.popleft()
        if seen[x][y] or not is_bg(x, y):
            continue
        seen[x][y] = True
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny]:
                q.append((nx, ny))
    m = Image.new("L", im.size, 0)
    mp = m.load()
    for x in range(w):
        for y in range(h):
            if seen[x][y]:
                mp[x, y] = 255
    return m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))


def main(src, out="data/portrait.txt"):
    im = Image.open(src).convert("RGB").resize((230, 230))
    bg = background_mask(im)
    lum = ImageOps.autocontrast(ImageOps.grayscale(im), cutoff=1)
    small = lum.resize((COLS, ROWS), Image.LANCZOS)
    bgs = bg.resize((COLS, ROWS), Image.BILINEAR)
    rows = []
    for y in range(ROWS):
        line = ""
        for x in range(COLS):
            if bgs.getpixel((x, y)) > 140:
                line += " "
                continue
            v = small.getpixel((x, y)) / 255
            i = 1 + round(v ** 0.9 * (len(RAMP) - 2))   # foreground never blank, so hair keeps its shape
            line += RAMP[i]
        rows.append(line.rstrip())
    Path(out).write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main(sys.argv[1])
