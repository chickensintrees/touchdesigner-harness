"""Layer review film: see what each layer of a film contributes, and what every event is, while it plays.

    python tools/review/layer_review.py <spec.json>

Bill, 2026-11-16, on a bare render: "it's not clear how I can react. Need more on screen and indications in
the video about what I'm looking at". And on the first version of this: "That interface you built to compare
them is killer. Save that. Make it part of our touchdesigner harness."

What it draws, per frame:
    panels      two or three pictures side by side (for example: the generated plate alone, the TouchDesigner
                layer alone on black, the finished film), each with a heading and a status line
    happening   a row for every event that is live on this frame: its name, what it does, what in the music
    now         it sits on, and which layer did it. A span stays up while it runs; an instant lingers so it
                can be read
    timeline    the music (bars, beats, drum hits, sung words) over one lane per layer with every event on it,
                and a playhead
It plays twice: full speed, then half speed with the sound slowed and its pitch kept.

The tool knows nothing about any project. Everything it draws is in the spec, which the project builds from
its own score (see spec_example() for the shape). Needs ffmpeg, numpy, Pillow and OpenCV; no TouchDesigner.
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
LINGER = 20            # frames an instant event's row stays up
FRESH = 6              # frames a new row is highlighted
ROWS = 5
BG, INK, DIM, LINE, NOW, MUSIC = (14, 16, 20), (232, 238, 244), (120, 132, 146), (52, 60, 72), (255, 255, 255), (150, 230, 170)
PALETTE = [(90, 190, 255), (255, 196, 70), (232, 238, 244), (255, 120, 210)]      # one colour per layer, in order
FONT_DIRS = ["C:/Windows/Fonts/", "/System/Library/Fonts/Supplemental/", "/Library/Fonts/", "/usr/share/fonts/truetype/dejavu/"]
FACES = {(False, False): ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"], (True, False): ["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"],
         (False, True): ["consola.ttf", "Courier New.ttf", "DejaVuSansMono.ttf"], (True, True): ["consolab.ttf", "Courier New Bold.ttf", "DejaVuSansMono-Bold.ttf"]}
_fonts = {}


def font(size, bold=False, mono=False):
    key = (size, bold, mono)
    if key not in _fonts:
        for d in FONT_DIRS:
            for name in FACES[(bold, mono)]:
                if (Path(d) / name).exists():
                    _fonts[key] = ImageFont.truetype(str(Path(d) / name), size)
                    break
            if key in _fonts:
                break
        else:
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]


def spec_example():
    """The shape of a spec. Frames count from 0; a 'frame1' makes an event a span."""
    return {
        "fps": 24, "frames": 48, "out": "review.mp4",
        "audio": {"file": "track.mp3", "start_s": 20.625},          # optional
        "layers": ["PLATE LAYER", "TOUCHDESIGNER LAYER"],            # one timeline lane and one colour each
        "panels": [                                                  # two or three
            {"label": "1  PLATE LAYER ALONE", "note": "as the video model made it", "layer": 0, "source": "plates.mov"},
            {"label": "2  TOUCHDESIGNER LAYER ALONE", "note": "what is added, on black", "layer": 1, "source": "solo/f_%04d.png"},
            {"label": "3  THE FILM", "note": "both", "layer": 2, "source": "frames/f_%04d.png"}],
        "captions": [["shot 1"] * 48, [""] * 48, [""] * 48],        # optional: a status line per panel per frame
        "music": {"bars": [{"frame": 0, "label": "bar 10"}], "beats": [0, 12.3, 24.7, 37.0],
                  "hits": [{"frame": 24, "size": 0.7}], "words": [{"frame": 11, "text": "we"}]},
        "events": [
            {"layer": 0, "frame": 24, "name": "CUT", "text": "new shot", "on": "bar 11", "who": "plate layer"},
            {"layer": 1, "frame": 11, "frame1": 24, "name": "TITLE", "text": "WE RISE", "on": "the sung words", "who": "TouchDesigner layer",
             "marks": [{"frame": 11}, {"frame": 23}]},
            {"layer": 1, "frame": 24, "name": "ACCENT", "text": "ring on the snare", "on": "snare hit", "who": "TouchDesigner layer",
             "spike": 0.7, "linger": 8, "quiet": True}],           # spike: drawn as a tick of that height; quiet: listed last
    }


def load_source(src, frames):
    """A movie file, or an image sequence pattern like dir/f_%04d.png, as BGR arrays."""
    if "%" in str(src):
        out = [cv2.imread(str(src) % i) for i in range(frames)]
    else:
        cap, out = cv2.VideoCapture(str(src)), []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            out.append(f)
        cap.release()
    if len(out) < frames or any(f is None for f in out[:frames]):
        raise FileNotFoundError("%s has fewer than %d frames" % (src, frames))
    return out[:frames]


def layout(n_panels):
    gap = 12
    pw = (W - gap * (n_panels + 1)) // n_panels
    ph = round(pw * 9 / 16)
    xs = [gap + i * (pw + gap) for i in range(n_panels)]
    now_y = 44 + ph + 34
    return {"pw": pw, "ph": ph, "xs": xs, "top": 44, "caption_y": 44 + ph + 6, "now_y": now_y,
            "timeline": (210, max(now_y + 30 + ROWS * 38 + 14, 700), 1760, H - 12)}


def live_events(spec, f):
    """Events to list on frame f, newest first; quiet ones (accents on every hit) after the rest."""
    out = []
    for e in spec["events"]:
        if e.get("unlisted"):
            continue
        end = e.get("frame1", e["frame"] + e.get("linger", LINGER))
        if e["frame"] <= f < end:
            out.append((e, f - e["frame"]))
    out.sort(key=lambda x: (bool(x[0].get("quiet")), x[1]))
    return out


def draw_timeline(d, box, spec, f):
    x0, y0, x1, y1 = box
    n = spec["frames"]
    layers = spec["layers"]
    lane_h = min(78, (y1 - y0 - 10) // (len(layers) + 1) - 8)

    def X(frame):
        return x0 + (x1 - x0) * frame / n

    small, tiny, lab = font(15), font(13), font(15, bold=True)
    ys = [y0 + 10 + i * (lane_h + 8) for i in range(len(layers) + 1)]
    for i, name in enumerate(["MUSIC"] + list(layers)):
        col = MUSIC if i == 0 else PALETTE[(i - 1) % len(PALETTE)]
        d.text((x0 - 198, ys[i] + lane_h // 2 - 9), name, font=lab, fill=col)
        d.rectangle((x0, ys[i], x1, ys[i] + lane_h), outline=LINE)
    m, y = spec.get("music", {}), ys[0]
    for b in m.get("bars", []):
        d.line((X(b["frame"]), y0, X(b["frame"]), y1), fill=LINE, width=2)
        if b["frame"] < n - 1:
            d.text((X(b["frame"]) + 5, y + 2), b["label"], font=small, fill=INK)
    for b in m.get("beats", []):
        d.line((X(b), y + lane_h - 16, X(b), y + lane_h), fill=DIM, width=1)
    for h in m.get("hits", []):
        r = 3 + 7 * h.get("size", 0.5)
        d.ellipse((X(h["frame"]) - r, y + lane_h * 0.55 - r, X(h["frame"]) + r, y + lane_h * 0.55 + r), fill=MUSIC)
    for w in m.get("words", []):
        d.text((X(w["frame"]) + 2, y + 20), "\u201c%s\u201d" % w["text"], font=tiny, fill=MUSIC)
    d.text((x1 + 12, y + 8), "dots: drum hits", font=tiny, fill=DIM)
    d.text((x1 + 12, y + 26), "ticks: beats", font=tiny, fill=DIM)
    # events: spans as bars (stacked in slots so they do not cover one another), instants as lines, spikes as ticks
    for li in range(len(layers)):
        y, col = ys[li + 1], PALETTE[li % len(PALETTE)]
        dark = tuple(int(c * 0.42) for c in col)
        slots = []
        for e in [e for e in spec["events"] if e["layer"] == li]:
            xa = X(e["frame"])
            if "spike" in e:
                d.line((xa, y + lane_h - 2, xa, y + lane_h - 2 - (lane_h * 0.45) * e["spike"]), fill=col, width=2)
                continue
            if "frame1" in e:
                slot = next((k for k, end in enumerate(slots) if end <= e["frame"]), len(slots))
                if slot == len(slots):
                    slots.append(0)
                slots[slot] = e["frame1"]
                yy = y + 3 + (slot % 3) * 18
                d.rectangle((xa + 1, yy, X(e["frame1"]) - 1, yy + 16), fill=dark)
                d.text((xa + 5, yy), e.get("short", e["name"]), font=tiny, fill=NOW)
                for mk in e.get("marks", []):
                    d.line((X(mk["frame"]), yy - 2, X(mk["frame"]), yy + 18), fill=NOW, width=2)
                    if mk.get("text"):
                        d.text((X(mk["frame"]) + 5, yy + 17), mk["text"], font=tiny, fill=NOW)
            else:
                d.line((xa, y - 3, xa, y + lane_h), fill=col, width=3)
                d.text((xa + 5, y + lane_h - 20), e.get("short", e["name"]), font=lab, fill=col)
    if any("spike" in e for e in spec["events"]):
        d.text((x1 + 12, ys[-1] + lane_h - 22), "ticks: accents", font=tiny, fill=DIM)
    d.line((X(f), y0, X(f), y1), fill=NOW, width=3)


def frame_image(spec, pictures, f, slow=False):
    lay = layout(len(pictures))
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    head, small = font(20, bold=True), font(15)
    for i, (panel, pics) in enumerate(zip(spec["panels"], pictures)):
        x, col = lay["xs"][i], PALETTE[panel.get("layer", i) % len(PALETTE)]
        im.paste(Image.fromarray(cv2.cvtColor(cv2.resize(pics[f], (lay["pw"], lay["ph"]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)), (x, lay["top"]))
        d.rectangle((x - 1, lay["top"] - 1, x + lay["pw"], lay["top"] + lay["ph"]), outline=LINE)
        d.text((x, 12), panel["label"], font=head, fill=col)
        tw = d.textlength(panel["label"], font=head)
        d.text((x + tw + 14, 16), panel.get("note", ""), font=small, fill=DIM)
        caps = spec.get("captions")
        if caps and caps[i]:
            d.text((x, lay["caption_y"]), caps[i][f], font=small, fill=col)
    y = lay["now_y"]
    d.text((12, y), "HAPPENING NOW", font=font(15, bold=True), fill=DIM)
    d.text((W - 330, y - 4), "PASS 2 OF 2: HALF SPEED" if slow else "PASS 1 OF 2: FULL SPEED", font=font(20, bold=True), fill=NOW if slow else DIM)
    y += 24
    for e, age in live_events(spec, f)[:ROWS]:
        col = PALETTE[e["layer"] % len(PALETTE)]
        fresh = age < FRESH
        if fresh:
            d.rectangle((8, y - 2, W - 8, y + 34), fill=(40, 46, 56))
        d.rectangle((12, y + 2, 20, y + 30), fill=col)
        d.text((30, y), e["name"], font=font(26, bold=True), fill=NOW if fresh else col)
        d.text((330, y + 5), e.get("text", ""), font=font(20), fill=INK)
        d.text((1060, y + 5), ("on: " + e["on"]) if e.get("on") else "", font=font(20), fill=MUSIC)
        d.text((1500, y + 5), e.get("who", ""), font=font(18), fill=col)
        y += 38
    draw_timeline(d, lay["timeline"], spec, f)
    return im


def render(spec, pictures=None):
    """Write the review film. pictures: one list of BGR frames per panel (loaded from each panel's 'source' if left out)."""
    n = spec["frames"]
    pictures = pictures or [load_source(p["source"], n) for p in spec["panels"]]
    out = Path(spec["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(spec["fps"]), "-i", "-"]
    audio = spec.get("audio")
    if audio:
        cmd += ["-i", str(audio["file"]), "-map", "0:v", "-map", "[out]", "-filter_complex",
                "[1:a]atrim=start=%.6f:duration=%.6f,asetpts=PTS-STARTPTS,asplit[a][b];[b]atempo=0.5[c];[a][c]concat=n=2:v=0:a=1[out]" % (audio["start_s"], n / spec["fps"]),
                "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(spec.get("crf", 26)), "-preset", "slow", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for slow in (False, True):
        for f in range(n):
            p.stdin.write(frame_image(spec, pictures, f, slow).tobytes() * (2 if slow else 1))
    p.stdin.close()
    if p.wait():
        raise RuntimeError("ffmpeg failed writing %s" % out)
    return out


if __name__ == "__main__":
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(render(spec))
