#!/usr/bin/env python3
"""Build the clock gallery page from tools/manifest.json.

The manifest is written by tools/capture/capture.lua (see tools/capture/).
This script only turns it into a static page: it groups the dials by the model
folder they live under, tidies the one-line blurbs, and writes index.html.
No build step, no dependencies, no framework -- GitHub Pages serves the result
as it is.

    python3 tools/build_site.py
"""

import json
import re
import html
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "manifest.json"
OUT = ROOT / "index.html"

# A blurb that is really just a filename, a model name, or boilerplate.
JUNK = re.compile(
    r"^("
    r"[\w.\-]+\.lua"          # vantage-field.lua
    r"|conky clock\b.*"        # "Conky clock", "Conky clock (the Astral set)…"
    r"|load error"
    r"|\d+b\b.*"              # bare model-ish strings handled below too
    r")$",
    re.I,
)


def model_of(dial_id: str) -> str:
    """The model folder a dial lives under; ids are <model>/<clock>[/<clock>]."""
    return dial_id.split("/")[0]


def slug_of(dial_id: str) -> str:
    return dial_id.split("/")[-1]


# Dials that two models made together. The clock tree's own README is the
# source of this: Claude Opus 5.5 wrote the design and the plan file, and
# Qwen3.8 Flash-Next IQ3_S wrote every line of code from it. These are listed
# in their own section so the co-author credit is impossible to miss, and they
# are left out of the single-author section for their folder.
PLANERS = {
    "set1": {
        "title": "First Opus plan",
        "date": "2026-10-18",
        "plan": "PLAN-opus-5.5-2026-10-18.md",
        "note": "Claude Opus 5.5 specified every colour, centre and size, the gear helper, "
                "and precomputed geometry such as the 60 points where minute rays meet the "
                "Ventura's asymmetric dial edge. Qwen3.8 Flash-Next IQ3_S wrote every line "
                "of code from that plan in three turns.",
        "ids": ["qwen3.8-flash-next-iq3s/ventura-shield",
                "qwen3.8-flash-next-iq3s/going-train",
                "qwen3.8-flash-next-iq3s/modulus"],
    },
    "set2": {
        "title": "Second Opus plan",
        "date": "2026-10-18",
        "plan": "PLAN-opus-5.5-2026-10-18-set2.md",
        "note": "Same split, built in one 18-minute delegated run with no feedback rounds.",
        "ids": ["qwen3.8-flash-next-iq3s/intra-chrono",
                "qwen3.8-flash-next-iq3s/flying-tourbillon",
                "qwen3.8-flash-next-iq3s/heliotrope"],
    },
    "astral": {
        "title": "The Astral set",
        "date": "2026-10-21",
        "plan": "PLAN-opus-5.5-2026-10-21-astral.md + astral/astro.lua",
        "note": "Opus also wrote the shared astronomy -- Meeus Sun, Moon, sidereal time, "
                "precession and eclipses, JPL planet elements, about 260 stars, the Milky Way "
                "and the Chaldean planetary hours -- checked against the eclipses of 2018-28 "
                "and the 2020 and 2026 great conjunctions. Qwen drew all three faces from it "
                "in one 57-minute run.",
        "ids": ["qwen3.8-flash-next-iq3s/long-exposure",
                "qwen3.8-flash-next-iq3s/saros",
                "qwen3.8-flash-next-iq3s/ephemeris-loom"],
    },
}

CREDIT = {"plan": "Claude Opus 5.5", "build": "Qwen3.8 Flash-Next IQ3_S"}

# The co-authored dials' own first comment lines say nothing useful ("Conky
# clock"), so their descriptions are written out here, taken from the clock
# tree's README, which records what each face actually shows.
BLURB = {
    "qwen3.8-flash-next-iq3s/ventura-shield":
        "A Hamilton Ventura with markers fanned out to the asymmetric dial edge.",
    "qwen3.8-flash-next-iq3s/going-train":
        "A skeleton: barrel, wheel train, stepping escape wheel, pallet fork and a 2.5 Hz "
        "balance whose hairspring breathes.",
    "qwen3.8-flash-next-iq3s/modulus":
        "A 120-pin times table whose multiplier is the hour plus two, so the string figure "
        "morphs through the day; the time is read from beads strung on the rim.",
    "qwen3.8-flash-next-iq3s/intra-chrono":
        "A Hamilton Intra-Matic–style panda chronograph: tachymeter flange, running seconds "
        "at 9, a 30-minute counter at 3, and a 4 Hz sweep.",
    "qwen3.8-flash-next-iq3s/flying-tourbillon":
        "A black-and-gold skeleton whose escape wheel, pallet fork and 2.5 Hz balance ride a "
        "cage at 6 that turns once a minute, with a blued pointer on the cage for the seconds.",
    "qwen3.8-flash-next-iq3s/heliotrope":
        "A 640-seed phyllotaxis head. The hands are beams of light that make the seeds glow, "
        "and one of 60 petals unfurls each second.",
    "qwen3.8-flash-next-iq3s/long-exposure":
        "Sidereal time as a live long-exposure photograph facing north: star trails, a leaning "
        "treeline, the smeared Milky Way, meteors from the real radiants, and an amber camera "
        "stamp for the local sidereal time.",
    "qwen3.8-flash-next-iq3s/saros":
        "Eclipse time on a bronze Antikythera-style spiral of 223 lunations holding every "
        "eclipse of 2018–2036 as an inlay, with a gilt dragon ring for the Moon's nodes.",
    "qwen3.8-flash-next-iq3s/ephemeris-loom":
        "Planetary time as a horoscope wheel with the Ascendant held at 9 o'clock: a year of "
        "each body's path woven to a bead on the now ring, retrograde runs dashed.",
}


def credit_of(dial_id: str):
    """Which co-authored set a dial belongs to, or None."""
    for key, s in PLANERS.items():
        if dial_id in s["ids"]:
            return key, s
    return None, None


def credit_line(dial_id: str) -> str:
    key, _ = credit_of(dial_id)
    if not key:
        return ""
    return (f"<b>{CREDIT['plan']}</b> plan · <b>{CREDIT['build']}</b> code")


def credit_plain(dial_id: str) -> str:
    key, _ = credit_of(dial_id)
    return "" if not key else f"{CREDIT['plan']} plan, {CREDIT['build']} code"


def clean_blurb(blurb: str, name: str, dial_id: str) -> str:
    """Drop blurbs that say nothing, and prefixes that just repeat the name."""
    b = (blurb or "").strip()
    if not b or JUNK.match(b):
        return ""
    if b.lower() in {model_of(dial_id).lower(), name.lower()}:
        return ""

    # "openworked-calibre : a skeletonised ..." / "glm-4.7-flash hamilton -- ..."
    # The prefix is the id, not a description.
    last = slug_of(dial_id).replace("_", "-")
    b = re.sub(rf"^{re.escape(last)}\s*[:\-—–]\s*", "", b, flags=re.I)
    b = re.sub(rf"^{re.escape(model_of(dial_id))}(\s+{re.escape(last)})?\s*[:\-—–]\s*",
               "", b, flags=re.I)
    # "Hamilton Atelier: a warm, ..." -- the name again.
    b = re.sub(rf"^{re.escape(name)}\s*[:\-—–]\s*", "", b, flags=re.I)
    # "Clock 1: field watch ..." -- numbering from a generation prompt.
    b = re.sub(r"^clock\s*\d+\s*[:\-—–]\s*", "", b, flags=re.I)

    b = b.strip(" -—–:")
    b = re.sub(r"[.,;:]?\u2026$", "\u2026", b)   # "the dial…." -> "the dial…"
    if len(b) < 4:
        return ""
    return b[0].upper() + b[1:]


def main() -> None:
    rows = json.loads(MANIFEST.read_text())
    for r in rows:
        # The manifest is written by capture.lua; keep the page independent of
        # wherever the PNG happened to be written.
        r["file"] = Path(r["file"]).name
        r["model"] = model_of(r["id"])
        r["slug"] = slug_of(r["id"])
        r["blurb"] = BLURB.get(r["id"]) or clean_blurb(r.get("blurb", ""), r["name"], r["id"])

    groups: "OrderedDict[str, list]" = OrderedDict()
    shared: "OrderedDict[str, list]" = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["model"], r["id"])):
        key, _ = credit_of(r["id"])
        if key:
            shared.setdefault(key, []).append(r)
        else:
            groups.setdefault(r["model"], []).append(r)
    # The dial whose author is unknown belongs at the end, not among the models.
    if "unknown" in groups:
        groups.move_to_end("unknown")

    n_dials = len(rows)
    n_models = len([m for m in groups if m != "unknown"])
    n_shared = sum(len(v) for v in shared.values())

    def card(r, credit=False):
        cap = html.escape(r["name"])
        blurb = (f'<p class="blurb">{html.escape(r["blurb"])}</p>'
                 if r["blurb"] else "")
        model = r["model"]
        note = credit_line(r["id"]) if credit else ""
        badge = '<span class="badge">co-authored</span>' if credit else ""
        plain = credit_plain(r["id"])
        text = html.escape(f"{r['name']} {model} {r['slug']} {r['blurb']} {plain}".lower())
        return f"""      <figure class="card" tabindex="0"
          data-img="assets/img/{html.escape(r['file'])}"
          data-name="{cap}" data-model="{html.escape(model)}"
          data-credit="{html.escape(plain)}" data-text="{text}">
        <div class="matte">{badge}<img src="assets/img/{html.escape(r['file'])}"
             alt="{cap}, an analogue clock face" loading="lazy" width="640" height="640"></div>
        <figcaption>
          <span class="name">{cap}</span>
          {blurb}
          {'<span class="credit">' + note + '</span>' if note else ''}
          <span class="slug">{html.escape(r['slug'])}</span>
        </figcaption>
      </figure>"""

    cards = []

    # Co-authored first: two names on the work, so it gets its own section.
    if shared:
        blocks = []
        for key, s in PLANERS.items():
            items = shared.get(key) or []
            if not items:
                continue
            blocks.append(
                '    <div class="setwrap">\n'
                f'      <h3 class="set"><span>{html.escape(s["title"])}</span>'
                f'<em>{html.escape(s["date"])}</em>'
                f'<code>{html.escape(s["plan"])}</code></h3>\n'
                f'      <p class="setnote">{html.escape(s["note"])}</p>\n'
                '      <div class="grid">\n'
                + "\n".join(card(r, credit=True) for r in items) +
                "\n      </div>\n    </div>")
        cards.append(
            f'  <section class="group shared" data-model="co-authored">\n'
            f'    <h2 class="model"><span class="model-name">'
            f'{html.escape(CREDIT["plan"])} \u00d7 {html.escape(CREDIT["build"])}</span>'
            f'<span class="model-n">{n_shared} co-authored</span></h2>\n'
            + "\n".join(blocks) + "\n  </section>")

    for model, items in groups.items():
        extra = ""
        n_shared_in = sum(1 for v in shared.values() for r in v if r["model"] == model)
        if n_shared_in:
            extra = (f'<span class="model-more">+{n_shared_in} co-authored '
                     f'listed above</span>')
        head = (
            f'<h2 class="model" id="m-{html.escape(model)}">'
            f'<span class="model-name">{html.escape(model)}</span>'
            f'{extra}<span class="model-n">{len(items)}</span></h2>'
        )
        tiles = [card(r) for r in items]
        cards.append(f'  <section class="group" data-model="{html.escape(model)}">\n'
                     f'    {head}\n    <div class="grid">\n' + "\n".join(tiles) +
                     "\n    </div>\n  </section>")

    page = TEMPLATE.replace("<!--CARDS-->", "\n".join(cards))
    page = page.replace("<!--N-->", str(n_dials))
    page = page.replace("<!--MODELS-->", str(n_models))
    page = page.replace("<!--SHARED-->", str(n_shared))
    OUT.write_text(page)
    print(f"{OUT}: {n_dials} dials in {len(groups)} groups"
          f" + {n_shared} co-authored in {len(shared)} sets")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clock Gallery — <!--N--> analogue dials drawn in Lua/Cairo</title>
<meta name="description" content="<!--N--> analogue clock faces, each one a Lua/Cairo program
  that Conky runs on a Linux desktop. Rendered offscreen at their desktop size — screenshots, not source.">
<meta property="og:title" content="Clock Gallery">
<meta property="og:description" content="<!--N--> analogue dials drawn in Lua/Cairo, rendered from the code that runs them.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='13' fill='none' stroke='%23c8a24a' stroke-width='2'/%3E%3Cpath d='M16 8v8l6 3' fill='none' stroke='%23e8e4dc' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E">
<style>
  :root{
    --bg:#0d1013; --ink:#e9e6df; --muted:#9aa3ad; --line:#252b32;
    --card:#161a1f; --matte:#242a31; --accent:#c8a24a;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
    --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,sans-serif;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);
       font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
  body::before{content:"";position:fixed;inset:0;pointer-events:none;
    background:radial-gradient(1200px 600px at 50% -10%,#1a2027 0%,transparent 60%)}
  header{position:relative;padding:56px 24px 8px;max-width:1320px;margin:0 auto}
  h1{font-family:var(--serif);font-weight:600;font-size:clamp(30px,5vw,52px);
     margin:0 0 10px;letter-spacing:.01em}
  .lede{max-width:74ch;color:var(--muted);margin:0 0 22px;font-size:16px}
  .lede b{color:var(--ink);font-weight:600}
  .bar{position:sticky;top:0;z-index:5;display:flex;gap:12px;align-items:center;flex-wrap:wrap;
       padding:12px 24px;margin:22px 0 0;background:rgba(13,16,19,.86);
       backdrop-filter:blur(10px);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
  .bar-in{max-width:1320px;margin:0 auto;width:100%;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
  .stats{color:var(--muted);font-size:13px;letter-spacing:.04em;text-transform:uppercase}
  .stats b{color:var(--accent);font-weight:600}
  #q{flex:1 1 240px;min-width:200px;background:#11151a;border:1px solid var(--line);
     border-radius:10px;color:var(--ink);padding:10px 14px;font:inherit;outline:none}
  #q:focus{border-color:#3d4650}
  button{background:#11151a;border:1px solid var(--line);color:var(--ink);border-radius:10px;
         padding:10px 14px;font:inherit;cursor:pointer}
  button:hover{border-color:#3d4650}
  main{max-width:1320px;margin:0 auto;padding:8px 24px 64px}
  .group{margin-top:38px}
  .model{display:flex;align-items:baseline;gap:12px;margin:0 0 16px;font-weight:600;
         font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
  .model::after{content:"";flex:1;height:1px;background:var(--line)}
  .model-n{color:var(--muted);letter-spacing:.06em;font-size:12px}
  .grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(210px,1fr))}
  .card{margin:0;background:var(--card);border:1px solid var(--line);border-radius:14px;
        padding:12px;cursor:zoom-in;transition:border-color .15s,transform .15s}
  .card:hover,.card:focus-visible{border-color:#3a434d;transform:translateY(-2px);outline:none}
  .matte{aspect-ratio:1;border-radius:9px;overflow:hidden;display:grid;place-items:center;
         background:radial-gradient(circle at 50% 45%,#2c333b 0%,#1d2228 72%)}
  body.light .matte{background:radial-gradient(circle at 50% 45%,#d8d5cf 0%,#b9b6b0 72%)}
  .matte img{width:100%;height:100%;object-fit:contain;display:block}
  figcaption{padding-top:10px}
  .name{display:block;font-family:var(--serif);font-size:16px}
  .blurb{margin:3px 0 0;color:var(--muted);font-size:13px;line-height:1.4}
  .slug{display:block;margin-top:7px;color:#6b747d;font-family:var(--mono);font-size:11px}
  .credit{display:block;margin-top:7px;font-size:12px;color:#a98d55}
  .credit b{color:#c8a24a;font-weight:600}
  .matte{position:relative}
  .badge{position:absolute;top:8px;left:8px;z-index:2;font-size:10px;letter-spacing:.1em;
         text-transform:uppercase;color:#e6d3a8;background:rgba(20,24,29,.72);
         border:1px solid #4a4132;border-radius:999px;padding:3px 8px}
  .set{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:26px 0 4px;
       font-size:13px;font-weight:600;letter-spacing:.06em;color:var(--ink)}
  .setwrap:first-of-type .set{margin-top:6px}
  .set em{font-style:normal;color:var(--muted);font-size:12px}
  .set code{font-family:var(--mono);font-size:11px;color:#7f8891}
  .setnote{margin:0 0 14px;color:var(--muted);font-size:13px;max-width:88ch}
  .model-more{color:#6b747d;font-size:11px;letter-spacing:.06em;text-transform:none}
  .skill{margin:34px 0 6px;border:1px solid var(--line);border-left:2px solid var(--accent);
         border-radius:12px;background:var(--card);padding:20px 22px}
  .skill h2{margin:0 0 8px;font-family:var(--serif);font-size:19px;font-weight:600}
  .skill h2 code{font-family:var(--mono);color:var(--accent);font-size:17px}
  .skill p{margin:0 0 10px;color:var(--muted);max-width:88ch}
  .skill p b,.skill p strong{color:var(--ink)}
  .brief{margin:12px 0;padding:14px 16px;border:1px solid var(--line);border-radius:9px;
         background:#11151a;font-size:13.5px;color:#b9c0c8}
  .brief li{margin:4px 0}
  .brief .quote{margin:0;color:var(--ink)}
  .brief ul{margin:12px 0 0;padding-left:20px}
  .skill .tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
  .skill .tags span{font-family:var(--mono);font-size:11px;color:#8d949c;
                    border:1px solid var(--line);border-radius:999px;padding:3px 9px}
  .hidden{display:none}
  .empty{color:var(--muted);padding:40px 0}
  footer{max-width:1320px;margin:0 auto;padding:24px;border-top:1px solid var(--line);
         color:var(--muted);font-size:13px;display:flex;gap:18px;flex-wrap:wrap;justify-content:space-between}
  footer code{font-family:var(--mono);color:#8d949c}
  #box{position:fixed;inset:0;z-index:20;display:none;place-items:center;
       background:rgba(6,8,10,.92);padding:24px}
  #box.on{display:grid}
  #box img{max-width:min(88vw,86vh);max-height:86vh;border-radius:12px;
           background:radial-gradient(circle at 50% 45%,#2c333b,#1d2228 72%)}
  #cap{margin-top:14px;text-align:center;color:var(--muted);font-size:14px}
  #cap b{display:block;font-family:var(--serif);font-size:19px;color:var(--ink);margin-bottom:4px}
  .nav{position:fixed;top:50%;transform:translateY(-50%);background:rgba(20,24,29,.7);
       border:1px solid var(--line);border-radius:999px;width:44px;height:44px;font-size:20px;
       display:grid;place-items:center;padding:0;color:var(--ink)}
  #prev{left:18px} #next{right:18px}
  #close{position:fixed;top:18px;right:18px;width:44px;height:44px;padding:0;border-radius:999px}
  @media (max-width:560px){.grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}
</style>
</head>
<body>
<header>
  <h1>Clock Gallery</h1>
  <p class="lede"><b><!--N--> analogue dials</b>, every one of them a Lua/Cairo program that Conky
  draws on a Linux desktop — hands, gear trains, moon phases, orbits and interference fringes, all
  painted a frame at a time. What is here are the <b>screenshots</b>, not the source: each image is
  that clock's own drawing code run once into an offscreen surface, at the size it is drawn on screen.</p>
</header>

<div class="bar"><div class="bar-in">
  <span class="stats"><b><!--N--></b> dials · <b><!--MODELS--></b> makers · <b><!--SHARED--></b> co-authored</span>
  <input id="q" type="search" placeholder="Filter by name, maker, or what it does…" aria-label="Filter dials">
  <button id="matte" title="Switch the tile behind each dial">Light matte</button>
  <span class="stats" id="shown"></span>
</div></div>

<main>
  <section class="skill">
    <h2>Where they come from: the <code>/clock</code> skill</h2>
    <p>Most of these dials were made by a <b>pi skill</b> invoked as <code>/clock</code>. A skill
    is a fixed prompt the harness hands to whatever model is being used, so every maker in this
    gallery started from the <em>same</em> brief and the same ground rules — which is what makes
    the sets comparable. The brief is short, and the last line is the point:</p>
    <div class="brief">
      <p class="quote">“This is an evaluation. I would like you to create
      3 analog clocks using Lua and displayed by Conky on my desktop. Place them at the top of the
      lower monitor. One will resemble a Hamilton watch, one will resemble a skeleton watch, and one
      will be unique and a truly one-of-a-kind design. There are already several on my computer
      working, but <b>DO NOT look at them</b>. This is an evaluation, and I want to see what you can
      do on your own. You are able to ask questions.”</p>
      <ul>
        <li>three clocks: one Hamilton-style field dial, one openworked skeleton, one original design</li>
        <li>every file for a clock stays in <code>~/.config/conky/clocks/&lt;model-name&gt;/</code></li>
        <li>no inspecting, copying, sourcing or modifying any clock already on the machine — each
            design starts from first principles</li>
      </ul>
    </div>
    <p>That is why the same three subjects keep reappearing under different makers: a field watch, a
    skeleton, and something with no hands at all. A companion skill, <code>/run-clock
    &lt;model&gt;</code>, runs that evaluation against a local model, supervises it — unsticking
    hangs, breaking loops, nudging with what is on screen — and then adds the finished clocks to
    the gallery.</p>
    <p>The <b><!--SHARED--></b> co-authored dials above are deliberately <em>not</em> a
    <code>/clock</code> evaluation: there one model wrote the design and the plan file and the other
    wrote every line of code from it.</p>
    <div class="tags"><span>/clock</span><span>/run-clock &lt;model&gt;</span>
      <span>Lua + cairo</span><span>conky 1.24</span></div>
  </section>
<!--CARDS-->
<p class="empty hidden" id="none">Nothing matches that.</p>
</main>

<footer>
  <span>Captured headlessly by <code>tools/capture/capture.lua</code> — the same code path the live
  desktop clocks run, with no window manager in the loop.</span>
  <span>640×640 PNG · transparent</span>
</footer>

<div id="box" role="dialog" aria-modal="true">
  <button id="close" aria-label="Close">✕</button>
  <button id="prev" class="nav" aria-label="Previous">‹</button>
  <button id="next" class="nav" aria-label="Next">›</button>
  <div><img id="big" alt=""><div id="cap"></div></div>
</div>

<script>
const cards=[...document.querySelectorAll('.card')];
const q=document.getElementById('q'),shown=document.getElementById('shown');
const none=document.getElementById('none');

function apply(){
  const w=(q.value||'').toLowerCase().split(/\s+/).filter(Boolean);
  let n=0;
  for(const c of cards){
    const t=c.dataset.text;
    const ok=w.every(x=>t.includes(x));
    c.classList.toggle('hidden',!ok);
    if(ok)n++;
  }
  for(const g of document.querySelectorAll('.group')){
    g.classList.toggle('hidden',!g.querySelector('.card:not(.hidden)'));
  }
  for(const w of document.querySelectorAll('.setwrap')){
    w.classList.toggle('hidden',!w.querySelector('.card:not(.hidden)'));
  }
  none.classList.toggle('hidden',n>0);
  shown.textContent=w.length?`${n} shown`:'';
}
q.addEventListener('input',apply);

const box=document.getElementById('box'),big=document.getElementById('big'),cap=document.getElementById('cap');
let order=[],i=0;
function view(k){
  i=(k+order.length)%order.length;
  const c=order[i];
  big.src=c.dataset.img;
  big.alt=c.dataset.name+', enlarged';
  const who=c.dataset.credit||c.dataset.model;
  cap.innerHTML=`<b>${c.dataset.name}</b>${who} · ${i+1} of ${order.length}`;
}
function open(c){
  order=cards.filter(x=>!x.classList.contains('hidden'));
  box.classList.add('on');
  document.body.style.overflow='hidden';
  view(order.indexOf(c));
}
function close(){box.classList.remove('on');document.body.style.overflow=''}
for(const c of cards){
  c.addEventListener('click',()=>open(c));
  c.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open(c)}});
}
document.getElementById('close').onclick=close;
document.getElementById('prev').onclick=()=>view(i-1);
document.getElementById('next').onclick=()=>view(i+1);
box.addEventListener('click',e=>{if(e.target===box)close()});
addEventListener('keydown',e=>{
  if(!box.classList.contains('on'))return;
  if(e.key==='Escape')close();
  if(e.key==='ArrowLeft')view(i-1);
  if(e.key==='ArrowRight')view(i+1);
});

const m=document.getElementById('matte');
const setLight=on=>{document.body.classList.toggle('light',on);m.textContent=on?'Dark matte':'Light matte'};
setLight(localStorage.getItem('matte')==='light');
m.onclick=()=>{const on=!document.body.classList.contains('light');
  localStorage.setItem('matte',on?'light':'dark');setLight(on)};
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
