"""The catalog page and its vote server, checked without a browser."""

import importlib.util
import json
import threading
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "catalog" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_catalog = _load("build_catalog")
collect_assets = _load("collect_assets")
serve = _load("serve")


def test_page_has_a_votable_card_for_every_scene(tmp_path):
    (tmp_path / "videos").mkdir()
    (tmp_path / "videos" / "sc_kinetic_type.mp4").write_bytes(b"x")
    (tmp_path / "extra.json").write_text(json.dumps([{"id": "thing", "title": "Thing", "text": "A thing."}]), encoding="utf-8")
    (tmp_path / "tracks.json").write_text(json.dumps({"sc_kinetic_type": "A <song>"}), encoding="utf-8")
    (tmp_path / "status.json").write_text(json.dumps({"thing": "Out of date: old picture", "sc_flow_mosh": "New this round"}), encoding="utf-8")
    count = build_catalog.build(tmp_path)
    page = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "<p class='status old'>Out of date: old picture</p>" in page and "<p class='status'>New this round</p>" in page
    assert page.count("class=music") == 1 and "Music: A &lt;song&gt;" in page
    scenes = sorted(p.parent.name for p in (ROOT / "experiments").glob("sc_*/preset.json"))
    assert count == len(scenes) + 1
    for scene in [*scenes, "thing"]:
        assert f"data-id='{scene}'" in page
    assert page.count("class=like") == count
    stamp = int((tmp_path / "videos" / "sc_kinetic_type.mp4").stat().st_mtime)
    assert f"src='videos/sc_kinetic_type.mp4?v={stamp}'" in page  # the address changes when the video is re-recorded
    assert "data-i='1' data-n='12'" in page  # a jump button for the second of twelve takes


def test_votes_are_cleaned():
    got = serve.clean_votes({"a": {"vote": "like", "note": "x"}, "b": {"vote": "maybe"}, "c": "like", "d": {"vote": "", "note": "n"}})
    assert got == {"a": {"vote": "like", "note": "x"}, "d": {"vote": "", "note": "n"}}


def test_byte_ranges():
    assert serve.byte_range("bytes=0-9", 100) == (0, 9)
    assert serve.byte_range("bytes=90-", 100) == (90, 99)
    assert serve.byte_range("bytes=-10", 100) == (90, 99)
    assert serve.byte_range("bytes=200-", 100) is None
    assert serve.byte_range(None, 100) is None


def test_server_saves_votes_and_serves_ranges(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(bytes(range(100)))
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(serve.Handler, directory=str(tmp_path)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        body = json.dumps({"sc_x": {"vote": "dislike", "note": "drop take 2"}}).encode()
        req = urllib.request.Request(base + "/votes", data=body, headers={"Content-Type": "application/json"})
        assert json.loads(urllib.request.urlopen(req).read()) == {"saved": 1}
        assert json.loads((tmp_path / "votes.json").read_text(encoding="utf-8"))["sc_x"]["vote"] == "dislike"
        assert json.loads(urllib.request.urlopen(base + "/votes").read())["sc_x"]["note"] == "drop take 2"
        part = urllib.request.urlopen(urllib.request.Request(base + "/clip.mp4", headers={"Range": "bytes=10-19"}))
        assert part.status == 206
        assert part.read() == bytes(range(10, 20))
        assert part.headers["Cache-Control"] == "no-cache"  # a rebuilt video must not be shown from the browser's copy
        assert urllib.request.urlopen(base + "/clip.mp4").headers["Cache-Control"] == "no-cache"
        assert urllib.request.urlopen(base + "/votes").headers["Cache-Control"] == "no-store"
    finally:
        server.shutdown()


def test_assets_get_their_own_tabs_and_sections(tmp_path):
    from PIL import Image

    pack = tmp_path / "pack"
    (pack / "models" / "lamp").mkdir(parents=True)
    (pack / "models" / "lamp" / "info.json").write_text(json.dumps({"prompt": "a lamp", "triangles": 1200}), encoding="utf-8")
    Image.new("RGBA", (64, 64), (200, 30, 30, 128)).save(pack / "models" / "lamp" / "basecolor.png")
    (pack / "sheets").mkdir()
    Image.new("RGB", (64, 32), (10, 10, 200)).save(pack / "sheets" / "map.png")
    (tmp_path / "objects.json").write_text(json.dumps([{"name": "kite", "group": "toys", "prompt": "a kite"}]), encoding="utf-8")
    cat = tmp_path / "cat"
    cat.mkdir()
    found = collect_assets.collect(cat, [("My pack", str(pack))], objects=tmp_path / "objects.json", objects_label="New")
    assert {(i["tab"], i["section"]) for i in found} == {("Models", "My pack"), ("Sheets and lettering", "My pack: sheets"), ("Models", "New: toys")}
    assert len({i["id"] for i in found}) == len(found) == 3
    assert (cat / "assets" / "my_pack" / "models" / "lamp.jpg").exists()
    count = build_catalog.build(cat)
    page = (cat / "index.html").read_text(encoding="utf-8")
    scenes = len(list((ROOT / "experiments").glob("sc_*/preset.json")))
    assert count == scenes + 3 and page.count("class=like") == count      # every asset can be voted on
    for tab in ("Scenes", "Models", "Sheets and lettering"):
        assert f"<section class=tab data-t='{tab}'>" in page and f"<button data-t='{tab}'>" in page
    assert "data-id='model:my_pack:lamp'" in page and "1,200 triangles" in page
    assert "<h2>New: toys <small>(1)</small></h2>" in page
