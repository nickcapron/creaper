import numpy as np
import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import genres, structure

FS = 22050
BAR_S = 2.0  # 120 BPM, 4/4


def bar(seed, level=0.3):
    """One bar of eight short notes at random pitches: its own melody and rhythm."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(BAR_S * FS))
    step = out.size // 8
    t = np.arange(step) / FS
    for i in range(8):
        if rng.random() < 0.2:
            continue  # a rest
        f = 110 * 2 ** (rng.integers(0, 36) / 12)
        out[i * step:(i + 1) * step] = np.sin(2 * np.pi * f * t) * np.exp(-t * rng.uniform(3, 12))
    return level * out


def song(seeds, level=0.3):
    return np.concatenate([bar(s, level) for s in seeds])


def measure(mono):
    starts = [i * BAR_S for i in range(int(mono.size / FS / BAR_S))]
    features = structure.bar_features(mono, FS, starts, len(starts) * BAR_S)
    return structure.repetition(features, structure.silent_bars(mono, FS, starts, len(starts) * BAR_S)), features, starts


def test_one_4_bar_loop_repeated_scores_as_a_loop():
    rep, _, _ = measure(song([0, 1, 2, 3] * 16))
    assert rep["bars"] == 64
    assert rep["near_duplicate_share"] >= 0.9
    assert rep["longest_loop_bars"] == 64


def test_a_song_that_varies_every_4_bars_scores_low():
    rep, _, _ = measure(song(range(64)))
    assert rep["near_duplicate_share"] < 0.2
    assert rep["longest_loop_bars"] == 4


def test_a_held_chord_over_two_bars_is_not_a_loop():
    # Neighbouring bars alike (a sustained chord) don't count as repetition.
    held = np.concatenate([np.tile(bar(s), 2) for s in range(16)])
    assert measure(held)[0]["near_duplicate_share"] < 0.2


def test_silent_bars_are_left_out():
    mono = np.concatenate([song(range(12)), np.zeros(int(8 * BAR_S * FS))])
    rep, _, _ = measure(mono)
    assert rep["bars"] == 12
    assert rep["near_duplicate_share"] < 0.2


def test_bar_starts_follow_tempo_and_meter_changes():
    tempo = {"start_tempo_bpm": 120, "start_time_signature": "4/4", "changes": [
        {"position": {"seconds": 0.0, "bar": 1}, "bpm": 120, "time_signature": "4/4"},
        {"position": {"seconds": 4.0, "bar": 3}, "bpm": 60},
        {"position": {"seconds": 12.0, "bar": 5}, "time_signature": "7/8"},
    ]}
    starts = structure.bar_starts(tempo, 22.0)
    # Two 2 s bars at 120, two 4 s bars at 60, then 7/8 at 60: 3.5 s.
    assert starts == pytest.approx([0, 2, 4, 8, 12, 15.5, 19])


def test_sections_show_the_energy_arc_and_copies():
    verse, chorus = song(range(8), 0.1), song(range(100, 108), 0.1)  # the chorus doesn't lift
    mono = np.concatenate([verse, chorus, chorus])
    starts = [i * BAR_S for i in range(24)]
    features = structure.bar_features(mono, FS, starts, 24 * BAR_S)
    sections = [{"name": "Verse", "start": 0, "end": 16}, {"name": "Chorus", "start": 16, "end": 32},
                {"name": "Chorus 2", "start": 32, "end": 48}]
    table = structure.section_table(sections, starts, features, np.stack([mono, mono], axis=1), FS, 0.0)
    assert [r["bars"] for r in table] == [8, 8, 8]
    assert [r["energy"] for r in table] == [2, 4, 4]
    assert table[2]["same_as"] == "Chorus" and "same_as" not in table[1]
    problems = structure.arc_problems(table)
    assert len(problems) == 1 and problems[0].startswith("Chorus should lift from Verse")
    rep = structure.repetition(features)
    findings = structure.judge(rep, table, 24, structure.form_bars(genres.find("house")))
    assert any("plays like Chorus" in f for f in findings)
    assert any("bars the genre's form runs to" in f for f in findings)


def test_a_chorus_that_lifts_passes():
    mono = np.concatenate([song(range(8), 0.1), song(range(100, 108), 0.2)])
    starts = [i * BAR_S for i in range(16)]
    features = structure.bar_features(mono, FS, starts, 16 * BAR_S)
    table = structure.section_table([{"name": "verse", "start": 0, "end": 16}, {"name": "chorus", "start": 16, "end": 32}],
                                    starts, features, mono[:, None], FS, 0.0)
    assert structure.arc_problems(table) == []
    assert table[1]["lufs"] - table[0]["lufs"] == pytest.approx(6, abs=0.5)


def test_measure_structure_tool_reads_regions_and_bars(monkeypatch):
    from creaper import ear_tools

    mono = np.concatenate([song(range(8), 0.1), song([50, 51, 52, 53] * 4, 0.2)])
    audio = np.stack([mono, mono], axis=1)

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"regions": [{"name": "Verse", "start": {"seconds": 0.0}, "end": {"seconds": 16.0}},
                                {"name": "Drop", "start": {"seconds": 16.0}, "end": {"seconds": 48.0}}]}
        if cmd == "get_tempo_map":
            return {"start_tempo_bpm": 120, "start_time_signature": "4/4", "changes": []}
        raise AssertionError(cmd)

    monkeypatch.setattr(ear_tools, "call", fake_call)
    monkeypatch.setattr(ear_tools, "_render", lambda *a: (audio, FS, {"start": {"seconds": 0.0}}))
    out = ear_tools.measure_structure(genre="house")
    assert out["bars"] == {"from": 1, "to": 24, "count": 24}
    # A bar of ring-out past the last region (REAPER's project end running on) isn't a bar of song.
    audio = np.concatenate([audio, 0.3 * audio[: int(BAR_S * FS)]])
    assert ear_tools.measure_structure()["bars"]["count"] == 24
    assert [s["name"] for s in out["sections"]] == ["Verse", "Drop"]
    assert out["genre_form_bars"] == structure.form_bars(genres.find("house"))
    assert out["longest_loop_bars"] == 16  # the drop is one 4-bar loop played four times
    assert any("bars the genre's form runs to" in f for f in out["findings"])


def test_one_bar_repeated_is_still_a_loop():
    rep, _, _ = measure(song([7] * 32))
    assert rep["near_duplicate_share"] >= 0.9 and rep["longest_loop_bars"] >= 24


def test_a_marker_rounded_past_the_bar_line_still_counts():
    # 95 BPM: bar 9 starts at 20.2105 s, and the bridge reports the marker as 20.211.
    bar95 = 240 / 95
    tempo = {"start_tempo_bpm": 95, "start_time_signature": "4/4", "changes": [
        {"position": {"seconds": round(8 * bar95, 3), "bar": 9}, "bpm": 140}]}
    starts = structure.bar_starts(tempo, 30.0)
    assert starts[9] == pytest.approx(8 * bar95 + 240 / 140, abs=1e-3)


def test_silence_after_the_music_doesnt_make_it_a_loop():
    music = song(range(16))
    for extra in (0, 8, 20):
        mono = np.concatenate([music, np.zeros(int(extra * BAR_S * FS))])
        rep, _, _ = measure(mono)
        assert rep["near_duplicate_share"] < 0.2 and rep["longest_loop_bars"] == 4, extra


def test_a_ringing_tail_bar_isnt_counted():
    mono = np.concatenate([song(range(8)), bar(99, 0.3 * 10 ** (-30 / 20))])
    starts = [i * BAR_S for i in range(9)]
    assert structure.tail_bars(mono, FS, starts, 9 * BAR_S) == 1
    assert structure.tail_bars(song(range(9)), FS, starts, 9 * BAR_S) == 0


def test_a_humanised_loop_still_reads_as_a_loop():
    def played(seed, take):
        # The same bar, each repeat with its own velocities (+-3 dB) and up to 10 ms late.
        rng, human = np.random.default_rng(seed), np.random.default_rng(1000 + take)
        out = np.zeros(int(BAR_S * FS))
        step = out.size // 8
        t = np.arange(step) / FS
        for i in range(8):
            if rng.random() < 0.2:
                continue
            f = 110 * 2 ** (rng.integers(0, 36) / 12)
            gain, late = 10 ** (human.uniform(-3, 3) / 20), int(human.uniform(0, 0.01) * FS)
            note = gain * np.sin(2 * np.pi * f * t) * np.exp(-t * rng.uniform(3, 12))
            out[i * step + late:(i + 1) * step] = note[: step - late]
        return 0.3 * out
    rep, _, _ = measure(np.concatenate([played(k % 4, k) for k in range(64)]))
    assert rep["near_duplicate_share"] >= 0.6
