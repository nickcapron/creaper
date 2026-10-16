"""Music-theory fixes from the v0.19.4 review pass."""
import pytest

from creaper import composer as C
from creaper import harmony as H
from creaper import music_tools, theory


@pytest.mark.parametrize("root,quality,numeral", [(1, "", "#III"), (8, "", "#VII"), (6, "", "#VI")])
def test_raised_degrees_in_minor_are_named_raised(root, quality, numeral):
    # C# major in A minor was "bIV", G# major "bI".
    k = H.parse_key("A minor")
    assert H.numeral_for(H.chord_in_key(root, H.CHORD_QUALITIES[quality], k), k).numeral == numeral


def test_no_secondary_dominant_of_a_diminished_chord():
    # F#7 in A minor was labelled "V/ii°": a diminished chord isn't tonicized.
    k = H.parse_key("A minor")
    labels = H.numeral_for(H.chord_in_key(6, H.CHORD_QUALITIES["7"], k), k).labels
    assert not any("ii°" in label for label in labels)


def test_voice_crossing_is_reported_in_the_order_given():
    # The voicings were sorted first, so crossed voices were reassigned and never reported.
    r = music_tools.check_voice_leading(voicings=[[48, 64, 55, 72], [47, 62, 55, 74]], key="C major")
    assert any(i["issue"] == "voice crossing" for i in r["issues"])


def test_a_sixth_is_not_an_unresolved_seventh():
    r = music_tools.check_voice_leading(chords=["C6", "G"], voicings=[["C3", "G3", "E4", "A4"], ["B2", "G3", "D4", "B4"]],
                                        key="C major")
    assert not any(i["issue"] == "unresolved seventh" for i in r["issues"])


def test_a_major_seventh_that_leaps_up_is_flagged():
    r = music_tools.check_voice_leading(chords=["Fmaj7", "C"], voicings=[["F3", "A3", "C4", "E5"], ["E3", "G3", "C4", "G5"]],
                                        key="C major")
    assert any(i["issue"] == "unresolved seventh" for i in r["issues"])


def test_a_short_drum_lane_repeats_to_fill_the_pattern():
    notes = theory.drum_pattern_notes({"kick": "x...x...x...x...", "closed hat": "x.x."})
    hats = sorted(n["start"] for n in notes if n["pitch"] == 42)
    assert hats == [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]


def test_maqsum_is_dum_tek_rest_tek_dum_rest_tek_rest():
    steps = C.RHYTHMS["maqsum"]["steps"]
    assert [i for i, c in enumerate(steps) if c != "."] == [0, 2, 6, 8, 12]


def test_seven_alt_spells_sharp_eleven_and_flat_thirteen():
    assert H.spell_chord(0, "C", H.CHORD_QUALITIES["7alt"]) == ["C", "E", "Bb", "Db", "D#", "F#", "Ab"]
    assert H.spell_chord(0, "C", H.CHORD_QUALITIES["7b5"]) == ["C", "E", "Gb", "Bb"]  # unchanged


def test_lower_case_sus_numerals_and_upper_case_maj7_parse():
    assert H.parse_roman("v7sus4", H.parse_key("C major")).chord.symbol == "G7sus4"
    assert theory.parse_chord("CMAJ7").intervals == theory.parse_chord("Cmaj7").intervals


@pytest.mark.parametrize("pc,mode,name", [(1, "minor", "C#"), (1, "major", "Db"), (8, "major", "Ab"),
                                         (8, "minor", "G#"), (6, "minor", "F#"), (3, "minor", "Eb")])
def test_detected_keys_get_the_simpler_signature(pc, mode, name):
    # C# minor came back as "Db minor" (8 flats, spelled with Fb and Bbb).
    assert H._simplest_tonic(pc, mode) == name
