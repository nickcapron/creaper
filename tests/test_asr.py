"""The opt-in speech recogniser: never imported unless used, how lines are found and
scored, its place in add_robot_vocal's result, and (when installed) the real model
hearing a talk box."""

import re
import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import asr, speech, vocal_tools


def test_creaper_never_imports_the_recogniser():
    code = ("import sys; from creaper import server, vocal_tools; "
            "print('faster_whisper' in sys.modules, 'ctranslate2' in sys.modules)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    assert out == "False False"


def test_the_model_is_pinned():
    assert re.fullmatch(r"[0-9a-f]{40}", asr.REVISION)
    assert asr.FILES == ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]  # no code, no pickles


def test_lyrics_and_what_was_heard_are_compared_word_by_word():
    assert asr.normalize("In-to the NIGHT, don't _ -") == ["into", "the", "night", "dont"]
    assert asr.words_matched("in-to the night _", "Into the night.") == 1.0
    assert asr.words_matched("street lights fly-ing past", "Streetlights flying past") == 1.0
    assert asr.words_matched("streetlights flying past", "street lights flying past") == 1.0
    # Only the key words count: 'on the' heard right doesn't save 'cold rain' heard wrong.
    assert asr.words_matched("cold rain on the glass", "Coating on the glass.") == pytest.approx(1 / 3, abs=0.01)
    assert asr.words_matched("cold rain on the glass", "Cold pain on the glass") == pytest.approx(2 / 3, abs=0.01)
    assert asr.words_matched("street lights fly-ing past", "Stress flight, flying ass") == 0.25
    assert asr.words_matched("all night long", "long night all") == pytest.approx(1 / 3, abs=0.01)  # in order
    assert asr.words_matched("in the", "in a") == 0.5          # a line of only small words counts them all
    assert asr.words_matched("all night long", "") == 0.0


def test_lines_end_at_rests_of_a_beat():
    spans = [(0, 0.9), (1, 1.9), (2, 3.9), (5, 5.9), (6, 7.9), (9, 9.9)]
    clips = [{"start_qn": a, "end_qn": b} for a, b in spans]
    seconds = [(a * 0.5, b * 0.5) for a, b in spans]
    assert asr.group_lines(clips, seconds) == [[0, 1, 2], [3, 4], [5]]
    assert asr.group_lines(clips, seconds, max_s=1.5) == [[0, 1], [2], [3, 4], [5]]


def _clips(tmp_path, words, spans):
    clips = []
    for i, (w, (a, b)) in enumerate(zip(words, spans)):
        f = tmp_path / f"{i:03d}.wav"
        sf.write(str(f), np.sin(np.arange(int(22050 * (b - a) * 0.5)) * 0.05) * 0.5, 22050)
        clips.append({"path": str(f), "start_qn": a, "end_qn": b, "word": w})
    return clips, [(a * 0.5, b * 0.5) for a, b in spans]


def test_lines_heard_wrong_are_named(monkeypatch, tmp_path):
    hook = ["cold", "rain", "on", "the", "glass"]
    words = hook + ["all", "night", "long"] + hook
    spans = [(i, i + 0.9) for i in range(5)] + [(7, 7.9), (8, 8.9), (9, 10.9)] + [(12 + i, 12.9 + i) for i in range(5)]
    clips, seconds = _clips(tmp_path, words, spans)
    heard_audio = []
    answers = iter([("Coating on the glass.", []), ("All night long.", ["long"]), ("Coating on the glass", [])])
    monkeypatch.setattr(asr, "transcribe", lambda audio: heard_audio.append(audio) or next(answers))
    out = asr.check_lines(clips, seconds)
    # Each line is heard alone, at 16 kHz, the words at their own times with a little air around them.
    assert len(heard_audio) == 3
    assert len(heard_audio[0]) == pytest.approx((2.0 + 0.45 + 2 * asr.PAD_S) * asr.RATE, rel=0.02)
    assert [h["line"] for h in out["heard"]] == ["cold rain on the glass", "all night long"]  # the repeat heard alike
    assert out["heard"][0]["heard_as"] == "Coating on the glass." and out["heard"][1]["words_matched"] == 1.0
    assert out["heard"][1]["unsure_of"] == ["long"] and "unsure_of" not in out["heard"][0] and out["unsure_note"]
    assert out["unclear_lines"] == ["cold rain on the glass"]
    assert "replace=True" in out["unclear_next"]


def test_a_recogniser_stuck_in_a_loop_is_cut_short(monkeypatch, tmp_path):
    clips, seconds = _clips(tmp_path, ["cold", "rain"], [(0, 0.9), (1, 1.9)])
    monkeypatch.setattr(asr, "transcribe", lambda audio: ("Cold " + "ah, " * 200, []))
    heard = asr.check_lines(clips, seconds)["heard"][0]["heard_as"]
    assert heard.endswith("...") and len(heard.split()) == 9


def test_all_heard_means_no_unclear_lines(monkeypatch, tmp_path):
    clips, seconds = _clips(tmp_path, ["all", "night", "long"], [(0, 0.9), (1, 1.9), (2, 3.9)])
    monkeypatch.setattr(asr, "transcribe", lambda audio: ("All night long!", []))
    out = asr.check_lines(clips, seconds)
    assert out["heard"][0]["words_matched"] == 1.0 and "unclear_lines" not in out and "unsure_note" not in out


def _robot_vocal(monkeypatch, tmp_path, **kw):
    import creaper.ear_tools as ear
    from test_singing import FS, vowel

    notes = [{"pitch": p, "start": s, "length": 0.9, "velocity": 90}
             for p, s in ((57, 0.0), (60, 1.0), (62, 2.0), (57, 4.0), (60, 5.0), (62, 6.0))]

    def fake_call(cmd, **k):
        return {"get_midi_notes": {"notes": notes, "start": {"qn": 0.0}, "track": 1},
                "project_paths": {"default_folder": str(tmp_path)},
                "qn_to_times": [q * 0.5 for q in k.get("qns", [])],
                "get_project_overview": {"tracks": [{"name": "Lead"}]},
                "place_audio_clips": {"track": {"name": k.get("track")}, "placed": len(k.get("clips", []))},
                "create_track": {}}[cmd]

    def fake_words(texts, folder, voice=None):
        folder.mkdir(parents=True, exist_ok=True)
        out = []
        for i, _ in enumerate(texts):
            speech._write(folder / f"{i}.wav", vowel(120, 0.3), FS)
            out.append(folder / f"{i}.wav")
        return out

    monkeypatch.setattr(vocal_tools, "call", fake_call)
    monkeypatch.setattr(speech, "speak", fake_words)
    monkeypatch.setattr(speech, "choose_voice", lambda v: "Piper Joe")
    monkeypatch.setattr(ear, "measure_vocal_clarity", lambda *a, **k: {"alone": {"score": 0.8}})
    return vocal_tools.add_robot_vocal(item_id="{M}", lyrics="cold rain glass all night long", **kw)


def test_add_robot_vocal_reports_what_was_heard_only_with_the_extra(monkeypatch, tmp_path):
    monkeypatch.setattr(asr, "available", lambda: False)
    plain = _robot_vocal(monkeypatch, tmp_path)
    assert "heard" not in plain and "unclear_lines" not in plain
    monkeypatch.setattr(asr, "available", lambda: True)
    heard = []
    answers = iter([("Coating glass", []), ("All night long", [])])
    monkeypatch.setattr(asr, "transcribe", lambda audio: heard.append(len(audio)) or next(answers))
    out = _robot_vocal(monkeypatch, tmp_path)
    assert len(heard) == 2                     # two lines: the rest at beat 4 splits them
    assert [h["line"] for h in out["heard"]] == ["cold rain glass", "all night long"]
    assert out["unclear_lines"] == ["cold rain glass"]
    monkeypatch.setattr(asr, "transcribe", lambda audio: (_ for _ in ()).throw(RuntimeError("no model")))
    failed = _robot_vocal(monkeypatch, tmp_path)
    assert "no model" in failed["heard"]["error"] and failed["words_placed"] == 6   # the vocal still stands


def test_the_tool_says_once_how_to_turn_it_on():
    doc = vocal_tools.add_robot_vocal.__doc__ or ""
    assert doc.count("creaper[asr]") == 1


# ---------------------------------------------------------------- the real model


def _piper(name):
    return next((v["name"] for v in speech.voices() if v["name"] == name), None)


@pytest.mark.skipif(not asr.available(), reason="needs the creaper[asr] extra")
@pytest.mark.skipif(_piper("Piper Kristin") is None, reason="needs the Piper Kristin voice")
def test_the_real_recogniser_hears_a_clear_talk_box_line_and_not_a_garbled_one(tmp_path):
    from creaper import talkbox

    words = ["all", "night", "long"]
    files = speech.speak(words, tmp_path, "Piper Kristin")
    clips, seconds = [], []
    for i, (f, w, pitch) in enumerate(zip(files, words, (57, 60, 62))):
        speech.fit_word(f, 0.9 if i < 2 else 1.9)
        x, fs = speech._read(f)
        speech._write(f, talkbox.cross_synthesize(x, fs, [(0.0, pitch)], seed=i), talkbox.RATE)
        clips.append({"path": str(f), "start_qn": float(i), "end_qn": i + (0.9 if i < 2 else 1.9), "word": w})
        seconds.append((i * 0.6, (i + (0.9 if i < 2 else 1.9)) * 0.6))
    out = asr.check_lines(clips, seconds)
    assert out["heard"][0]["words_matched"] == 1.0, out
    # The same words played backwards keep the voice and lose the words.
    for c in clips:
        x, fs = sf.read(c["path"])
        sf.write(c["path"], x[::-1], fs)
    assert asr.check_lines(clips, seconds)["unclear_lines"] == ["all night long"]
