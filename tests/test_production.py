import pytest

from creaper import styles, theory
from creaper.knowledge import Knowledge
from creaper.server import Lfo, Ramp, _automation_points


def n(pitch, start, length=0.5, velocity=100, channel=1):
    return {"pitch": pitch, "start": start, "length": length, "velocity": velocity, "channel": channel}


# --------------------------------------------------------------------- MIDI

def test_quantize_full_partial_and_swing():
    notes = [n(60, 0.07), n(62, 0.48), n(64, 1.02)]
    assert [x["start"] for x in theory.quantize(notes, 0.25)] == [0.0, 0.5, 1.0]
    assert theory.quantize(notes, 0.25, strength=0.5)[0]["start"] == pytest.approx(0.035)
    swung = theory.quantize([n(60, 0.25), n(62, 0.5)], 0.25, swing=66.67)
    assert swung[0]["start"] == pytest.approx(1 / 3, abs=1e-3)  # off-beat 16th delayed
    assert swung[1]["start"] == 0.5                               # on-beat untouched


def test_humanize_stays_in_range_and_is_seedable():
    notes = [n(60, i * 0.5, velocity=126) for i in range(20)]
    a = theory.humanize(notes, timing=0.05, velocity=10, seed=1)
    assert a == theory.humanize(notes, timing=0.05, velocity=10, seed=1)
    assert all(abs(x["start"] - y["start"]) <= 0.05 + 1e-9 and 1 <= x["velocity"] <= 127 for x, y in zip(a, notes))


def test_transpose_and_range_check():
    assert [x["pitch"] for x in theory.transpose([n(60, 0), n(64, 1)], -12)] == [48, 52]
    with pytest.raises(ValueError):
        theory.transpose([n(120, 0)], 12)


def test_snap_to_scale():
    # C# and F# into C major: C# -> C (tie goes down), F# -> F (tie goes down)
    snapped = theory.snap_to_scale([n(61, 0), n(66, 1), n(64, 2)], "C", "major")
    assert [x["pitch"] for x in snapped] == [60, 65, 64]
    assert theory.snap_to_scale([n(61, 0)], "C", "major", "up")[0]["pitch"] == 62
    assert theory.snap_to_scale([n(70, 0)], "A", "minor")[0]["pitch"] == 69  # A# -> A
    with pytest.raises(ValueError):
        theory.snap_to_scale([n(60, 0)], "C", "klingon")


def test_velocity_fixed_ramp_and_scale():
    notes = [n(60, 0, velocity=50), n(60, 1, velocity=50), n(60, 2, velocity=50)]
    assert [x["velocity"] for x in theory.set_velocity(notes, value=90)] == [90, 90, 90]
    assert [x["velocity"] for x in theory.set_velocity(notes, start=40, end=120)] == [40, 80, 120]
    assert [x["velocity"] for x in theory.set_velocity(notes, scale=3)] == [127, 127, 127]


def test_strum_and_legato():
    chord = [n(64, 0, 2), n(60, 0, 2), n(67, 0, 2)]
    up = theory.strum(chord, delay=0.05)
    assert [(x["pitch"], x["start"]) for x in up] == [(60, 0.0), (64, 0.05), (67, 0.1)]
    down = theory.strum(chord, delay=0.05, direction="down")
    assert [x["pitch"] for x in down] == [67, 64, 60]
    lines = theory.legato([n(60, 0, 0.25), n(62, 1, 0.25), n(64, 2, 0.25)])
    assert [x["length"] for x in lines] == [1.0, 1.0, 0.25]


# --------------------------------------------------------------- automation

def test_ramp_points():
    pts = _automation_points(None, Ramp(start_bar=9, end_bar=17, start_value=20, end_value=80), None)
    assert [(p["bar"], p["value"], p["shape"]) for p in pts] == [(9, 20, "smooth"), (17, 80, "linear")]
    with pytest.raises(ValueError):
        _automation_points(None, Ramp(start_bar=5, end_bar=5, start_value=0, end_value=1), None)


@pytest.mark.parametrize("wave", ["sine", "triangle", "square", "saw"])
def test_lfo_points_stay_in_range_and_span(wave):
    pts = _automation_points(None, None, Lfo(start_bar=1, end_bar=3, cycles_per_bar=2, low=-6, high=0, wave=wave))
    assert min(p["value"] for p in pts) >= -6 - 1e-9 and max(p["value"] for p in pts) <= 0 + 1e-9
    assert pts[0]["bar"] == 1 and pts[-1]["bar"] == pytest.approx(3)


def test_needs_something():
    with pytest.raises(ValueError):
        _automation_points(None, None, None)


# ------------------------------------------------------------------- styles

def test_find_styles_by_name_and_alias():
    assert styles.find_style("DnB").name == "drum and bass"
    assert styles.find_style("90s r&b").name == "r&b"
    with pytest.raises(ValueError, match="Known"):
        styles.find_style("sea shanty")
    for s in styles.STYLES:
        assert s.lufs[0] < s.lufs[1] and s.lra[0] < s.lra[1]


def test_compare_flags_loud_and_peaky_masters():
    analysis = {
        "loudness": {"integrated_lufs": -5.0, "loudness_range_lu": 2.0},
        "levels": {"true_peak_dbtp": 0.4},
        "stereo": {"low_end_correlation_below_150hz": 0.3},
        "spectrum": {"bands": {"sub (20-60 Hz)": {"share_pct": 20}, "bass (60-250 Hz)": {"share_pct": 40}},
                     "spectral_centroid_hz": 1500},
    }
    findings = {f["area"]: f for f in styles.compare(analysis, styles.find_style("lo-fi"))}
    assert findings["integrated loudness (LUFS)"]["verdict"] == "high"
    assert findings["true peak (dBTP)"]["verdict"] == "high"
    assert findings["loudness range (LU)"]["verdict"] == "low"
    assert findings["low-end mono compatibility"]["verdict"] == "check"
    assert findings["low end (% of energy below 250 Hz)"]["verdict"] == "info"
    ok = styles.compare({"loudness": {"integrated_lufs": -12, "loudness_range_lu": 6},
                         "levels": {"true_peak_dbtp": -1.5}}, styles.find_style("lo-fi"))
    assert all(f["verdict"] == "ok" for f in ok)


# ---------------------------------------------------------------- knowledge

def test_knowledge_store(tmp_path):
    k = Knowledge(tmp_path / "knowledge.json")
    a = k.add("Prefers dark, warm pads", "preference")
    k.add("Cutoff is called 'CutOff' on the Mini V3", "plugin", "Mini V3")
    assert k.add("prefers dark, warm pads", "preference")["id"] == a["id"]  # no duplicates
    assert [x["topic"] for x in k.find("pads")] == ["preference"]
    assert k.find(subject="mini")[0]["subject"] == "Mini V3"
    assert len(Knowledge(tmp_path / "knowledge.json").find()) == 2
    k.delete(a["id"])
    assert len(k.find()) == 1
    with pytest.raises(ValueError):
        k.add("x", "gossip")
