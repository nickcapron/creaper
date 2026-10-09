import pytest

from creaper import theory


@pytest.mark.parametrize("name, value", [
    ("C4", 60), ("A4", 69), ("F#3", 54), ("Bb2", 46), ("Cb4", 59), ("E#4", 65),
    ("C-1", 0), ("G9", 127), ("c4", 60), ("bb2", 46), (60, 60), ("60", 60),
])
def test_note_to_midi(name, value):
    assert theory.note_to_midi(name) == value


@pytest.mark.parametrize("bad", ["H4", "C", "C10", "", True])
def test_note_to_midi_rejects(bad):
    with pytest.raises(ValueError):
        theory.note_to_midi(bad)


def test_midi_to_note_round_trips():
    for n in range(128):
        assert theory.note_to_midi(theory.midi_to_note(n)) == n


@pytest.mark.parametrize("symbol, root, intervals, bass", [
    ("C", 0, (0, 4, 7), None),
    ("Am7", 9, (0, 3, 7, 10), None),
    ("F#m7b5", 6, (0, 3, 6, 10), None),
    ("Bbmaj7", 10, (0, 4, 7, 11), None),
    ("Cmaj7/E", 0, (0, 4, 7, 11), 4),
    ("D/F#", 2, (0, 4, 7), 6),
    ("C6/9", 0, (0, 4, 7, 9, 14), None),
    ("Ebsus2", 3, (0, 2, 7), None),
    ("GMaj7", 7, (0, 4, 7, 11), None),
])
def test_parse_chord(symbol, root, intervals, bass):
    chord = theory.parse_chord(symbol)
    assert (chord.root, chord.intervals, chord.bass) == (root, intervals, bass)


def test_parse_chord_rejects_unknown_quality():
    with pytest.raises(ValueError, match="unknown chord quality"):
        theory.parse_chord("Cblorp")


def test_voice_leading_moves_less_than_root_position():
    chords = [theory.parse_chord(c) for c in ["C", "Am", "F", "G"]]
    led = theory.voice_progression(chords, voice_leading=True)
    blocky = theory.voice_progression(chords, voice_leading=False)

    def total_movement(vs):
        return sum(theory._movement(a, b) for a, b in zip(vs, vs[1:]))

    assert total_movement(led) < total_movement(blocky)
    for voicing, chord in zip(led, chords):
        assert {n % 12 for n in voicing} == {(chord.root + i) % 12 for i in chord.intervals}


def test_drum_pattern():
    notes = theory.drum_pattern_notes({"kick": "x... x...", "snare": "....|X..."}, repeats=2)
    kicks = [n["start"] for n in notes if n["pitch"] == 36]
    snares = [n for n in notes if n["pitch"] == 38]
    assert kicks == [0.0, 1.0, 2.0, 3.0]
    assert [n["start"] for n in snares] == [1.0, 3.0]
    assert all(n["velocity"] == 127 and n["channel"] == 10 for n in snares)


def test_drum_swing_delays_offbeats():
    notes = theory.drum_pattern_notes({"hat": "xxxx"}, swing=66.67)
    starts = [n["start"] for n in notes]
    assert starts[0] == 0 and starts[2] == 0.5
    assert starts[1] == pytest.approx(1 / 3, abs=1e-3)


def test_drum_names_and_errors():
    assert theory.drum_pitch("Hi-Hat") == 42
    assert theory.drum_pitch("open_hat") == 46
    assert theory.drum_pitch("C1") == 24
    with pytest.raises(ValueError):
        theory.drum_pitch("kazoo")
    with pytest.raises(ValueError, match="unknown step"):
        theory.drum_pattern_notes({"kick": "x?x"})
