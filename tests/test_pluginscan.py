import fx_synth as F
import pytest

from creaper import pluginscan as P

X = P.test_signal(F.FS)

EXPECT = {
    "passthrough": "no audible change", "gain": "gain", "lowpass": "eq/filter", "highpass": "eq/filter",
    "reverb": "reverb", "delay": "delay", "compressor": "compressor", "limiter": "limiter",
    "gate": "gate/expander", "saturation": "distortion", "distortion": "distortion",
    "tremolo": "modulation", "chorus": "modulation", "widener": "stereo",
}


@pytest.mark.parametrize("effect", list(EXPECT))
def test_recognises_reference_effects(effect):
    m = P.analyze_effect(X, getattr(F, effect)(X), F.FS)
    assert m["roles"][0] == EXPECT[effect], (effect, m["roles"], m["summary"])


def test_details():
    assert "tremolo" in P.analyze_effect(X, F.tremolo(X), F.FS)["summary"]
    assert "chorus" in P.analyze_effect(X, F.chorus(X), F.FS)["summary"]
    assert "cuts highs" in P.analyze_effect(X, F.lowpass(X), F.FS)["summary"]
    m = P.analyze_effect(X, F.latency(X), F.FS)
    assert m["latency_ms"] == pytest.approx(10, abs=0.1) and m["roles"] == ["no audible change"]
    d = P.analyze_effect(X, F.delay(X), F.FS)
    assert d["echoes_s"][0] == pytest.approx(0.375, abs=0.01)


def test_silent_effect():
    import numpy as np

    m = P.analyze_effect(X, np.zeros((len(X), 2)), F.FS)
    assert m["roles"] == ["no output"]


def test_catalog_roundtrip(tmp_path):
    cat = P.PluginCatalog(tmp_path / "catalog.json")
    assert cat.all() == {}
    cat.put("VST3: Thing (Dev)", {"kind": "effect", "roles": ["reverb"]})
    assert cat.get("VST3: Thing (Dev)")["roles"] == ["reverb"]


def _features(audio, pitch, note_off=None):
    from creaper import listen

    f = listen.features(audio, F.FS, note_off=note_off)
    f.update({"pitch": pitch, "note": str(pitch)})
    return f


def test_instrument_summaries():
    import drum_synth as D
    import numpy as np

    from creaper import listen

    octaves = [24 + 12 * i for i in range(7)]
    silent_kit = [_features(np.zeros(int(0.8 * F.FS)), p) for p in range(36, 52)]
    synth = [_features(D.tone(listen.note_freq(p), length=2.0), p, note_off=1.0) for p in octaves]
    s = P.analyze_instrument(synth, silent_kit)
    assert s["roles"] == ["pitched instrument"] and "in tune" in s["summary"]

    kit_sounds = list(D.KIT.values())
    kit = [_features(kit_sounds[i % len(kit_sounds)](length=0.8), p) for i, p in enumerate(range(36, 52))]
    silent_octaves = [_features(np.zeros(int(2 * F.FS)), p, note_off=1.0) for p in octaves]
    k = P.analyze_instrument(silent_octaves, kit)
    assert "drum kit" in k["roles"]

    nothing = P.analyze_instrument(silent_octaves, silent_kit)
    assert nothing["roles"] == ["silent"]
