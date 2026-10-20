from collections import Counter

import pytest
from test_song import reaper  # noqa: F401  (the fixture; imports creaper.server first)

from creaper import genres
from creaper.genres import _template


def test_every_module_loads():
    assert genres.LOAD_ERRORS == {}


def test_template_validates():
    assert genres.validate(_template.GENRES[0]) == []


@pytest.mark.parametrize("genre", genres.GENRES, ids=lambda g: g.name)
def test_every_genre_validates(genre):
    assert genres.validate(genre) == []


def test_names_and_aliases_are_unique():
    names = Counter(genres.norm(n) for g in genres.GENRES for n in (g.name, *g.aliases))
    assert [n for n, c in names.items() if c > 1] == []


def test_find():
    assert genres.find("Deep House").name == "deep house" or genres.find("deep house")
    with pytest.raises(ValueError):
        genres.find("zzzz qqqq")


def test_profiles_give_a_full_track_length():
    from creaper import music_tools
    length = music_tools.get_genre_profile("house")["length"]
    assert length["bars"] == 160 and length["minutes"] == "5:12"


def test_compose_prompt_defaults_to_full_length():
    from creaper import server
    assert "full-length" in server.compose("house")
    assert "a 16-bar piece" in server.compose("house", bars="16")


# ------------------------------------------------------------- eurobeat

def test_eurobeat_is_its_own_style_under_any_of_its_names():
    from creaper import music_tools
    g = genres.find("eurobeat")
    assert genres.validate(g) == []
    for name in ("Super Eurobeat", "Initial D", "initial d style", "euro beat", "90s Eurobeat"):
        assert genres.find(name) is g, name
    assert genres.find("eurodance").name == "eurodance"     # the slower 90s style stays separate
    assert 150 <= g.tempo[0] <= g.tempo_default == 155 <= g.tempo[1] <= 160
    assert g.bass_style == "octaves" and g.fill_style == "snare_roll" and g.melody_density == "busy"
    assert "eurobeat" in [x["genre"] for x in music_tools.list_genres(search="initial d")["genres"]]


def test_eurobeat_harmony_climbs_to_v_and_lifts_the_last_chorus():
    from creaper import music_tools, song_tools
    g = genres.find("eurobeat")
    names = [n for n, _ in song_tools._numbered(list(g.form))]
    plan = {r["section"]: r for r in music_tools.plan_harmony(genre="eurobeat", key="A minor", sections=names,
                                                              lift_last_chorus=True)["sections"]}
    assert plan["Verse 1"]["chords"] == "Am F G Am"
    assert plan["Pre-chorus 1"]["chords"].split()[-1] == "E"     # the major V leans into the chorus
    assert plan["Chorus 1"]["key"] == "A minor" and plan["Chorus 3"]["key"] == "B minor"


def test_eurobeat_builds_a_song_at_its_tempo(reaper):
    from creaper import song_tools
    out = song_tools.build_song(genre="super eurobeat", seed=5, lift_last_chorus=True)
    g = genres.find("eurobeat")
    assert out["genre"] == "eurobeat" and 150 <= reaper.bpm <= 160 and reaper.meter == "4/4"
    assert [r["name"] for r in reaper.regions] == [n for n, _ in song_tools._numbered(list(g.form))]
    assert out["bars"] == sum(b for _, b in g.form)
    assert {s["section"]: s["key"] for s in out["sections"]}["Chorus 3"] == "B minor"
    # The galloping bass: an octave jump between most neighbouring 8ths.
    bass = next(i for i in reaper.items.values() if i["track"]["name"] == "Bass" and "Verse 1" in i["name"])
    pitches = [n["pitch"] for n in sorted(bass["notes"], key=lambda n: n["start"])]
    jumps = sum(abs(a - b) == 12 for a, b in zip(pitches, pitches[1:]))
    assert jumps > len(pitches) / 2
    assert not [f for f in out["song_map"]["findings"] if f["status"] == "fail"], out["song_map"]["findings"]



# ------------------------------------------------------------- sound palettes

def test_palettes_name_real_genres_and_roles():
    from creaper.genres import palettes
    from creaper.sound_tools import ROLES
    for name, p in palettes.PALETTES.items():
        assert genres.find(name).name == name
        assert set(p.sounds) <= set(ROLES), name
        assert set(p.drums) <= {"kick", "snare", "clap", "hat"}, name
    # A genre without its own palette takes its parent's.
    child = next((g for g in genres.GENRES if g.parent in palettes.PALETTES and g.name not in palettes.PALETTES), None)
    if child:
        assert palettes.palette(child) is palettes.PALETTES[child.parent]
    assert palettes.sound_for(genres.find("synthwave"), "pad").subtype == "Classic Synth Pad"


def test_palette_words_exist_in_the_arturia_library():
    import os
    from creaper import arturia
    from creaper.genres import palettes
    if not arturia.default_path().exists() and not os.environ.get("CREAPER_ARTURIA_DB"):
        pytest.skip("Arturia's preset library isn't installed here")
    words = arturia.vocabulary(arturia.connect())
    for name, p in palettes.PALETTES.items():
        for role, s in p.sounds.items():
            assert s.type in words["types"], (name, role, s.type)
            assert s.subtype is None or s.subtype in words["subtypes"], (name, role, s.subtype)
            for c in s.characteristics:
                assert c in words["characteristics"] + words["styles"], (name, role, c)
            assert s.genre is None or s.genre in words["genres"], (name, role, s.genre)


def test_get_genre_profile_shows_the_palette():
    from creaper import music_tools
    profile = music_tools.get_genre_profile("synthwave")
    assert profile["sound_palette"]["by_role"]["bass"]["genre_tag"] == "Synthwave"
    assert "sound_palette" not in music_tools.get_genre_profile("bebop")


def test_outrun_is_its_own_driving_style_not_pop_synthwave():
    from creaper import composer
    from creaper.genres import palettes
    outrun = genres.find("outrun")
    assert outrun.name == "outrun" and outrun.parent == "synthwave"
    assert genres.find("cyberpunk").name == "darksynth"
    # Its peaks are sections build_song writes a hook into, and nothing tells it to lift the key.
    assert "chorus" in {composer.section_kind(name) for name, _ in outrun.form}
    assert "chorus" in {composer.section_kind(name) for name, _ in genres.find("darksynth").form}
    assert "no step-up key change" in outrun.harmony
    synthwave = genres.find("synthwave")
    assert "without shame" not in synthwave.theory and "Lift the last chorus" not in synthwave.harmony
    # Grit in place of the synthwave gloss, and no bells.
    assert palettes.sound_for(outrun, "bass").subtype == "Hard Bass"
    assert palettes.sound_for(outrun, "bell") is None
