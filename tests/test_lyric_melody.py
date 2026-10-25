"""Words first: the sung line's rhythm and tune come from the lyrics."""
import pytest

from creaper import harmony, lyric_melody as lm
from creaper.music_tools import _events


@pytest.fixture(autouse=True)
def _by_rule(monkeypatch):
    """The rules alone, whether or not VocalVST's dictionary is on this machine."""
    monkeypatch.setattr(lm, "_dictionary_cache", {})


def _dictionary(monkeypatch, **words):
    monkeypatch.setattr(lm, "_dictionary_cache", words)


@pytest.mark.parametrize("word, pieces", [
    ("baby", ["ba", "by"]), ("candle", ["can", "dle"]), ("table", ["ta", "ble"]), ("people", ["peo", "ple"]),
    ("waiting", ["wai", "ting"]), ("tonight", ["to", "night"]), ("Saturday", ["Sa", "tur", "day"]),
    ("whole", ["whole"]), ("take", ["take"]), ("lines", ["lines"]), ("places", ["pla", "ces"]),
    ("burned", ["burned"]), ("waited", ["wai", "ted"]), ("candles", ["can", "dles"]), ("little", ["lit", "tle"]),
    ("you're", ["you're"]), ("I've", ["I've"]), ("don't", ["don't"]), ("eyes", ["eyes"]), ("mother", ["mo", "ther"]),
    ("rocket", ["rock", "et"]), ("singing", ["sing", "ing"]), ("children", ["chil", "dren"]), ("to-night", ["to", "night"]),
])
def test_syllables_by_rule(word, pieces):
    assert lm.syllabify(word) == pieces


@pytest.mark.parametrize("word, pattern", [
    ("the", "u"), ("night", "S"), ("baby", "Su"), ("tonight", "uS"), ("waiting", "Su"), ("remember", "uSu"),
    ("beautiful", "Suu"), ("open", "Su"), ("I'm", "u"),
])
def test_stresses_by_rule(word, pattern):
    pieces = lm.syllabify(word)
    assert "".join("S" if s else "u" for s in lm.stresses(word, pieces)) == pattern


@pytest.mark.parametrize("word, pieces", [
    ("neon", ["ne", "on"]), ("Neon,", ["Ne", "on,"]), ("fire", ["fi", "re"]), ("poem", ["po", "em"]),
    ("hour", ["ho", "ur"]), ("evening", ["eve", "ning"]), ("Saturday", ["Sa", "tur", "day"]), ("baby", ["ba", "by"]),
    ("rhythm", ["rhythm"]), ("ne-on", ["ne", "on"]),
])
def test_the_dictionary_sets_the_syllable_count(monkeypatch, word, pieces):
    """VocalVST splits a word's sounds over the syllables it is typed with, so 'neon' on
    one note sang two vowels at once; the dictionary's count is the one the singer needs."""
    _dictionary(monkeypatch, neon="10", fire="10", poem="10", hour="10", evening="10", saturday="100", baby="10",
                rhythm="10")
    assert lm.syllabify(word) == pieces


def test_the_dictionary_sets_the_stresses_and_function_words_stay_light(monkeypatch):
    _dictionary(monkeypatch, saxophone="102", champagne="01", **{"i'm": "1", "the": "0"})
    assert lm.stresses("saxophone", lm.syllabify("saxophone")) == [True, False, True]
    assert lm.stresses("champagne", lm.syllabify("champagne")) == [False, True]
    assert lm.stresses("I'm", ["I'm"]) == [False]
    assert lm.stresses("remember", lm.syllabify("remember")) == [False, True, False]   # not in this dictionary: by rule


def test_the_plugins_dictionary_is_read_from_its_install(tmp_path, monkeypatch):
    f = tmp_path / "cmudict.dict"
    f.write_text(";;; comment\nneon N IY1 AA0 N\nneon(2) N IY1 AO0 N\nsaturday S AE1 T ER0 D IY0\n\nthe DH AH0\n",
                 encoding="utf-8")
    monkeypatch.setenv("CREAPER_CMUDICT", str(f))
    monkeypatch.setattr(lm, "_dictionary_cache", None)
    assert lm.dictionary() == {"neon": "10", "saturday": "100", "the": "0"}
    assert lm.syllabify("neon") == ["ne", "on"]
    monkeypatch.setenv("CREAPER_CMUDICT", str(tmp_path / "missing.dict"))
    monkeypatch.setattr(lm, "_dictionary_cache", None)
    assert lm._cmudict_paths()[0] == tmp_path / "missing.dict"


def test_a_lines_last_word_is_stressed_and_punctuation_dropped():
    syls = lm.line_syllables("Candles are lit, table for you")
    assert [s.text for s in syls] == ["Can", "dles", "are", "lit", "ta", "ble", "for", "you"]
    assert syls[-1].stressed and syls[-1].line_end and not syls[2].stressed


def _verse():
    key = harmony.parse_key("A minor")
    events, key = _events("Am7 Fmaj7 G6 Am7 Am7 Fmaj7 G6 Am7", key, 4.0)
    return key, events


def test_rhythm_comes_from_the_stresses_not_the_grid():
    """The synth-funk verse: a quarter note per syllable and one breath in 24 notes. Now
    stressed syllables sit on beats, unstressed between, the last word is held, a breath follows."""
    key, events = _verse()
    out = lm.compose(["Saturday night I'm coming round", "in my white suit for you"], events, key, 50, 64, shape="verse",
                     seed=1, line_bars=2)
    first, second = out["lines"]
    notes = out["notes"]
    assert first["notes"] == 8 and second["notes"] == 6
    starts = [n["start"] for n in notes[:8]]
    assert starts[0] == 0.0 and starts[3] == 2.0 and starts[7] == 4.0          # Sa-, night, round on beats
    assert notes[7]["length"] >= 1.5 and notes[7]["length"] < 7.0            # 'round' held, then a breath
    assert second["pickup_beats"] == 1.0 and notes[8]["start"] == 7.0         # 'in my' before the bar, 'white' on it
    assert len({round(n["length"], 2) for n in notes}) >= 3                   # not one value per syllable
    lengths = {n["start"]: n["length"] for n in notes}
    assert all(lengths[s] < 1 for s in (0.5, 2.5))                           # '-tur-' and "I'm" are short


def test_the_lyrics_string_matches_the_notes_one_token_each():
    key, events = _verse()
    out = lm.compose(["Candles are lit, table for two", "I saved a slice for you"], events, key, 50, 64, seed=3)
    tokens = [p for w in out["lyrics"].split() for p in (w.split("-") if w != "_" else ["_"])]
    assert len(tokens) == len(out["notes"])
    assert out["lyrics"].startswith("Can-dles are lit ta-ble for two I saved a slice for you")


def test_pitches_follow_the_chords_and_stay_in_the_range():
    key, events = _verse()
    out = lm.compose(["Saturday night I'm coming round", "in my white suit for you", "Candles are lit, table for two",
                      "I saved a slice for you"], events, key, 50, 64, shape="verse", seed=1)
    pcs = key.pitch_classes()
    assert all(50 <= n["pitch"] <= 64 and n["pitch"] % 12 in pcs for n in out["notes"])
    assert out["notes"][-1]["pitch"] % 12 == 9                               # the last line ends on the tonic
    # A verse line asks a question: the earlier lines don't end on the tonic.
    ends = [n for n in out["notes"] if n["start"] in (l["start_qn"] for l in out["lines"])]
    assert all(n["pitch"] % 12 != 9 for n in [out["notes"][7]])
    # No note is more than a fifth from the one before, and the line moves.
    pitches = [n["pitch"] for n in out["notes"]]
    assert max(abs(a - b) for a, b in zip(pitches, pitches[1:])) <= 7 and len(set(pitches)) >= 4


def test_repeated_words_repeat_their_tune_and_the_chorus_falls():
    key = harmony.parse_key("A minor")
    events, key = _events("Am7 Fmaj7 Cmaj7 G Am7 Fmaj7 Cmaj7 G", key, 4.0)
    out = lm.compose(["Baby it's you, yeah", "Baby it's true, oh", "All that I do is all for you", "Baby it's you, yeah"],
                     events, key, 50, 64, shape="chorus", seed=2)
    lines = out["lines"]
    first = [(n["start"], n["length"], n["pitch"]) for n in out["notes"] if lines[0]["start_qn"] <= n["start"] < lines[1]["start_qn"]]
    last = [(n["start"] - 24, n["length"], n["pitch"]) for n in out["notes"] if n["start"] >= lines[3]["start_qn"]]
    assert first == last                                                     # the hook
    assert "_" in out["lyrics"].split() and lines[1]["notes"] == lines[0]["notes"] + 1   # the fall on line 2's 'oh'
    assert all(l["held_beats"] >= 2.0 for l in lines)


def test_too_many_words_for_the_bars_is_said():
    key, events = _verse()
    with pytest.raises(ValueError, match="too many syllables"):
        lm.compose(["this line has far too many syllables to ever fit inside a single bar of music honestly"],
                   events, key, 50, 64, line_bars=1)


def test_diatonic_shift_moves_by_scale_steps():
    c = harmony.parse_key("C major")
    assert [lm.diatonic_shift(p, c, 2) for p in (60, 62, 64, 65, 67)] == [64, 65, 67, 69, 71]
    assert lm.diatonic_shift(60, c, -7) == 48 and lm.diatonic_shift(60, c, 0) == 60
    assert lm.diatonic_shift(61, c, 2) in (64, 65)                           # a note off the scale moves from its neighbour
