import drum_synth as d
import pytest

from creaper import listen


@pytest.mark.parametrize("kind", list(d.KIT))
def test_classifies_synthesized_drums(kind):
    f = listen.features(d.KIT[kind](), d.FS)
    assert listen.classify_drum(f)[0] == kind


def test_silence():
    f = listen.features(d.kick() * 1e-5, d.FS)
    assert f["silent"] and listen.classify_drum(f)[0] == "silent"


def test_pitch_and_envelope_of_a_held_tone():
    for freq in (55, 110, 440, 880):
        f = listen.features(d.tone(freq), d.FS, note_off=1.0)
        assert abs(f["pitch_hz"] - freq) < freq * 0.02
        assert f["decay_s"] is None and f["sustain_db"] > -8 and f["release_s"] < 0.5


def test_lanes_and_pitch_tracking():
    kit = []
    for pitch, (kind, fn) in zip(range(36, 46), d.KIT.items()):
        f = listen.features(fn(), d.FS)
        f.update({"pitch": pitch, "note": str(pitch)})
        f["kind"], f["confidence"] = listen.classify_drum(f)
        kit.append(f)
    lanes = listen.choose_lanes(kit)
    assert lanes["kick"] == 36 and lanes["snare"] == 37 and lanes["closed hat"] == 39
    assert listen.tracks_pitch(kit)[0] is False

    synth = []
    for pitch in (36, 48, 60, 72):
        f = listen.features(d.tone(listen.note_freq(pitch + 12)), d.FS, note_off=1.0)
        f.update({"pitch": pitch, "note": str(pitch)})
        synth.append(f)
    follows, offset = listen.tracks_pitch(synth)
    assert follows and offset == 12
    summary = listen.describe_patch(synth)
    assert summary["follows_pitch"] and summary["transposition_semitones"] == 12 and "sustained" in summary["character"]


def test_map_kit_on_synthesized_kits():
    import random

    rng = random.Random(4)
    kinds = ["kick", "snare", "closed hat", "open hat", "clap", "crash", "tom"]
    for gm in (True, False):
        for _ in range(5):
            keys = rng.sample(range(24, 84), len(kinds)) if not gm else [36, 38, 42, 46, 39, 49, 45]
            kit = []
            for kind, pitch in zip(kinds, keys):
                f = listen.features(d.KIT[kind](), d.FS)
                f.update({"pitch": pitch, "note": str(pitch)})
                kit.append(f)
            lanes, labels = listen.map_kit(kit)
            truth = dict(zip(kinds, keys))
            for lane in ("kick", "snare", "closed hat"):
                assert lanes[lane] == truth[lane], (gm, lane, lanes)
            if gm:
                assert listen.follows_gm(lanes)


def test_late_start_is_measured_not_mistaken_for_attack():
    import numpy as np

    hat = d.closed_hat()
    late = np.concatenate([np.zeros(int(0.3 * d.FS)), hat])[: len(hat)]
    f = listen.features(late, d.FS)
    assert 295 <= f["starts_late_ms"] <= 305 and f["attack_ms"] < 5
    assert listen.features(hat, d.FS)["starts_late_ms"] < 2


def test_harmonic_fit_finds_the_real_octave():
    saw = d.tone(220.0, length=0.5, held=0.5)
    assert listen.harmonic_fit(saw, d.FS, 220.0)[0] == 0
    assert listen.harmonic_fit(saw, d.FS, 440.0)[0] == -1   # sounds an octave below the played note
    assert listen.harmonic_fit(saw, d.FS, 110.0)[0] == 1    # sounds an octave above
    k, score, _ = listen.harmonic_fit(d.closed_hat(0.5), d.FS, 220.0)
    assert score < 0.5                                       # noise isn't harmonic
