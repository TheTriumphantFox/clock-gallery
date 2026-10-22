# Clock Gallery

79 analogue clock faces, each one a Lua/Cairo program that
[Conky](https://github.com/brndnmtthws/conky) draws on a Linux desktop. This
site is the **screenshots only** — the clock source lives elsewhere and is not
published here.

Every image is the clock's own drawing code run once into an offscreen cairo
surface: same code path, same vector artwork, same size as it is drawn on
screen, with no window manager, compositor or screen capture in the loop. That
is why the hands, gears and moon phases come out crisp rather than as a
photograph of a monitor.

- 79 dials, 22 makers, one page
- 640×640 transparent PNGs in `assets/img/`
- filter, lightbox, and a light/dark matte behind each dial
- no framework, no build step, no external requests — GitHub Pages serves the
  files as they are

## The dials

The tree they come from is organised by the model that wrote each clock, and
the page keeps that grouping: each section is one maker, and the small
monospace line under a caption is the dial's folder name. Recurring subjects
across makers — a Hamilton-style field dial, an openworked skeleton, an
orrery with no hands — are easy to compare side by side.

## Regenerating the images

Needs the clock tree locally (default `~/.config/conky/clocks`) and a conky
built with Lua + cairo:

```sh
CAP_OUT=assets/img CAP_META=tools/manifest.json conky -c tools/capture/capture.conf
python3 tools/build_site.py
```

`tools/capture/capture.lua` asks the clock tree's own loader for every dial it
can discover, draws each one into an image surface, and writes
`tools/manifest.json` (id, name, one-line description, filename).
`tools/build_site.py` turns that manifest into `index.html`.

Options: `CLOCK_DIR` (clock tree), `CAP_SIZE` (canvas in px, default 640),
`CAP_IDS` (file of ids, one per line), `CAP_ONLY` (substring filter).

## Layout

    index.html              the gallery
    assets/img/*.png        one 640×640 render per dial
    tools/capture/          headless capture, run through conky
    tools/build_site.py     manifest -> index.html
    tools/manifest.json     the metadata the page is built from
