import os

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


def test_instrument_kinds_from_library_names():
    kinds = samplelib.instrument_kinds
    assert kinds("CelloEnsSusVib") == ["strings"] and kinds("SViolinPizz") == ["strings"]
    assert kinds("FHornSus") == ["brass"] and kinds("BassoonStac") == ["woodwinds"]
    assert kinds("EGuitarFSBS-dist1 bridge 20220911", "FreePats Distorted Guitar 1") == ["guitar"]
    assert kinds("Black_Pearl_2023_repack", "AVL Drumkits/BLACK_PEARL_2023_repack") == ["drum kit"]
    assert kinds("Timpani") == ["percussion"] and kinds("Harp") == ["harp"]
    # Whole words: a harpsichord isn't a harp, a bassoon isn't a bass, an upright bass isn't a piano.
    assert kinds("Harpsichord") == ["keys"] and kinds("UprightBass") == ["bass"] and kinds("VSUpright1") == ["keys"]
    assert kinds("Bass Fat Pizzicato", "Augmented STRINGS") == ["strings", "bass"]
    assert kinds("Thorn Pad") == [] and kinds("Tubular Bells") == ["percussion"]


def test_sfz_instruments_are_checked_once_per_file_version(tmp_path, monkeypatch):
    root = tmp_path / "samples"
    _sfz(root, "Cello", "c.wav")
    _sfz(root, "Broken", "gone.wav", write_sample=False)
    checks = []
    real = samplelib.playable_sfz
    monkeypatch.setattr(samplelib, "playable_sfz", lambda p: checks.append(p) or real(p))
    lib = samplelib.SampleLibrary(tmp_path / "data")
    lib.set_folders([str(root)])
    assert [i["name"] for i in lib.index()["instruments"]] == ["Cello"] and len(checks) == 2
    checks.clear()
    lib._save_index({**lib.index(), "built": "old", "partial": True})   # a rebuild without refresh
    assert [i["name"] for i in lib.index()["instruments"]] == ["Cello"] and checks == []
    lib.index(refresh=True)                      # refresh= re-checks both (a sample may have arrived)
    assert sorted(os.path.basename(c) for c in checks) == ["Broken.sfz", "Cello.sfz"]


def _sfz(folder, name, sample="s.wav", write_sample=True):
    """An .sfz instrument with one region (and, unless asked not to, its sample)."""
    folder.mkdir(parents=True, exist_ok=True)
    if write_sample:
        sf.write(str(folder / sample), np.zeros(4410, dtype="float32"), 44100)
    (folder / f"{name}.sfz").write_text(f"<region> sample={sample} key=36\n")


def test_the_index_lists_sfz_instruments_and_find_samples_offers_them(tmp_path, monkeypatch):
    from creaper import sample_tools

    root = tmp_path / "samples"
    _sfz(root / "AVL Drumkits" / "Kit", "Black_Pearl", "kick.wav")
    _sfz(root / "Orchestra", "CelloEnsSusVib", "c.wav")
    lib = samplelib.SampleLibrary(tmp_path / "data")
    lib.set_folders([str(root)])
    assert {i["name"]: i["kinds"] for i in lib.index()["instruments"]} == {
        "Black_Pearl": ["drum kit"], "CelloEnsSusVib": ["strings"]}
    assert [i["name"] for i in lib.instruments(None, "snare")] == ["Black_Pearl"]
    assert [i["name"] for i in lib.instruments("cello", None)] == ["CelloEnsSusVib"]
    assert lib.instruments(None, None) == [] and lib.instruments(None, "guitar") == []
    monkeypatch.setattr(sample_tools, "library", lib)
    out = sample_tools.find_samples(role="strings", listen=False)
    assert out["instruments"][0]["sfz_path"].endswith("CelloEnsSusVib.sfz") and "tip" not in out
    assert "build_sampled_instrument" in out["instruments_note"]


def test_instruments_named_for_the_role_come_before_ones_in_a_folder_named_for_it(tmp_path):
    root = tmp_path / "samples"
    _sfz(root / "Augmented STRINGS" / "Factory", "Bizarre Radio FM")     # a texture in a strings folder
    _sfz(root / "VSCO", "SViolinVib")
    lib = samplelib.SampleLibrary(tmp_path / "data")
    lib.set_folders([str(root)])
    assert [i["name"] for i in lib.instruments(None, "strings")] == ["SViolinVib", "Bizarre Radio FM"]


def test_an_sfz_missing_its_samples_isnt_listed(tmp_path):
    root = tmp_path / "samples"
    _sfz(root, "Broken Cello", "gone.wav", write_sample=False)
    _sfz(root, "Cello", "c.wav")
    lib = samplelib.SampleLibrary(tmp_path / "data")
    lib.set_folders([str(root)])
    assert [i["name"] for i in lib.index()["instruments"]] == ["Cello"]


def test_an_index_from_before_instruments_is_rebuilt(tmp_path):
    root = tmp_path / "samples"
    _sfz(root, "Guitar", "g.wav")
    lib = samplelib.SampleLibrary(tmp_path / "data")
    lib.set_folders([str(root)])
    lib._save_index({"folders": [str(root)], "built": "old", "files": []})
    assert [i["name"] for i in lib.index()["instruments"]] == ["Guitar"]


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


@pytest.mark.parametrize("name,key", [
    ("Pad_in_D_minor", "D minor"),     # was D major: "_" wasn't allowed before "minor"
    ("Main_B_loop_120", None),         # was B major: "in" inside "Main"
    ("Latin_A_perc", None),            # was A major: "in" inside "Latin"
    ("Rain_in_a_jar_vox", None),       # was A major: a lowercase "a" taken for a key
    ("Guitar key E", "E major"),
    ("Lead in Bb", "Bb major"),
    ("Strings_C_major_90bpm", "C major"),
])
def test_keys_from_names_dont_misfire(name, key):
    assert samplelib.key_from_name(name) == key


def test_very_short_samples_can_be_analysed(tmp_path):
    # A 23 ms click is shorter than the 2048-sample analysis window, which scipy refused.
    import numpy as np
    import soundfile as sf

    from creaper import perception
    fs = 44100
    click = np.zeros(1000)
    click[:40] = np.hanning(40)
    path = tmp_path / "click.wav"
    sf.write(str(path), click, fs)
    assert samplelib.onset_envelope(click, fs) is not None
    assert samplelib.analyze(str(path))
    assert perception.spectrogram_png(click, fs)[:4] == b"\x89PNG"



# ------------------------------------------------------- drums by measurement

FS44 = 44100


def _kick(fs=FS44):
    t = np.arange(int(0.6 * fs)) / fs
    body = np.sin(2 * np.pi * (50 + 80 * np.exp(-t * 40)) * t) * np.exp(-t * 6)
    click = np.random.default_rng(0).standard_normal(t.size) * np.exp(-t * 400) * 0.6
    return 0.8 * (body + click)


def _hat(fs=FS44):
    t = np.arange(int(0.15 * fs)) / fs
    return 0.5 * np.random.default_rng(1).standard_normal(t.size) * np.exp(-t * 40)


def test_hit_measures_tell_a_kick_from_a_hat():
    kick, hat = samplelib.hit_measures(_kick(), FS44), samplelib.hit_measures(_hat(), FS44)
    assert kick["sub_share"] > 0.4 and hat["sub_share"] < 0.05
    assert kick["punch_db"] > 3
    assert hat["top_hz"] > 15000


def test_lofi_files_are_flagged(tmp_path):
    import soundfile as sf
    from scipy import signal
    sf.write(str(tmp_path / "clean.wav"), _hat(), FS44, subtype="PCM_24")
    sf.write(str(tmp_path / "eight.wav"), _hat(), FS44, subtype="PCM_U8")
    low_rate = signal.resample_poly(_hat(), 1, 2)  # an old sampler's 22 kHz file
    sf.write(str(tmp_path / "dull.wav"), low_rate, FS44 // 2, subtype="PCM_16")
    sf.write(str(tmp_path / "kick.wav"), _kick(), FS44, subtype="PCM_24")
    assert not samplelib.analyze(str(tmp_path / "kick.wav")).get("lofi")  # a kick has no top end anyway
    clean, eight, dull_ = (samplelib.analyze(str(tmp_path / n)) for n in ("clean.wav", "eight.wav", "dull.wav"))
    assert not clean.get("lofi") and clean["bit_depth"] == 24 and clean["v"] == samplelib.ANALYSIS_VERSION
    assert eight["lofi"] and eight["bit_depth"] == 8
    assert dull_["lofi"]


def test_drum_fit_scores_against_a_genre_target():
    from creaper import genres
    from creaper.genres import palettes
    house_kick = palettes.palette(genres.find("house")).drums["kick"]
    good = {"sub_share": 0.9, "decay_s": 0.3, "punch_db": 2}
    thin = {"sub_share": 0.05, "decay_s": 0.3, "punch_db": 2}
    assert samplelib.drum_fit(good, house_kick) == (0.0, [])
    score, why = samplelib.drum_fit(thin, house_kick)
    assert score > 2 and "sub share" in why[0]


def test_find_samples_ranks_kicks_for_the_style(tmp_path, monkeypatch):
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    folder = tmp_path / "kicks"
    folder.mkdir()
    sf.write(str(folder / "a thin kick.wav"), _hat(), FS44, subtype="PCM_24")   # named kick, sounds like a click
    sf.write(str(folder / "b deep kick.wav"), _kick(), FS44, subtype="PCM_24")
    lib = samplelib.SampleLibrary(tmp_path / "cfg")
    lib.set_folders([str(folder)])
    monkeypatch.setattr(sample_tools, "library", lib)
    out = sample_tools.find_samples(role="kick", style="house")
    assert [s["name"] for s in out["shown"]][0].startswith("b deep kick")
    assert out["shown"][0]["fit"]["score"] <= out["shown"][1]["fit"]["score"]


def test_velocity_bands_cover_every_velocity_once():
    from creaper import server  # noqa: F401
    from creaper.sample_tools import velocity_bands
    assert velocity_bands(1) == [(1, 127)]
    for n in (2, 3, 4):
        bands = velocity_bands(n)
        assert bands[0][0] == 1 and bands[-1][1] == 127
        assert all(b[0] == a[1] + 1 for a, b in zip(bands, bands[1:]))


def test_build_drum_kit_with_alternatives_and_layers(tmp_path, monkeypatch):
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    loud, soft, click = tmp_path / "snare loud.wav", tmp_path / "snare soft.wav", tmp_path / "click.wav"
    sf.write(str(loud), _hat() * 1.0, FS44)
    sf.write(str(soft), _hat() * 0.2, FS44)
    sf.write(str(click), _hat(), FS44)
    kick = tmp_path / "kick.wav"
    sf.write(str(kick), _kick(), FS44)
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_project_overview":
            return {"tracks": [{"name": "Drums"}]}
        if cmd == "build_sampler_kit":
            return {"track": {"name": "Drums"}, "pads": [{"fx": i + 1, "note": p["note"]} for i, p in enumerate(kw["pads"])]}
        return {}
    monkeypatch.setattr(sample_tools, "call", fake_call)
    out = sample_tools.build_drum_kit(track="Drums", samples={"kick": str(kick), "snare": [str(loud), str(soft)]},
                                      layers={"kick": [sample_tools.Layer(path=str(click), gain_db=-9)]}, trim_silence=False)
    pads = next(kw for cmd, kw in calls if cmd == "build_sampler_kit")["pads"]
    assert [p["note"] for p in pads] == [36, 36, 38, 38]          # the layer shares the kick's key
    sets = [kw for cmd, kw in calls if cmd == "set_fx_parameters"]
    by_fx = {kw["fx"]: {c["parameter"]: c["display_value"] for c in kw["changes"]} for kw in sets}
    assert by_fx[2] == {"Volume": -9}                              # the kick's click layer
    assert by_fx[3] == {"Minimum velocity": 1, "Maximum velocity": 64}   # the soft snare takes the soft hits
    assert by_fx[4] == {"Minimum velocity": 65, "Maximum velocity": 127}
    assert out["kit"]["snare"]["samples"] == ["snare soft (velocity 1-64)", "snare loud (velocity 65-127)"]
    assert "layer, -9 dB" in out["kit"]["kick"]["samples"][1]
    with pytest.raises(ValueError, match="layers for lanes that have no sample"):
        sample_tools.build_drum_kit(track="Drums", samples={"kick": str(kick)},
                                    layers={"clap": [sample_tools.Layer(path=str(click))]}, trim_silence=False)



def test_a_loop_named_kick_cant_outrank_real_kicks(tmp_path, monkeypatch):
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    folder = tmp_path / "kicks"
    folder.mkdir()
    sf.write(str(folder / "a kick loop.wav"), np.tile(_kick()[: FS44 // 2], 8), FS44, subtype="PCM_24")
    sf.write(str(folder / "b deep kick.wav"), _kick(), FS44, subtype="PCM_24")
    lib = samplelib.SampleLibrary(tmp_path / "cfg")
    lib.set_folders([str(folder)])
    monkeypatch.setattr(sample_tools, "library", lib)
    shown = sample_tools.find_samples(role="kick", style="house")["shown"]
    assert shown[0]["name"].startswith("b deep kick")


def test_vocal_phrases_carry_their_tempo_and_key():
    assert samplelib.bpm_from_name("Vox_Hook_124_Am") == 124
    assert samplelib.key_from_name("Vox_Hook_124_Am") == "A minor"
    assert samplelib.bpm_from_name("acapella 98 F#m") == 98
    assert samplelib.bpm_from_name("Vocal Chop 03") is None          # a take number, not a tempo
    assert samplelib.bpm_from_name("Female Vox C4 sustain") is None
