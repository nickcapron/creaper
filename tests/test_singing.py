"""A speech voice made to sing: PSOLA pitch moves that keep the formants, the word
stretch, vibrato, phrase splitting, the double, HNR, and add_robot_vocal(style='sung')."""

import numpy as np
import pytest
import soundfile as sf
from scipy import signal

from creaper import server  # noqa: F401  (import order: server first)
from creaper import singing, speech, vocal_tools

FS = 22050


def vowel(f0=140.0, seconds=0.6, formants=(700, 1200, 2600), fs=FS, jitter=0.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(fs * seconds)
    src = np.zeros(n)
    t = 0.0
    while t < n:
        src[int(t)] = 1.0
        t += fs / f0 * (1 + rng.normal(0, jitter))
    y = src
    for f in formants:
        b, a = signal.iirpeak(f, 8, fs)
        y = signal.lfilter(b, a, y)
    return y / np.max(np.abs(y)) * 0.8


def median_f0(y, lo=0, hi=None, fs=FS):
    c, f0, _ = singing.f0_track(y, fs)
    keep = (c >= lo * fs) & (c < (hi if hi is not None else len(y) / fs) * fs) & (f0 > 0)
    return float(np.median(f0[keep]))


def envelope_peak(y, lo=400, hi=1000, fs=FS):
    f, p = signal.welch(y, fs, nperseg=2048)
    k = int(150 / (f[1] - f[0]))
    smooth = np.convolve(p, np.ones(k) / k, mode="same")
    band = (f > lo) & (f < hi)
    return float(f[band][np.argmax(smooth[band])])


def first_formant(y, fs=FS, order=18):
    """The lowest resonance of an LPC envelope above 300 Hz (independent of where the harmonics fall)."""
    from scipy.linalg import solve_toeplitz
    y = signal.lfilter([1, -0.63], [1], y)                  # pre-emphasis
    r = np.array([np.dot(y[: len(y) - k], y[k:]) for k in range(order + 1)])
    a = solve_toeplitz(r[:order], -r[1: order + 1])
    w, h = signal.freqz([1.0], np.concatenate([[1.0], a]), worN=4096, fs=fs)
    env = 20 * np.log10(np.abs(h) + 1e-12)
    peaks = signal.find_peaks(env)[0]
    return float(next(w[k] for k in peaks if w[k] > 300))


def test_psola_moves_the_pitch_and_keeps_the_voice():
    x = vowel(140)
    for target in (110.0, 220.0, 300.0):
        y = singing.psola(x, FS, int(FS * 1.2), lambda t: t * 0.5, lambda t: target)
        assert median_f0(y) == pytest.approx(target, rel=0.02)
        # The first formant stays near 700 Hz: moved with the pitch (no formant keeping) it
        # would land at 700 x target / 140, 1.1-1.5 kHz for the upward shifts.
        assert abs(first_formant(y) - first_formant(x)) < 150, (target, first_formant(y), first_formant(x))
        assert len(y) == int(FS * 1.2)
    same = singing.psola(x, FS, len(x), lambda t: t, lambda t: None)
    assert median_f0(same) == pytest.approx(140, rel=0.02)


def test_a_word_is_sung_on_its_notes_with_vibrato_on_the_long_one():
    x = vowel(150, 0.5)
    word = singing.sing_word(x, FS, 1.2, [(0.0, 57), (0.3, 64)], (int(0.05 * FS), int(0.45 * FS)))
    assert len(word) == int(1.2 * FS)
    assert median_f0(word, 0.05, 0.28) == pytest.approx(220, rel=0.02)
    assert median_f0(word, 0.5, 1.1) == pytest.approx(329.6, rel=0.03)
    c, f0, _ = singing.f0_track(word, FS)
    held = f0[(c > 0.8 * FS) & (c < 1.15 * FS) & (f0 > 0)]
    short = f0[(c > 0.05 * FS) & (c < 0.28 * FS) & (f0 > 0)]
    assert np.ptp(12 * np.log2(held / 329.6)) > 0.4                      # vibrato on the held note
    assert np.ptp(12 * np.log2(short / 220)) < 0.2                        # none on the short one


def test_the_vowel_is_held_and_the_consonants_keep_their_speed():
    fs = FS
    m = singing.vowel_map(np.zeros(fs), fs, 2 * fs, (int(0.2 * fs), int(0.8 * fs)))
    assert m(int(0.1 * fs)) == int(0.1 * fs)                            # the onset at natural speed
    assert m(2 * fs - 1) == pytest.approx(fs - 1, abs=2)                # the tail too
    assert m(int(1.0 * fs)) == pytest.approx(0.2 * fs + 0.8 * fs * 0.6 / 1.6, rel=0.01)


def test_a_phrase_is_cut_at_the_quiet_between_words():
    gaps = [0.0, 0.4, 0.75, 1.35]
    lengths = [0.35, 0.3, 0.55, 0.4]
    phrase = np.zeros(int(FS * 1.9))
    for g, n in zip(gaps, lengths):
        w = vowel(140, n)
        phrase[int(g * FS): int(g * FS) + len(w)] += w
    phrase += np.random.default_rng(0).normal(0, 1e-3, len(phrase))
    spans = singing.split_phrase(phrase, FS, [1.0, 1.0, 1.0, 1.0])       # the weights don't know the lengths
    starts = [a / FS for a, _ in spans]
    for found, true_end, true_next in zip(starts[1:], [g + n for g, n in zip(gaps, lengths)], gaps[1:]):
        assert true_end - 0.02 <= found <= true_next + 0.02, (found, true_end, true_next)


def test_hnr_tells_a_clean_voice_from_a_rough_one():
    clean = singing.hnr_db(vowel(140, 1.0), FS)
    rough = vowel(140, 1.0, jitter=0.08, seed=1) + np.random.default_rng(2).normal(0, 0.15, int(FS))
    rough_hnr = singing.hnr_db(rough, FS)
    assert clean > 12 and (rough_hnr is None or rough_hnr < clean - 5)
    assert singing.hnr_db(np.zeros(FS), FS) is None


def test_the_double_is_late_and_detuned_either_side():
    y = vowel(200, 0.5)
    st = singing.double(y, FS)
    assert st.shape == (len(y), 2)
    d = int(singing.DOUBLE["delay_s"] * FS)
    assert np.allclose(st[:d, 0], st[:d, 1])                             # the double starts later
    assert not np.allclose(st[d + 200:, 0], st[d + 200:, 1])            # and differs left and right


def test_add_robot_vocal_sings_a_line(monkeypatch, tmp_path):
    notes = [{"pitch": p, "start": i * 1.0, "length": 0.9, "velocity": 90} for i, p in enumerate((57, 60, 62, 64))]
    notes.append({"pitch": 60, "start": 4.0, "length": 2.0, "velocity": 90})
    calls = []

    def fake_call(cmd, **kw):
        calls.append(cmd)
        if cmd == "get_midi_notes":
            return {"notes": notes, "start": {"qn": 0.0}, "track": 1}
        if cmd == "project_paths":
            return {"default_folder": str(tmp_path)}
        if cmd == "qn_to_times":
            return [q * 0.5 for q in kw["qns"]]                         # 120 BPM
        if cmd == "get_project_overview":
            return {"tracks": [{"name": "Lead"}]}
        if cmd == "create_track":
            return {"track": {"name": kw["name"]}}
        if cmd == "place_audio_clips":
            return {"track": {"name": kw["track"]}, "placed": len(kw["clips"])}
        raise AssertionError(cmd)

    def fake_phrase(text, path, voice=None):
        words = text.split()
        audio = np.concatenate([np.concatenate([vowel(130 + 10 * i, 0.3), np.zeros(int(0.08 * FS))])
                                for i, _ in enumerate(words)])
        path.parent.mkdir(parents=True, exist_ok=True)
        speech._write(path, audio, FS)
        return path

    monkeypatch.setattr(vocal_tools, "call", fake_call)
    def fake_words(texts, folder, voice=None):
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, _ in enumerate(texts):
            path = folder / f"{i + 1:03d}.wav"
            speech._write(path, vowel(130 + 10 * i, 0.3), FS)
            paths.append(path)
        return paths

    monkeypatch.setattr(speech, "speak_phrase", fake_phrase)
    monkeypatch.setattr(speech, "speak", fake_words)
    monkeypatch.setattr(speech, "choose_voice", lambda v: "Piper Kristin")
    import creaper.ear_tools as ear
    monkeypatch.setattr(ear, "measure_vocal_clarity", lambda *a, **k: {"alone": {"score": 0.8}})
    dry = vocal_tools.add_robot_vocal(item_id="{M}", lyrics="we sing all night _", style="sung", double=False)
    dry_file = sorted(next(iter(sorted(tmp_path.glob("creaper vocals/*")))).glob("0*.wav"))[0]
    assert sf.info(str(dry_file)).channels == 1 and dry["words_placed"] == 4
    for d in tmp_path.glob("creaper vocals/*"):
        import shutil
        shutil.rmtree(d)
    out = vocal_tools.add_robot_vocal(item_id="{M}", lyrics="we sing all night _", style="sung")
    assert out["style"] == "sung" and out["words_placed"] == 4 and out["vocal"]["name"] == "Sung Vocal"
    assert out["harmonics_to_noise_db"] > 10
    assert 8 < out["shift_semitones"] < 12                      # words at 130-160 Hz, the melody around C4
    assert "shift_note" in out                                   # the voice speaks far below this melody
    folder = next(tmp_path.glob("creaper vocals/*"))
    sung = sorted(folder.glob("0*.wav"))
    assert len(sung) == 4 and all(sf.info(str(f)).channels == 2 for f in sung)
    assert len(list((folder / "speech").glob("*.wav"))) == 4
    last, fs = sf.read(str(sung[-1]))
    assert len(last) / fs == pytest.approx(1.5, abs=0.02)               # "night": E4 then a held C4, 3 beats
    c, f0, _ = singing.f0_track(last.mean(axis=1), fs)
    assert np.median(f0[(c > 0.1 * fs) & (c < 0.45 * fs) & (f0 > 0)]) == pytest.approx(329.6, rel=0.03)
    assert np.median(f0[(c > 0.7 * fs) & (f0 > 0)]) == pytest.approx(261.6, rel=0.03)
    # Two syllables a beat are fine sung; the robot styles still refuse them.
    with pytest.raises(ValueError):
        vocal_tools.assign_lyrics("a b c d e f g h", [{"pitch": 60, "start": i * 0.5, "length": 0.5} for i in range(8)])
    vocal_tools.assign_lyrics("a b c d e f g h", [{"pitch": 60, "start": i * 0.5, "length": 0.5} for i in range(8)],
                              vocal_tools.SUNG_MAX_PER_BEAT)



# ------------------------------------------------------------- review regressions

def _word(f0, formants, seconds, fs=FS):
    return vowel(f0, seconds, formants)


def test_words_are_found_in_connected_speech():
    # Four "words" (different vowels) run together with no gap, each spoken at its own
    # pace; the reference has them alone at other lengths.
    shapes = [(300, 2300, 3000), (700, 1200, 2600), (450, 900, 2500), (350, 1900, 2700)]
    phrase_lengths = [0.25, 0.4, 0.2, 0.5]
    alone_lengths = [0.35, 0.3, 0.3, 0.4]
    phrase = np.concatenate([_word(140, f, n) for f, n in zip(shapes, phrase_lengths)])
    alone = [_word(140, f, n) for f, n in zip(shapes, alone_lengths)]
    spans = singing.align_words(phrase, FS, alone)
    truth = np.cumsum([0] + phrase_lengths)
    for (a, b), t0, t1 in zip(spans, truth, truth[1:]):
        assert abs(a / FS - t0) < 0.04 and abs(b / FS - t1) < 0.04, (a / FS, b / FS, t0, t1)


def test_every_word_gets_room_even_when_they_crowd():
    tiny = vowel(140, 0.06)
    spans = singing.align_words(tiny, FS, [vowel(140, 0.1)] * 8)
    assert len(spans) == 8 and all(b > a for a, b in spans)
    assert singing.sing_word(np.zeros(0), FS, 0.3, [(0.0, 60)], (0, 0)).shape == (int(0.3 * FS),)


def test_the_held_part_is_voiced_and_a_slowed_hiss_stays_a_hiss():
    rng = np.random.default_rng(3)
    hiss = rng.normal(0, 0.3, int(0.15 * FS))                         # an 's' louder than the vowel after it
    word = np.concatenate([hiss, vowel(140, 0.2) * 0.4])
    a, b = singing.voiced_span(word, FS)
    assert a >= 0.13 * FS and b > 0.3 * FS
    assert singing.voiced_span(hiss, FS) is None
    slow = singing.psola(hiss, FS, int(0.6 * FS), lambda t: t * 0.2, lambda t: None)
    c, f0, _ = singing.f0_track(slow, FS)
    assert (f0 > 0).mean() < 0.2                                       # no 200 Hz buzz from repeated grains


def test_a_sung_line_too_dense_says_sung():
    line = [{"pitch": 60, "start": i * 0.25, "length": 0.25} for i in range(16)]
    with pytest.raises(ValueError, match="a sung voice"):
        vocal_tools.assign_lyrics(" ".join(["la"] * 16), line, vocal_tools.SUNG_MAX_PER_BEAT)
