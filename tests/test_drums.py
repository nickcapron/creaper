import pytest

from creaper import theory
from creaper.drums import DrumMaps

# Note names as drum plugins report them (styles vary a lot between vendors).
REASYNDR = {0: "Kick", 1: "Snare", 2: "Blip", 3: "Tick", 16: "Kick", 17: "Snare", 32: "Kick", 33: "Snare", 48: "Kick"}
STUDIO_KIT = {
    36: "Kick 1", 35: "Kick 2", 38: "Snare Center", 40: "Snare Rim", 37: "Side Stick",
    42: "HH Closed", 44: "HH Pedal", 46: "HH Open", 49: "Crash L", 51: "Ride Bow", 53: "Ride Bell",
}


@pytest.mark.parametrize("lane, pitch", [
    ("kick", 36), ("snare", 38), ("closed hat", 42), ("open hat", 46), ("pedal hat", 44),
    ("hihat", 42), ("ride bell", 53), ("crash", 49), ("ride", 51),
])
def test_matches_vendor_note_names(lane, pitch):
    assert theory.resolve_drum_lane(lane, note_names=STUDIO_KIT).pitch == pitch


def test_repeated_names_pick_the_one_nearest_general_midi():
    # ReaSynDr repeats Kick every 16 notes; 32 is closest to GM kick (36).
    lane = theory.resolve_drum_lane("kick", note_names=REASYNDR)
    assert lane.pitch == 32
    assert "Kick" in lane.source


def test_falls_back_to_general_midi_then_errors():
    assert theory.resolve_drum_lane("tambourine", note_names=REASYNDR).source == "General MIDI"
    with pytest.raises(ValueError, match="Available"):
        theory.resolve_drum_lane("laser zap", note_names=REASYNDR)


def test_explicit_notes_win():
    assert theory.resolve_drum_lane("C1", note_names=STUDIO_KIT).pitch == 24
    assert theory.resolve_drum_lane("60").pitch == 60


def test_drum_map_beats_note_names_and_carries_channels():
    drum_map = {"Kick": {"pitch": 60, "channel": 1}, "Snare": {"pitch": 60, "channel": 2}, "Closed Hat": {"pitch": 60, "channel": 9}}
    snare = theory.resolve_drum_lane("snare", drum_map, STUDIO_KIT)
    assert (snare.pitch, snare.channel) == (60, 2)
    hat = theory.resolve_drum_lane("hh closed", drum_map, STUDIO_KIT)
    assert hat.channel == 9


def test_pattern_uses_per_lane_channels():
    drum_map = {"kick": {"pitch": 60, "channel": 1}, "snare": {"pitch": 60, "channel": 2}}
    notes = theory.drum_pattern_notes(
        {"kick": "x...", "snare": "..x."}, channel=10,
        resolve=lambda lane: theory.resolve_drum_lane(lane, drum_map))
    assert {(n["pitch"], n["channel"]) for n in notes} == {(60, 1), (60, 2)}


def test_drum_map_entries():
    assert theory.drum_map_entry("C1") == {"pitch": 24}
    assert theory.drum_map_entry(36) == {"pitch": 36}
    assert theory.drum_map_entry({"note": "C4", "channel": 3}) == {"pitch": 60, "channel": 3}
    with pytest.raises(ValueError):
        theory.drum_map_entry({"note": "C4", "channel": 17})


@pytest.mark.parametrize("lane, channel", [
    ("kick", 1), ("snare", 2), ("tom", 3), ("clap", 3), ("closed hat", 4), ("hihat", 4), ("chh", 4),
    ("open hat", 5), ("ohh", 5), ("crash", 5),
])
def test_sila_is_built_in(tmp_path, lane, channel):
    maps = DrumMaps(tmp_path / "drum_maps.json")
    name, mapping = maps.find("VST3i: SILA (SILA) (18 out)")
    assert name == "SILA"
    hit = theory.resolve_drum_lane(lane, mapping, note_names={})
    assert (hit.pitch, hit.channel) == (60, channel)
    assert "channel N" in maps.notes_for("VST3i: SILA (SILA) (18 out)")


def test_a_saved_map_overrides_a_built_in_one(tmp_path):
    maps = DrumMaps(tmp_path / "drum_maps.json")
    maps.save("SILA", {"kick": {"note": "C4", "channel": 7}})
    _, mapping = maps.find("VST3i: SILA (SILA) (18 out)")
    assert mapping == {"kick": {"pitch": 60, "channel": 7}}
    assert maps.find("VSTi: ReaSynth (Cockos)") is None


def test_drum_map_storage(tmp_path):
    maps = DrumMaps(tmp_path / "drum_maps.json")
    assert maps.find("VST3i: Analog Rytm (Elektron)") is None
    maps.save("Analog Rytm", {"kick": {"note": "C4", "channel": 1}, "snare": {"note": "C4", "channel": 2}})
    maps.save("Analog Rytm MKII", {"kick": "C1"})
    name, mapping = maps.find("VST3i: Analog Rytm MKII (Elektron Music Machines) (8->20ch)")
    assert name == "Analog Rytm MKII" and mapping == {"kick": {"pitch": 24}}
    name, _ = maps.find("VSTi: Analog Rytm (Elektron Music Machines)")
    assert name == "Analog Rytm"
    assert maps.delete("analog rytm") and not maps.delete("analog rytm")
    assert list(DrumMaps(tmp_path / "drum_maps.json").all()) == ["Analog Rytm MKII"]
