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


def _read_midi(data):
    """Minimal reader for the files midi_with_lyrics writes: [(track, tick, kind, value)]."""
    assert data[:4] == b"MThd"
    ntracks, ppq = int.from_bytes(data[10:12], "big"), int.from_bytes(data[12:14], "big")
    pos, events = 14, []
    for t in range(ntracks):
        assert data[pos:pos + 4] == b"MTrk"
        end = pos + 8 + int.from_bytes(data[pos + 4:pos + 8], "big")
        pos += 8
        tick = 0
        while pos < end:
            delta = 0
            while True:
                b = data[pos]; pos += 1
                delta = (delta << 7) | (b & 0x7F)
                if b < 0x80:
                    break
            tick += delta
            status = data[pos]
            if status == 0xFF:
                kind, length = data[pos + 1], data[pos + 2]
                value = data[pos + 3:pos + 3 + length]
                pos += 3 + length
                events.append((t, tick, f"meta{kind:02x}", value))
            else:
                events.append((t, tick, "on" if status & 0xF0 == 0x90 else "off", data[pos + 1]))
                pos += 3
    return ppq, events


def test_midi_with_lyrics_puts_each_syllable_on_its_note():
    from creaper.vocal_tools import midi_with_lyrics, singer_syllables
    line = [n(0, 1, 64), n(1, 0.5, 67), n(1.5, 1.5, 69), n(3, 1, 67)]
    words = singer_syllables("dan-cing in _", line)
    assert words == ["dan", "cing", "in", "-"]
    notes = [dict(x, start=x["start"] + 4, velocity=90, lyric=w) for x, w in zip(line, words)]
    ppq, events = _read_midi(midi_with_lyrics(notes, [(0, 120.0), (8, 100.0)], (4, 4)))
    tempos = [(tick, int.from_bytes(v, "big")) for t, tick, k, v in events if k == "meta51"]
    assert tempos == [(0, 500000), (8 * ppq, 600000)]
    lyrics = [(tick, v.decode()) for t, tick, k, v in events if k == "meta05"]
    ons = [(tick, p) for t, tick, k, p in events if k == "on"]
    assert lyrics == [(4 * ppq, "dan"), (5 * ppq, "cing"), (int(5.5 * ppq), "in"), (7 * ppq, "-")]
    assert ons == [(4 * ppq, 64), (5 * ppq, 67), (int(5.5 * ppq), 69), (7 * ppq, 67)]
    assert sum(1 for e in events if e[2] == "off") == 4


def test_singer_syllables_count_must_match():
    from creaper.vocal_tools import singer_syllables
    with pytest.raises(ValueError, match="3 syllables and holds but the melody has 2 notes"):
        singer_syllables("to-night _", [n(0), n(1)])


def test_talkbox_saw_follows_the_notes():
    from creaper import talkbox, samplelib
    y = talkbox.saw([(0.0, 57), (0.5, 64)], 1.0)
    assert len(y) == talkbox.RATE
    for a, b, hz in ((0.1, 0.4, 220.0), (0.6, 0.9, 329.6)):
        got, _ = samplelib.vocal_pitch(y[int(a * talkbox.RATE): int(b * talkbox.RATE)], talkbox.RATE)
        assert abs(got - hz) / hz < 0.01


def test_talkbox_sings_the_melody_and_keeps_consonants_noisy():
    from creaper import talkbox, samplelib
    fs = 16000
    rng = np.random.default_rng(0)
    t = np.arange(int(0.3 * fs)) / fs
    vowel = sum(np.sin(2 * np.pi * 150 * k * t) / k for k in range(1, 30)) * 0.3   # a buzzy "voice" at 150 Hz
    hiss = rng.standard_normal(int(0.15 * fs)) * 0.2                              # an "s"
    y = talkbox.cross_synthesize(np.concatenate([vowel, hiss]), fs, [(0.0, 69)])  # sung on A4
    assert abs(len(y) - int(0.45 * talkbox.RATE)) < 64
    hz, _ = samplelib.vocal_pitch(y[int(0.05 * talkbox.RATE): int(0.25 * talkbox.RATE)], talkbox.RATE)
    assert abs(hz - 440) < 5                                                       # the melody's pitch, not the voice's

    def flatness(seg):
        p = np.abs(np.fft.rfft(seg)) ** 2 + 1e-12
        return np.exp(np.mean(np.log(p))) / np.mean(p)
    voiced = flatness(y[int(0.05 * talkbox.RATE): int(0.25 * talkbox.RATE)])
    hissed = flatness(y[int(0.33 * talkbox.RATE): int(0.43 * talkbox.RATE)])
    assert hissed > 10 * voiced                                                    # the "s" stays noise


def test_piper_voices_list_licenses_and_prefer_ones_safe_to_release(tmp_path, monkeypatch):
    for stem in ("en_US-lessac-medium", "en_GB-cori-medium", "en_US-norman-medium", "xx_YY-mystery-low"):
        (tmp_path / f"{stem}.onnx").write_bytes(b"")
        (tmp_path / f"{stem}.onnx.json").write_text("{}")
    monkeypatch.setattr(speech, "piper_dir", lambda: tmp_path)
    monkeypatch.setattr(speech.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(speech, "_system_voices", lambda: [{"name": "System Voice", "gender": "female", "engine": "sapi"}])
    found = speech.voices()
    assert [v["name"] for v in found] == ["Piper Norman", "Piper Cori (UK)", "Piper Lessac", "Piper xx_YY-mystery-low",
                                          "System Voice"]
    assert found[0]["license"] == "public domain" and found[2]["license"].startswith("non-commercial")
    assert found[3]["license"].startswith("unknown")
    assert speech.choose_voice(None) == "Piper Norman"          # best voice safe for released music
    assert speech.choose_voice("female") == "Piper Cori (UK)"
    assert speech.voice_license("Piper Lessac").startswith("non-commercial")


def test_no_piper_means_system_voices_only(monkeypatch):
    monkeypatch.setattr(speech.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(speech, "_system_voices", lambda: [{"name": "System Voice", "engine": "sapi"}])
    assert [v["name"] for v in speech.voices()] == ["System Voice"]
    assert speech.choose_voice(None) is None
