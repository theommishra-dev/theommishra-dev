# Profile cards

The README is a stack of animated SVG cards in `cards/`.

| File | Job |
|---|---|
| `config.py` | All the words, numbers, links and colours on the cards. Edit this first. |
| `render_readme_cards.py` | Draws every card into `cards/`. Standard library only. `STATIC=1` writes the final frame to `cards/static/` (git-ignored) for screenshots. |
| `fetch_contributions.py` | Pulls the contribution calendar and repo stats into `data/contributions.json` (GraphQL). |
| `subset_fonts.py` | One-off: subsets Instrument Serif and JetBrains Mono (OFL, sources in `fonts/src/`) to WOFF with `pyftsubset`, and writes `fonts/metrics.json`. Needs fonttools. |
| `make_portrait.py` | One-off: turns the avatar into `data/portrait.txt`. Needs Pillow. |

The Action in `.github/workflows/cards.yml` runs fetch then render every day and commits any change.

Preview locally: `python -m http.server` in the repo root, then open `/preview.html` (animated) or `/preview.html?static` (after `STATIC=1 python scripts/render_readme_cards.py`).
