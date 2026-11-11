"""An experiment must be playable from its own controls, and a control must do something."""

import fake_td


def _experiment(td, controls, inner=()):
    """A COMP /project1/x with the given custom parameters and inner operators."""
    r = td._registry
    P = fake_td.Par
    pars = [P(name, val, custom=True, **kw) for name, val, kw in controls]
    pars.append(P("externaltox", "", custom=False))
    fake_td.OP(r, "/project1/x", "baseCOMP", pars=pars)
    for make in inner:
        make(r)
    return "/project1/x"


def _expr(name, par, expr):
    return lambda r: fake_td.TOP(
        r, "/project1/x/" + name, "levelTOP",
        pars=[fake_td.Par(par, 1.0, default=1.0, mode=fake_td.ParMode.EXPRESSION, expr=expr)],
    )


def _script(name, text, kind="executeDAT"):
    return lambda r: fake_td.DAT(r, "/project1/x/" + name, kind, text=text, n_inputs=0)


THREE = [("Text", "HELLO", {}), ("Amount", 0.5, {}), ("Speed", 1.0, {})]
WIRED = (
    _expr("text1", "text", "parent().par.Text"),
    _expr("level1", "opacity", "parent().par.Amount * 2"),
    _script("driver", "def onFrameStart(frame):\n    s = parent().par.Speed.eval()\n"),
)


def test_lists_each_control_with_what_reads_it(td):
    import tdh

    found = {c["name"]: c for c in tdh.controls(_experiment(td, THREE, WIRED))}
    assert set(found) == {"Text", "Amount", "Speed"}
    assert found["Text"]["used_by"] == ["text1"]
    assert found["Amount"]["used_by"] == ["level1"]
    assert found["Speed"]["used_by"] == ["driver"]
    assert found["Text"]["value"] == "HELLO" and found["Text"]["kind"] == "control"


def test_check_passes_when_three_controls_are_wired(td):
    import tdh

    _experiment(td, THREE, WIRED)
    report = tdh.check({"root": "/project1/x", "checks": [{"type": "controls"}]}, print_summary=False)
    assert report["status"] == "pass"
    assert report["results"][0]["count"] == 3


def test_check_fails_with_too_few_controls(td):
    import tdh

    _experiment(td, THREE[:1], WIRED[:1])
    report = tdh.check({"root": "/project1/x", "checks": [{"type": "controls"}]}, print_summary=False)
    assert report["status"] == "fail"
    assert "expose" in report["results"][0]["hint"]


def test_a_control_wired_to_nothing_fails_the_check(td):
    import tdh

    _experiment(td, THREE + [("Decoy", 0.3, {})], WIRED)
    result = tdh.check({"root": "/project1/x", "checks": [{"type": "controls"}]}, print_summary=False)["results"][0]
    assert result["status"] == "fail"
    assert result["unused"] == ["Decoy"]


def test_similar_names_do_not_count_as_a_reference(td):
    import tdh

    # Only Speedup is read; Speed must not ride on it.
    inner = (_expr("a", "x", "parent().par.Speedup + parent().par.Text + parent().par.Amount"),)
    _experiment(td, THREE + [("Speedup", 2.0, {})], inner)
    found = {c["name"]: c["users"] for c in tdh.controls("/project1/x")}
    assert found == {"Text": 1, "Amount": 1, "Speed": 0, "Speedup": 1}


def test_bracket_and_bind_references_count(td):
    import tdh

    def bound(r):
        p = fake_td.Par("opacity", 1.0, default=1.0, mode=fake_td.ParMode.BIND)
        p.bindExpr = "parent().par.Amount"
        fake_td.TOP(r, "/project1/x/b", "levelTOP", pars=[p])

    inner = (_expr("a", "x", "parent().par['Text'] and me.parent().par[\"Speed\"]"), bound)
    _experiment(td, THREE, inner)
    assert all(c["users"] == 1 for c in tdh.controls("/project1/x"))


def test_readouts_are_not_controls_and_buttons_are(td):
    import tdh

    controls = THREE + [("Now", "showing", {"readOnly": True}), ("Reset", 0, {"isPulse": True})]
    inner = WIRED + (_script("pe", "def onPulse(par):\n    if par.name == 'Reset': parent().par.Reset\n", "parameterexecuteDAT"),)
    _experiment(td, controls, inner)
    kinds = {c["name"]: c["kind"] for c in tdh.controls("/project1/x")}
    assert kinds["Now"] == "readout" and kinds["Reset"] == "button"
    result = tdh.check({"root": "/project1/x", "checks": [{"type": "controls", "min": 4}]}, print_summary=False)["results"][0]
    assert result["status"] == "pass" and "Now" not in result["controls"]


def test_built_in_parameters_and_generated_dats_are_ignored(td):
    import tdh

    # An Info DAT's text changes every frame and is not authored: it cannot make a control live.
    inner = WIRED[:2] + (_script("info1", "parent().par.Speed", "infoDAT"),)
    _experiment(td, THREE, inner)
    found = {c["name"]: c["users"] for c in tdh.controls("/project1/x")}
    assert "externaltox" not in found
    assert found["Speed"] == 0


def test_allow_unused_names_a_deliberate_exception(td):
    import tdh

    _experiment(td, THREE + [("Preview", True, {})], WIRED)
    spec = {"root": "/project1/x", "checks": [{"type": "controls", "allow_unused": ["Preview"]}]}
    assert tdh.check(spec, print_summary=False)["status"] == "pass"


def test_a_comp_with_no_custom_parameters_fails_quietly(td):
    import tdh

    _experiment(td, [], ())
    result = tdh.check({"root": "/project1/x", "checks": [{"type": "controls"}]}, print_summary=False)["results"][0]
    assert result["status"] == "fail" and result["count"] == 0


def test_show_reports_what_it_opened(td):
    import tdh

    _experiment(td, THREE, WIRED)
    assert tdh.show("/project1/x") == {"comp": "/project1/x", "opened": []}  # the fake has no windows


def test_template_requires_controls():
    import json
    from pathlib import Path

    spec = json.loads((Path(__file__).parent.parent / "experiments" / "_template" / "checks.json").read_text())
    assert any(c["type"] == "controls" for c in spec["checks"])
