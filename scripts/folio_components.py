"""The drawn components of the profile: header, section labels, project cards
and the figures band.

Each builder returns an SVG string for one theme. build_folio.py calls them
once per theme and writes the pair.
"""

from folio_theme import (
    THEMES, MONO, SANS, svg_open, svg_close, text, hairline, frame,
    registration, signet, rule_with_ticks,
)

HEADER_W = 880
LABEL_W, LABEL_H = 880, 38
CARD_W, CARD_H = 272, 164
FIGURES_W, FIGURES_H = 880, 96


def wrap(body, max_chars, lines=2):
    """Break text on word boundaries. Monospace, so characters are a fair
    proxy for width. Returns at most `lines` strings; anything that does not
    fit is dropped rather than silently overlapping what sits below."""
    words, out, cur = body.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = w
            if len(out) == lines:
                break
    if cur and len(out) < lines:
        out.append(cur)
    return out[:lines]



def header(profile, pal):
    """Identity block: signet, handle, real name, what the person does.

    Height is derived from the content. A longer tagline grows the block
    rather than pushing the location line into the crop marks.
    """
    pad, left_in = 26, 12
    lines = wrap(profile["tagline"], 110, lines=3)

    tag_top = pad + 100
    loc_y = tag_top + (len(lines) - 1) * 19 + 26
    box_h = loc_y - pad + 16
    height = box_h + 2 * pad

    o = [svg_open(HEADER_W, height, pal)]
    left = pad + left_in
    right = HEADER_W - pad - left_in

    o.append(registration(pad, pad, HEADER_W - 2 * pad, box_h, pal, arm=9))
    o.append(signet(left, pad + 18, 32, pal))

    o.append(text(left + 56, pad + 40, profile["handle"], pal,
                  size=27, fill="ink", family=MONO, weight=500))
    o.append(text(left + 56, pad + 62, profile["name"], pal,
                  size=13, fill="chrome", family=MONO))

    o.append(hairline(left, pad + 78, right, pad + 78, pal))

    for i, line in enumerate(lines):
        o.append(text(left, tag_top + i * 19, line, pal,
                      size=14, fill="ink", family=SANS))

    o.append(text(left, loc_y, profile["location"], pal,
                  size=11.5, fill="dim", family=MONO, spacing=1.2))
    if profile.get("status"):
        o.append(text(right, loc_y, profile["status"], pal,
                      size=11.5, fill="accent", family=MONO,
                      anchor="end", spacing=1.2))
    return "".join(o) + svg_close()


def label(title, meta, pal):
    """A section heading. Numbered rule, title, right-aligned count."""
    o = [svg_open(LABEL_W, LABEL_H, pal)]
    o.append(text(0, 22, title.upper(), pal,
                  size=13, fill="ink", family=MONO, weight=500, spacing=3.4))

    approx = len(title) * (13 * 0.6 + 3.4) + 18
    o.append(hairline(approx, 17, LABEL_W - len(meta) * 7.0 - 16, 17, pal, opacity=0.9))
    o.append(text(LABEL_W - 4, 22, meta, pal,
                  size=11.5, fill="dim", family=MONO, anchor="end", spacing=1.4))
    return "".join(o) + svg_close()


# --- per-card glyphs -------------------------------------------------------
# Each card carries a small drawing of what the repository actually does.
# They are built from the same hairline vocabulary as everything else.

def _glyph(kind, x, y, w, h, pal):
    o = []
    if kind == "curriculum":
        # ten session marks across two weeks, the first five filled
        for i in range(10):
            gx = x + i * (w / 10.0)
            filled = i < 5
            o.append(f'<rect x="{gx:.1f}" y="{y + (0 if filled else 5)}" '
                     f'width="{w / 10.0 - 4:.1f}" height="{h - (0 if filled else 10)}" '
                     f'fill="{pal["chrome"] if filled else "none"}" '
                     f'stroke="{pal["dim"]}" stroke-width="1"/>')
    elif kind == "exercises":
        # a log with one line picked out
        for i in range(6):
            ly = y + 3 + i * ((h - 6) / 5.0)
            hit = i == 3
            width = w * (0.95 if hit else (0.5 + 0.1 * (i % 3)))
            o.append(hairline(x, ly, x + width, ly, pal,
                              "accent" if hit else "dim",
                              1.6 if hit else 1, opacity=1 if hit else 0.65))
    elif kind == "tooling":
        # severity histogram: 3 / 3 / 3 and a tall critical
        bars = [(0.95, "accent"), (0.62, "chrome"), (0.4, "dim"), (0.22, "dim")]
        bw = w / 6.0
        for i, (frac, col) in enumerate(bars):
            bh = h * frac
            o.append(f'<rect x="{x + i * bw * 1.35:.1f}" y="{y + h - bh:.1f}" '
                     f'width="{bw:.1f}" height="{bh:.1f}" fill="{pal[col]}"/>')
    elif kind == "writeups":
        for i in range(5):
            ly = y + 2 + i * ((h - 4) / 4.0)
            o.append(hairline(x, ly, x + w * (0.9 if i % 2 == 0 else 0.6),
                              ly, pal, "dim", 1, opacity=0.7))
    else:
        o.append(frame(x, y, w, h, pal, "dim"))
    return "".join(o)


def card(repo, pal):
    """One repository, drawn as a measured card."""
    o = [svg_open(CARD_W, CARD_H, pal)]
    pad = 12
    inner_w, inner_h = CARD_W - 2 * pad, CARD_H - 2 * pad
    left = pad + 14

    o.append(frame(pad, pad, inner_w, inner_h, pal, "line", 1, "panel"))
    o.append(registration(pad, pad, inner_w, inner_h, pal, arm=6, opacity=0.8))

    o.append(_glyph(repo.get("glyph", ""), left, pad + 16, inner_w - 28, 34, pal))
    o.append(hairline(left, pad + 62, CARD_W - left, pad + 62, pal))

    name = repo["name"]
    size = 13 if len(name) <= 22 else 11
    o.append(text(left, pad + 82, name, pal,
                  size=size, fill="ink", family=MONO, weight=500))

    for i, line in enumerate(wrap(repo["blurb"], 34, lines=2)):
        o.append(text(left, pad + 100 + i * 14, line, pal,
                      size=10.5, fill="chrome", family=MONO))

    o.append(text(left, CARD_H - pad - 12, repo.get("meta", ""), pal,
                  size=10, fill="dim", family=MONO, spacing=1.1))
    return "".join(o) + svg_close()


def figures(stats, pal):
    """The numbers band. One measured rule, values above their labels."""
    o = [svg_open(FIGURES_W, FIGURES_H, pal)]
    o.append(rule_with_ticks(0, 30, FIGURES_W, pal, ticks=len(stats) * 2))

    step = FIGURES_W / float(len(stats))
    for i, item in enumerate(stats):
        cx = i * step + 4
        colour = "accent" if item.get("emphasis") else "ink"
        o.append(text(cx, 22, str(item["value"]), pal,
                      size=25, fill=colour, family=MONO, weight=500))
        o.append(text(cx, 50, item["label"].upper(), pal,
                      size=10, fill="dim", family=MONO, spacing=2.2))
        if item.get("note"):
            o.append(text(cx, 66, item["note"], pal,
                          size=10, fill="chrome", family=MONO))
        if i:
            o.append(hairline(i * step - 10, 4, i * step - 10, 72, pal, opacity=0.8))
    return "".join(o) + svg_close()
