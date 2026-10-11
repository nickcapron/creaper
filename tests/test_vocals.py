"""Robot vocals: matching lyrics to a melody, and preparing the spoken words."""
import wave

import numpy as np
import pytest

from creaper import speech
from creaper.vocal_tools import assign_lyrics, melody_line


def n(start, length=1.0, pitch=60, **kw):
    return {"start": start, "length": length, "pitch": pitch, **kw}


def test_melody_line_sings_the_top_note_of_each_chord():
    notes = [n(0, pitch=60), n(0, pitch=67), n(0, pitch=64), n(1, pitch=62), n(2, pitch=70, muted=True), n(2, pitch=65)]
    assert [x["pitch"] for x in melody_line(notes)] == [67, 62, 65]


def test_one_word_per_note_with_hyphens_and_holds():
    line = [n(0), n(1), n(2), n(3, length=2), n(4.5)]
    words = assign_lyrics("All to-night _ long!", line)
    assert [w["text"] for w in words] == ["All", "tonight", "long"]
    assert (words[0]["start"], words[0]["end"]) == (0, 1)
    assert (words[1]["start"], words[1]["end"]) == (1, 4.5)  # two notes, held over a third, up to "long"
    assert (words[2]["start"], words[2]["end"]) == (4.5, 5.5)


def test_word_never_overlaps_the_next():
    words = assign_lyrics("la la", [n(0, length=3), n(2)])
    assert words[0]["end"] == 2


@pytest.mark.parametrize("lyrics, match", [
    ("one two three", "cover 3 notes but the melody has 2"),
    ("_ two", "can't start with a hold"),
    ("", "give the lyrics"),
    ("!! two", "nothing to sing"),
])
def test_lyrics_errors(lyrics, match):
    with pytest.raises(ValueError, match=match):
        assign_lyrics(lyrics, [n(0), n(1)])


def test_trim_silence_cuts_the_gaps_and_evens_the_level(tmp_path):
    rate = 44100
    tone = 0.1 * np.sin(2 * np.pi * 220 * np.arange(rate // 2) / rate)
    audio = np.concatenate([np.zeros(rate // 2), tone, np.zeros(rate)])
    path = tmp_path / "word.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((audio * 32767).astype("<i2").tobytes())
    length = speech.trim_silence(path)
    assert 0.5 <= length <= 0.53
    with wave.open(str(path), "rb") as w:
        out = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2") / 32768
    assert abs(np.abs(out).max() - 10 ** (-3 / 20)) < 0.01
