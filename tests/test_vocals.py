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


def test_harmony_follows_chords_from_outside_the_key():
    from creaper import composer, harmony
    key = harmony.parse_key("F# minor")
    melody = [{"pitch": 73, "start": 0, "length": 2, "velocity": 100},   # C#5 over F#7 (F# A# C# E)
              {"pitch": 71, "start": 4, "length": 2, "velocity": 100}]   # B4 over Bm (B D F#)
    chords = [{"pitch": p, "start": 0, "length": 4} for p in (54, 58, 61, 64)] + \
             [{"pitch": p, "start": 4, "length": 4} for p in (59, 62, 66)]
    plain = composer.add_harmony(melody, key, 2, below=True)
    assert plain[2]["pitch"] == 69  # A: in the key, but rubs against the chord's A#
    fitted = composer.add_harmony(melody, key, 2, below=True, chord_at=composer.chord_lookup(chords))
    assert fitted[2]["pitch"] == 70  # A#4, the chord's 3rd
    assert fitted[3]["pitch"] == 66  # F#4 (the diatonic G#4 isn't in Bm), still below the melody


def test_chord_lookup_holds_stabs_and_pushed_chords():
    from creaper import composer
    stabs = [{"pitch": p, "start": 3.5, "length": 0.25} for p in (62, 66, 69)]  # D major pushed before bar 2
    at = composer.chord_lookup(stabs)
    assert at(4.0) == {2, 6, 9}       # the pushed chord is in force on the downbeat
    assert at(3.0) is None            # nothing struck yet
    assert at(9.0) is None            # held no longer than a bar


def test_plan_chops_follows_the_pattern_holds_and_chords():
    from creaper.vocal_tools import plan_chops
    slices = [{"start": 0.0, "end": 0.4, "pitch": 69.3},   # A, a little sharp
              {"start": 0.5, "end": 0.6, "pitch": 64.0},
              {"start": 0.7, "end": 0.75}]                 # too short to use
    c_major = {0, 4, 7}
    chops = plan_chops(slices, "x-..x...", bars=1, chord_at=lambda qn: c_major, seconds_per_qn=0.5, seed=3)
    assert [c["start"] for c in chops] == [0, 1.0, 2.0, 3.0]          # every 'x' in the repeating pattern
    first = slices[chops[0]["slice"]]
    assert chops[0]["length"] == min(0.5, round((first["end"] - first["start"]) / 0.5, 4))  # held 2 16ths, if it lasts
    for c in chops:
        p = slices[c["slice"]]["pitch"] + c["semitones"]
        assert round(p) % 12 in c_major and abs(p - round(p)) < 0.01  # on a chord tone, in tune
        assert abs(c["semitones"]) <= 6
    assert all(c["slice"] != 2 for c in chops)


def test_plan_chops_caps_length_at_the_slice():
    from creaper.vocal_tools import plan_chops
    chops = plan_chops([{"start": 0.0, "end": 0.1, "pitch": 60}], "x---------------", bars=1, chord_at=None,
                       seconds_per_qn=0.5)
    assert chops == [{"slice": 0, "start": 0, "length": 0.2, "semitones": 0.0}]


def test_pattern_needs_a_chop():
    from creaper.vocal_tools import parse_pattern
    with pytest.raises(ValueError, match="x starts a chop"):
        parse_pattern("....")


def test_slice_vocal_finds_syllables_and_their_pitch(tmp_path):
    fs = 44100
    def syllable(hz, seconds):
        t = np.arange(int(seconds * fs)) / fs
        tone = sum(a * np.sin(2 * np.pi * hz * k * t) for k, a in ((1, 0.4), (2, 0.8), (3, 0.5)))
        return tone * np.hanning(len(t)) ** 0.3 * 0.3
    gap = np.zeros(int(0.15 * fs))
    audio = np.concatenate([gap, syllable(220, 0.3), gap, syllable(330, 0.25), gap])
    path = tmp_path / "vox.wav"
    speech._write(path, audio, fs)
    from creaper import samplelib
    slices = samplelib.slice_vocal(str(path))
    assert len(slices) == 2
    assert abs(slices[0]["pitch"] - 57) < 0.3 and abs(slices[1]["pitch"] - 64.02) < 0.3   # A3, E4
    assert 0.1 < slices[0]["start"] < 0.2
