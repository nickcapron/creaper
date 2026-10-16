"""Per-section levels and drum-lane levels (measure_tracks per_section)."""

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import mix_tools, structure

FS = 22050


def hit(level, seconds=0.06):
    t = np.arange(int(seconds * FS)) / FS
    return level * np.sin(2 * np.pi * 200 * t)


def test_section_balance_flags_parts_out_of_place():
    levels = {"Verse": {"Drums": -12.0, "Snare": -9.0, "Pad": -22.0},
              "Chorus": {"Drums": -10.0, "Snare": -10.0, "Pad": -40.0, "Lead": None}}
    roles = {"Drums": "drums", "Snare": "snare", "Pad": "pad", "Lead": "lead"}
    flags = mix_tools.section_balance(levels, roles)
    # Verse: snare 3 over the drums where it sits 3 under: 6 LU over its place.
    assert any(f.startswith("Verse: Snare is 6.0 LU over its place") for f in flags)
    assert any(f.startswith("Chorus: Pad is 20.0 LU under its place") and "buried" in f for f in flags)
    assert not any("Lead" in f or "Drums" in f for f in flags)


def test_section_balance_without_drums_uses_the_parts_median():
    levels = {"Intro": {"Pad": -20.0, "Keys": -17.0, "Lead": -6.0}}
    flags = mix_tools.section_balance(levels, {"Pad": "pad", "Keys": "keys", "Lead": "lead"})
    assert len(flags) == 1 and flags[0].startswith("Intro: Lead is") and "with the rest" in flags[0]


def test_hit_levels_skip_hits_that_land_with_another_drum():
    mono = np.zeros(4 * FS)
    kick_at, shaker_at = [0.0, 1.0, 2.0], [0.0, 0.5, 1.5, 2.5]   # one shaker hit lands on a kick
    for t in kick_at:
        mono[int(t * FS): int(t * FS) + int(0.06 * FS)] += hit(0.5)
    for t in shaker_at:
        mono[int(t * FS): int(t * FS) + int(0.06 * FS)] += hit(0.4)
    levels, lanes = mix_tools.hit_levels(mono, FS, {"kick": kick_at, "shaker": shaker_at})
    assert lanes == {"silent": [], "with_others": []}
    # 0.5 and 0.4 amplitude sines: -9.0 and -10.9 dB RMS; the doubled hit is left out.
    assert levels["kick"] == pytest.approx(-9.0, abs=0.3)
    assert levels["shaker"] == pytest.approx(-10.9, abs=0.3)
    flags = mix_tools.lane_balance(levels)
    assert len(flags) == 1 and flags[0].startswith("shaker hits are -2") and "overpowering" in flags[0]


def test_silent_lanes_and_lanes_only_heard_with_others():
    mono = np.zeros(4 * FS)
    for t in (0.0, 1.0, 2.0):
        mono[int(t * FS): int(t * FS) + int(0.06 * FS)] += hit(0.5)
    # The clap always lands on a kick; the kit has no hat sound at all (and a silent hat
    # landing on the kick at 0 doesn't make the kick a shared hit).
    levels, lanes = mix_tools.hit_levels(mono, FS, {"kick": [0.0, 1.0, 2.0], "clap": [1.0, 2.0],
                                                    "closed hat": [0.0, 0.5, 1.5, 2.5]})
    assert lanes == {"silent": ["closed hat"], "with_others": ["clap"]}
    assert set(levels) == {"kick", "clap"}
    assert mix_tools.lane_balance({"kick": -9.0, "clap": -30.0}, ["clap"]) == []


def test_lane_balance_needs_a_kick_and_knows_lane_names():
    assert mix_tools.lane_balance({"closed hat": -10.0, "snare": -8.0}) == []
    assert mix_tools.lane_target("Bass Drum 1") == 0 and mix_tools.lane_target("HH open") == -10
    assert mix_tools.lane_target("Cowbell") == -8 and mix_tools.lane_target("pad") is None
    assert mix_tools.lane_balance({"Kick": -6.0, "Snare": -9.0, "Closed Hat": -16.0}) == []


def test_qn_to_seconds_follows_the_tempo_map():
    tempo = {"start_tempo_bpm": 120, "changes": [
        {"position": {"seconds": 0.0, "qn": 0.0}, "bpm": 120},
        {"position": {"seconds": 8.0, "qn": 16.0}, "bpm": 60}]}
    assert structure.qn_to_seconds(tempo, 4) == pytest.approx(2.0)
    assert structure.qn_to_seconds(tempo, 18) == pytest.approx(10.0)
    assert structure.qn_to_seconds({"start_tempo_bpm": 90}, 3) == pytest.approx(2.0)


def test_measure_tracks_per_section(monkeypatch, tmp_path):
    from creaper import ear_tools
    renders = tmp_path / "renders"
    renders.mkdir()
    monkeypatch.setattr(ear_tools.bridge, "directory", tmp_path)
    seconds = 8.0
    n = int(seconds * FS)
    # Drums: kick every 0.5 s at a steady level; a loud shaker on the off-beats.
    drums = np.zeros(n)
    for i in range(16):
        drums[int(i * 0.5 * FS): int(i * 0.5 * FS) + int(0.06 * FS)] += hit(0.5)
        drums[int((i * 0.5 + 0.25) * FS): int((i * 0.5 + 0.25) * FS) + int(0.06 * FS)] += hit(0.45)
    # A pad that's at a fair level in the verse and blasting in the chorus.
    t = np.arange(n) / FS
    pad = np.where(t < 4, 0.05, 0.6) * np.sin(2 * np.pi * 330 * t)

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"tracks": [{"number": 1, "name": "Drums", "item_count": 1}, {"number": 2, "name": "Pad", "item_count": 1}],
                    "regions": [{"name": "Verse", "start": {"seconds": 0.0}, "end": {"seconds": 4.0}},
                                {"name": "Chorus", "start": {"seconds": 4.0}, "end": {"seconds": 8.0}}]}
        if cmd == "render_stems":
            files = []
            for name, x in (("Drums", drums), ("Pad", pad)):
                f = renders / f"{name}.wav"
                sf.write(str(f), np.stack([x, x], axis=1), FS)
                files.append(str(f))
            return {"stems": [{"track": {"number": 1, "name": "Drums"}, "file": files[0]},
                              {"track": {"number": 2, "name": "Pad"}, "file": files[1]}],
                    "files": files, "start": {"seconds": 0.0}, "end": {"seconds": seconds}}
        if cmd == "get_tempo_map":
            return {"start_tempo_bpm": 120, "start_time_signature": "4/4", "changes": []}
        if cmd == "get_track_details":
            return {"items": [{"id": "{A}", "type": "midi", "start": {"seconds": 0.0, "qn": 0.0}}]}
        if cmd == "get_instrument_notes":
            return {"instrument": "Some Kit", "note_names": []}
        if cmd == "get_midi_notes":
            notes = [{"pitch": 36, "start": i * 1.0, "length": 0.25, "channel": 10} for i in range(16)]
            notes += [{"pitch": 70, "start": i * 1.0 + 0.5, "length": 0.25, "channel": 10} for i in range(16)]
            return {"notes": notes}
        raise AssertionError(cmd)

    monkeypatch.setattr(ear_tools, "call", fake_call)
    out = ear_tools.measure_tracks(per_section=True)
    assert set(out["sections"]) == {"Verse", "Chorus"}
    assert out["roles"] == {"Drums": "drums", "Pad": "pad"}
    assert any(f.startswith("Chorus: Pad is") and "over its place" in f for f in out["balance"])
    assert not any(f.startswith("Verse: Pad") for f in out["balance"])
    kit = out["drum_kits"]["Drums"]
    assert set(kit["hit_level_db"]) == {"kick", "shaker"}
    assert any(f.startswith("shaker hits are") and "overpowering" in f for f in kit["findings"])
    assert not list(renders.iterdir())  # the stems are cleaned up


def test_measure_tracks_per_section_without_regions_says_so(monkeypatch, tmp_path):
    from creaper import ear_tools
    renders = tmp_path / "renders"
    renders.mkdir()
    monkeypatch.setattr(ear_tools.bridge, "directory", tmp_path)
    f = renders / "A.wav"
    sf.write(str(f), np.stack([hit(0.3, 2.0)] * 2, axis=1), FS)

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"tracks": [{"number": 1, "name": "A", "item_count": 1}]}
        if cmd == "render_stems":
            return {"stems": [{"track": {"number": 1, "name": "A"}, "file": str(f)}], "files": [str(f)],
                    "start": {"seconds": 0.0}, "end": {"seconds": 2.0}}
        if cmd == "get_tempo_map":
            return {"start_tempo_bpm": 120}
        raise AssertionError(cmd)
    monkeypatch.setattr(ear_tools, "call", fake_call)
    out = ear_tools.measure_tracks(per_section=True)
    assert "A" in out["tracks"] and "sections" not in out and "regions" in out["note"]
