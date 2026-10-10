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
