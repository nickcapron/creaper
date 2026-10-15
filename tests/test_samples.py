import drum_synth as d
import numpy as np
import pytest
import soundfile as sf

from creaper import project_tools, samplelib


def test_names():
    assert samplelib.bpm_from_name("Funky Drum Loop 96bpm") == 96
    assert samplelib.bpm_from_name("break_174_dnb loop") == 174
    assert samplelib.bpm_from_name("Kick 808") is None
    assert samplelib.key_from_name("Pad Am 120bpm") == "A minor"
    assert samplelib.key_from_name("Chords_F#min_loop") == "F# minor"
    assert samplelib.key_from_name("Lead C maj") == "C major"
    assert samplelib.key_from_name("Kick A") is None
    assert "kick" in samplelib.roles_from_name("XOX kick1")
    assert "open hat" in samplelib.roles_from_name("HHOPEN3")
    assert "closed hat" in samplelib.roles_from_name("rd-6 closedhat")
    assert "snare" in samplelib.roles_from_name("SNAREA12")


def _drum_loop(bpm: float, bars: int = 2) -> np.ndarray:
    beat = 60 / bpm
    n = int(bars * 4 * beat * d.FS)
    x = np.zeros(n + d.FS)
    kick, hat, snare = d.kick(0.4), d.closed_hat(0.2) * 0.5, d.snare(0.3)
    for i in range(bars * 8):  # 8th notes
        t = int(i * beat / 2 * d.FS)
        x[t: t + len(hat)] += hat
        if i % 4 == 0:
            x[t: t + len(kick)] += kick
        if i % 4 == 2:
            x[t: t + len(snare)] += snare
    return x[:n] * 0.5


@pytest.mark.parametrize("bpm", [90, 120, 140, 174])
def test_loop_tempo(bpm):
    x = _drum_loop(bpm)
    est, _ = samplelib.estimate_bpm(x, d.FS, len(x) / d.FS)
    assert est == pytest.approx(bpm, rel=0.02)


def test_loop_key():
    t = np.arange(int(4 * d.FS)) / d.FS
    x = sum(np.sin(2 * np.pi * f * t) for f in (220.0, 261.63, 329.63)) / 3  # A minor triad
    x += 0.5 * sum(np.sin(2 * np.pi * f * t) for f in (293.66, 349.23, 440.0)) / 3 * (t > 2)  # D minor
    assert samplelib.estimate_key(x, d.FS)[0]["key"] in ("A minor", "C major", "D dorian", "A dorian")


def test_analyze_files(tmp_path):
    loop = tmp_path / "Drum Loop 120bpm.wav"
    sf.write(str(loop), _drum_loop(120), d.FS)
    kick = tmp_path / "kick1.wav"
    sf.write(str(kick), d.kick(), d.FS)
    a = samplelib.analyze(str(loop))
    assert a["kind"] == "loop" and a["bpm"] == pytest.approx(120, rel=0.02) and a["bars_at_4_4"] == pytest.approx(2, abs=0.05)
    k = samplelib.analyze(str(kick))
    assert k["kind"] == "one-shot" and k["sounds_like"] == "kick"

    lib = samplelib.SampleLibrary(tmp_path / "cfg")
    lib.set_folders([str(tmp_path)])
    idx = lib.index(refresh=True)
    assert {f["name"] for f in idx["files"]} == {"Drum Loop 120bpm", "kick1"}
    assert [f["name"] for f in lib.search(role="kick")] == ["kick1"]
    assert [f["name"] for f in lib.search(kind="loop", bpm=60)] == ["Drum Loop 120bpm"]  # half time matches


def test_program_names():
    assert project_tools._program_number("Electric Piano 1") == 5
    assert project_tools._program_number(1) == 1
    assert project_tools._program_number("marimba") == 13
    with pytest.raises(ValueError):
        project_tools._program_number("piano")  # ambiguous
    with pytest.raises(ValueError):
        project_tools._program_number(200)


def test_short_hits_analyze_without_crashing(tmp_path):
    """An envelope shorter than the smoothing window used to crash analyze (FM Perc 1.wav)."""
    import numpy as np
    import soundfile as sf
    from creaper import samplelib
    fs = 44100
    hit = np.exp(-np.arange(int(0.12 * fs)) / (0.02 * fs)) * np.random.default_rng(0).standard_normal(int(0.12 * fs))
    path = tmp_path / "perc.wav"
    sf.write(str(path), hit * 0.5, fs)
    for n in range(8, 16):
        assert samplelib.onset_envelope(np.zeros(2048 + 512 * n), fs).shape == (n,)
    assert samplelib.analyze(str(path))["kind"] == "one-shot"


def test_kit_keys_match_the_pattern_lanes():
    """build_drum_kit put the toms on other keys than add_drum_pattern plays them on."""
    from creaper import theory
    from creaper.sample_tools import GM_LANES
    for lane, note in GM_LANES.items():
        try:
            assert theory.drum_pitch(lane) == note, lane
        except ValueError:
            pass  # a lane add_drum_pattern doesn't name


def test_parallel_searches_dont_fight_over_the_index(tmp_path):
    """Claude's parallel find_samples calls failed with 'Access denied' on the shared index."""
    import json
    import threading
    from creaper.samplelib import SampleLibrary
    lib = SampleLibrary(tmp_path)
    files = [{"path": f"C:/s/{i}.wav", "name": str(i)} for i in range(40)]
    lib._save_index({"folders": [], "files": files})
    errors = []

    def worker(k):
        try:
            for i in range(k, 40, 8):
                lib.remember(f"C:/s/{i}.wav", {"kind": "one-shot", "n": i})
                lib._load_index()
        except Exception as e:  # noqa: BLE001
            errors.append(e)
    threads = [threading.Thread(target=worker, args=(k,)) for k in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    saved = json.loads(lib.index_path.read_text(encoding="utf-8"))
    assert all(f.get("analysis", {}).get("n") == i for i, f in enumerate(saved["files"]))
    assert not list(tmp_path.glob("*.tmp"))
