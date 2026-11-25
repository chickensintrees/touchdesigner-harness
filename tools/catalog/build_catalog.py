"""Build a catalog page of every scene, with a video of each and like / dislike votes.

    python tools/catalog/build_catalog.py <catalog folder>
    python tools/catalog/serve.py <catalog folder>

The folder holds what the page shows:
    videos/film.mp4          the demo film (optional)
    videos/<scene>.mp4       one reel per scene: every take for the same length of time, in order
    extra.json               other things to vote on (optional):
                             [{"id", "title", "text", "video", "poster", "group"}]
    tracks.json              the music each video plays (optional): {"<id>": "<track name>"}
    status.json              a line of status per item (optional): {"<id>": "Out of date: ..."}; a line that starts
                             with "Out of date" is drawn as a warning, so nobody reviews a stale video by mistake
    archive.json             more items in the same form as assets.json (for example old recordings awaiting a keep-or-delete vote)
    assets.json              things to vote on that are not videos (optional; collect_assets.py writes it):
                             [{"id", "title", "text", "tab", "section", "image", "audio"}]

The page is tabbed, one kind of thing per tab, so a long catalog never shows more
than one kind at once. An item's "tab" names its tab; "section" is a heading inside it.
Scene titles, techniques and take names come from each experiments/sc_*/preset.json,
posters from docs/media/gallery. Votes are saved by serve.py to votes.json in the folder.
"""

import html
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CSS = """
:root{--bg:#f6f4ef;--fg:#1b1a17;--mut:#6b675f;--card:#fff;--line:#dedad0;--good:#1f7a4d;--bad:#b3311b;--acc:#2049dd}
@media (prefers-color-scheme:dark){:root{--bg:#141412;--fg:#ecebe6;--mut:#a09c92;--card:#1e1e1b;--line:#33322d;--good:#58c08c;--bad:#f0755c;--acc:#8fa6ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}
main{max-width:1280px;margin:0 auto;padding:16px 16px 80px}
h1{font-size:26px;margin:8px 0 2px}h2{font-size:20px;margin:36px 0 12px;border-top:1px solid var(--line);padding-top:18px}
.lead{color:var(--mut);margin:0 0 8px;max-width:75ch}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 0;display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:14px}
.bar button,.vote button,.takes button{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;padding:4px 10px;cursor:pointer}
.bar button.on{border-color:var(--acc);color:var(--acc)}
#saved{color:var(--mut);margin-left:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(400px,100%),1fr));gap:16px}
@media (max-width:540px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.card.like{border-color:var(--good)}.card.dislike{border-color:var(--bad)}
.card video,.card img{display:block;width:100%;aspect-ratio:16/9;background:#000;object-fit:contain}
.grid.one{grid-template-columns:minmax(0,860px)}
.takes,.vote{min-width:0}
.body{padding:10px 14px 14px}
.card h3{margin:0;font-size:17px}
.slug{font:12px ui-monospace,Consolas,monospace;color:var(--mut)}
.card p{margin:6px 0 0;font-size:14px}
.takes{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
.takes button{font-size:12px;padding:2px 7px}
.vote{display:flex;gap:6px;margin-top:10px;align-items:center}
.vote button{font-weight:600;padding:6px 14px}
.vote button.like.on{background:var(--good);border-color:var(--good);color:#fff}
.vote button.dislike.on{background:var(--bad);border-color:var(--bad);color:#fff}
.vote input{flex:1;min-width:0;font:inherit;font-size:14px;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
.hide{display:none}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:14px 0 0}
.tabs button{font:inherit;font-size:15px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px 6px 0 0;padding:7px 12px;cursor:pointer}
.tabs button.on{border-color:var(--acc);color:var(--acc);font-weight:600}
.tabs small{color:var(--mut);font-weight:400;margin-left:4px}
.tab{display:none}.tab.on{display:block}
.tab h2{border-top:0;margin:22px 0 10px;padding-top:0;font-size:17px}
.tab h2 small{color:var(--mut);font-weight:400}
.grid.small{grid-template-columns:repeat(auto-fill,minmax(min(210px,100%),1fr));gap:12px}
.grid.small .card img{aspect-ratio:1/1;background:var(--bg)}
.grid.small .card h3{font-size:15px}.grid.small .vote{flex-wrap:wrap}.grid.small .vote button{padding:4px 10px}
.grid.small .vote input{flex-basis:100%}
.status{font-size:13px;color:var(--mut);margin:6px 0 0}.status.old{color:var(--bad);font-weight:600}
.card audio{display:block;width:100%;margin-top:8px}
"""

JS = """
const votes = {};
const cards = [...document.querySelectorAll('.card')];
let timer = null;
function paint() {
  let like = 0, dislike = 0;
  for (const c of cards) {
    const v = (votes[c.dataset.id] || {}).vote || '';
    c.classList.toggle('like', v === 'like');
    c.classList.toggle('dislike', v === 'dislike');
    c.querySelector('button.like').classList.toggle('on', v === 'like');
    c.querySelector('button.dislike').classList.toggle('on', v === 'dislike');
    if (v === 'like') like++;
    if (v === 'dislike') dislike++;
  }
  const f = document.querySelector('.bar button.on').dataset.f;
  for (const c of cards) {
    const v = (votes[c.dataset.id] || {}).vote || '';
    c.classList.toggle('hide', !(f === 'all' || (f === 'none' ? v === '' : v === f)));
  }
  // each tab says how many of its things are voted on; a heading with nothing under it is hidden
  let here = '';
  for (const t of document.querySelectorAll('.tab')) {
    const mine = [...t.querySelectorAll('.card')];
    const voted = mine.filter(c => (votes[c.dataset.id] || {}).vote).length;
    const b = document.querySelector('.tabs button[data-t="' + t.dataset.t + '"]');
    if (b) b.querySelector('small').textContent = voted + '/' + mine.length;
    if (t.classList.contains('on')) here = (mine.length - voted) + ' of ' + mine.length + ' here not voted. ';
    for (const sec of t.querySelectorAll('.sec')) sec.classList.toggle('hide', !sec.querySelector('.card:not(.hide)'));
  }
  document.getElementById('count').textContent = here + 'All tabs: ' + like + ' liked, ' + dislike + ' disliked, ' + (cards.length - like - dislike) + ' not voted';
}
function show(name) {
  const tabs = [...document.querySelectorAll('.tab')];
  const want = tabs.find(t => t.dataset.t === name) || tabs[0];
  for (const t of tabs) {
    t.classList.toggle('on', t === want);
    if (t !== want) for (const m of t.querySelectorAll('video,audio')) m.pause();
  }
  for (const b of document.querySelectorAll('.tabs button')) b.classList.toggle('on', b.dataset.t === want.dataset.t);
  try { history.replaceState(null, '', '#' + want.dataset.t); } catch (e) {}
  paint();
}
for (const b of document.querySelectorAll('.tabs button')) b.addEventListener('click', () => show(b.dataset.t));
function save() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const s = document.getElementById('saved');
    try { localStorage.setItem('catalog-votes', JSON.stringify(votes)); } catch (e) {}
    try {
      const r = await fetch('/votes', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(votes)});
      s.textContent = r.ok ? 'Votes saved' : 'Not saved (' + r.status + ')';
    } catch (e) { s.textContent = 'Not saved: open this page through tools/catalog/serve.py'; }
  }, 300);
}
for (const c of cards) {
  const id = c.dataset.id;
  for (const b of c.querySelectorAll('.vote button')) {
    b.addEventListener('click', () => {
      const want = b.classList.contains('like') ? 'like' : 'dislike';
      const cur = votes[id] || {vote: '', note: ''};
      cur.vote = cur.vote === want ? '' : want;
      votes[id] = cur; paint(); save();
    });
  }
  c.querySelector('.vote input').addEventListener('input', (e) => {
    const cur = votes[id] || {vote: '', note: ''};
    cur.note = e.target.value; votes[id] = cur; save();
  });
  for (const b of c.querySelectorAll('.takes button')) {
    b.addEventListener('click', () => {
      const v = c.querySelector('video');
      const go = () => { v.currentTime = v.duration * (+b.dataset.i) / (+b.dataset.n); v.play(); };
      if (v.readyState >= 1) go(); else { v.addEventListener('loadedmetadata', go, {once: true}); v.load(); }
    });
  }
}
for (const b of document.querySelectorAll('.bar button')) {
  b.addEventListener('click', () => { document.querySelector('.bar button.on').classList.remove('on'); b.classList.add('on'); paint(); });
}
(async () => {
  let got = null;
  try { const r = await fetch('/votes'); if (r.ok) got = await r.json(); } catch (e) {}
  if (!got) { try { got = JSON.parse(localStorage.getItem('catalog-votes') || '{}'); } catch (e) { got = {}; } }
  Object.assign(votes, got);
  for (const c of cards) c.querySelector('.vote input').value = (votes[c.dataset.id] || {}).note || '';
  show(decodeURIComponent(location.hash.slice(1)));
})();
"""


def scenes():
    """[{id, title, text, takes: [name]}] for every hub scene, in title order."""
    out = []
    for preset in sorted((REPO / "experiments").glob("sc_*/preset.json")):
        doc = json.loads(preset.read_text(encoding="utf-8"))
        out.append({
            "id": preset.parent.name,
            "title": doc["title"],
            "text": doc["technique"],
            "takes": [t["name"] for t in doc["takes"]],
        })
    return sorted(out, key=lambda s: s["title"])


def card(item, folder):
    e = html.escape
    video = item.get("video") or f"videos/{item['id']}.mp4"
    poster = item.get("poster", "")
    image = item.get("image", "")
    if image and (folder / image).exists():
        media = f"<img loading=lazy alt='{e(item['title'])}' src='{e(image)}'>"
    elif image or item.get("audio"):
        media = ""
    elif (folder / video).exists():
        attr = f" poster='{e(poster)}'" if poster and (folder / poster).exists() else ""
        load = "none" if attr else "metadata"
        stamp = int((folder / video).stat().st_mtime)  # a re-recorded video is a new address, so no browser shows a stale copy
        media = f"<video controls preload='{load}' playsinline{attr} src='{e(video)}?v={stamp}'></video>"
    elif poster and (folder / poster).exists():
        media = f"<img alt='{e(item['title'])}' src='{e(poster)}'>"
    else:
        media = ""
    takes = ""
    if item.get("takes") and (folder / video).exists():
        buttons = "".join(
            f"<button data-i='{i}' data-n='{len(item['takes'])}' title='Jump to this take'>{i} {e(n)}</button>"
            for i, n in enumerate(item["takes"])
        )
        takes = f"<div class=takes>{buttons}</div>"
    music = f"<p class=music>Music: {e(item['music'])}</p>" if item.get("music") else ""
    audio = f"<audio controls preload=none src='{e(item['audio'])}'></audio>" if item.get("audio") and (folder / item["audio"]).exists() else ""
    text = f"<p>{e(item['text'])}</p>" if item.get("text") else ""
    if item.get("status"):
        old = " old" if item["status"].lower().startswith("out of date") else ""
        text = f"<p class='status{old}'>{e(item['status'])}</p>" + text
    return (
        f"<div class=card data-id='{e(item['id'])}'>{media}<div class=body>"
        f"<h3>{e(item['title'])}</h3><div class=slug>{e(item['id'])}</div>{text}{music}{audio}{takes}"
        "<div class=vote><button class=like>Like</button><button class=dislike>Dislike</button>"
        "<input placeholder='Note: what to change or drop'></div></div></div>"
    )


TABS = {"Demo film": "Film", "Spike candidates": "Candidates", "Candidates": "Candidates", "Scenes": "Scenes"}


def build(folder):
    folder = Path(folder)
    (folder / "posters").mkdir(parents=True, exist_ok=True)
    groups = {}
    if (folder / "videos/film.mp4").exists():
        groups["Demo film"] = [{"id": "film", "title": "Demo film", "text": "The strongest takes of the scenes, cut to the music.", "video": "videos/film.mp4"}]
    extra = folder / "extra.json"
    if extra.exists():
        for item in json.loads(extra.read_text(encoding="utf-8")):
            groups.setdefault(item.get("group", "Candidates"), []).append(item)
    listed = scenes()
    for s in listed:
        src = REPO / "docs/media/gallery" / f"{s['id']}_takes.jpg"
        if src.exists():
            shutil.copyfile(src, folder / "posters" / f"{s['id']}.jpg")
            s["poster"] = f"posters/{s['id']}.jpg"
    groups["Scenes"] = listed
    tracks = folder / "tracks.json"
    if tracks.exists():
        names = json.loads(tracks.read_text(encoding="utf-8"))
        for items in groups.values():
            for item in items:
                if names.get(item["id"]):
                    item["music"] = names[item["id"]]
    # one tab per kind of thing; inside a tab, items sit under their section headings
    tabs = {}
    for name, items in groups.items():
        for item in items:
            tabs.setdefault(item.get("tab") or TABS.get(name, name), {}).setdefault(item.get("section", ""), []).append(item)
    for more in ("assets.json", "generated.json", "archive.json"):   # further things to vote on, each naming its own tab
        assets = folder / more
        if assets.exists():
            for item in json.loads(assets.read_text(encoding="utf-8")):
                tabs.setdefault(item.get("tab", "Assets"), {}).setdefault(item.get("section", ""), []).append(item)
    status = folder / "status.json"
    if status.exists():
        lines = json.loads(status.read_text(encoding="utf-8"))
        for sections in tabs.values():
            for items in sections.values():
                for item in items:
                    if lines.get(item["id"]):
                        item["status"] = lines[item["id"]]
    e = html.escape
    parts = [
        "<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
        f"<title>Scene catalog</title><style>{CSS}</style><main><h1>Scene catalog</h1>",
        "<p class=lead>One kind of thing per tab. Play or look, then vote: likes stay, dislikes get reworked or removed, and the note says which. "
        "Each tab shows how many of its items you have voted on.</p>",
        "<div class=tabs>" + "".join(f"<button data-t='{e(t)}'>{e(t)}<small></small></button>" for t in tabs) + "</div>",
        "<div class=bar><button class=on data-f=all>All</button><button data-f=none>Not voted</button>"
        "<button data-f=like>Liked</button><button data-f=dislike>Disliked</button><span id=count></span><span id=saved></span></div>",
    ]
    total = 0
    for tab, sections in tabs.items():
        parts.append(f"<section class=tab data-t='{e(tab)}'>")
        for section, items in sections.items():
            total += len(items)
            small = all((i.get("image") or i.get("audio")) and not i.get("wide") for i in items)
            kind = " small" if small else (" one" if len(items) == 1 and len(sections) == 1 else "")
            head = f"<h2>{e(section)} <small>({len(items)})</small></h2>" if section else ""
            parts.append(f"<div class=sec>{head}<div class='grid{kind}'>")
            parts += [card(i, folder) for i in items]
            parts.append("</div></div>")
        parts.append("</section>")
    parts.append(f"</main><script>{JS}</script></html>")
    (folder / "index.html").write_text("\n".join(parts), encoding="utf-8")
    return total


if __name__ == "__main__":
    print(build(sys.argv[1]), "items")
