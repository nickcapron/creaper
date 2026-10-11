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
