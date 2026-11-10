import json

import numpy as np
from PIL import Image

import tdh
from tdh import checks
from tdh import imaging as cap
from tdh import snapshots as snapshot


def test_info(td):
    info = tdh.info()
    assert info["td_build"] == "33230"
    assert info["harness_repo"].endswith("touchdesigner-harness") or info["harness_repo"]


def test_errors_tagged_and_excludes_harness_components(broken):
    found = tdh.errors("/project1")
    assert found == [{"path": "/project1/broken", "kind": "error", "message": "Compile error line 3"}]


def test_errors_clean_network(td):
    assert tdh.errors("/project1") == []


def test_stats_and_nan(td):
    s = tdh.stats("/project1/out1")
    assert (s["width"], s["height"]) == (96, 64)
    assert abs(s["mean"] - 0.5) < 1e-6 and s["nan_count"] == 0
    td.op("/project1/out1").pixels[0, 0, 0] = np.nan
    assert tdh.stats("/project1/out1")["nan_count"] == 1


OUT = "/project1/out1"


def test_motion_needs_two_samples(td):
    out = td.op(OUT)
    assert tdh.motion(out) == {"status": "pending"}
    td.tick(1.0, {OUT: 3})  # cook driver ran 3 frames; +1 for motion's own read
    assert tdh.motion(out) == {"status": "ok", "delta": 0.0, "cooks": 4}
    out.pixels = np.ones((64, 96, 4), np.float32)
    td.tick(1.0, {OUT: 1})
    assert tdh.motion(out)["delta"] > 0.4


def test_motion_waits_for_min_elapsed_time(td):
    # Live finding: two checks ~0.1 s apart passed with cooks: 2. Too close to mean anything.
    out = td.op(OUT)
    tdh.motion(out)
    td.tick(0.1, {OUT: 2})
    m = tdh.motion(out)
    assert m["status"] == "pending" and "0.10s apart" in m["hint"]
    out.pixels = np.ones((64, 96, 4), np.float32)
    td.tick(0.9, {OUT: 50})  # still compared against the first sample, now 1.0 s old
    m = tdh.motion(out)
    assert m["status"] == "ok" and m["cooks"] == 53 and m["delta"] > 0.4


def test_motion_stalled_when_only_our_read_cooks(td):
    # Live finding: without a driver, the probe's own read forces exactly one cook,
    # and a time-driven source draws a new frame -> looks like motion. Must be stalled.
    out = td.op(OUT)
    tdh.motion(out)
    out.pixels = np.ones((64, 96, 4), np.float32)  # new frame drawn by the forced cook
    td.tick(1.0)
    m = tdh.motion(out)
    assert m["status"] == "stalled" and m["cooks"] == 1 and m["delta"] > 0.4
    out.pixels = np.zeros((64, 96, 4), np.float32)  # and again: still only the forced cook
    td.tick(1.0)
    report = tdh.check({"checks": [{"type": "moving", "path": OUT}]}, print_summary=False)
    assert report["status"] == "fail" and report["results"][0]["cooks"] == 1


def test_motion_detects_stalled_cooking(td):
    # TD cooks on demand: no viewer -> no cooks -> frozen output. Must not read as "static".
    out = td.op(OUT)
    tdh.motion(out)
    td.tick(1.0)
    assert tdh.motion(out)["status"] == "stalled"
    td.tick(1.0)
    report = tdh.check({"checks": [{"type": "moving", "path": OUT}]}, print_summary=False)
    assert report["status"] == "fail" and "cook driver" in report["results"][0]["hint"]


def test_capture_png_roundtrip(td, tmp_path):
    px = np.zeros((40, 100, 4), np.float32)
    px[:20, :, 0] = 1.0  # bottom rows red in TD's bottom-up order
    td.op("/project1/out1").pixels = px
    res = tdh.capture("/project1/out1", tmp_path / "c.png", max_size=50)
    assert (res["width"], res["height"]) == (50, 20)
    img = np.asarray(Image.open(res["file"]).convert("RGB"))
    assert img.shape == (20, 50, 3)
    assert img[-1, 0, 0] == 255 and img[0, 0, 0] == 0  # flipped upright: red at bottom


def test_downscale_noop_when_small():
    a = np.zeros((10, 10, 3))
    assert cap.downscale(a, 64) is a


def test_checks_pass(td):
    spec = {
        "root": "/project1",
        "checks": [
            {"type": "no_errors"},
            {"type": "not_black", "path": "out1"},
            {"type": "no_nan", "path": "out1"},
            {"type": "chop_range", "path": "lfo1", "min": 0, "max": 1},
            {"type": "resolution", "path": "out1", "max": [1280, 1280]},
            {"type": "cook_budget", "max_ms": 100},
        ],
    }
    assert tdh.check(spec, print_summary=False)["status"] == "pending"  # cook_budget's first sample
    td.tick(1.0, {OUT: 60})
    report = tdh.check(spec, print_summary=False)
    assert report["status"] == "pass", report


def test_checks_fail_and_pending(broken):
    td = broken
    td.op("/project1/out1").pixels = np.zeros((8, 8, 4), np.float32)
    report = tdh.check({"checks": [
        {"type": "no_errors"},
        {"type": "not_black", "path": "out1"},
        {"type": "moving", "path": "out1"},
        {"type": "chop_range", "path": "lfo1", "max": 0.5},
        {"type": "resolution", "path": "missing"},
    ]}, print_summary=False)
    by = [r["status"] for r in report["results"]]
    assert by == ["fail", "fail", "pending", "fail", "error"]
    assert report["status"] == "fail"
    assert "FAIL" in checks.summary(report)


def test_pending_only_is_pending(td):
    spec = {"checks": [{"type": "moving", "path": "out1"}]}
    out = td.op(OUT)
    assert tdh.check(spec, print_summary=False)["status"] == "pending"
    td.tick(1.0, {OUT: 60})
    assert tdh.check(spec, print_summary=False)["status"] == "fail"  # cooking, but static image
    out.pixels = np.ones((64, 96, 4), np.float32)
    td.tick(1.0, {OUT: 60})
    assert tdh.check(spec, print_summary=False)["status"] == "pass"


def test_validate():
    assert checks.validate({"checks": [{"type": "nope"}, {"type": "cook_budget"}, {"type": "not_black"}]}) == [
        "checks[0]: unknown type 'nope'",
        "checks[1]: cook_budget needs max_ms",
        "checks[2]: not_black needs a path",
    ]


def test_snapshot_records_structure(td, tmp_path):
    res = tdh.snapshot("/project1", tmp_path / "net.json")
    snap = json.loads((tmp_path / "net.json").read_text())
    assert res["ops"] == len(snap["ops"])
    ops = snap["ops"]
    assert "TDMCP" not in ops and "TDMCP/inner" not in ops
    assert ops["noise1"]["pars"] == {"period": 4.0}  # only non-default
    assert ops["level1"]["inputs"] == [["noise1"]]
    assert ops["level1"]["pars"] == {"brightness1": {"expr": "absTime.seconds % 1"}}
    assert ops["notes"]["text"] == ["hello", "world"]
    assert "text" not in ops["info1"]  # generated DAT text is not recorded
    assert "inputs" not in ops["lfo1"]


def test_snapshot_is_deterministic(td):
    assert snapshot.dumps(snapshot.build("/project1")) == snapshot.dumps(snapshot.build("/project1"))


def test_snapshot_synced_dat_points_to_file(td):
    td.op("/project1/notes").par.file.val = "experiments/x/notes.txt"
    ops = snapshot.build("/project1")["ops"]
    assert ops["notes"]["text_file"] == "experiments/x/notes.txt" and "text" not in ops["notes"]


def test_save_tox(td, tmp_path):
    res = tdh.save_tox("/project1", tmp_path / "x" / "x.tox")
    assert res["comp"] == "/project1"
    assert (tmp_path / "x" / "x.tox").read_bytes() == b"fake tox /project1"


def test_cook_budget_counts_only_cooking_ops(td):
    # Live finding: a static Ramp TOP cooked once (43 ms at creation) and was summed
    # on every check, failing a 12 ms budget while TD held 60 fps at ~0.4 ms/frame.
    spec = {"checks": [{"type": "cook_budget", "path": "/project1", "max_ms": 1}]}
    for o in td._registry.values():
        o.totalCooks, o.cpuCookTime, o.gpuCookTime = 1, 0.0, 0.0
    td.op("/project1/level1").cpuCookTime = 43.0  # stale creation cook, never cooks again
    td.op("/project1/noise1").cpuCookTime = 0.3
    td.op(OUT).cpuCookTime = 0.1
    first = tdh.check(spec, print_summary=False)
    assert first["status"] == "pending"
    td.tick(1.0, {"/project1/noise1": 60, OUT: 60})
    report = tdh.check(spec, print_summary=False)
    r = report["results"][0]
    assert report["status"] == "pass", report
    assert r["cook_ms"] == 0.4 and r["active_ops"] == 2 and r["idle_ops"] > 0
    assert tdh.cook_ms("/project1") > 43  # the raw sum still shows the stale value


def test_cook_budget_fails_when_cooking_ops_are_over(td):
    spec = {"checks": [{"type": "cook_budget", "path": "/project1", "max_ms": 0.1}]}
    assert tdh.check(spec, print_summary=False)["status"] == "pending"
    td.tick(1.0, {OUT: 60})
    report = tdh.check(spec, print_summary=False)
    assert report["status"] == "fail" and report["results"][0]["active_ops"] == 1


def test_paths_use_forward_slashes(td):
    assert "\\" not in tdh.info()["harness_repo"]


def test_snapshot_treats_value_equal_to_default_as_default(td):
    # Live: noiseTOP.par.tx read 0, default 0, but isDefault False -> 'tx: 0.0' noise.
    par = td.op("/project1/noise1").par.seed
    par.reported_default = False
    assert "seed" not in snapshot.build("/project1")["ops"]["noise1"].get("pars", {})
    par.val = 2
    assert snapshot.build("/project1")["ops"]["noise1"]["pars"]["seed"] == 2
