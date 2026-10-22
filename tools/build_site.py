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
    r"|conky clock"           # "Conky clock"
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
        r["blurb"] = clean_blurb(r.get("blurb", ""), r["name"], r["id"])

    groups: "OrderedDict[str, list]" = OrderedDict()
    for r in sorted(rows, key=lambda r: (r["model"], r["id"])):
        groups.setdefault(r["model"], []).append(r)
    # The dial whose author is unknown belongs at the end, not among the models.
    if "unknown" in groups:
        groups.move_to_end("unknown")

    n_dials = len(rows)
    n_models = len([m for m in groups if m != "unknown"])

    cards = []
    for model, items in groups.items():
        head = (
            f'<h2 class="model" id="m-{html.escape(model)}">'
            f'<span class="model-name">{html.escape(model)}</span>'
            f'<span class="model-n">{len(items)}</span></h2>'
        )
        tiles = []
        for r in items:
            cap = html.escape(r["name"])
            blurb = (f'<p class="blurb">{html.escape(r["blurb"])}</p>'
                     if r["blurb"] else "")
            text = html.escape(f"{r['name']} {model} {r['slug']} {r['blurb']}".lower())
            tiles.append(
                f"""      <figure class="card" tabindex="0"
          data-img="assets/img/{html.escape(r['file'])}"
          data-name="{cap}" data-model="{html.escape(model)}"
          data-text="{text}">
        <div class="matte"><img src="assets/img/{html.escape(r['file'])}"
             alt="{cap}, an analogue clock face" loading="lazy" width="640" height="640"></div>
        <figcaption>
          <span class="name">{cap}</span>
          {blurb}
          <span class="slug">{html.escape(r['slug'])}</span>
        </figcaption>
      </figure>""")
        cards.append(f'  <section class="group" data-model="{html.escape(model)}">\n'
                     f'    {head}\n    <div class="grid">\n' + "\n".join(tiles) +
                     "\n    </div>\n  </section>")

    page = TEMPLATE.replace("<!--CARDS-->", "\n".join(cards))
    page = page.replace("<!--N-->", str(n_dials))
    page = page.replace("<!--MODELS-->", str(n_models))
    OUT.write_text(page)
    print(f"{OUT}: {n_dials} dials in {len(groups)} groups")


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
  <span class="stats"><b><!--N--></b> dials · <b><!--MODELS--></b> makers</span>
  <input id="q" type="search" placeholder="Filter by name, maker, or what it does…" aria-label="Filter dials">
  <button id="matte" title="Switch the tile behind each dial">Light matte</button>
  <span class="stats" id="shown"></span>
</div></div>

<main>
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
  cap.innerHTML=`<b>${c.dataset.name}</b>${c.dataset.model} · ${i+1} of ${order.length}`;
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
