"""check_groove: does a MIDI part play like a performance or a machine."""

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import feel

BAR, BEAT, BPM = 4.0, 1.0, 120.0
JOBS = {36: "kick", 38: "backbeat", 42: "hats"}


def grid_beat(bars=16, velocity=100):
    """Four-on-the-floor kick, backbeat snare, 8th hats, all on the grid at one velocity."""
    notes = []
    for b in range(bars):
        for i in range(4):
            notes.append({"pitch": 36, "start": b * BAR + i, "length": 0.25, "velocity": velocity})
        for i in (1, 3):
            notes.append({"pitch": 38, "start": b * BAR + i, "length": 0.25, "velocity": velocity})
        for i in range(8):
            notes.append({"pitch": 42, "start": b * BAR + i / 2, "length": 0.25, "velocity": velocity})
    return notes


def test_grid_output_fails():
    report = feel.check_groove(grid_beat(), BAR, BEAT, BPM, JOBS)
    assert report["verdict"] == "fail"
    assert report["timing"]["on_grid_share"] == 1.0
    assert "plays like a machine" in report["findings"][0]
    assert report["bars_same_as_previous"] == 1.0
    assert any("repeat the bar before" in f for f in report["findings"])


@pytest.mark.parametrize("name", ["natural", "laid back", "tight"])
def test_feel_apply_output_passes(name):
    played = feel.apply(grid_beat(), "drums", name, bpm=BPM, seed=3)
    report = feel.check_groove(played, BAR, BEAT, BPM, JOBS)
    assert report["verdict"] != "fail"
    assert all(sd >= feel.FLAT_VELOCITY_SD for lane, sd in report["velocity_spread"].items() if lane == "hats")
    assert not any("machine" in f for f in report["findings"])
    # Feel moves notes by milliseconds, not grid steps: the bars still read as repeats.
    assert report["bars_same_as_previous"] == 1.0


def test_tight_feel_is_called_on_the_grid_with_accents():
    played = feel.apply(grid_beat(), "drums", "tight", bpm=BPM, seed=1)
    report = feel.check_groove(played, BAR, BEAT, BPM, JOBS)
    if report["timing"]["on_grid_share"] >= feel.ROBOTIC_SHARE:
        assert any("programmed electronic" in f for f in report["findings"])


def test_swing_is_measured_against_the_genre():
    straight = feel.check_groove(feel.apply(grid_beat(), "drums", "natural", bpm=BPM, seed=2), BAR, BEAT, BPM, JOBS,
                                 genre_swing=66)
    assert straight["swing_8ths_pct"] == pytest.approx(50, abs=3)
    assert any("swing is" in f for f in straight["findings"])
    swung = [dict(n, start=n["start"] + (1 / 6 if round(n["start"] * 2) % 2 else 0)) for n in grid_beat()]
    swung = feel.apply(swung, "drums", "natural", bpm=BPM, seed=2)
    report = feel.check_groove(swung, BAR, BEAT, BPM, JOBS, genre_swing=66)
    assert report["swing_8ths_pct"] == pytest.approx(66.7, abs=3)
    assert not any("swing is" in f for f in report["findings"])


def test_a_missing_fill_before_a_section_is_named():
    notes = grid_beat(16)
    report = feel.check_groove(notes, BAR, BEAT, BPM, JOBS, sections=[("Chorus", 9)])
    assert report["no_fill_into"] == ["Chorus (bar 9)"]
    # A snare roll in bar 8 is a fill.
    notes = [n for n in notes if not (7 * BAR <= n["start"] < 8 * BAR and n["pitch"] == 38)]
    notes += [{"pitch": 38, "start": 7 * BAR + 2 + i / 4, "length": 0.2, "velocity": 70 + 6 * i} for i in range(8)]
    report = feel.check_groove(notes, BAR, BEAT, BPM, JOBS, sections=[("Chorus", 9)])
    assert "no_fill_into" not in report


def test_too_few_notes():
    assert feel.check_groove(grid_beat(1)[:4], BAR, BEAT, BPM)["verdict"] == "n/a"


def test_check_groove_tool(monkeypatch):
    from creaper import ear_tools

    notes = grid_beat(8)

    def fake_call(cmd, **kw):
        if cmd == "get_project_overview":
            return {"time_signature": "4/4", "tempo_bpm": 120,
                    "regions": [{"name": "Verse", "start": {"bar": 1}}, {"name": "Drop", "start": {"bar": 5}}]}
        if cmd == "get_track_details":
            return {"name": "Drums", "items": [{"id": "{A}", "type": "midi", "start": {"qn": 0.0}}]}
        if cmd == "get_instrument_notes":
            return {"instrument": "Kit", "note_names": []}
        if cmd == "get_midi_notes":
            return {"notes": notes}
        raise AssertionError(cmd)

    monkeypatch.setattr(ear_tools, "call", fake_call)
    out = ear_tools.check_groove("Drums", genre="house")
    assert out["role"] == "drums" and out["verdict"] == "fail"
    assert set(out["velocity_spread"]) == {"kick", "backbeat", "hats"}
    assert out["no_fill_into"] == ["Drop (bar 5)"]
    assert "genre_swing" in out
