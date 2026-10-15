"""MCP tools for the tempo map, MIDI program changes and controller editing, and routing."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .server import DESTRUCTIVE, READ_ONLY, ItemId, call, tool

# ------------------------------------------------------------- tempo map


class TempoChange(BaseModel):
    bar: float = Field(ge=1, description="Bar where the change happens, 1-based")
    beat: float = Field(1, ge=1, description="Beat within the bar (tempo only; time signatures change on beat 1)")
    bpm: float | None = Field(None, gt=0, le=960, description="New tempo; omit to keep the tempo and change only the time signature")
    numerator: int | None = Field(None, ge=1, le=64, description="New time signature top number, e.g. 7 for 7/8")
    denominator: Literal[1, 2, 4, 8, 16, 32] | None = None
    ramp_to_next: bool = Field(False, description="Glide smoothly from this tempo to the next change (accelerando/ritardando)")


@tool(annotations=READ_ONLY)
def get_tempo_map() -> dict:
    """Reads the project's tempo map: every tempo and time-signature change, with the
    bar where each happens and whether it ramps to the next. Use it before writing
    parts in a song with tempo or meter changes; set_tempo_map writes them and
    set_tempo sets a single tempo for the whole song. Read-only."""
    return call("get_tempo_map")


@tool()
def set_tempo_map(
    changes: Annotated[list[TempoChange], Field(description=(
        "Tempo/time-signature changes, e.g. [{'bar': 17, 'bpm': 128}, {'bar': 33, 'numerator': 7, 'denominator': 8}]. "
        "For a ramp: [{'bar': 25, 'bpm': 120, 'ramp_to_next': true}, {'bar': 33, 'bpm': 140}]"))] = (),
    remove_bars: Annotated[list[float] | None, Field(description="Remove the changes at these bars")] = None,
    clear: Annotated[bool, Field(description="Remove every change after the first before adding")] = False,
) -> dict:
    """Adds, changes or removes tempo and time-signature changes: tempo jumps between
    sections, ramps (accelerando/ritardando), odd-meter bars. One undo step. Items stay
    at their bar positions; the starting tempo is set with set_tempo."""
    return call("set_tempo_map", changes=[c.model_dump() for c in changes], remove_bars=remove_bars or [], clear=clear)


# ------------------------------------------------------------ MIDI extras

GM_PROGRAMS = (
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano", "Electric Piano 1",
    "Electric Piano 2", "Harpsichord", "Clavinet", "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
    "Xylophone", "Tubular Bells", "Dulcimer", "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
    "Distortion Guitar", "Guitar Harmonics", "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)",
    "Fretless Bass", "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin", "Viola", "Cello",
    "Contrabass", "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1",
    "String Ensemble 2", "Synth Strings 1", "Synth Strings 2", "Choir Aahs", "Voice Oohs", "Synth Choir",
    "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn", "Brass Section", "Synth Brass 1",
    "Synth Brass 2", "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn", "Bassoon",
    "Clarinet", "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)", "Lead 5 (charang)",
    "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)", "Pad 1 (new age)", "Pad 2 (warm)",
    "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",
    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)",
    "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba", "Bagpipe", "Fiddle", "Shanai",
    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal",
    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot",
)


def _program_number(program: int | str) -> int:
    if isinstance(program, int):
        if not 1 <= program <= 128:
            raise ValueError("program numbers go from 1 to 128")
        return program
    text = str(program).strip().lower()
    if text.isdigit():
        return _program_number(int(text))
    for i, name in enumerate(GM_PROGRAMS):
        if text == name.lower():
            return i + 1
    matches = [i for i, name in enumerate(GM_PROGRAMS) if text in name.lower()]
    if len(matches) == 1:
        return matches[0] + 1
    if matches:
        raise ValueError(f"'{program}' matches several General MIDI programs: {', '.join(GM_PROGRAMS[i] for i in matches[:8])}")
    raise ValueError(f"no General MIDI program called '{program}' (give a number 1-128)")


@tool()
def add_program_change(
    item_id: ItemId,
    program: Annotated[int | str, Field(description="1-128, or a General MIDI name like 'Electric Piano 1', 'String Ensemble 1'")],
    position: Annotated[float, Field(ge=0, description="QN from the item start")] = 0.0,
    channel: Annotated[int, Field(ge=1, le=16, description="MIDI channel the instrument listens on")] = 1,
    bank_msb: Annotated[int | None, Field(ge=0, le=127, description="Bank select MSB (CC0), for synths with banks")] = None,
    bank_lsb: Annotated[int | None, Field(ge=0, le=127, description="Bank select LSB (CC32)")] = None,
) -> dict:
    """Writes a program change into a MIDI item, to switch the sound of an instrument
    that follows program changes (General MIDI synths, hardware synths through
    ReaControlMIDI, multitimbral plugins), with an optional bank select first. Most
    plugin synths ignore these: for them, load_sound, list_fx_presets/update_fx or
    set_fx_parameters change the sound. Returns the program number and its General
    MIDI name."""
    number = _program_number(program)
    events = []
    if bank_msb is not None:
        events.append({"position": position, "cc": 0, "value": bank_msb})
    if bank_lsb is not None:
        events.append({"position": position, "cc": 32, "value": bank_lsb})
    events.append({"position": position + (0.001 if events else 0), "cc": "program", "value": number - 1})
    result = call("add_midi_cc", item_id=item_id, channel=channel, events=events)
    result["program"] = f"{number}" + (f" ({GM_PROGRAMS[number - 1]} in General MIDI)" if number <= 128 else "")
    return result


CCKind = Literal["cc", "pitchbend", "program", "aftertouch", "poly aftertouch"]


@tool(annotations=READ_ONLY)
def get_midi_cc(
    item_id: ItemId,
    kind: Annotated[CCKind | None, Field(description="Only this kind of event")] = None,
    cc: Annotated[int | None, Field(ge=0, le=127, description="Only this controller number (1 mod wheel, 7 volume, 11 expression, 64 sustain)")] = None,
    channel: Annotated[int | None, Field(ge=1, le=16, description="Only events on this MIDI channel")] = None,
    start: Annotated[float | None, Field(description="From this QN position in the item")] = None,
    end: Annotated[float | None, Field(description="Up to this QN position")] = None,
    limit: Annotated[int, Field(ge=1, le=20000, description="Most events to return")] = 2000,
) -> dict:
    """Reads a MIDI item's controller events: CCs (mod wheel, sustain, expression...),
    pitch bend, program changes and aftertouch, with positions in QN. The notes
    themselves are read with get_midi_notes; add_midi_cc writes controllers and
    delete_midi_cc clears them. Read-only."""
    return call("get_midi_cc", item_id=item_id, kind=kind, cc=cc, channel=channel, start=start, end=end, limit=limit)


@tool(annotations=DESTRUCTIVE)
def delete_midi_cc(
    item_id: ItemId,
    kind: CCKind | None = None,
    cc: Annotated[int | None, Field(ge=0, le=127)] = None,
    channel: Annotated[int | None, Field(ge=1, le=16)] = None,
    start: float | None = None,
    end: float | None = None,
) -> dict:
    """Deletes controller events matching the filters (all of them if none are given),
    e.g. clear the sustain pedal (cc=64) or old pitch bends. One undo step."""
    return call("delete_midi_cc", item_id=item_id, kind=kind, cc=cc, channel=channel, start=start, end=end)


# --------------------------------------------------------------- routing

@tool(annotations=READ_ONLY)
def get_routing() -> dict:
    """How audio and MIDI flow through the project: folders, which tracks go to the
    master or their folder, every send (destination, level, pan, pre/post, channels,
    sidechain inputs, MIDI) and hardware outputs. Read it before changing routing."""
    return call("get_routing")


@tool()
def create_folder(
    name: Annotated[str, Field(description="e.g. 'Drums', 'Backing Vocals'")],
    tracks: Annotated[list[str | int], Field(min_length=1, description="Tracks to put inside it")],
    color: Annotated[str | None, Field(description="#RRGGBB")] = None,
) -> dict:
    """Groups tracks in a folder: a new folder track above them that they play through,
    so the group can be leveled, muted and processed together (effects on the folder
    track act like a bus). Use create_bus instead to keep tracks where they are and send them."""
    return call("create_folder", name=name, tracks=tracks, color=color)


@tool()
def set_master_send(
    track: Annotated[str | int, Field(description="Track number or name")],
    enabled: Annotated[bool, Field(description="False: the track only plays through its sends (e.g. a pure sidechain trigger)")],
) -> dict:
    """Turns a track's direct output to the master (or its parent folder) on or off,
    keeping its sends. Turn it off for a track that should only be heard through a
    bus or used as a sidechain trigger; set_send manages the sends themselves and
    get_routing shows the result. Returns the track's state."""
    return call("set_track_properties", track=track, main_send=enabled)
