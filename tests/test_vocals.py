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
    assert min(abs(hz - 440), abs(hz - 220)) < 5        # the melody's note (A4, doubled an octave down), not the voice's
    low = talkbox.cross_synthesize(np.concatenate([vowel, hiss]), fs, [(0.0, 57)])   # A3: no doubling
    hz_low, _ = samplelib.vocal_pitch(low[int(0.05 * talkbox.RATE): int(0.25 * talkbox.RATE)], talkbox.RATE)
    assert abs(hz_low - 220) < 3
    assert talkbox.sub_octave_level(60) == 0 and talkbox.sub_octave_level(72) == talkbox.SUB_OCTAVE

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


def test_default_voice_is_remembered_and_used(tmp_path, monkeypatch):
    monkeypatch.setattr(speech, "default_voice_file", lambda: tmp_path / "default.json")
    installed = [{"name": "Piper Joe", "gender": "male", "engine": "piper", "license": "CC0"},
                 {"name": "Piper Kristin", "gender": "female", "engine": "piper", "license": "public domain"}]
    monkeypatch.setattr(speech, "voices", lambda: installed)
    assert speech.choose_voice(None) == "Piper Joe"          # nothing chosen yet: the best installed
    assert speech.set_default_voice("kristin") == "Piper Kristin"
    assert speech.choose_voice(None) == "Piper Kristin"
    assert speech.choose_voice("male") == "Piper Joe"        # asking for a voice still wins
    installed.pop()                                          # uninstalled: back to the best one
    assert speech.choose_voice(None) == "Piper Joe"


def test_syllable_counts():
    from creaper.vocal_tools import syllables
    assert [syllables(w) for w in ("one", "more", "time", "tonight", "little", "around", "world", "free")] == \
        [1, 1, 1, 2, 2, 2, 1, 1]


def test_dense_lyrics_are_refused():
    eighths = [n(i * 0.5, length=0.5) for i in range(16)]
    with pytest.raises(ValueError, match=r"8 syllables in the 4 beats from beat 1 .*one per beat"):
        assign_lyrics(" ".join(["la"] * 16), eighths)
    # The same notes with words held over them are fine: one syllable per beat.
    held = " ".join(["la _"] * 8)
    assert len(assign_lyrics(held, eighths)) == 8
    # Long words crammed on single notes count every syllable.
    quarters = [n(i) for i in range(4)]
    with pytest.raises(ValueError, match="too many words"):
        assign_lyrics("tonight forever tonight forever", quarters)
    assert len(assign_lyrics("one more time now", quarters)) == 4
    assert len(assign_lyrics(" ".join(["la"] * 16), eighths, max_per_beat=None)) == 16


def test_one_sung_slice_doesnt_become_every_chop():
    """Only one of ten slices had a pitch, and all 72 chops played it: one syllable over and over."""
    from creaper.vocal_tools import plan_chops
    slices = [{"start": 0.0, "end": 0.4, "pitch": 68.5}] + [{"start": 0.5 + i * 0.2, "end": 0.65 + i * 0.2}
                                                             for i in range(5)]
    chops = plan_chops(slices, "x.x.x.x.", bars=2, chord_at=lambda qn: {5, 8, 0}, seconds_per_qn=0.5)
    assert len({c["slice"] for c in chops}) == 6
    assert all(c["semitones"] == 0 for c in chops if "pitch" not in slices[c["slice"]])   # nothing to tune them by


def _chop_fakes(monkeypatch, tracks):
    from creaper import sample_tools, vocal_tools
    calls = []

    def fake(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_project_overview":
            return {"tempo_bpm": 125, "time_signature": "4/4", "tracks": tracks}
        if cmd == "bar_to_qn":
            return {"qn": (kw["bar"] - 1) * 4}
        if cmd == "add_fx":
            return {"index": 1 + sum(c == "add_fx" for c, _ in calls[:-1]), "name": kw["name"]}
        if cmd == "place_audio_clips":
            return {"placed": len(kw["clips"])}
        return {}
    monkeypatch.setattr(vocal_tools, "call", fake)
    monkeypatch.setattr(sample_tools, "_check_audio", lambda p: p)
    return calls


def _dark_phrase(tmp_path):
    fs = 44100
    def syllable(hz, seconds):
        t = np.arange(int(seconds * fs)) / fs
        return np.sin(2 * np.pi * hz * t) * np.hanning(len(t)) ** 0.3 * 0.3
    gap = np.zeros(int(0.1 * fs))
    audio = np.concatenate([gap] + [x for hz in (110, 123, 131, 147) for x in (syllable(hz, 0.25), gap)])
    path = tmp_path / "low vox.wav"
    speech._write(path, audio, fs)
    return str(path)


def test_dark_chops_go_up_an_octave_through_a_chop_chain(monkeypatch, tmp_path):
    """Chops of a dark sample, left dry, sounded like burping to the user."""
    from creaper import vocal_tools
    calls = _chop_fakes(monkeypatch, [])
    out = vocal_tools.chop_vocal(path=_dark_phrase(tmp_path), track="Scat Chops", bars=1, key="F minor", glitch=True)
    added = [kw["name"] for c, kw in calls if c == "add_fx"]
    assert added == ["ReaPitch", "ReaEQ", "JS: Bit Reduction/Dither"]
    pitch = next(kw["changes"] for c, kw in calls if c == "set_fx_parameters" and kw["fx"] == 1)
    assert {"parameter": "1: Shift (oct)", "display_value": 1} in pitch
    assert out["why_octave"].startswith("the sample is dark") and len(out["chain"]) == 3


def test_more_chops_on_the_track_keep_its_chain(monkeypatch, tmp_path):
    from creaper import vocal_tools
    calls = _chop_fakes(monkeypatch, [{"name": "Scat Chops", "fx": ["VST: ReaPitch (Cockos)"]}])
    out = vocal_tools.chop_vocal(path=_dark_phrase(tmp_path), track="Scat Chops", bars=1)
    assert not any(c in ("add_fx", "create_track") for c, _ in calls)
    assert out["chain"] == "kept the track's own effects"


def test_chops_can_stay_as_sung(monkeypatch, tmp_path):
    from creaper import vocal_tools
    calls = _chop_fakes(monkeypatch, [])
    vocal_tools.chop_vocal(path=_dark_phrase(tmp_path), track="Chops", bars=1, octave=0)
    assert [kw["name"] for c, kw in calls if c == "add_fx"] == ["ReaEQ"]



# ------------------------------------------------------------------ VocalVST

# A VocalVST instance's state as REAPER reports it (vst_chunk), after a pass that
# captured six notes, with lyrics "hel lo world this is me" and no voicebank.
VOCALVST_CHUNK = (
    "XgIAAAEAAABWQzIhGQIAADw/eG1sIHZlcnNpb249IjEuMCIgZW5jb2Rpbmc9IlVURi04Ij8+IDxWb2NhbFZTVCBseXJpY3M9ImhlbCBsbyB3b3Js"
    "ZCB0aGlzIGlzIG1lIiBiYW5rPSIiPjxzdGF0ZT48UEFSQU0gaWQ9ImdhaW4iIHZhbHVlPSIwLjAiLz48UEFSQU0gaWQ9Im1vZGUiIHZhbHVlPSIw"
    "LjAiLz48UEFSQU0gaWQ9InJlbmRlciIgdmFsdWU9IjAuMCIvPjwvc3RhdGU+PG5vdGVzPjxuIHM9IjAuMCIgZT0iMC40NSIgbT0iNjAiIHY9IjAu"
    "Nzg3NDAxNTU2OTY4Njg5Ii8+PG4gcz0iMC41IiBlPSIwLjk1MDAwMDAwMDAwMDAwMDEiIG09IjYyIiB2PSIwLjc4NzQwMTU1Njk2ODY4OSIvPjxu"
    "IHM9IjEuMCIgZT0iMS40NSIgbT0iNjQiIHY9IjAuNzg3NDAxNTU2OTY4Njg5Ii8+PG4gcz0iMS41IiBlPSIxLjk1IiBtPSI2NCIgdj0iMC43ODc0"
    "MDE1NTY5Njg2ODkiLz48biBzPSIyLjAiIGU9IjIuNDUiIG09IjYyIiB2PSIwLjc4NzQwMTU1Njk2ODY4OSIvPjxuIHM9IjIuNSIgZT0iMi45NSIg"
    "bT0iNjAiIHY9IjAuNzg3NDAxNTU2OTY4Njg5Ii8+PC9ub3Rlcz48L1ZvY2FsVlNUPgAAAAAAAAAAAEpVQ0VQcml2YXRlRGF0YQABAUJ5cGFzcwAB"
    "AQMAHQAAAAAAAABKVUNFUHJpdmF0ZURhdGEAAAAAAAAAAA=="
)


def test_vocalvst_state_is_read_and_rewritten_in_place():
    import base64
    import struct

    from creaper.vocal_tools import vocalvst_captured, vocalvst_lyrics, vocalvst_state, vocalvst_state_with_lyrics

    assert vocalvst_lyrics(VOCALVST_CHUNK) == "hel lo world this is me"
    assert vocalvst_captured(VOCALVST_CHUNK) == {"notes": 6, "from_seconds": 0.0, "to_seconds": 2.95}
    new = vocalvst_state_with_lyrics(VOCALVST_CHUNK, 'we "ride" & <fall> to night')
    assert vocalvst_lyrics(new) == 'we "ride" & <fall> to night'
    assert vocalvst_captured(new) == vocalvst_captured(VOCALVST_CHUNK)   # the notes survive
    old_raw, at, old_n, _ = vocalvst_state(VOCALVST_CHUNK)
    new_raw, at2, new_n, xml = vocalvst_state(new)
    assert at2 == at and new_n == len(xml.encode()) + 1
    assert struct.unpack_from("<I", new_raw, 0)[0] - struct.unpack_from("<I", old_raw, 0)[0] == new_n - old_n
    assert new_raw[at + 8 + new_n:] == old_raw[at + 8 + old_n:]        # REAPER's controller state is untouched
    assert vocalvst_lyrics(vocalvst_state_with_lyrics(new, "")) == ""
    with pytest.raises(ValueError, match="JUCE"):
        vocalvst_state(base64.b64encode(b"something else").decode())


def _vocalvst_bridge(tmp_path, monkeypatch, log_on_render=True, sounds_after=None, takes_switch=True,
                     sees_bank=lambda path: True, notes=None, master_muted=False, pass_fails=False,
                     keeps_speaker=True):
    """A fake bridge with VocalVST on track 1 and a six-note item (3 s from 2.0 s, at
    120 BPM, so a quarter note is 0.5 s); returns the call log. `notes` replaces the
    item's notes (start and length in quarter notes from the item's start)."""
    from creaper import vocal_tools

    state = {"chunk": VOCALVST_CHUNK, "renders": 0, "item_end": 5.0, "created": []}
    calls = []
    log = tmp_path / "host.log"
    log.write_text("2026-10-20T17:09:05.251-07:00 loaded in Reaper (plugin)\n")
    renders = tmp_path / "renders"
    renders.mkdir()
    if notes is None:
        notes = [{"pitch": p, "start": i * 1.0, "length": 0.9, "velocity": 100} for i, p in enumerate((60, 62, 64, 64, 62, 60))]

    def item():
        return {"id": "{I}", "type": "midi", "muted": False, "start": {"seconds": 2.0, "qn": 4.0, "bar": 2},
                "end": {"seconds": state["item_end"]}, "length_qn": (state["item_end"] - 2.0) * 2,
                "length_seconds": state["item_end"] - 2.0}

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_track_details":
            return {"number": 1, "name": "Vocal", "fx": [{"index": 1, "name": "VST3i: VocalVST (vocalvst)"}],
                    "items": [item()]}
        if cmd == "get_midi_notes":
            return {"notes": notes, **item()}
        if cmd == "edit_item":
            assert kw["item_id"] == "{I}" and kw["length_qn"] > 0
            state["item_end"] = 2.0 + kw["length_qn"] * 0.5
            return item()
        if cmd == "capture_fx_state":
            return {"plugin": "VST3i: VocalVST (vocalvst)", "file": "vocalvst.vst3", "chunk": state["chunk"]}
        if cmd == "apply_fx_state":
            chunk = kw["state"]["chunk"]
            bank = vocal_tools.vocalvst_bank(chunk)
            if bank and not sees_bank(bank):       # the plugin keeps only a folder it can see
                chunk = vocal_tools.vocalvst_state_with(chunk, bank="")
            if not keeps_speaker:                   # an older build: no voices
                chunk = vocal_tools.vocalvst_state_with(chunk, speaker="")
            state["chunk"] = chunk
            return {}
        if cmd == "get_fx_parameters":
            return {"parameters": [{"name": "Render", "display": "On" if not takes_switch else "Off",
                                    "value": 0 if takes_switch else 1}]}
        if cmd == "set_fx_parameter":
            if kw["parameter"] == "Render" and log_on_render:
                with log.open("a") as f:
                    f.write("2026-10-20T19:00:00.000-07:00 Rendered: 1 phrase, 6 notes, 3.7 s\n")
            return {}
        if cmd == "transport":
            if kw.get("action") == "play":           # the plugin logs its capture after the pass
                with log.open("a") as f:
                    f.write("2026-10-20T18:59:00.000-07:00#ab12/Vocal run 2.00 s to 5.00 s captured; notes 6 -> 6\n")
            return {}
        if cmd == "recording_status":
            if pass_fails:
                raise RuntimeError("REAPER went away")
            return {"playing": False}
        if cmd == "get_project_overview":
            return {"master": {"mute": master_muted}, "tracks": [{"number": 1, "name": "Vocal"}]}
        if cmd == "set_track_properties":
            return {}
        if cmd == "render_audio":
            import numpy as np
            import soundfile as sf

            state["renders"] += 1
            f = renders / f"r{state['renders']}.wav"
            loud = sounds_after is not None and state["renders"] > sounds_after
            sf.write(str(f), (0.3 if loud else 0.0) * np.ones((4800, 2), dtype="float32"), 48000)
            return {"files": [str(f)]}
        if cmd == "create_track":                       # add_vocal_harmony's second singer
            state["created"].append(kw["name"])
            return {"name": kw["name"], "number": 2, "instrument": {"name": "VST3i: VocalVST (vocalvst)"}}
        if cmd == "create_midi_item":
            return {"id": "{H}", **item()}
        if cmd == "add_midi_notes":
            return {"notes": len(kw["notes"])}
        raise AssertionError(cmd)

    monkeypatch.setattr(vocal_tools, "call", fake_call)
    monkeypatch.setattr(vocal_tools, "VOCALVST_LOG", log)
    monkeypatch.setattr(vocal_tools, "_sleep", lambda s: None)
    banks = tmp_path / "voicebanks"
    (banks / "Canary_DS").mkdir(parents=True)
    (banks / "Canary_DS" / "dsconfig.yaml").write_text("acoustic: dsacoustic/acoustic.onnx\n")
    monkeypatch.setattr(vocal_tools, "VOICEBANK_ROOT", banks)
    monkeypatch.setattr(vocal_tools, "bridge", type("B", (), {
        "directory": tmp_path,
        "call": lambda self, cmd, params=None, timeout=30.0: fake_call(cmd, **(params or {}))})())
    return calls, state


def test_render_vocalvst_sets_lyrics_plays_the_pass_then_renders(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, state = _vocalvst_bridge(tmp_path, monkeypatch)
    out = vocal_tools.render_vocalvst(track="Vocal", lyrics="we ride at dawn to-night", mode="rap")
    cmds = [c for c, _ in calls]
    assert cmds.index("apply_fx_state") < cmds.index("transport") < cmds.index("recording_status")
    assert vocal_tools.vocalvst_lyrics(state["chunk"]) == "we ride at dawn to night"
    assert vocal_tools.vocalvst_bank(state["chunk"]).endswith("Canary_DS") and out["voicebank"] == "Canary_DS"
    params = [(kw["parameter"], kw["display_text"]) for c, kw in calls if c == "set_fx_parameter"]
    assert params == [("Mode", "Rap"), ("Render", "On")]
    play = next(kw for c, kw in calls if c == "transport")
    assert play["action"] == "play" and play["start_seconds"] == 1.7 and play["end_seconds"] == 5.5
    assert cmds.index("render_audio") < cmds.index("set_fx_parameter", cmds.index("set_fx_parameter") + 1)
    assert out["result"].startswith("Rendered: 1 phrase") and out["captured"]["notes"] == 6
    assert out["lyrics"] == "we ride at dawn to night" and "warning" not in out


TIGER_CONFIG = """# v106
acoustic: dsacoustic/acoustic.onnx
speakers:
  - dsacoustic/tiger_fresh
  - dsacoustic/tiger_electric   # power
  - "dsacoustic/tiger_royal"

augmentation_args:
  random_pitch_shifting:
    enabled: true
"""


def _tiger(tmp_path):
    bank = tmp_path / "voicebanks" / "TIGER_DS_v106"
    bank.mkdir(parents=True)
    (bank / "dsconfig.yaml").write_text(TIGER_CONFIG)
    return bank


def test_bank_speakers_reads_the_dsconfig_list():
    from creaper.vocal_tools import bank_speakers

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        bank = _tiger(Path(d))
        assert bank_speakers(bank) == ["tiger_fresh", "tiger_electric", "tiger_royal"]
        assert bank_speakers(Path(d)) == []


def test_render_vocalvst_sings_with_the_voice_asked_for(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _, state = _vocalvst_bridge(tmp_path, monkeypatch)
    tiger = _tiger(tmp_path)
    out = vocal_tools.render_vocalvst(track=1, lyrics="one two three four five six", voice="tiger_electric")
    assert vocal_tools.vocalvst_bank(state["chunk"]) == str(tiger)
    assert vocal_tools.vocalvst_attr(state["chunk"], "speaker") == "tiger_electric"
    assert out["voicebank"] == "TIGER_DS_v106" and out["voice"] == "tiger_electric" and "voices" not in out
    out = vocal_tools.render_vocalvst(track=1, voice="TIGER")          # the bank's default voice
    assert vocal_tools.vocalvst_attr(state["chunk"], "speaker") == "" and out["voice"] == "the bank's default"
    with pytest.raises(ValueError, match="no VocalVST voice 'tiger_growl'.*tiger_electric"):
        vocal_tools.render_vocalvst(track=1, voice="tiger_growl")


def test_render_vocalvst_offers_the_other_voices_when_none_is_asked_for(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch)
    _tiger(tmp_path)
    out = vocal_tools.render_vocalvst(track=1)
    assert out["voicebank"] == "Canary_DS" and "tiger_electric" in out["voices"]


def test_render_vocalvst_says_when_the_plugin_drops_the_voice(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch, keeps_speaker=False)
    _tiger(tmp_path)
    with pytest.raises(ValueError, match="didn't take the voice 'tiger_royal'"):
        vocal_tools.render_vocalvst(track=1, voice="tiger_royal")


def test_render_vocalvst_says_where_the_line_sits_for_the_voice(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch)
    out = vocal_tools.render_vocalvst(track=1)               # D4 in the middle: fine for Canary
    assert out["range"]["middle"] == "D4" and "advice" not in out["range"]
    high = [{"pitch": p, "start": i * 1.0, "length": 0.9, "velocity": 100} for i, p in enumerate((72, 74, 76, 72, 71, 72))]
    (tmp_path / "high").mkdir()
    _vocalvst_bridge(tmp_path / "high", monkeypatch, notes=high)
    out = vocal_tools.render_vocalvst(track=1)
    assert "sits high" in out["range"]["advice"] and "down 12" in out["range"]["advice"]


def test_range_advice_knows_each_voice():
    from creaper.vocal_tools import range_advice

    low_male = [50, 52, 55, 57, 55, 52]                       # D3-A3: TIGER's middle
    assert "advice" not in range_advice(low_male, "TIGER_DS_v106")
    assert "sits low" in range_advice(low_male, "Canary_DS_v106")["advice"]
    assert "sits low" in range_advice(low_male, "TIGER_DS_v106", "tiger_royal")["advice"]   # falsetto sits higher
    assert "advice" not in range_advice([90, 91], "SomeOtherBank") and "sweet_spot" not in range_advice([90], "X")


def test_render_vocalvst_warns_when_syllables_come_too_fast(tmp_path, monkeypatch):
    from creaper import vocal_tools

    fast = [{"pitch": 62, "start": i * 0.25, "length": 0.2, "velocity": 100} for i in range(6)]   # 125 ms apart
    _vocalvst_bridge(tmp_path, monkeypatch, notes=fast)
    out = vocal_tools.render_vocalvst(track=1, lyrics=" ".join(["la"] * 6))
    assert "125 ms" in out["words"]
    (tmp_path / "slow").mkdir()
    _vocalvst_bridge(tmp_path / "slow", monkeypatch)
    assert "words" not in vocal_tools.render_vocalvst(track=1, lyrics="one two three four five six")


def test_vocalvst_state_gains_a_field_it_lacked():
    from creaper.vocal_tools import vocalvst_attr, vocalvst_captured, vocalvst_lyrics, vocalvst_state_with

    new = vocalvst_state_with(VOCALVST_CHUNK, speaker="tiger_glam")
    assert vocalvst_attr(new, "speaker") == "tiger_glam" and vocalvst_lyrics(new) == "hel lo world this is me"
    assert vocalvst_captured(new) == vocalvst_captured(VOCALVST_CHUNK)


def test_vocalvst_pass_span_reaches_the_last_note():
    from creaper.vocal_tools import vocalvst_pass_span

    items = [{"start": {"seconds": 2.0}, "end": {"seconds": 5.0}}]        # 6 quarter notes at 120 BPM
    inside = {"notes": [{"start": 0.0, "length": 1.0}, {"start": 4.0, "length": 1.5}],
              "length_qn": 6.0, "length_seconds": 3.0}
    assert vocalvst_pass_span(items, [inside]) == (1.7, 5.5)             # the item bounds, with lead and tail
    beyond = {"notes": [{"start": 0.0, "length": 1.0}, {"start": 10.0, "length": 1.9},
                        {"start": 20.0, "length": 1.0, "muted": True}],  # a muted note doesn't count
              "length_qn": 6.0, "length_seconds": 3.0}
    start, end = vocalvst_pass_span(items, [beyond])
    assert (start, end) == (1.7, 2.0 + 11.9 * 0.5 + 0.5)                  # past the item end, to the last note
    assert vocalvst_pass_span([{"start": {"seconds": 0.1}, "end": {"seconds": 1.0}}], [{"notes": []}]) == (0.0, 1.5)


def test_render_vocalvst_lengthens_the_item_and_plays_past_its_old_end(tmp_path, monkeypatch):
    from creaper import vocal_tools

    # Six notes two beats apart: the last ends at 11.9 quarter notes, in a six-quarter-note item.
    notes = [{"pitch": 60 + i, "start": i * 2.0, "length": 1.9, "velocity": 100} for i in range(6)]
    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch, notes=notes)
    out = vocal_tools.render_vocalvst(track=1, lyrics="one two three four five six")
    edit = next(kw for c, kw in calls if c == "edit_item")
    assert edit == {"item_id": "{I}", "length_qn": 12}                   # the last note ends inside, a beat spare
    play = next(kw for c, kw in calls if c == "transport")
    assert (play["start_seconds"], play["end_seconds"]) == (1.7, 8.5)    # the lengthened item's end, plus the tail
    assert out["pass"] == {"from_seconds": 1.7, "to_seconds": 8.5} and out["captured"]["notes"] == 6
    assert "{I} to 8.0 s" in out["extended_items"]


def test_render_vocalvst_reports_a_partial_capture_as_an_error(tmp_path, monkeypatch):
    from creaper import vocal_tools

    # Eight notes on the track; the plugin's state (VOCALVST_CHUNK) holds six captured.
    notes = [{"pitch": 60, "start": i * 1.0, "length": 0.9, "velocity": 100} for i in range(8)]
    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch, notes=notes)
    with pytest.raises(ValueError, match=r"captured 6 of the track's 8 notes .* 2 were missed"):
        vocal_tools.render_vocalvst(track=1)
    assert ("set_fx_parameter", {"track": 1, "fx": 1, "parameter": "Render", "display_text": "On"}) not in calls
    assert "transport" in [c for c, _ in calls]                          # the pass did run, over the whole item


def test_render_vocalvst_refuses_a_note_before_its_item(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch, notes=[{"pitch": 60, "start": -1.0, "length": 0.5, "velocity": 100}])
    with pytest.raises(ValueError, match=r"item \{I\} .* bar 2 .* 1.00 quarter notes before it"):
        vocal_tools.render_vocalvst(track=1)


def test_render_vocalvst_holds_notes_with_plus_and_checks_the_count(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _, state = _vocalvst_bridge(tmp_path, monkeypatch)
    vocal_tools.render_vocalvst(track=1, lyrics="go _ go _ go _")
    assert vocal_tools.vocalvst_lyrics(state["chunk"]) == "go + go + go +"
    with pytest.raises(ValueError, match="6 notes"):
        vocal_tools.render_vocalvst(track=1, lyrics="too few words")


def test_render_vocalvst_hears_the_take_when_the_plugin_writes_no_log(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch, log_on_render=False, sounds_after=1)
    out = vocal_tools.render_vocalvst(track=1, mode="scat")
    assert out["lyrics"] is None and "plays the new take" in out["result"]


def test_render_vocalvst_explains_a_render_that_never_comes(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch, log_on_render=False)
    monkeypatch.setattr(vocal_tools.time, "monotonic", _FakeClock())
    with pytest.raises(ValueError, match="No voicebank"):
        vocal_tools.render_vocalvst(track=1, timeout_seconds=30)


class _FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        self.t += 2.0
        return self.t


def test_render_vocalvst_needs_the_plugin_and_notes(monkeypatch):
    from creaper import vocal_tools

    monkeypatch.setattr(vocal_tools, "call", lambda cmd, **kw: {"number": 2, "name": "Lead", "fx": [], "items": []})
    with pytest.raises(ValueError, match="no VocalVST"):
        vocal_tools.render_vocalvst(track="Lead")


def test_render_vocalvst_refuses_fast_without_a_voicebank(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch)
    monkeypatch.setattr(vocal_tools, "VOICEBANK_ROOT", tmp_path / "nowhere")
    with pytest.raises(ValueError, match="no voicebank"):
        vocal_tools.render_vocalvst(track=1)
    assert "transport" not in [c for c, _ in calls]      # no ten-minute wait for nothing


def test_render_vocalvst_gives_up_when_the_switch_stays_on(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch, log_on_render=False, takes_switch=False)
    monkeypatch.setattr(vocal_tools.time, "monotonic", _FakeClock())
    with pytest.raises(ValueError, match="stays On"):
        vocal_tools.render_vocalvst(track=1)


def test_render_vocalvst_offers_the_packaged_app_cache_when_the_plugin_cannot_see_the_first(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _, state = _vocalvst_bridge(tmp_path, monkeypatch, sees_bank=lambda path: "LocalCache" in path)
    cache = tmp_path / "Packages" / "Claude_x" / "LocalCache" / "Local" / "VocalVST" / "voicebanks" / "Canary_DS"
    cache.mkdir(parents=True)
    (cache / "dsconfig.yaml").write_text("acoustic: dsacoustic/acoustic.onnx\n")
    monkeypatch.setattr(vocal_tools, "voicebank_roots", lambda: [tmp_path / "voicebanks", cache.parent])
    out = vocal_tools.render_vocalvst(track=1)
    assert vocal_tools.vocalvst_bank(state["chunk"]) == str(cache) and out["voicebank"] == "Canary_DS"

    monkeypatch.setattr(vocal_tools, "voicebank_roots", lambda: [tmp_path / "voicebanks"])
    vocal_tools.vocalvst_state_with(state["chunk"], bank="")
    state["chunk"] = vocal_tools.vocalvst_state_with(state["chunk"], bank="")
    with pytest.raises(ValueError, match="can't see them"):
        vocal_tools.render_vocalvst(track=1)


def test_voicebank_roots_include_packaged_app_caches(tmp_path, monkeypatch):
    from creaper import vocal_tools

    local = tmp_path / "AppData" / "Local"
    cache = local / "Packages" / "Claude_abc" / "LocalCache" / "Local" / "VocalVST" / "voicebanks"
    cache.mkdir(parents=True)
    monkeypatch.setattr(vocal_tools, "VOICEBANK_ROOT", local / "VocalVST" / "voicebanks")
    assert vocal_tools.voicebank_roots() == [local / "VocalVST" / "voicebanks", cache]


def test_render_vocalvst_mutes_the_master_only_for_the_pass(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch)
    vocal_tools.render_vocalvst(track=1)
    mutes = [(i, kw["mute"]) for i, (c, kw) in enumerate(calls) if c == "set_track_properties"]
    play = next(i for i, (c, kw) in enumerate(calls) if c == "transport")
    render = next(i for i, (c, kw) in enumerate(calls) if c == "set_fx_parameter" and kw["parameter"] == "Render")
    assert [m for _, m in mutes] == [True, False]
    assert mutes[0][0] < play < mutes[1][0] < render
    assert all(kw["track"] == "master" for c, kw in calls if c == "set_track_properties")


def test_render_vocalvst_puts_the_master_back_when_the_pass_fails(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch, pass_fails=True)
    with pytest.raises(RuntimeError):
        vocal_tools.render_vocalvst(track=1)
    assert [kw["mute"] for c, kw in calls if c == "set_track_properties"] == [True, False]


def test_render_vocalvst_leaves_a_muted_master_muted(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch, master_muted=True)
    vocal_tools.render_vocalvst(track=1)
    assert not [c for c, _ in calls if c == "set_track_properties"]


def test_vocalvst_counts_as_an_installed_singer(monkeypatch):
    from creaper import vocal_tools

    monkeypatch.setattr(vocal_tools, "call", lambda cmd, **kw: {"plugins": [{"name": "VocalVST"}]})
    assert "VocalVST" in vocal_tools.singing_synths()
    assert "render_vocalvst" in vocal_tools.SINGERS["VocalVST"][1]


def test_render_vocalvst_sets_expression_only_when_asked(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, _ = _vocalvst_bridge(tmp_path, monkeypatch)
    out = vocal_tools.render_vocalvst(track="Vocal", lyrics="we ride at dawn to-night", expression=0.4)
    expr = [kw for c, kw in calls if c == "set_fx_parameter" and kw["parameter"] == "Expression"]
    assert expr == [{"track": "Vocal", "fx": 1, "parameter": "Expression", "value": 0.4}] and out["expression"] == 0.4
    calls.clear()
    out = vocal_tools.render_vocalvst(track="Vocal", lyrics="we ride at dawn to-night")
    assert not [kw for c, kw in calls if c == "set_fx_parameter" and kw["parameter"] == "Expression"]
    assert out["expression"] == "the plugin's own"


def test_add_vocal_harmony_stacks_a_third_above_with_the_lead_words(tmp_path, monkeypatch):
    from creaper import vocal_tools

    calls, state = _vocalvst_bridge(tmp_path, monkeypatch)
    vocal_tools.render_vocalvst(track="Vocal", lyrics="we ride at dawn to-night")
    calls.clear()
    out = vocal_tools.add_vocal_harmony(track="Vocal", interval="third above", key="C major", pan=-0.4)
    assert state["created"] == ["Vocal Harmony"]
    created = next(kw for c, kw in calls if c == "create_track")
    assert created["instrument"] == "VocalVST"
    item = next(kw for c, kw in calls if c == "create_midi_item")
    assert item["track"] == "Vocal Harmony" and item["start_bar"] == 2 and item["length_qn"] == 6.0
    added = next(kw for c, kw in calls if c == "add_midi_notes")
    assert [n["pitch"] for n in added["notes"]] == [64, 65, 67, 67, 65, 64] and added["replace"]   # C D E E D C, a third up
    props = next(kw for c, kw in calls if c == "set_track_properties" and "pan" in kw)
    assert props == {"track": "Vocal Harmony", "pan": -0.4, "volume_db": -6.0}
    assert vocal_tools.vocalvst_lyrics(state["chunk"]) == "we ride at dawn to night"   # the same words
    expr = next(kw for c, kw in calls if c == "set_fx_parameter" and kw["parameter"] == "Expression")
    assert expr["value"] == 0.6 and expr["track"] == "Vocal Harmony"
    assert out["items"] == 1 and out["key"] == "C major" and out["render"].startswith("Rendered") and "warning" not in out


def test_add_vocal_harmony_outside_the_bars_or_without_notes_is_said(tmp_path, monkeypatch):
    from creaper import vocal_tools

    _vocalvst_bridge(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="none of the lead's items start in that range"):
        vocal_tools.add_vocal_harmony(track="Vocal", start_bar=10, key="C major")


def test_write_vocal_melody_writes_the_line_and_returns_its_lyrics(monkeypatch):
    from creaper import music_tools, vocal_tools

    calls = []

    def fake(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "add_midi_notes":
            return {"notes": len(kw["notes"]), "end": {"bar": 9}}
        return {"time_signature": "4/4", "tempo_bpm": 112}

    monkeypatch.setattr(vocal_tools, "call", fake)
    monkeypatch.setattr(music_tools, "call", fake)
    monkeypatch.setattr(vocal_tools, "installed_voices", lambda: {"TIGER": (None, ""), "tiger_disco": (None, "tiger_disco")})
    out = vocal_tools.write_vocal_melody(item_id="{I}", lyrics="Baby it's you, yeah / Baby it's true, oh",
                                         chords="Am7 Fmaj7 Cmaj7 G", key="A minor", shape="chorus", seed=2)
    added = next(kw for c, kw in calls if c == "add_midi_notes")
    assert added["item_id"] == "{I}" and added["replace"] and len(added["notes"]) == out["notes_written"]
    assert out["lyrics"].split()[:2] == ["Ba-by", "it's"] and out["range"]["voice"].startswith("male (D3-E4)")
    assert out["line_bars"] == 2.0 and len(out["lines"]) == 2 and out["key"] == "A minor"
    assert all(50 <= n["pitch"] <= 64 for n in added["notes"])
