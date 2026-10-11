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


RATE = 44100


def _zero_crossing_hz(x):
    crossings = np.nonzero(np.diff(np.signbit(x)))[0]
    return (len(crossings) / 2) / (len(x) / RATE)


def test_time_stretch_keeps_pitch_and_hits_the_length():
    tone = 0.5 * np.sin(2 * np.pi * 220 * np.arange(int(0.2 * RATE)) / RATE)
    for factor in (0.6, 2.0, 4.0):
        out = speech.time_stretch(tone, int(len(tone) * factor), RATE)
        assert len(out) == int(len(tone) * factor)
        middle = out[len(out) // 4: -len(out) // 4]
        assert abs(_zero_crossing_hz(middle) - 220) < 6


def _word():
    """A made-up word: a 40 ms noise consonant, a 200 ms vowel, a 30 ms noise ending."""
    rng = np.random.default_rng(1)
    head = 0.05 * rng.standard_normal(int(0.04 * RATE))
    vowel = 0.6 * np.sin(2 * np.pi * 180 * np.arange(int(0.2 * RATE)) / RATE)
    tail = 0.05 * rng.standard_normal(int(0.03 * RATE))
    return head, vowel, tail


def test_vowel_span_finds_the_sustained_part():
    head, vowel, tail = _word()
    start, end = speech.vowel_span(np.concatenate([head, vowel, tail]), RATE)
    assert abs(start - len(head)) <= 0.011 * RATE
    assert abs(end - (len(head) + len(vowel))) <= 0.011 * RATE


def test_fit_word_holds_the_vowel_and_keeps_the_consonants(tmp_path):
    head, vowel, tail = _word()
    path = tmp_path / "word.wav"
    speech._write(path, np.concatenate([head, vowel, tail]), RATE)
    speed = speech.fit_word(path, 1.0)
    out, rate = speech._read(path)
    assert rate == RATE and abs(len(out) - RATE) <= 1
    assert speed < 0.3  # slowed down overall...
    # ...but the consonant at the start is untouched noise at its natural length, not smeared.
    first = out[int(0.006 * RATE): int(0.035 * RATE)]
    assert np.sqrt(np.mean(first ** 2)) < 0.1 and _zero_crossing_hz(first) > 2000


def test_fit_word_speeds_up_a_word_that_is_too_long(tmp_path):
    head, vowel, tail = _word()
    path = tmp_path / "word.wav"
    speech._write(path, np.concatenate([head, vowel, tail]), RATE)
    speed = speech.fit_word(path, 0.15)
    out, _ = speech._read(path)
    assert abs(len(out) - int(0.15 * RATE)) <= 1 and speed > 1.7
