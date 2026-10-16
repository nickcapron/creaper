from collections import Counter

import pytest

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
