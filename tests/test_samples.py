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
    # A waveform with no tail to read ranked as a perfect kick: now it costs.
    score, why = samplelib.drum_fit({"sub_share": 0.9, "decay_s": None, "punch_db": 2}, house_kick)
    assert score == samplelib.UNMEASURED_DECAY_COST and "decay unmeasured" in why[0]


def test_every_genre_ranks_its_drums_and_synth_waveforms_stay_out(tmp_path, monkeypatch):
    """Pop had no palette, so a 90s pop kick search went unranked and the top results were
    Arturia wavetable cycles that 'sound like' a kick, then a sub-only LinnDrum hit."""
    import soundfile as sf
    from creaper import genres, server  # noqa: F401
    from creaper import sample_tools
    from creaper.genres import palettes
    for g in genres.GENRES:
        for lane in ("kick", "snare", "clap", "hat"):
            assert palettes.drum_target(g, lane) is not None, (g.name, lane)
    assert palettes.drum_target(genres.find("house"), "kick") is palettes.PALETTES["house"].drums["kick"]
    assert palettes.drum_target(genres.find("pop"), "kick") is palettes.FAMILY_DRUMS["pop"]["kick"]
    assert palettes.drum_target(genres.find("pop"), "tom") is None
    hits, waves = tmp_path / "hits", tmp_path / "Factory" / "Wavetables"
    hits.mkdir(), waves.mkdir(parents=True)
    sf.write(str(waves / "BD Smash.wav"), _kick()[: FS44 // 8], FS44, subtype="PCM_24")   # a kick's first cycles
    sf.write(str(hits / "deep kick.wav"), _kick(), FS44, subtype="PCM_24")
    lib = samplelib.SampleLibrary(tmp_path / "cfg")
    lib.set_folders([str(tmp_path)])
    monkeypatch.setattr(sample_tools, "library", lib)
    out = sample_tools.find_samples(role="kick", style="pop")
    assert [s["name"] for s in out["shown"]] == ["deep kick"] and "fit" in out["shown"][0]
    assert [s["name"] for s in sample_tools.find_samples(search="BD")["shown"]] == ["BD Smash"]   # by name, still there


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
                                      layers={"kick": [sample_tools.Layer(path=str(click), gain_db=-9)]}, trim_silence=False,
                                      fill_gaps=False)     # not the user's library's crash
    pads = next(kw for cmd, kw in calls if cmd == "build_sampler_kit")["pads"]
    assert [p["note"] for p in pads] == [36, 36, 38, 38]          # the layer shares the kick's key
    sets = [kw for cmd, kw in calls if cmd == "set_fx_parameters"]
    by_fx = {kw["fx"]: {c["parameter"]: c["display_value"] for c in kw["changes"]} for kw in sets}
    # Balanced at build time: the snare's hits measure 6.9 dB under the kick's and belong 2 under, so it
    # comes up 4.9 dB; then the kit is trimmed so its loudest full-velocity hit (that snare) peaks at -6.
    kick_db = by_fx[1]["Volume"]
    assert kick_db == pytest.approx(-10.9, abs=0.2)
    assert by_fx[2] == {"Volume": pytest.approx(kick_db - 9, abs=0.01)}            # the kick's click layer, 9 under its lane
    assert by_fx[3] == {"Minimum velocity": 1, "Maximum velocity": 64, "Volume": pytest.approx(-6.0, abs=0.2)}
    assert by_fx[4] == {"Minimum velocity": 65, "Maximum velocity": 127, "Volume": by_fx[3]["Volume"]}
    assert out["levels"]["snare"].startswith("-6.0 dB (hits -7 dB against the kick, target -2)")
    assert out["kit"]["snare"]["samples"] == ["snare soft (velocity 1-64)", "snare loud (velocity 65-127)"]
    assert len(out["warnings"]) == 1 and out["warnings"][0].startswith("no crash lane")
    calls.clear()
    plain = sample_tools.build_drum_kit(track="Drums", samples={"kick": str(kick), "snare": [str(loud), str(soft)]},
                                        layers={"kick": [sample_tools.Layer(path=str(click), gain_db=-9)]},
                                        trim_silence=False, balance=False)
    sets = {kw["fx"]: {c["parameter"]: c["display_value"] for c in kw["changes"]} for cmd, kw in calls if cmd == "set_fx_parameters"}
    assert sets[2] == {"Volume": -9} and 1 not in sets and "levels" not in plain   # as the files come
    with pytest.raises(ValueError, match="layers for lanes that have no sample"):
        sample_tools.build_drum_kit(track="Drums", samples={"kick": str(kick)},
                                    layers={"clap": [sample_tools.Layer(path=str(click))]}, trim_silence=False)



def test_one_long_ringing_kick_is_a_hit_not_a_loop(tmp_path):
    """AVL's Black Pearl kick: 1.6 s with a resonant tail, read as a 123 BPM loop in A
    phrygian, so no drum search could rank it. Eight real hits are still a loop."""
    import soundfile as sf
    t = np.arange(int(1.7 * FS44)) / FS44
    ring = 0.9 * np.sin(2 * np.pi * (48 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 2.5)
    ring += np.random.default_rng(2).standard_normal(t.size) * np.exp(-t * 300) * 0.5
    one, many = tmp_path / "22-Kick-1.wav", tmp_path / "kicks loop.wav"
    sf.write(str(one), ring, FS44)
    sf.write(str(many), np.tile(_kick()[: FS44 // 2], 8), FS44)
    hit, loop = samplelib.analyze(str(one)), samplelib.analyze(str(many))
    assert hit["kind"] == "one-shot" and hit["sounds_like"] == "kick" and "bpm" not in hit
    assert loop["kind"] == "loop" and loop["bpm"]
    hits = samplelib.onset_times(samplelib.onset_envelope(np.tile(_kick()[: FS44 // 2], 8), FS44), FS44)
    assert 7 <= len(hits) <= 8 and all(0.45 < b - a < 0.55 for a, b in zip(hits, hits[1:]))   # the first can hide in the window


def test_kit_warnings_name_what_the_grooves_will_do_wrong(tmp_path):
    """The 90s pop kit: no crash lane (every crash silent), the snare's clap layer was the
    clap lane's sample (doubled on 2 and 4), a sub-only kick the limiter choked on."""
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    t = np.arange(int(0.6 * FS44)) / FS44
    thud, clap, snare, crash = (tmp_path / n for n in ("BD pitched.wav", "clap.wav", "snare.wav", "crash.wav"))
    sf.write(str(thud), 0.8 * np.sin(2 * np.pi * 45 * t) * np.exp(-t * 5) * (1 - np.exp(-t * 60)), FS44)   # swells in
    for p in (clap, snare, crash):
        sf.write(str(p), _hat(), FS44)
    warnings = sample_tools.kit_warnings({"kick": str(thud), "snare": str(snare), "clap": str(clap)},
                                        {"snare": [sample_tools.Layer(path=str(clap), gain_db=-7)]})
    assert [w.split(":")[0] for w in warnings] == [
        "no crash lane", "the snare lane's layer is the clap lane's own sample", "the kick has no attack (its first 10 ms sit 7.1 dB under its body)"]
    sf.write(str(thud), _kick(), FS44)
    assert sample_tools.kit_warnings({"kick": str(thud), "crash": str(crash)}, {"kick": [sample_tools.Layer(path=str(clap))]}) == []


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


def test_a_kit_without_a_crash_or_a_kick_attack_is_filled_from_the_library(tmp_path, monkeypatch):
    """Two songs in a row kept SILA's sub-only LinnDrum kick and no crash lane after being
    warned: now the library fills both, and says so, unless asked not to."""
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    t = np.arange(int(0.4 * FS44)) / FS44
    soft_kick = tmp_path / "BD_sub.wav"
    sf.write(str(soft_kick), 0.8 * np.sin(2 * np.pi * 50 * t) * (1 - np.exp(-t * 60)) * np.exp(-t * 6), FS44)
    punchy, crash, dull = tmp_path / "909 kick.wav", tmp_path / "crash.wav", tmp_path / "boom.wav"
    for p in (punchy, crash, dull):
        sf.write(str(p), _kick(), FS44)
    v = samplelib.ANALYSIS_VERSION
    shelf = {"kick": [{"path": str(dull), "name": "boom", "analysis": {"v": v, "kind": "one-shot", "punch_db": 1.0, "decay_s": 0.2}},
                      {"path": str(punchy), "name": "909 kick", "analysis": {"v": v, "kind": "one-shot", "punch_db": 7.5, "decay_s": 0.2}},
                      {"path": str(soft_kick), "name": "BD_sub", "analysis": {"v": v, "kind": "one-shot", "punch_db": 9.0, "decay_s": 0.9}}],
             "crash": [{"path": str(crash), "name": "crash", "analysis": {"v": v, "kind": "one-shot", "decay_s": 1.8}},
                       {"path": str(dull), "name": "stale", "analysis": {"v": "old", "kind": "one-shot", "decay_s": 3.0}}]}
    monkeypatch.setattr(sample_tools, "library", type("L", (), {"search": lambda self, text=None, role=None, **k: shelf.get(role, [])})())
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_project_overview":
            return {"tracks": [{"name": "Drums"}]}
        if cmd == "build_sampler_kit":
            return {"track": {"name": "Drums"}, "pads": [{"fx": i + 1, "note": p["note"]} for i, p in enumerate(kw["pads"])]}
        return {}
    monkeypatch.setattr(sample_tools, "call", fake_call)
    out = sample_tools.build_drum_kit(track="Drums", samples={"kick": str(soft_kick), "snare": str(dull)}, trim_silence=False)
    pads = next(kw for cmd, kw in calls if cmd == "build_sampler_kit")["pads"]
    assert [p["note"] for p in pads] == [36, 36, 38, 49]                  # the kick, its punch layer, snare, crash
    assert pads[1]["name"] == "kick layer - 909 kick"                      # the punchiest short kick, not the sub itself
    assert "crash" in out["kit"] and "warnings" not in out
    assert len(out["added"]) == 2 and "crash lane added" in out["added"][0] and "909 kick layered under the kick" in out["added"][1]
    calls.clear()
    bare = sample_tools.build_drum_kit(track="Drums", samples={"kick": str(soft_kick), "snare": str(dull)}, trim_silence=False,
                                       fill_gaps=False)
    assert "added" not in bare and len(bare["warnings"]) == 2
    calls.clear()
    kept = sample_tools.build_drum_kit(track="Drums", samples={"kick": str(soft_kick), "snare": str(dull)}, layers={"kick": []},
                                       trim_silence=False)
    assert len(kept["added"]) == 1 and "crash" in kept["added"][0]         # layers={'kick': []} keeps the kick bare


def test_kit_levels_balance_the_lanes_and_trim_the_kit(tmp_path):
    import soundfile as sf
    from creaper import server  # noqa: F401
    from creaper import sample_tools
    kick, hat, crash, cowbell = (tmp_path / n for n in ("kick.wav", "hat.wav", "crash.wav", "cow.wav"))
    sf.write(str(kick), _kick(), FS44)
    sf.write(str(hat), _hat() * 0.1, FS44)             # a hat 20 dB too quiet
    sf.write(str(crash), np.tile(_hat(), 4), FS44)
    sf.write(str(cowbell), _hat(), FS44)
    pads = [{"note": 36, "path": str(kick)}, {"note": 42, "path": str(hat)}, {"note": 49, "path": str(crash)},
            {"note": 56, "path": str(cowbell)}]
    setup = [{"lane": lane, "layer": False, "gain_db": 0.0} for lane in ("kick", "closed hat", "crash", "cowbell")]
    levels = sample_tools.kit_levels(pads, setup)
    against = {lane: v["against_kick_db"] + v["set_db"] - levels["kick"]["set_db"] for lane, v in levels.items()}
    assert against["closed hat"] == pytest.approx(-10, abs=0.1) and against["crash"] == pytest.approx(-8, abs=0.1)
    assert against["cowbell"] == pytest.approx(-8, abs=0.1)        # named in the targets (perc family)
    peaks = {"kick": sample_tools.hit_level_db(str(kick))[1], "closed hat": sample_tools.hit_level_db(str(hat))[1],
             "crash": sample_tools.hit_level_db(str(crash))[1], "cowbell": sample_tools.hit_level_db(str(cowbell))[1]}
    assert max(peaks[lane] + v["set_db"] for lane, v in levels.items()) == pytest.approx(sample_tools.KIT_PEAK_DB, abs=0.01)
    # A clicky sample with a quiet body (a sharp peak, little RMS) is not boosted past the kick's peak by more
    # than PEAK_OVER_KICK_DB, so the trim doesn't drag the whole kit down (a rig kit lost 22 dB that way).
    clicky = tmp_path / "click snare.wav"
    spike = _hat() * 0.02
    spike[0] = 0.99
    sf.write(str(clicky), spike, FS44)
    with_click = sample_tools.kit_levels(pads + [{"note": 38, "path": str(clicky)}],
                                         setup + [{"lane": "snare", "layer": False, "gain_db": 0.0}])
    kick_peak, click_peak = sample_tools.hit_level_db(str(kick))[1], sample_tools.hit_level_db(str(clicky))[1]
    assert with_click["snare"]["set_db"] - with_click["kick"]["set_db"] == pytest.approx(
        kick_peak + sample_tools.PEAK_OVER_KICK_DB - click_peak, abs=0.1)
    assert with_click["kick"]["set_db"] >= -12.5
    # A layer counts toward the kit's peak: a quiet kick with a full-scale punch layer under it.
    quiet_kick = tmp_path / "quiet kick.wav"
    sf.write(str(quiet_kick), _kick() * 0.1, FS44)
    layered = sample_tools.kit_levels(
        [{"note": 36, "path": str(quiet_kick)}, {"note": 36, "path": str(kick)}, {"note": 42, "path": str(hat)}],
        [{"lane": "kick", "layer": False, "gain_db": 0.0}, {"lane": "kick", "layer": True, "gain_db": -3.0},
         {"lane": "closed hat", "layer": False, "gain_db": 0.0}])
    assert sample_tools.hit_level_db(str(kick))[1] - 3 + layered["kick"]["set_db"] == pytest.approx(sample_tools.KIT_PEAK_DB, abs=0.01)
    # The sampler's Volume stops at +12 dB: a lane that would need more is capped and says so.
    faint = tmp_path / "faint hat.wav"
    sf.write(str(faint), _hat() * 0.002, FS44)
    capped = sample_tools.kit_levels(
        [{"note": 36, "path": str(kick)}, {"note": 42, "path": str(faint)}],
        [{"lane": "kick", "layer": False, "gain_db": 0.0}, {"lane": "closed hat", "layer": False, "gain_db": 0.0}])
    assert capped["closed hat"]["set_db"] == sample_tools.RS5K_VOLUME_MAX_DB and capped["closed hat"]["capped"]
    # A silent file (or one whose first seconds are) is moved with the kit, not left at 0 dB.
    silent = tmp_path / "silent.wav"
    sf.write(str(silent), np.zeros(FS44), FS44)
    moved = sample_tools.kit_levels(pads + [{"note": 60, "path": str(silent)}],
                                    setup + [{"lane": "gong", "layer": False, "gain_db": 0.0}])
    assert moved["gong"]["set_db"] == moved["kick"]["set_db"] and moved["gong"]["against_kick_db"] is None
    # No kick: the loudest lane is the reference; a lane the targets don't know sits 6 under.
    other = sample_tools.kit_levels(pads[1:] + [{"note": 60, "path": str(cowbell)}],
                                    setup[1:] + [{"lane": "gong", "layer": False, "gain_db": 0.0}])
    assert other["gong"]["target_db"] == sample_tools.OTHER_LANE_DB and "kick" not in other
    assert sample_tools.kit_levels([], []) == {}
