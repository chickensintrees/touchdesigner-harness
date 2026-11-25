"""Generate the asset pack's instrumental tracks with the ElevenLabs Music API.

    python tools/assets/make_music.py <pack_dir> [track ...]

Writes <pack_dir>/music/<track>.mp3 for each track in TRACKS (or the ones named).
Needs the ELEVENLABS_API_KEY environment variable and the `requests` package.
Each call is charged to that ElevenLabs account. A track that already exists is
skipped, so delete it to regenerate.

After generating, a track still needs its analysis feed before the hub can use
it: analyse the audio into a score, then run tools/audiofeed/bake_feed.py into
<pack_dir>/feeds/<track>/.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests

URL = "https://api.elevenlabs.io/v1/music"

# Length: on 2026-11-11 the API returned 180 s and 210 s for requests of 96 s and 84 s,
# so "duration_seconds" was not honoured as sent here. Check the API's current
# parameter for length before relying on it; the pack's tracks are those longer takes.
#
# Arrangements are described section by section: the scene cutter changes scene on
# section changes and treats loud passages differently, so contrast matters.
TRACKS = {
    "drive": {
        "seconds": 96,
        "prompt": (
            "Instrumental electronic track, 124 BPM, four-on-the-floor. No vocals. "
            "Punchy kick drum, crisp clap on beats two and four, tight closed hi-hats, a rolling analogue bassline, "
            "a bright plucked synth lead with a memorable melody, warm chord pads. "
            "Clear arrangement with strong contrast: a sparse intro with filtered drums and bass, a build with a rising "
            "sweep and snare roll, a full energetic drop, a breakdown with no kick where only pads and the lead remain, "
            "a second build, a bigger final drop, then a short outro. Clean, modern, confident, uplifting."
        ),
    },
    "drift": {
        "seconds": 84,
        "prompt": (
            "Instrumental downtempo track, 86 BPM, broken beat. No vocals. "
            "Deep sub bass, a soft thudding kick and rim clicks in a syncopated pattern, shimmering plucked arpeggio, "
            "long evolving pads, a slow glassy lead melody, tape-like warmth. "
            "Spacious and patient with clear sections: an almost silent opening of pads alone, the beat enters gently, "
            "a fuller middle passage with the arpeggio and lead, a near-silent breakdown, a final fuller passage, "
            "and a fade to quiet. Mysterious, nocturnal, cinematic."
        ),
    },
}


def generate(name, spec, out_dir, key):
    out = out_dir / (name + ".mp3")
    if out.exists():
        print(name, "exists, skipped")
        return out
    started = time.time()
    response = requests.post(
        URL,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={"prompt": spec["prompt"], "duration_seconds": spec["seconds"], "output_format": "mp3_44100_128"},
        timeout=600,
    )
    if response.status_code != 200:
        raise SystemExit("%s: HTTP %s %s" % (name, response.status_code, response.text[:400]))
    out.write_bytes(response.content)
    print("%s: %d kB in %.0f s" % (name, len(response.content) // 1024, time.time() - started))
    return out


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    out_dir = Path(argv[1]) / "music"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in argv[2:] or list(TRACKS):
        generate(name, TRACKS[name], out_dir, key)


if __name__ == "__main__":
    main(sys.argv)
