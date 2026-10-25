# Build pipeline

`README.md` at the repository root is generated. Do not edit it by hand, your
changes will be overwritten on the next build.

```bash
python3 scripts/build_folio.py     # regenerate folio/ and README.md
python3 scripts/check_folio.py     # validate before pushing
python3 scripts/build_folio.py --check   # freshness only, writes nothing
```

Standard library only. Nothing here reaches the network.

## Where things come from

| Source | Owns |
|---|---|
| `data/profile.json` | Identity, tagline, location, status, the figures band, footer links |
| `data/repos.json` | Sections, and the repositories inside each one |
| `scripts/folio_theme.py` | Palette for both themes, type stack, shared SVG primitives, contrast maths |
| `scripts/folio_components.py` | The drawn components: header, section label, repository card, figures band |
| `scripts/build_folio.py` | Renders every component once per theme, then writes the README |

To change what the profile says, edit `data/`. To change how it looks, edit
`folio_components.py`. Those two concerns do not mix, which is the point.

## Themes

Every asset is generated twice, `-dark.svg` and `-light.svg`. The README picks
between them with a `<picture>` element and `prefers-color-scheme`, so the
profile follows the reader's GitHub theme.

Colours are declared only in `folio_theme.py`. Components reference tokens
(`ink`, `dim`, `chrome`, `accent`, `line`, `panel`, `bg`) and never literals,
so a palette change reaches everything at once and `check_folio.py` can verify
the whole set.

## Type

SVG text uses generic font stacks rather than a bundled face. GitHub serves
these images through its own proxy, which will not load a webfont, so a
bundled font would silently fall back anyway. Sizes and spacing are set to
survive that substitution rather than depend on one specific face.

Text is drawn into the images, so it is not selectable. Every section
therefore repeats its links as plain Markdown underneath, and every image
carries real alt text. The profile is usable with images disabled.

## Checks

`check_folio.py` is the gate, and CI runs it on every push:

| Check | Catches |
|---|---|
| assets | A README referencing an image that was never built, or built assets nothing references |
| xml | Malformed SVG from a bad string substitution |
| contrast | Any text colour falling below WCAG AA against the surface behind it, in either theme |
| alt text | An image shipped without a description |
| links | A malformed URL, or the same URL listed twice |
| freshness | Committed output drifting from what `data/` would build now |

The contrast check is the one that earns its keep. It caught the first palette
failing AA on the muted text colour in both themes, which is the colour used
for licence lines and locations: small, grey, and exactly what a sighted
designer stops noticing.

## Adding a repository

Add an entry to the right section in `data/repos.json`:

```json
{
  "slug": "repo-name",
  "name": "repo-name",
  "blurb": "One line, about sixty characters",
  "meta": "LICENCE . detail",
  "glyph": "tooling",
  "url": "https://github.com/SilentPayload/repo-name"
}
```

`glyph` picks the small drawing on the card: `curriculum`, `exercises`,
`tooling` or `writeups`. Then rebuild and check.

Blurbs wrap to two lines at 34 characters each. Anything longer is dropped
rather than drawn over the footer, so keep them short and check the render.
