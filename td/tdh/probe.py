"""Read-only inspection: errors, TOP pixel stats, motion, cook time, info."""

from __future__ import annotations

import numpy as np

from ._td import REPO_ROOT, get_op, td, walk

_KINDS = (("error", "errors"), ("warning", "warnings"), ("script", "scriptErrors"))


def _messages(node, method):
    fn = getattr(node, method, None)
    if fn is None:
        return []
    try:
        text = fn(recurse=False)
    except TypeError:
        text = fn()
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def errors(root="/project1", warnings=True):
    """Every error / warning / script error under root, one entry per message,
    tagged with the operator path that owns it."""
    out = []
    for node in walk(root):
        for kind, method in _KINDS:
            if kind == "warning" and not warnings:
                continue
            for msg in _messages(node, method):
                out.append({"path": node.path, "kind": kind, "message": msg})
    return out


def _pixels(top):
    """RGB float array (h, w, 3) from a TOP, NaNs preserved."""
    arr = np.asarray(get_op(top).numpyArray(), dtype=np.float32)
    if arr.ndim == 2:
        arr = arr[..., None]
    if arr.shape[2] == 1:
        arr = np.repeat(arr, 3, axis=2)
    return arr[..., :3]


def stats(top):
    """Pixel statistics for a TOP: size, mean/min/max/std, luma, NaN count."""
    rgb = _pixels(top)
    nan = int(np.isnan(rgb).sum())
    clean = np.nan_to_num(rgb, nan=0.0, posinf=1.0, neginf=0.0)
    luma = clean @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    return {
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
        "mean": float(clean.mean()),
        "min": float(clean.min()),
        "max": float(clean.max()),
        "std": float(clean.std()),
        "luma_mean": float(luma.mean()),
        "nan_count": nan,
    }


def signature(top, size=16):
    """Small grayscale thumbnail used to detect motion between two calls."""
    rgb = np.nan_to_num(_pixels(top))
    gray = rgb.mean(axis=2)
    h, w = gray.shape
    ys = np.linspace(0, h - 1, min(size, h)).astype(int)
    xs = np.linspace(0, w - 1, min(size, w)).astype(int)
    return gray[np.ix_(ys, xs)]


_last_signature: dict = {}


def total_cooks(node):
    """TD's running cook counter for an OP, or None if this build lacks it."""
    val = getattr(get_op(node), "totalCooks", None)
    return int(val) if isinstance(val, (int, float)) else None


def _now():
    """Seconds on TD's absolute clock, or None if unavailable."""
    clock = getattr(td(), "absTime", None)
    val = getattr(clock, "seconds", None)
    return float(val) if isinstance(val, (int, float)) else None


MIN_MOTION_SECONDS = 0.5


def motion(top, min_seconds=MIN_MOTION_SECONDS):
    """Compare this frame with the one seen on an earlier call for the same TOP.

    Returns {'status': 'pending'} on the first call, and also when the
    previous sample is less than min_seconds old (the stored sample is kept,
    so the next call compares against it). Otherwise
    {'status': 'ok', 'delta': mean abs difference (0..1), 'cooks': n}, or
    {'status': 'stalled', ...} if the TOP cooked at most once in between
    (the one cook our own pixel read forces).

    TD cooks on demand: with no viewer or output pulling on it, a network
    stops cooking and time-based CHOPs (trail, lag, feedback) freeze. 'stalled'
    means "nothing cooked", not "nothing moved" -- add a cook driver (see
    td-new-experiment) rather than concluding the output is static.

    The main thread must not block, so motion is measured across two separate
    calls (e.g. two tdh.check runs about a second apart), not by waiting."""
    node = get_op(top)
    now = _now()
    prev = _last_signature.get(node.path)
    if prev is not None and now is not None and prev[2] is not None and now - prev[2] < min_seconds:
        return {"status": "pending", "hint": f"samples {now - prev[2]:.2f}s apart; need >= {min_seconds}s"}
    sig = signature(node)
    cooks = total_cooks(node)
    _last_signature[node.path] = (sig, cooks, now)
    if prev is None or prev[0].shape != sig.shape:
        return {"status": "pending"}
    prev_sig, prev_cooks, _ = prev
    delta = float(np.abs(sig - prev_sig).mean())
    if cooks is not None and prev_cooks is not None:
        cooked = cooks - prev_cooks
        # Reading pixels forces one cook by itself. With a time-driven source
        # (absTime, Trail, Feedback) that single forced cook draws a new frame
        # and looks like motion, so <= 1 cook between samples means "nothing
        # else is cooking this TOP", i.e. no cook driver (confirmed live).
        if cooked <= 1:
            return {"status": "stalled", "delta": delta, "cooks": cooked}
        return {"status": "ok", "delta": delta, "cooks": cooked}
    return {"status": "ok", "delta": delta}


def _op_ms(node):
    total = 0.0
    for attr in ("cpuCookTime", "gpuCookTime"):
        val = getattr(node, attr, None)
        if isinstance(val, (int, float)):
            total += float(val)
    return total


def cook_ms(root="/project1"):
    """Sum of every op's last cpuCookTime + gpuCookTime (ms) under root.

    Raw and naive: an op that cooked once long ago (a static Ramp TOP at
    creation, 43 ms on a real install) is still counted. For a per-frame
    budget use cook_sample(), which counts only ops that are cooking."""
    return sum(_op_ms(node) for node in walk(root))


_last_cooks: dict = {}


def cook_sample(root="/project1"):
    """Per-frame cook cost of root: CPU + GPU ms summed over the ops whose
    totalCooks went up since the previous cook_sample() of the same root.

    First call -> {'status': 'pending'} (it only records counters).
    Then {'status': 'ok', 'cook_ms', 'active_ops', 'idle_ops'}. Ops without a
    totalCooks attribute are counted as active (conservative)."""
    root_op = get_op(root)
    previous = _last_cooks.get(root_op.path)
    current, total, active, idle = {}, 0.0, 0, 0
    for node in walk(root_op):
        tc = getattr(node, "totalCooks", None)
        tc = int(tc) if isinstance(tc, (int, float)) else None
        current[node.path] = tc
        if previous is None:
            continue
        before = previous.get(node.path)
        if tc is None or (before is not None and tc > before):
            total += _op_ms(node)
            active += 1
        elif before is None:
            total += _op_ms(node)  # created since the last sample: count it once, conservatively
            active += 1
        else:
            idle += 1
    _last_cooks[root_op.path] = current
    if previous is None:
        return {"status": "pending"}
    return {"status": "ok", "cook_ms": total, "active_ops": active, "idle_ops": idle}


def info():
    """Who and where: TD build, project, harness repo path."""
    t = td()
    app = getattr(t, "app", None)
    project = getattr(t, "project", None)
    return {
        "td_version": getattr(app, "version", None),
        "td_build": getattr(app, "build", None),
        "os": getattr(app, "osName", None),
        "project": getattr(project, "name", None),
        "project_folder": getattr(project, "folder", None),
        "harness_repo": REPO_ROOT.as_posix(),
    }
