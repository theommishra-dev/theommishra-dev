"""Render the profile README cards into cards/*.svg.

    python scripts/render_readme_cards.py            # animated cards
    STATIC=1 python scripts/render_readme_cards.py   # final frame only, for screenshots

Standard library only. Reads data/contributions.json (refreshed daily by the Action),
data/portrait.txt and the subset fonts in fonts/. Text and colours live in config.py.

The cards are shown through <img>, so they use only what works there: an inline <style>
with CSS keyframes, SMIL <set>/<animateTransform>, and fonts embedded as base64 WOFF.
Every animation sits behind prefers-reduced-motion: no-preference, and the markup
without animation IS the final frame.
"""
import base64
import json
import os
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import config as C

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"
# STATIC frames go to cards/static/ (git-ignored) so they never replace the animated cards
OUT = ROOT / ("cards/static" if STATIC else "cards")
METRICS = json.loads((ROOT / "fonts/metrics.json").read_text())
COL = C.COLORS

SERIF = "'Instrument Serif', Georgia, serif"
MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"
EASE = "cubic-bezier(.23,1,.32,1)"          # strong ease-out
SPRING = "cubic-bezier(.34,1.56,.64,1)"     # small overshoot

# Page-level stagger: each card starts later so the README plays top to bottom.
START = {"hero": 0.0, "tiles": 0.7, "activity": 1.1, "repos": 1.6, "certs": 2.0, "heatmap": 2.4}


# ---------- helpers ----------

def width(text, font, size):
    m = METRICS[font]
    return sum(m.get(ch, 0.6) for ch in text) * size


def font_face(*names):
    css = []
    for n in names:
        family, weight = n.split("-")
        fam = "Instrument Serif" if family == "serif" else "JetBrains Mono"
        b64 = base64.b64encode((ROOT / f"fonts/{n}.woff").read_bytes()).decode()
        css.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                   f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(css)


KEYFRAMES = f"""
@keyframes rise{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes swing{{from{{opacity:0;transform:translateY(30px) rotate(-3deg)}}to{{opacity:1;transform:none}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:none}}}}
@keyframes pop{{0%{{opacity:0;transform:scale(0)}}70%{{opacity:1;transform:scale(1.25)}}to{{opacity:1;transform:none}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
@keyframes ring{{0%{{opacity:.45;transform:scale(.08)}}60%,100%{{opacity:0;transform:scale(1)}}}}
@keyframes sweep{{0%{{transform:translateX(-260px) skewX(-18deg)}}35%,100%{{transform:translateX(560px) skewX(-18deg)}}}}
@keyframes nudge{{0%,70%,100%{{transform:none}}80%{{transform:translate(3px,-3px)}}90%{{transform:translate(0,0)}}}}
"""


def style(fonts, anim_css, extra_static=""):
    """Fonts + base classes always; animation rules only when motion is welcome."""
    smil_rules = ".smil{display:none}"
    css = font_face(*fonts) + smil_rules + extra_static
    if not STATIC:
        css += KEYFRAMES
        css += ("@media (prefers-reduced-motion:no-preference){"
                ".smil{display:inline}.smil-final{display:none}" + anim_css + "}")
    return f"<style>{css}</style>"


def svg(w, h, label, body, fonts, anim_css="", extra_static="", frame=True):
    bg = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="{COL["bg"]}" stroke="{COL["line"]}"/>'
          if frame else "")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'{style(fonts, anim_css, extra_static)}'
            f'{bg}{body}</svg>\n')


def anim(cls, delay):
    """class + delay; in STATIC mode no class, so nothing moves."""
    if STATIC:
        return ""
    return f' class="{cls}" style="animation-delay:{delay:.3f}s"'


def smil(xml):
    return "" if STATIC else xml


def text(x, y, s, size, fill, font=MONO, weight=400, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{extra}>{escape(s)}</text>')


def star(x, y, s, fill):
    """5-point star path (the mono font has no star glyph)."""
    import math
    pts = []
    for i in range(10):
        r = s if i % 2 == 0 else s * 0.45
        a = -math.pi / 2 + i * math.pi / 5
        pts.append(f"{x + r * math.cos(a):.2f},{y + r * math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def write(name, content):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(content)
    print(f"{(OUT / name).relative_to(ROOT)}.svg  {len(content.encode()) / 1024:.1f} KB")


# ---------- data ----------

def load():
    d = json.loads((ROOT / "data/contributions.json").read_text())
    days = [(date.fromisoformat(x["date"]), x["count"]) for x in d["days"]]
    return d, days


def stats(days):
    today = days[-1][0]
    year = [(dt, c) for dt, c in days if dt > today - timedelta(days=365)]
    active = sum(1 for _, c in year if c)
    busiest = max(year, key=lambda x: (x[1], x[0]))
    longest = run = 0
    for _, c in year:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # current streak: today may still be empty, so count back from yesterday in that case
    i = len(days) - 1
    if days[i][1] == 0:
        i -= 1
    current = 0
    while i >= 0 and days[i][1]:
        current += 1
        i -= 1
    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    months.reverse()
    per_month = [(ym, sum(c for dt, c in year if (dt.year, dt.month) == ym)) for ym in months]
    return {"total": sum(c for _, c in year), "active": active, "busiest": busiest,
            "longest": longest, "current": current, "months": per_month, "today": today}


# ---------- cards ----------

def hero():
    h = C.HERO
    t0 = START["hero"]
    body = []
    css = (f".rise{{animation:rise .9s {EASE} both}}.fade{{animation:fade .5s ease-out both}}"
           f".dot{{animation:pulse 2.4s ease-in-out infinite}}")
    # kicker with pulsing dot
    body.append(f'<circle cx="46" cy="52" r="4" fill="{COL["accent"]}"{anim("dot", t0)}/>')
    body.append(f'<g{anim("rise", t0 + .05)}>{text(60, 56.5, h["kicker"], 13, COL["muted"])}</g>')
    # name, one word at a time
    size, x, y = 104, 36, 160
    words = []
    for i, w in enumerate(h["name"]):
        words.append((w, x))
        body.append(f'<g{anim("rise", t0 + .15 + i * .14)}>{text(x, y, w, size, COL["ink"], SERIF)}</g>')
        x += width(w + " ", "serif-400", size)
    # shine sweeping across the last word: a gradient moved with SMIL (no background-clip in SVG)
    last, lx = words[-1]
    lw = width(last, "serif-400", size)
    body.append(smil(
        f'<defs><linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="{lx:.0f}" y1="0" '
        f'x2="{lx + 120:.0f}" y2="0" gradientTransform="translate(-200 0)">'
        f'<stop offset="0" stop-color="{COL["accent"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{COL["accent"]}" stop-opacity="1"/>'
        f'<stop offset="1" stop-color="{COL["accent"]}" stop-opacity="0"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" '
        f'values="-200 0;{lw + 80:.0f} 0;{lw + 80:.0f} 0" keyTimes="0;.28;1" dur="5s" '
        f'begin="{t0 + 1.4:.1f}s" repeatCount="indefinite"/></linearGradient></defs>'
        f'<g class="smil">{text(lx, y, last, size, "url(#shine)", SERIF)}</g>'))
    # one line about me
    for i, line in enumerate(h["about"]):
        body.append(f'<g{anim("rise", t0 + .45 + i * .1)}>{text(40, 208 + i * 23, line, 15, COL["ink"])}</g>')
    # tags
    x = 40
    for i, tag in enumerate(h["tags"]):
        w = width(tag, "mono-400", 11.5) + 22
        body.append(f'<g{anim("rise", t0 + .7 + i * .06)}>'
                    f'<rect x="{x:.1f}" y="262" width="{w:.1f}" height="26" rx="13" fill="none" stroke="{COL["line"]}"/>'
                    f'{text(x + 11, 279, tag, 11.5, COL["muted"])}</g>')
        x += w + 8
    # ASCII portrait, one row at a time
    rows = (ROOT / "data/portrait.txt").read_text().rstrip("\n").split("\n") if C.PORTRAIT else []
    if rows:
        fs, lh = 6.3, 7.5
        cols = max(len(r) for r in rows)
        px = 880 - 36 - cols * fs * .6
        py = (320 - len(rows) * lh) / 2 + lh * .8
        for i, r in enumerate(rows):
            if r.strip():
                body.append(f'<g{anim("fade", t0 + .25 + i * .018)}>'
                            f'{text(px, py + i * lh, r, fs, COL["ink"], extra=" xml:space=\"preserve\" opacity=\".78\"")}</g>')
    label = f'{" ".join(h["name"])}. {" ".join(h["about"])}'
    write("hero", svg(880, 320, label, "".join(body), ["serif-400", "mono-400"], css,
                      "text{white-space:pre}"))


def tile(i, t):
    W, H = 286, 220
    t0 = START["tiles"] + i * .15
    css = (f".swing{{transform-origin:50% 100%;animation:swing .9s {SPRING} both}}"
           f".ring{{transform-box:fill-box;transform-origin:center;animation:ring 4.5s ease-out infinite}}"
           f".sweep{{animation:sweep 6s {EASE} infinite}}.nudge{{animation:nudge 3s ease-in-out infinite}}"
           f".rise{{animation:rise .8s {EASE} both}}")
    v, fmt, suf = t["value"], t["fmt"], t["suffix"]
    if v is None:  # the Claude tile counts the certifications in config.CERTS
        v = len(C.CERTS)
    word = isinstance(v, str)  # a word instead of a number: no count-up, it just rises in
    final = v if word else fmt.format(v) + suf
    big = []
    # count-up: 18 SMIL <set> frames (CSS cannot change text)
    frames = 18
    begin = t0 + .45
    if word:
        big.append(f'<g{anim("rise", begin)}>{text(20, 122, final, 64, COL["ink"], SERIF)}</g>')
    elif not STATIC:
        sets = []
        for k in range(1, frames + 1):
            p = 1 - (1 - k / frames) ** 3
            val = v * p
            s = (fmt.format(int(round(val))) if "d" in fmt or "," in fmt else fmt.format(round(val, 1))) + suf
            if k == frames:
                s = final
            b = begin + (k - 1) * .05
            end = "" if k == frames else f' dur="0.05s"'
            fill = ' fill="freeze"' if k == frames else ""
            sets.append(f'<g visibility="hidden"><set attributeName="visibility" to="visible" begin="{b:.2f}s"{end}{fill}/>'
                        f'{text(20, 122, s, 64, COL["ink"], SERIF)}</g>')
        big.append(f'<g class="smil">{"".join(sets)}</g>')
    if not word:
        big.append(f'<g class="smil-final">{text(20, 122, final, 64, COL["ink"], SERIF)}</g>')
    body = [
        f'<defs><clipPath id="c{i}"><rect width="{W}" height="{H}" rx="16"/></clipPath>'
        f'<linearGradient id="g{i}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>',
        f'<g{anim("swing", t0)}>',
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="{COL["bg"]}" stroke="{COL["line"]}"/>',
        f'<g clip-path="url(#c{i})">',
        "" if STATIC else f'<circle cx="{W}" cy="0" r="170" fill="none" stroke="{COL["accent"]}" stroke-width="1.5" opacity="0" '
                          f'class="ring" style="animation-delay:{t0 + 1.2:.2f}s"/>',
        "" if STATIC else f'<rect x="0" y="-20" width="90" height="{H + 40}" fill="url(#g{i})" class="sweep" '
                          f'style="animation-delay:{t0 + 2:.2f}s;transform:translateX(-260px)"/>',
        '</g>',
        text(22, 38, t["label"], 11, COL["accent_ink"], weight=600, extra=' letter-spacing="1.6"'),
        f'<g{anim("nudge", t0 + 1.6)}>{text(W - 22, 40, "↗", 17, COL["muted"], extra=" text-anchor=\"end\"")}</g>',
        *big,
        text(22, 158, t["caption"][0], 12.5, COL["muted"]),
        text(22, 177, t["caption"][1], 12.5, COL["muted"]),
        text(22, 203, t["cta"] + " →", 12.5, COL["ink"], weight=600),
        '</g>',
    ]
    label = f'{t["label"].title()}: {final} {" ".join(t["caption"])}. {t["cta"]}.'
    # frame=False: the card's own rect lives inside the swinging group
    write(f'tile-{t["file"]}', svg(W, H, label, "".join(body), ["serif-400", "mono-400", "mono-600"], css, frame=False))


def activity(s):
    W, H = 880, 310
    t0 = START["activity"]
    css = (f".rise{{animation:rise .8s {EASE} both}}"
           f".grow{{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s {EASE} both}}"
           f".pop{{transform-box:fill-box;transform-origin:50% 100%;animation:pop .5s {EASE} both}}")
    body = [f'<g{anim("rise", t0)}>{text(40, 64, "Contributions", 36, COL["ink"], SERIF)}'
            f'{text(40, 88, "per month, last 12 months", 12, COL["muted"])}</g>']
    bd, bc = s["busiest"]
    cells = [("CONTRIBUTIONS", f'{s["total"]:,}', "in the last year"),
             ("ACTIVE DAYS", str(s["active"]), "of 365"),
             ("STREAK", f'{s["current"]} day' + ("" if s["current"] == 1 else "s"), f'best {s["longest"]}'),
             ("BUSIEST DAY", bd.strftime("%-d %b %Y"), f'{bc} contributions' if bc != 1 else "1 contribution")]
    sx = [372, 492, 600, 708]
    for i, (lab, val, sub) in enumerate(cells):
        body.append(f'<g{anim("rise", t0 + .1 + i * .07)}>'
                    f'{text(sx[i], 46, lab, 9.5, COL["muted"], extra=" letter-spacing=\"1.2\"")}'
                    f'{text(sx[i], 70, val, 17, COL["ink"], weight=600)}'
                    f'{text(sx[i], 88, sub, 11, COL["muted"])}</g>')
    # bars
    base, top = 262, 132
    hmax = base - top
    mx = max(c for _, c in s["months"]) or 1
    best = max(range(12), key=lambda i: (s["months"][i][1], i))
    slot = (W - 80) / 12
    bw = 34
    body.append(f'<line x1="40" y1="{base + .5}" x2="{W - 40}" y2="{base + .5}" stroke="{COL["line"]}"/>')
    for i, ((y, m), c) in enumerate(s["months"]):
        cx = 40 + slot * i + slot / 2
        x = cx - bw / 2
        mon = date(y, m, 1).strftime("%b")
        lab = mon + (f" {y % 100:02d}" if i == 0 or m == 1 else "")
        body.append(text(cx, base + 22, lab, 11, COL["muted"], extra=' text-anchor="middle"'))
        if c == 0:
            body.append(f'<rect x="{x:.1f}" y="{base - 3}" width="{bw}" height="3" rx="1.5" fill="{COL["faint"]}" opacity=".6"/>')
            continue
        h = max(6, c / mx * hmax)
        r = 4
        fill = COL["accent"] if i == best else COL["bar"]
        path = (f'M{x:.1f},{base} V{base - h + r:.1f} Q{x:.1f},{base - h:.1f} {x + r:.1f},{base - h:.1f} '
                f'H{x + bw - r:.1f} Q{x + bw:.1f},{base - h:.1f} {x + bw:.1f},{base - h + r:.1f} V{base} Z')
        body.append(f'<path d="{path}" fill="{fill}"{anim("grow", t0 + .3 + i * .06)}/>')
        if i == best:
            body.append(f'<g{anim("pop", t0 + .3 + i * .06 + .7)}>'
                        f'{text(cx, base - h - 10, str(c), 13, COL["ink"], weight=600, extra=" text-anchor=\"middle\"")}</g>')
    m_name = date(*s["months"][best][0], 1).strftime("%B %Y")
    label = (f'Contributions per month, last 12 months: {s["total"]} in total, {s["active"]} active days, '
             f'current streak {s["current"]} (best {s["longest"]}), busiest day {bd:%-d %b %Y} with {bc}. '
             f'Best month {m_name}.')
    write("activity", svg(W, H, label, "".join(body), ["serif-400", "mono-400", "mono-600"], css))


def heatmap(days, s):
    W, H = 880, 250
    t0 = START["heatmap"]
    css = (f".rise{{animation:rise .8s {EASE} both}}"
           f".pop{{transform-box:fill-box;transform-origin:center;animation:pop .45s {EASE} both}}")
    today = s["today"]
    # last 53 weeks, Sunday-first columns like GitHub
    start = today - timedelta(days=(today.weekday() + 1) % 7 + 52 * 7)
    counts = dict(days)
    nz = sorted(c for c in counts.values() if c)
    def level(c):
        if not c:
            return 0
        # quartiles of the non-zero days, like GitHub
        q = [nz[int(len(nz) * f)] for f in (.25, .5, .75)] if len(nz) >= 4 else [1, 2, 3]
        return 1 + sum(c > t for t in q)
    left, gx0, gy0, step, cell = 40, 74, 96, 14.5, 11.5
    body = [f'<g{anim("rise", t0)}>{text(left, 56, "A year on GitHub", 30, COL["ink"], SERIF)}</g>',
            f'<g{anim("rise", t0 + .05)}>{text(W - 40, 56, f"{s['total']} contributions", 12, COL["muted"], extra=" text-anchor=\"end\"")}</g>']
    for r, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(text(left, gy0 + r * step + cell - 2, lab, 10, COL["muted"]))
    last_month = None
    for col in range(53):
        wk = start + timedelta(days=col * 7)
        if wk.month != last_month and col < 51:
            if last_month is not None or wk.day <= 7:
                body.append(text(gx0 + col * step, gy0 - 10, wk.strftime("%b"), 10, COL["muted"]))
            last_month = wk.month
        cells = []
        for r in range(7):
            d = wk + timedelta(days=r)
            if d > today:
                break
            c = counts.get(d, 0)
            lv = level(c)
            cells.append(f'<rect x="{gx0 + col * step:.1f}" y="{gy0 + r * step:.1f}" width="{cell}" height="{cell}" '
                         f'rx="2.5" fill="{C.RAMP[lv]}"><title>{d:%-d %b %Y}: {c}</title></rect>')
        body.append(f'<g{anim("pop", t0 + .2 + col * .016)}>{"".join(cells)}</g>')
    # legend
    lx = W - 40 - 5 * step - 34
    ly = gy0 + 7 * step + 22
    body.append(text(lx - 8, ly + cell - 1.5, "Less", 10, COL["muted"], extra=' text-anchor="end"'))
    for i, c in enumerate(C.RAMP):
        body.append(f'<rect x="{lx + i * step:.1f}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" fill="{c}"/>')
    body.append(text(lx + 5 * step + 4, ly + cell - 1.5, "More", 10, COL["muted"]))
    label = f'Contribution graph for the last year: {s["total"]} contributions on {s["active"]} days.'
    write("heatmap", svg(W, H, label, "".join(body), ["serif-400", "mono-400"], css))


def repo_card(i, r, meta):
    W, H = 432, 184
    t0 = START["repos"] + i * .12
    css = f".rise{{animation:rise .8s {EASE} both}}.fade{{animation:fade .6s ease-out both}}"
    size = 30
    while width(r["name"], "serif-400", size) > W - 80 and size > 20:
        size -= 1
    body = [f'<g{anim("rise", t0)}>',
            text(24, 54, r["name"], size, COL["ink"], SERIF),
            text(W - 24, 50, "↗", 16, COL["muted"], extra=' text-anchor="end"'),
            *[text(24, 88 + k * 19, line, 12, COL["muted"]) for k, line in enumerate(r["lines"])],
            f'<line x1="24" y1="{H - 46.5}" x2="{W - 24}" y2="{H - 46.5}" stroke="{COL["line"]}"/>']
    fx, fy = 24, H - 22
    lang = meta.get("language")
    if lang:
        body.append(f'<circle cx="{fx + 5}" cy="{fy - 4}" r="5" fill="{meta.get("language_color") or COL["muted"]}"/>')
        body.append(text(fx + 16, fy, lang, 11.5, COL["muted"]))
        fx += 16 + width(lang, "mono-400", 11.5) + 22
    body.append(star(fx + 6, fy - 4.5, 6.5, COL["accent"]))
    body.append(text(fx + 18, fy, str(meta.get("stars", 0)), 11.5, COL["muted"]))
    if meta.get("pushed"):
        upd = "updated " + date.fromisoformat(meta["pushed"][:10]).strftime("%b %Y")
        body.append(text(W - 24, fy, upd, 11.5, COL["muted"], extra=' text-anchor="end"'))
    body.append("</g>")
    label = f'{r["name"]}: {" ".join(r["lines"])}'
    write(f'repo-{r["name"].lower()}', svg(W, H, label, "".join(body), ["serif-400", "mono-400"], css))


def certs():
    W = 880
    cols, gap, row_h = 3, 10, 62
    col_w = (W - 80 - gap * (cols - 1)) / cols
    rows = -(-len(C.CERTS) // cols)
    H = 112 + rows * row_h + 18
    t0 = START["certs"]
    css = (f".rise{{animation:rise .8s {EASE} both}}"
           f".pop{{transform-box:fill-box;transform-origin:center;animation:pop .45s {EASE} both}}")
    first, last = C.CERTS[0]["date"], C.CERTS[-1]["date"]
    body = [f'<g{anim("rise", t0)}>{text(40, 64, "Anthropic certifications", 34, COL["ink"], SERIF)}'
            f'{text(40, 88, f"{len(C.CERTS)} courses, {first} to {last}", 12, COL["muted"])}</g>',
            f'<g{anim("rise", t0 + .05)}>{text(W - 40, 60, "LinkedIn ↗", 12.5, COL["muted"], extra=" text-anchor=\"end\"")}</g>']
    for i, c in enumerate(C.CERTS):
        col, row = i % cols, i // cols
        x, y = 40 + col * (col_w + gap), 128 + row * row_h
        name, size = c["name"], 12.5
        while width(name, "mono-600", size) > col_w - 38 and size > 10:
            size -= .5
        d = t0 + .2 + i * .07
        body.append(f'<g{anim("rise", d)}>'
                    f'<rect x="{x:.1f}" y="{y - 16}" width="{col_w:.1f}" height="{row_h - 10}" rx="10" fill="{COL["panel"]}" stroke="{COL["line"]}"/>'
                    f'{text(x + 26, y + 3, name, size, COL["ink"], weight=600)}'
                    f'{text(x + 26, y + 23, f"{c['track']}  ·  {c['date']}", 11, COL["muted"])}</g>')
        # amber check, popping in after its row
        body.append(f'<g{anim("pop", d + .35)}><circle cx="{x + 13}" cy="{y - 1}" r="6" fill="{COL["accent"]}"/>'
                    f'<path d="M{x + 10},{y - 1} l2,2.2 l4,-4.4" fill="none" stroke="{COL["bg"]}" stroke-width="1.6" '
                    f'stroke-linecap="round" stroke-linejoin="round"/></g>')
    label = f"Anthropic certifications ({len(C.CERTS)}): " + "; ".join(f'{c["name"]}, {c["date"]}' for c in C.CERTS) + "."
    write("certs", svg(W, H, label, "".join(body), ["serif-400", "mono-400", "mono-600"], css))


def main():
    d, days = load()
    s = stats(days)
    hero()
    for i, t in enumerate(C.TILES):
        tile(i, t)
    activity(s)
    for i, r in enumerate(C.REPOS):
        repo_card(i, r, d["repos"].get(r["name"], {}))
    certs()
    heatmap(days, s)
    print("STATIC (final frame)" if STATIC else "animated")


if __name__ == "__main__":
    main()
