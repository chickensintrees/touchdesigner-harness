"""Capture a TOP to a small PNG on disk so the agent can look at it.

Encodes the PNG itself (numpy + zlib) so it needs no PIL inside TD, and
downscales by block-averaging so images sent to the model stay small.
"""

from __future__ import annotations

import struct
import zlib

import numpy as np

from ._td import get_op, resolve_path
from .probe import _pixels


def downscale(rgb, max_size):
    """Block-average an (h, w, 3) array so its longest side is <= max_size."""
    h, w = rgb.shape[:2]
    factor = max(1, -(-max(h, w) // max_size))  # ceil division
    if factor == 1:
        return rgb
    h2, w2 = h // factor, w // factor
    cropped = rgb[: h2 * factor, : w2 * factor]
    return cropped.reshape(h2, factor, w2, factor, -1).mean(axis=(1, 3))


def to_uint8(rgb):
    clean = np.nan_to_num(rgb, nan=0.0, posinf=1.0, neginf=0.0)
    return (np.clip(clean, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def encode_png(rgb8):
    """Encode an (h, w, 3) uint8 array as an RGB PNG."""
    h, w = rgb8.shape[:2]
    rows = np.ascontiguousarray(rgb8[..., :3])
    raw = b"".join(b"\x00" + rows[y].tobytes() for y in range(h))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )


def capture(top, file, max_size=768, flip=True):
    """Save a TOP's current frame as a PNG (longest side <= max_size).

    file: path; relative paths resolve against the harness repo root.
    flip: TD's numpyArray() rows start at the bottom of the image; flip so
          the PNG is upright. Set False if a capture comes out upside down.
    Returns {'file', 'width', 'height', 'source_width', 'source_height'}.
    """
    node = get_op(top)
    rgb = _pixels(node)
    if flip:
        rgb = rgb[::-1]
    small = downscale(rgb, max_size)
    out = resolve_path(file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(encode_png(to_uint8(small)))
    return {
        "file": out.as_posix(),
        "width": int(small.shape[1]),
        "height": int(small.shape[0]),
        "source_width": int(rgb.shape[1]),
        "source_height": int(rgb.shape[0]),
    }
