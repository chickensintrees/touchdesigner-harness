"""The footage player's channels, checked without TouchDesigner."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location("channels", ROOT / "experiments" / "sw_footage" / "channels.py")
channels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(channels)


def test_every_clip_is_shown_before_any_comes_back():
    for count in (18, 6, 7, 1, 21):
        for step in (1, 5, 7, 9, 18):
            seen = [channels.clip_for(n, 3, step, count) for n in range(count)]
            assert sorted(seen) == list(range(count)), (count, step)
            assert channels.clip_for(count, 3, step, count) == seen[0]


def test_neighbouring_channels_differ_and_first_clip_is_the_control():
    assert channels.clip_for(0, 4, 7, 18) == 4
    assert all(channels.clip_for(n, 0, 7, 18) != channels.clip_for(n + 1, 0, 7, 18) for n in range(40))


def test_a_new_channel_every_so_many_bars():
    assert [channels.channel_at(b, 2.0) for b in (0.0, 1.99, 2.0, 5.5)] == [0, 0, 1, 2]
    assert channels.channel_at(3.0, 0.0) == 12  # a silly setting is held at a quarter of a bar
