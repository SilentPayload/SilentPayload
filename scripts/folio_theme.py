"""Shared palette, type scale and SVG primitives for the folio build.

Every generated asset is produced twice, once per theme, and the README picks
between them with a <picture> element. Nothing here reaches the network and
nothing depends on a font being installed: type is declared with generic
families so GitHub renders it with whatever the viewer has.
"""

from xml.sax.saxutils import escape

# --- palette ---------------------------------------------------------------
# Drawn from the drafting-table end of the spectrum: warm bone ink on near
# black, with a single clay accent reserved for things that are actually
# urgent. The light theme is the same drawing on paper, not an inversion.

THEMES = {
    "dark": {
        "bg":     "#0c0c0c",
        "panel":  "#121211",
        "ink":    "#d8d4b4",
        "dim":    "#7f7d74",
        "chrome": "#9d9a8c",
        "accent": "#e8735f",
        "line":   "#2a2924",
    },
    "light": {
        "bg":     "#faf8f2",
        "panel":  "#f2efe4",
        "ink":    "#26251f",
        "dim":    "#706d62",
        "chrome": "#5c5a50",
        "accent": "#b8492f",
        "line":   "#ddd9cc",
    },
}

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# The SP signet, in an 18 x 14 grid. A blocky S and P sharing a baseline.
SIGNET_PATH = ("M0 0h8v3H3v2.5h5V14H0v-3h5V8.5H0z"
               "M10 0h8v8.5h-5V14h-3zm3 3v2.5h2V3z")


def svg_open(width, height, pal, bg=True):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img">'
    ]
    if bg:
        parts.append(f'<rect width="{width}" height="{height}" fill="{pal["bg"]}"/>')
    return "".join(parts)


def svg_close():
    return "</svg>"


def text(x, y, body, pal, size=13, fill="ink", family=MONO, weight=400,
         anchor="start", spacing=None, opacity=None):
    attrs = [
        f'x="{x}"', f'y="{y}"',
        f'font-family="{family}"',
        f'font-size="{size}"',
        f'font-weight="{weight}"',
        f'fill="{pal[fill]}"',
    ]
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    return f'<text {" ".join(attrs)}>{escape(body)}</text>'


def hairline(x1, y1, x2, y2, pal, stroke="line", width=1, dash=None, opacity=None):
    attrs = [
        f'x1="{x1}"', f'y1="{y1}"', f'x2="{x2}"', f'y2="{y2}"',
        f'stroke="{pal[stroke]}"', f'stroke-width="{width}"',
    ]
    if dash:
        attrs.append(f'stroke-dasharray="{dash}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    return f'<line {" ".join(attrs)}/>'


def frame(x, y, w, h, pal, stroke="line", width=1, fill="none"):
    f = "none" if fill == "none" else pal[fill]
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{f}" '
            f'stroke="{pal[stroke]}" stroke-width="{width}"/>')


def registration(x, y, w, h, pal, arm=7, stroke="dim", width=1, opacity=0.9):
    """Crop marks at the four corners of a box.

    This is the folio's recurring device. It sits outside the content box the
    way printer's marks sit outside a trim edge, so a card reads as something
    drawn and measured rather than a rounded UI tile.
    """
    out = []
    for cx, cy, dx, dy in (
        (x, y, 1, 1),
        (x + w, y, -1, 1),
        (x, y + h, 1, -1),
        (x + w, y + h, -1, -1),
    ):
        out.append(hairline(cx, cy, cx + arm * dx, cy, pal, stroke, width, opacity=opacity))
        out.append(hairline(cx, cy, cx, cy + arm * dy, pal, stroke, width, opacity=opacity))
    return "".join(out)


def signet(x, y, scale, pal, fill="ink"):
    s = scale / 14.0
    return (f'<g transform="translate({x},{y}) scale({s})" fill="{pal[fill]}">'
            f'<path d="{SIGNET_PATH}"/></g>')


def rule_with_ticks(x, y, w, pal, ticks=8, stroke="line"):
    """A measured rule: one hairline with evenly spaced tick marks."""
    out = [hairline(x, y, x + w, y, pal, stroke)]
    for i in range(ticks + 1):
        tx = x + (w * i / ticks)
        length = 4 if i % 2 == 0 else 2
        out.append(hairline(tx, y, tx, y - length, pal, stroke))
    return "".join(out)


# --- contrast, used by check_folio.py --------------------------------------

def _channel(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(fg, bg):
    a, b = luminance(fg), luminance(bg)
    lo, hi = sorted((a, b))
    return (hi + 0.05) / (lo + 0.05)
