"""Speakers: nothing in the project plays out loud unless a person turned it up.

An Audio Device Out CHOP is created with its volume at 1, so an operator dropped
into a network plays at full volume on the user's speakers the moment the
timeline runs. The rule (AGENTS.md rule 17): a speaker's volume is driven by a
control on its experiment that defaults to 0. A speaker with a plain constant
volume above 0 was never given that control, and is a fault.

    tdh.speakers()            every Audio Device Out, its volume, and whether a control drives it
    tdh.mute()                silence the faulty ones (constant volume above 0); returns their paths
    tdh.mute(everything=True) also switch off the ones a control turned up

`tdh.info()` reports the faulty ones as `speakers_on`, and every `tdh.check(...)`
fails while its experiment has one. Unlike the rest of tdh, mute() changes
parameters: it is the one fix that must never wait for a build step.
"""

from __future__ import annotations

from ._td import get_op, walk

SPEAKER = "audiodeviceoutCHOP"


def _value(par, fallback):
    if par is None:
        return fallback
    try:
        return par.eval()
    except Exception:  # noqa: BLE001 -- a broken expression must not hide the speaker
        return fallback


def _controlled(par):
    """True when the volume follows an expression, an export or a bind, not a typed number."""
    return par is not None and getattr(getattr(par, "mode", None), "name", "CONSTANT") != "CONSTANT"


def speakers(root="/project1"):
    """Every Audio Device Out under root: [{path, volume, active, controlled, loud, fault}]."""
    found = []
    for node in walk(get_op(root)):
        if getattr(node, "OPType", "") != SPEAKER:
            continue
        vol = node.par.volume
        volume = float(_value(vol, 1.0) or 0.0)
        active = bool(_value(node.par.active, True))
        controlled = _controlled(vol)
        loud = active and volume > 0
        found.append({"path": node.path, "volume": volume, "active": active, "controlled": controlled,
                      "loud": loud, "fault": loud and not controlled})
    return found


def faults(root="/project1"):
    """Paths of speakers that are audible with no control behind their volume."""
    return [s["path"] for s in speakers(root) if s["fault"]]


def mute(root="/project1", everything=False):
    """Silence the speakers under root. Returns {"muted": [paths], "left_on": [paths]}.

    A constant volume is set to 0. A volume that a control drives is left alone
    (somebody turned it up) unless everything=True, which switches that output off.
    """
    muted, left = [], []
    for s in speakers(root):
        if not s["loud"]:
            continue
        node = get_op(s["path"])
        if not s["controlled"]:
            node.par.volume.val = 0
            muted.append(s["path"])
        elif everything:
            node.par.active.val = False
            muted.append(s["path"])
        else:
            left.append(s["path"])
    return {"muted": muted, "left_on": left}
