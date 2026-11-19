"""One-off helper: subset the source fonts into small WOFF files in fonts/.

Run locally when the fonts or the glyph set change (needs fonttools):
    ../../.venv/bin/python scripts/subset_fonts.py
The renderer only base64-embeds the WOFFs, so the daily Action needs no pip installs.
Source TTFs (SIL OFL 1.1) are in fonts/src/ with their licences.
"""
import json
import subprocess
import sys
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "fonts/src", ROOT / "fonts"
# printable ASCII + the few symbols the cards draw
EXTRA = "→↗↑·×★●"
UNICODES = "U+0020-007E," + ",".join(f"U+{ord(c):04X}" for c in EXTRA)


def subset(src, dst):
    subprocess.run([sys.executable, "-m", "fontTools.subset", str(src),
                    f"--unicodes={UNICODES}", "--flavor=woff", "--layout-features=kern,tnum,zero",
                    "--no-hinting", "--desubroutinize", f"--output-file={dst}"], check=True)
    print(f"{dst.name}: {dst.stat().st_size / 1024:.1f} KB")
    f = TTFont(dst)
    upm, hmtx = f["head"].unitsPerEm, f["hmtx"]
    return {chr(u): round(hmtx[g][0] / upm, 4) for u, g in f.getBestCmap().items()}


def main():
    # advance widths in em, so the renderer can measure text without fonttools
    metrics = {"serif-400": subset(SRC / "InstrumentSerif-Regular.ttf", OUT / "serif-400.woff")}
    for wght in (400, 600):
        tmp = OUT / f"_mono-{wght}.ttf"
        instancer.instantiateVariableFont(TTFont(SRC / "JetBrainsMono.ttf"), {"wght": wght}).save(tmp)
        metrics[f"mono-{wght}"] = subset(tmp, OUT / f"mono-{wght}.woff")
        tmp.unlink()
    (OUT / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
