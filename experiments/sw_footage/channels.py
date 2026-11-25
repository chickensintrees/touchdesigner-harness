# Which clip is on which channel. Pure Python with no TouchDesigner in it, so
# tests/test_footage.py can check it; inside TouchDesigner the player's driver
# calls it once per frame.
import math


def stride(step, count):
    """The nearest step at or above `step` that visits every one of `count` clips before any repeats."""
    count = max(1, int(count))
    step = max(1, int(step)) % count or 1
    while math.gcd(step, count) != 1:
        step += 1
    return step


def clip_for(channel, first, step, count):
    """The clip (0..count-1) shown on channel number `channel` (0, 1, 2, ...)."""
    count = max(1, int(count))
    return (int(first) + int(channel) * stride(step, count)) % count


def channel_at(bar_pos, bars):
    """The channel number at this place in the music: a new one every `bars` bars."""
    return int(math.floor(float(bar_pos) / max(0.25, float(bars))))
