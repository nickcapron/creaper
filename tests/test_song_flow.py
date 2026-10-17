"""The song checklist as Claude follows it, across tools: the order of the stages, the
tracks build_song writes onto, a lead for a voice, sections, lengths and roles."""

import pytest
from test_song import FakeReaper, reaper  # noqa: F401  (the fixture)

from creaper import server  # noqa: F401  (import order: server first)
from creaper import ear_tools, mix_tools, song_tools, songmap


def test_the_checklist_opens_the_tab_before_the_plan():
    text = server.INSTRUCTIONS
    assert text.index("new_project_tab") < text.index("start_song(brief")
    sounds = text.index("finish_stage(\"sounds\")")
    assert text.index("Drums, Bass, Chords") < sounds < text.index("build_song(genre, key)")


def test_the_sounds_stage_passes_on_chosen_sounds_before_the_parts(reaper, tmp_path):  # noqa: F811
    reaper.project = str(tmp_path / "song.rpp")
    song_tools.start_song(brief="b", genre="pop", length="3 minutes")
    for name in ("Drums", "Bass", "Chords", "Lead"):
        reaper.add_track(name, instrument="Some Synth")
    rows = song_tools.finish_stage(stage="sounds")["checks"]
    assert len(rows) == 4 and all(r["status"] == "pass" for r in rows)


def test_build_song_says_which_new_tracks_need_a_sound(reaper):  # noqa: F811
    for name in ("Drums", "Bass", "Chords", "Lead"):
        reaper.add_track(name, instrument="Some Synth")
    out = song_tools.build_song(genre="pop", key="C major", seed=1,
                                sections=["Verse:8", "Chorus 1:8", "Verse 2:8", "Chorus 2:8"])
    assert out["needs_sound"] == ["Counter"]
    assert out["tracks"]["lead"] == "Lead"


def test_a_lead_for_a_voice_is_low_and_has_no_counter(reaper):  # noqa: F811
    out = song_tools.build_song(genre="pop", key="C major", seed=5, lead_for="voice",
                                sections=["Verse:8", "Chorus 1:8", "Chorus 2:8"])
    assert "counter" not in out["tracks"]
    lead = [n for i in reaper.items.values() if i["track"]["name"] == "Lead" for n in i["notes"]]
    assert lead and 52 <= min(n["pitch"] for n in lead) and max(n["pitch"] for n in lead) <= 64


def test_nested_regions_are_not_sections_anywhere():
    regions = [{"name": "Verse", "start": {"seconds": 0.0}, "end": {"seconds": 16.0}},
               {"name": "vocals in", "start": {"seconds": 4.0}, "end": {"seconds": 8.0}},
               {"name": "Chorus", "start": {"seconds": 16.0}, "end": {"seconds": 32.0}}]
    assert [s["name"] for s in ear_tools._sections(regions, 0, 40)] == ["Verse", "Chorus"]


@pytest.mark.parametrize("text,bars", [("a 3-minute song", 90), ("three minutes", 90), ("3:30", 105),
                                       ("3-4 minutes", 90), ("16 bars", 16), ("a 30 s loop", 15)])
def test_lengths_as_people_write_them(text, bars):
    assert song_tools.target_bars(text, 120, 4) == bars


def test_the_transitions_track_mixes_as_fx_and_leads_are_found_by_role():
    assert mix_tools.role_of("Transitions") == "fx"
    assert songmap._lead_and_chords(["Drums", "Plucks", "Piano"]) == ("Plucks", "Piano")
    assert songmap._lead_and_chords(["Pad Lead", "Keys"]) == ("Pad Lead", "Keys")
