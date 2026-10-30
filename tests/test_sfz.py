"""SFZ instruments, WAV loop points, and velocity layers and round robins from names."""

import struct

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import sample_tools, sfz


def tone(path, midi, seconds=1.0, fs=22050, loop=None, unity=None):
    t = np.arange(int(fs * seconds)) / fs
    x = 0.5 * np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t)
    sf.write(str(path), x.astype(np.float32), fs, subtype="PCM_16")
    if loop is not None or unity is not None:
        data = struct.pack("<9I", 0, 0, int(1e9 / fs), unity or 60, 0, 0, 0, 1 if loop else 0, 0)
        if loop:
            data += struct.pack("<6I", 0, 0, loop[0], loop[1], 0, 0)
        chunk = b"smpl" + struct.pack("<I", len(data)) + data
        raw = bytearray(path.read_bytes()) + chunk
        raw[4:8] = struct.pack("<I", len(raw) - 8)
        path.write_bytes(bytes(raw))
    return path


def test_note_names_follow_sfz():
    assert sfz.note_value("c4") == 60 and sfz.note_value("C#4") == 61 and sfz.note_value("db4") == 61
    assert sfz.note_value("a-1") == 9 and sfz.note_value(72) == 72 and sfz.note_value("64") == 64
    with pytest.raises(ValueError):
        sfz.note_value("h4")


def test_regions_inherit_their_headers(tmp_path):
    (tmp_path / "inc.sfz").write_text("<region> sample=Choir Ah C5.wav key=c5\n")
    text = """
    // a comment
    #define $LOOP loop_continuous
    <control> default_path=samples/
    <global> ampeg_release=0.4 loop_mode=$LOOP
    <group> lovel=1 hivel=63 seq_length=2
    <region> sample=Ah p C4 rr1.wav lokey=b3 hikey=c#4 pitch_keycenter=c4 seq_position=1
    <region> sample=Ah p C4 rr2.wav lokey=b3 hikey=c#4 pitch_keycenter=c4 seq_position=2
    /* a block
       comment */
    <group> lovel=64 hivel=127
    <region> sample=Ah f C4.wav lokey=b3 hikey=c#4 pitch_keycenter=c4 transpose=12 tune=-30 loop_mode=no_loop
    <region> sample=rel.wav key=60 trigger=release
    #include "inc.sfz"
    """
    regions = sfz.parse(text, tmp_path)
    assert len(regions) == 5
    first = regions[0]
    assert first["path"] == str((tmp_path / "samples" / "Ah p C4 rr1.wav").resolve())
    assert first["loop_mode"] == "loop_continuous" and first["hivel"] == "63" and first["ampeg_release"] == "0.4"
    assert regions[2]["lovel"] == "64" and "seq_length" not in regions[2]     # a new group resets the old one
    assert regions[4]["path"].endswith("Choir Ah C5.wav")
    zones = sfz.zones(regions)
    by_vel = {(z["lo"], z.get("lovel")): z for z in zones}
    soft = by_vel[(59, 1)]
    assert soft["hi"] == 61 and soft["hivel"] == 63 and len(soft["files"]) == 2
    assert soft["files"][0].endswith("rr1.wav") and soft["root"] == 60
    loud = by_vel[(59, 64)]
    assert loud["root"] == pytest.approx(60 - 12 + 0.3) and "files" not in loud
    assert not any(z["path"].endswith("rel.wav") for z in zones)             # release triggers left out
    assert any(z["lo"] == z["hi"] == 72 for z in zones)                      # key= sets the range and root


def test_wav_loops_come_from_the_smpl_chunk(tmp_path):
    looped = tone(tmp_path / "pad C3.wav", 48, loop=(4410, 17640), unity=48)
    assert sfz.wav_loop(str(looped)) == {"start": 4410, "end": 17640, "unity_note": 48}
    assert sfz.wav_loop(str(tone(tmp_path / "plain.wav", 48))) is None
    fields = sfz.loop_fields((4410, 17640), 22050, 22050)["loop"]
    assert fields["start_ms"] == pytest.approx(200.0) and fields["end_frac"] == pytest.approx(17641 / 22050)
    regions = sfz.parse(f"<region> sample={looped.name} lokey=40 hikey=56", tmp_path)
    z = sfz.zones(regions, sample_tools._frames)[0]
    assert z["root"] == 48 and z["loop"]["start_ms"] == pytest.approx(200.0)   # unity note and loop, no opcodes
    regions = sfz.parse(f"<region> sample={looped.name} key=48 loop_mode=no_loop", tmp_path)
    assert "loop" not in sfz.zones(regions, sample_tools._frames)[0]


def test_names_give_velocity_layers_and_round_robins():
    assert sfz.name_layers("Violin_C4_pp_rr2.wav") == ("Violin_C4", 1, 2)
    assert sfz.name_layers("Choir Ah Soft C3.wav") == ("Choir_Ah_C3", 2, None)
    assert sfz.name_layers("Cello-G2-ff.wav") == ("Cello_G2", 6, None)
    assert sfz.name_layers("Piano_C4_v3.wav") == ("Piano_C4", 3, None)
    assert sfz.name_layers("Brass F4.wav") == ("Brass_F4", None, None)        # a capital F is the note
    assert sfz.velocity_ranges([1, 6, 3]) == {1: (1, 42), 3: (43, 85), 6: (86, 127)}


def _fake_bridge(monkeypatch):
    sent = {}

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"tracks": []}
        if cmd == "create_track":
            return {}
        if cmd == "build_sampled_instrument":
            sent.update(kw)
            return {"track": {"name": kw["track"]}, "zones": [{"fx": i + 1} for i in range(len(kw["zones"]))],
                    "gain_db": kw.get("gain_db") if sent.get("_bridge_knows_gain", True) else None}
        if cmd == "set_fx_parameters":
            sent.setdefault("volumes", []).append((kw["fx"], kw["changes"]))
            return {}
        raise AssertionError(cmd)

    monkeypatch.setattr(sample_tools, "call", fake_call)
    return sent


def test_an_sfz_file_builds_its_zones(monkeypatch, tmp_path):
    for name, midi in (("A C3 rr1.wav", 48), ("A C3 rr2.wav", 48), ("A C4.wav", 60)):
        tone(tmp_path / name, midi)
    (tmp_path / "choir.sfz").write_text(
        "<group> loop_mode=no_loop\n"
        "<region> sample=A C3 rr1.wav lokey=40 hikey=54 pitch_keycenter=48 seq_position=1\n"
        "<region> sample=A C3 rr2.wav lokey=40 hikey=54 pitch_keycenter=48 seq_position=2\n"
        "<region> sample=A C4.wav lokey=55 hikey=70 pitch_keycenter=60\n")
    sent = _fake_bridge(monkeypatch)
    out = sample_tools.build_sampled_instrument(track="Choir", sfz_path=str(tmp_path / "choir.sfz"))
    assert [(z["lo"], z["hi"]) for z in sent["zones"]] == [(40, 54), (55, 70)]
    assert len(sent["zones"][0]["files"]) == 2 and out["zones"][0]["round_robin"] == 2
    assert out["sfz"] == "choir.sfz" and out["plays"] == "E2 to A#4"
    with pytest.raises(ValueError, match="missing"):
        (tmp_path / "broken.sfz").write_text("<region> sample=nope.wav key=60\n")
        sample_tools.build_sampled_instrument(track="Choir", sfz_path=str(tmp_path / "broken.sfz"))
    with pytest.raises(ValueError, match="samples, or an .sfz"):
        sample_tools.build_sampled_instrument(track="Choir")


def test_named_layers_and_round_robins_build_from_samples(monkeypatch, tmp_path):
    files = []
    for midi, note in ((48, "C3"), (60, "C4")):
        for dyn in ("pp", "ff"):
            for rr in (1, 2):
                files.append(str(tone(tmp_path / f"Viola_{note}_{dyn}_rr{rr}.wav", midi, seconds=0.6)))
    files.append(str(tone(tmp_path / "Viola_C5_pp.wav", 72, seconds=0.6, loop=(1000, 9000))))
    sent = _fake_bridge(monkeypatch)
    out = sample_tools.build_sampled_instrument(track="Viola", samples=files)
    zones = sent["zones"]
    assert out["velocity_layers"] == 2
    c3 = [z for z in zones if z["lo"] <= 48 <= z["hi"]]
    assert sorted((z["lovel"], z["hivel"]) for z in c3) == [(1, 64), (65, 127)]
    assert all(len(z["files"]) == 2 for z in c3)
    c5 = next(z for z in zones if z["lo"] <= 72 <= z["hi"])
    assert "lovel" not in c5                                     # recorded soft only: it plays at every velocity
    assert c5["loop"]["start_ms"] == pytest.approx(1000 / 22050 * 1000, rel=1e-3)
    # The instrument comes out at a known level: the tones peak at 0.5 (-6 dBFS), so every sampler is set -4 dB.
    assert sent["gain_db"] == pytest.approx(sample_tools.INSTRUMENT_PEAK_DB + 6.0, abs=0.15)
    assert "peaks at -6 dBFS" in out["level"] and "volumes" not in sent     # the bridge took the gain itself


def test_an_older_bridge_gets_the_samplers_volumes_set_one_by_one(monkeypatch, tmp_path):
    files = [str(tone(tmp_path / f"Banjo_{n}.wav", m, seconds=0.6)) for n, m in (("D3", 50), ("D4", 62))]
    sent = _fake_bridge(monkeypatch)
    sent["_bridge_knows_gain"] = False
    out = sample_tools.build_sampled_instrument(track="Banjo", samples=files)
    assert [fx for fx, _ in sent["volumes"]] == [1, 2]
    assert all(ch == [{"parameter": "Volume", "display_value": sent["gain_db"]}] for _, ch in sent["volumes"])
    assert sample_tools.instrument_level([{"path": files[0]}])["trim_db"] == pytest.approx(-4.0, abs=0.15)
    assert sample_tools.instrument_level([{"path": str(tmp_path / "missing.wav")}]) is None
    assert "level" in out



# ------------------------------------------------------------- review regressions

def test_keyswitches_and_controller_layers_aren_t_round_robins(tmp_path):
    text = """
    <global> sw_default=24
    <group> sw_last=24
    <region> sample=sus.wav key=60
    <group> sw_last=26
    <region> sample=stac.wav key=60
    <group> locc1=0 hicc1=63
    <region> sample=pp.wav key=61
    <group> locc1=64 hicc1=127
    <region> sample=ff.wav key=61
    <group> lorand=0 hirand=0.5
    <region> sample=a.wav key=62
    <group> lorand=0.5 hirand=1
    <region> sample=b.wav key=62
    <region> sample=*sine key=63
    """
    zones = {z["lo"]: z for z in sfz.zones(sfz.parse(text, tmp_path))}
    assert zones[60]["path"].endswith("sus.wav") and "files" not in zones[60]   # the default articulation
    assert zones[61]["path"].endswith("pp.wav") and "files" not in zones[61]    # the CC1 = 0 layer
    assert len(zones[62]["files"]) == 2                                         # random takes: round robins
    assert 63 not in zones                                                     # a generator, not a sample


def lines(*rows):
    return "\n".join(rows) + "\n"


def test_defines_reach_includes_and_regions_keep_their_own_ranges(tmp_path):
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "inc.sfz").write_text(lines("<region> sample=a.wav key=$KC", '#include "parts/inc2.sfz"'))
    (tmp_path / "parts" / "inc2.sfz").write_text(lines("<region> sample=b.wav key=$KC2"))
    text = lines("#define $KC 60", "#define $KC2 62", '#include "parts/inc.sfz"')
    keys = sorted(z["lo"] for z in sfz.zones(sfz.parse(text, tmp_path)))
    assert keys == [60, 62]                                       # nested include from the root's folder
    text = lines("<group> key=60", "<region> sample=a.wav lokey=48 hikey=59", "<region> sample=b.wav lokey=60 hikey=72")
    spans = sorted((z["lo"], z["hi"]) for z in sfz.zones(sfz.parse(text, tmp_path)))
    assert spans == [(48, 59), (60, 72)]
    text = lines("<global> ampeg_release=1", "<control> default_path=Samples/",
                 "<region> sample=a.wav key=60 lovel=1.0 hivel=64.0")
    r = sfz.parse(text, tmp_path)[0]
    assert r["ampeg_release"] == "1" and r["path"].endswith("a.wav") and "Samples" in r["path"]
    assert sfz.zones([r])[0]["hivel"] == 64


def test_a_missing_release_sample_doesn_t_block_the_instrument(tmp_path):
    tone(tmp_path / "a.wav", 60)
    (tmp_path / "i.sfz").write_text(lines("<region> sample=a.wav key=60",
                                          "<region> sample=gone.wav key=60 trigger=release"))
    assert len(sfz.load(str(tmp_path / "i.sfz"))) == 1


def swell(path, midi, ms, seconds=1.5, fs=22050):
    """A bowed sustain: silent for 20 ms, then rising to full level over ms."""
    t = np.arange(int(fs * seconds)) / fs
    x = 0.5 * np.sin(2 * np.pi * 440 * 2 ** ((midi - 69) / 12) * t) * np.clip((t - 0.02) / (ms / 1000), 0, 1)
    sf.write(str(path), x.astype(np.float32), fs, subtype="PCM_16")
    return path


def test_slow_onsets_are_trimmed_for_a_moving_line(monkeypatch, tmp_path):
    # Public Inquiry: VSCO cello section sustains swelled in over 135-215 ms; as a solo line at 72 BPM
    # they read 'kinda fake' until each sampler's start was moved past most of the swell.
    files = [str(swell(tmp_path / f"Cello_{n}.wav", m, 300)) for n, m in (("C2", 36), ("C3", 48))]
    sent = _fake_bridge(monkeypatch)
    out = sample_tools.build_sampled_instrument(track="Cello", samples=files)
    assert "tighten_attack_ms=50" in out["attack"] and not any("start_frac" in z for z in sent["zones"])
    # A bow that speaks at once and then keeps swelling for seconds (Karoryfer's solo cello) isn't slow.
    t = np.arange(int(22050 * 4.0)) / 22050
    bow = np.sin(2 * np.pi * 130.8 * t) * np.clip(t / 0.02, 0, 1) * (0.25 + 0.25 * np.clip(t / 3.0, 0, 1))
    sf.write(str(tmp_path / "Bow_C3.wav"), bow.astype(np.float32), 22050, subtype="PCM_16")
    assert sample_tools.onset(str(tmp_path / "Bow_C3.wav"))[1] < 30
    sent = _fake_bridge(monkeypatch)                     # this fake bridge doesn't report trims: set from here
    out = sample_tools.build_sampled_instrument(track="Cello", samples=files, tighten_attack_ms=50)
    z = sent["zones"][0]
    assert z["attack_ms"] == sample_tools.TRIM_FADE_MS
    start_s = z["start_frac"] * 1.5                      # the file is 1.5 s; it speaks (half its level) at ~170 ms
    assert 0.11 < start_s < 0.13                         # so it starts 50 ms before that
    assert "2 of 2 zones trimmed" in out["attack"]
    offsets = [ch for _, ch in sent["volumes"] if ch[0]["parameter"] == "Sample start offset"]
    assert len(offsets) == 2 and offsets[0][1] == {"parameter": "Attack", "display_value": sample_tools.TRIM_FADE_MS}
    quick = [str(tone(tmp_path / "Pluck_C3.wav", 48))]   # already speaks at once: left alone, no advice
    sent = _fake_bridge(monkeypatch)
    out = sample_tools.build_sampled_instrument(track="Pluck", samples=quick, tighten_attack_ms=50)
    assert "start_frac" not in sent["zones"][0] and "0 of 1 zones trimmed" in out["attack"]
    assert "attack" not in sample_tools.build_sampled_instrument(track="Pluck", samples=quick)
