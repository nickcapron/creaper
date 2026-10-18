"""What the user had to coach the vocals through, done by creaper: new takes onto the
same track, an octave toward the voice, hard tuning, a voice EQ, honest syllable counts,
and the panel's patience with long tools."""

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import chat, singing, speech, vocal_tools
from test_singing import FS, median_f0, vowel


@pytest.mark.parametrize("word,count", [("lines", 1), ("tires", 1), ("times", 1), ("burned", 1), ("places", 2),
                                        ("changes", 2), ("waited", 2), ("tonight", 2), ("little", 2)])
def test_syllables_are_counted_as_sung(word, count):
    assert vocal_tools.syllables(word) == count


def test_hard_tuning_snaps_onto_the_notes():
    x = vowel(140, 0.5)
    hard = singing.sing_word(x, FS, 1.2, [(0.0, 57), (0.6, 64)], (int(0.05 * FS), int(0.45 * FS)), hard=True)
    c, f0, _ = singing.f0_track(hard, FS)
    held = f0[(c > 0.75 * FS) & (c < 1.15 * FS) & (f0 > 0)]
    assert np.ptp(12 * np.log2(held / 329.6)) < 0.2                      # no vibrato
    just_after = f0[(c > 0.64 * FS) & (c < 0.7 * FS) & (f0 > 0)]           # past the tracker's 35 ms window
    assert np.all(np.abs(12 * np.log2(just_after / 329.6)) < 0.3)       # no glide: on the new note at once


def test_the_voice_eq_brings_presence():
    from scipy import signal
    x = vowel(150, 1.0, formants=(500, 900, 2400))

    def share(y):
        f, p = signal.welch(y, FS, nperseg=2048)
        return p[(f >= 2000) & (f < 4000)].sum() / p.sum()
    assert share(singing.voice_eq(x, FS)) > 1.8 * share(x)


def test_a_new_take_goes_onto_the_same_track(monkeypatch, tmp_path):
    notes = [{"pitch": p, "start": i * 1.0, "length": 0.9, "velocity": 90} for i, p in enumerate((45, 48, 50))]
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_midi_notes":
            return {"notes": notes, "start": {"qn": 0.0}, "track": 1}
        if cmd == "project_paths":
            return {"default_folder": str(tmp_path)}
        if cmd == "qn_to_times":
            return [q * 0.5 for q in kw["qns"]]
        if cmd == "get_project_overview":
            return {"tracks": [{"name": "Lead"}, {"name": "Hook", "guid": "{H}"}]}
        if cmd == "get_track_details":
            return {"items": [{"id": "{old1}"}, {"id": "{old2}"}]}
        if cmd == "place_audio_clips":
            return {"track": {"name": kw["track"]}, "placed": len(kw["clips"])}
        if cmd in ("delete_item", "create_track"):
            return {}
        raise AssertionError(cmd)

    def fake_phrase(text, path, voice=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        speech._write(path, np.concatenate([np.r_[vowel(120, 0.3), np.zeros(1500)] for _ in text.split()]), FS)
        return path

    def fake_words(texts, folder, voice=None):
        folder.mkdir(parents=True, exist_ok=True)
        out = []
        for i, _ in enumerate(texts):
            f = folder / f"{i}.wav"
            speech._write(f, vowel(120, 0.3), FS)
            out.append(f)
        return out

    monkeypatch.setattr(vocal_tools, "call", fake_call)
    monkeypatch.setattr(speech, "speak_phrase", fake_phrase)
    monkeypatch.setattr(speech, "speak", fake_words)
    monkeypatch.setattr(speech, "choose_voice", lambda v: "Piper Joe")
    import creaper.ear_tools as ear
    monkeypatch.setattr(ear, "measure_vocal_clarity", lambda *a, **k: {"alone": {"score": 0.8}})
    out = vocal_tools.add_robot_vocal(item_id="{M}", lyrics="go go go", style="sung", name="Hook", replace=True,
                                      tuning="hard")
    cmds = [c for c, _ in calls]
    assert "create_track" not in cmds and cmds.count("delete_item") == 2
    assert next(kw for c, kw in calls if c == "place_audio_clips")["track"] == "Hook"
    assert "kept" in out["replaced"]


def test_the_panel_lets_long_tools_run():
    assert chat.TOOL_TIMEOUT_MS >= 2 * 3600 * 1000
