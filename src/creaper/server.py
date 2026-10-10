"""The creaper MCP server: tools that let Claude read and change a REAPER project."""

from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from . import analysis, theory
from .bridge import Bridge, BridgeError

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer
    from mcp.server.fastmcp.exceptions import ToolError

INSTRUCTIONS = """\
creaper controls the user's open REAPER project.

Conventions:
- Tracks are referred to by number (1 = top track), by name, or as "master".
- Bars and beats are 1-based, as on REAPER's ruler. Beats are time-signature beats.
- Inside a MIDI item, note positions and lengths are in quarter notes (QN) from the
  item start: 1 = quarter, 0.5 = eighth, 0.25 = sixteenth, 4 = one bar of 4/4.
- Notes can be names (C4 = middle C = 60, F#3, Bb2) or MIDI numbers.
- MIDI items are identified by the item_id returned from create_midi_item or
  get_track_details. "selected" means the item the user has selected.

Start with get_project_overview to learn the tempo, key landmarks and tracks.
Every change is one undo step named "creaper: ...", so the user can Ctrl+Z it, or
you can call undo. Before deleting things or making large changes the user didn't
ask for, check with them. To judge a mix, use analyze_audio for real measurements
rather than guessing.
"""

mcp = MCPServer("creaper", instructions=INSTRUCTIONS)
bridge = Bridge()

READ_ONLY = ToolAnnotations(readOnlyHint=True)
DESTRUCTIVE = ToolAnnotations(destructiveHint=True)


def tool(annotations: ToolAnnotations | None = None):
    """Registers an MCP tool whose expected failures reach Claude with their message.

    The MCP SDK hides the text of any exception that isn't a ToolError, but REAPER's
    answers ("there is no track named ...") are what Claude needs to fix its call.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except (BridgeError, ValueError) as e:
                raise ToolError(str(e)) from e

        mcp.tool(annotations=annotations)(wrapper)
        return fn

    return decorator

TrackRef = Annotated[str | int, Field(description='Track number (1 = top), track name, or "master"')]
FxRef = Annotated[str | int, Field(description="FX position in the chain (1 = first) or name, e.g. 'ReaComp'")]
ItemId = Annotated[str, Field(description='MIDI item id from create_midi_item/get_track_details, or "selected"')]
Bar = Annotated[float | None, Field(description="Bar number, 1-based. Fractions are parts of the bar (5.5 = halfway through bar 5).")]
Beat = Annotated[float | None, Field(description="Beat within the bar, 1-based (default 1)")]


def call(cmd: str, timeout: float = 30.0, **params: Any) -> Any:
    return bridge.call(cmd, params, timeout=timeout)


class Note(BaseModel):
    pitch: str | int = Field(description="Note name like C4, F#3, Bb2, or MIDI number (C4 = 60)")
    start: float = Field(ge=0, description="Start in quarter notes from the item start")
    length: float = Field(gt=0, description="Length in quarter notes")
    velocity: int = Field(96, ge=1, le=127)
    channel: int = Field(1, ge=1, le=16)


class ChordEvent(BaseModel):
    chord: str = Field(description="Chord symbol, e.g. Am7, F#m7b5, Cmaj7/E, Bb, Dsus4")
    length: float = Field(4.0, gt=0, description="Length in quarter notes (4 = a bar of 4/4)")
    start: float | None = Field(None, ge=0, description="Start in QN from the item start; default: right after the previous chord")


class CCEvent(BaseModel):
    position: float = Field(ge=0, description="Position in quarter notes from the item start")
    cc: int | Literal["pitchbend"] = Field(description="CC number (1 = mod wheel, 7 = volume, 11 = expression, 64 = sustain) or 'pitchbend'")
    value: int = Field(description="0-127 for CCs (sustain: 127 = down, 0 = up); -8192..8191 for pitchbend")


def _with_note_names(notes: list[dict]) -> list[dict]:
    for n in notes:
        n["note"] = theory.midi_to_note(n["pitch"])
    return notes


# ------------------------------------------------------------------ reading


@tool(annotations=READ_ONLY)
def get_project_overview() -> dict:
    """Start here. Returns tempo, time signature, length, edit cursor, time selection,
    transport state, markers and regions, the master track, every track (volume, pan,
    mute/solo, FX chain, item count) and the user's selected items."""
    return call("get_project_overview")


@tool(annotations=READ_ONLY)
def get_track_details(track: TrackRef) -> dict:
    """Everything about one track: its items (with ids, positions and note counts), FX
    chain with presets, sends and receives."""
    return call("get_track_details", track=track)


@tool(annotations=READ_ONLY)
def get_fx_parameters(
    track: TrackRef,
    fx: FxRef,
    search: Annotated[str | None, Field(description="Only parameters whose name contains these words, e.g. 'threshold'")] = None,
    offset: int = 0,
    limit: int = 100,
) -> dict:
    """Lists an FX's parameters with their current value (0-1) and displayed value
    (e.g. '-18.0 dB'). Plugins can have hundreds of parameters, so search narrows it."""
    return call("get_fx_parameters", track=track, fx=fx, search=search, offset=offset, limit=limit)


@tool(annotations=READ_ONLY)
def list_installed_fx(
    search: Annotated[str | None, Field(description="Words to match, e.g. 'compressor', 'eq', 'reverb', 'synth'")] = None,
    limit: int = 50,
) -> dict:
    """Searches the user's installed plugins (VST, VST3, AU, CLAP, JS). Use the returned
    names with add_fx or create_track's instrument. REAPER's own ReaPlugs (ReaEQ,
    ReaComp, ReaVerbate, ReaDelay, ReaSynth, ReaLimit...) are always available."""
    return call("list_installed_fx", search=search, limit=limit)


@tool(annotations=READ_ONLY)
def get_midi_notes(item_id: ItemId) -> dict:
    """Reads the notes in a MIDI item (positions in quarter notes from the item start)."""
    result = call("get_midi_notes", item_id=item_id)
    _with_note_names(result.get("notes", []))
    return result


# -------------------------------------------------------------- arrangement


@tool()
def set_tempo(
    bpm: Annotated[float | None, Field(gt=0, le=960)] = None,
    numerator: Annotated[int | None, Field(ge=1, le=64, description="Time signature top number")] = None,
    denominator: Annotated[Literal[1, 2, 4, 8, 16, 32] | None, Field(description="Time signature bottom number")] = None,
) -> dict:
    """Sets the project's starting tempo and/or time signature."""
    return call("set_tempo", bpm=bpm, numerator=numerator, denominator=denominator)


@tool()
def create_track(
    name: str,
    instrument: Annotated[str | None, Field(description="Instrument plugin to load, e.g. 'ReaSynth' or a name from list_installed_fx")] = None,
    position: Annotated[int | None, Field(description="Track number it should become; default: last")] = None,
    color: Annotated[str | None, Field(description="#RRGGBB")] = None,
) -> dict:
    """Adds a track, optionally with an instrument so MIDI on it makes sound."""
    return call("create_track", name=name, instrument=instrument, position=position, color=color)


@tool()
def set_track_properties(
    track: TrackRef,
    name: str | None = None,
    volume_db: Annotated[float | None, Field(le=12, description="Fader level in dB (0 = unity)")] = None,
    pan: Annotated[float | None, Field(ge=-1, le=1, description="-1 = hard left, 0 = center, 1 = hard right")] = None,
    mute: bool | None = None,
    solo: bool | None = None,
    color: Annotated[str | None, Field(description="#RRGGBB")] = None,
    selected: bool | None = None,
) -> dict:
    """Changes a track's name, fader, pan, mute, solo, color or selection."""
    return call("set_track_properties", track=track, name=name, volume_db=volume_db, pan=pan,
                mute=mute, solo=solo, color=color, selected=selected)


@tool(annotations=DESTRUCTIVE)
def delete_track(track: TrackRef) -> dict:
    """Deletes a track and everything on it (undoable). Confirm with the user first."""
    return call("delete_track", track=track)


@tool()
def add_marker(
    name: str,
    bar: Annotated[float, Field(ge=1, description="Bar number, 1-based")],
    beat: Beat = None,
    end_bar: Annotated[float | None, Field(description="Give this to make a region (e.g. a song section) ending at this bar")] = None,
    color: Annotated[str | None, Field(description="#RRGGBB")] = None,
) -> dict:
    """Adds a marker, or a region when end_bar is given (e.g. 'Chorus' from bar 17 to 25)."""
    return call("add_marker", name=name, start_bar=bar, start_beat=beat, end_bar=end_bar, color=color)


@tool()
def transport(
    action: Literal["play", "stop", "pause", "go_to"],
    start_bar: Bar = None,
    start_beat: Beat = None,
    end_bar: Annotated[float | None, Field(description="With play: stop (or loop) here")] = None,
    loop: bool = False,
) -> dict:
    """Plays, stops, pauses or moves the edit cursor. play with start_bar/end_bar lets
    the user hear a section ('play bars 9 to 17')."""
    return call("transport", action=action, start_bar=start_bar, start_beat=start_beat, end_bar=end_bar, loop=loop)


@tool()
def undo(steps: Annotated[int, Field(ge=1, le=50)] = 1) -> dict:
    """Undoes the most recent changes in REAPER (Claude's or the user's)."""
    return call("undo", steps=steps)


@tool()
def run_action(
    command: Annotated[str | int, Field(description="Numeric action id (e.g. 40029) or named command (e.g. '_SWS_ABOUT')")],
) -> dict:
    """Runs any action from REAPER's action list. Use it for things the other tools
    don't cover, and only when the user wants that action."""
    return call("run_action", command=command)


# --------------------------------------------------------------------- MIDI


@tool()
def create_midi_item(
    track: TrackRef,
    start_bar: Annotated[float | None, Field(ge=1, description="Bar to start at, 1-based; default: the edit cursor")] = None,
    start_beat: Beat = None,
    length_bars: Annotated[float | None, Field(gt=0)] = None,
    length_qn: Annotated[float | None, Field(gt=0, description="Length in quarter notes, instead of length_bars")] = None,
    name: str | None = None,
) -> dict:
    """Creates an empty MIDI item (default 4 bars) and returns its item_id for adding
    notes, chords or drums."""
    return call("create_midi_item", track=track, start_bar=start_bar, start_beat=start_beat,
                length_bars=length_bars, length_qn=length_qn, name=name)


@tool()
def add_midi_notes(
    item_id: ItemId,
    notes: list[Note],
    replace: Annotated[bool, Field(description="Delete the item's existing notes first")] = False,
) -> dict:
    """Writes notes into a MIDI item: melodies, basslines, arpeggios, anything. The item
    grows to fit notes past its end."""
    payload = [
        {"pitch": theory.note_to_midi(n.pitch), "start": n.start, "length": n.length,
         "velocity": n.velocity, "channel": n.channel}
        for n in notes
    ]
    return call("add_midi_notes", item_id=item_id, notes=payload, replace=replace)


@tool()
def add_chord_progression(
    item_id: ItemId,
    chords: list[ChordEvent],
    octave: Annotated[int, Field(ge=0, le=8, description="Octave of the voicing; 4 puts chords around middle C")] = 4,
    voice_leading: Annotated[bool, Field(description="Pick inversions that move as little as possible")] = True,
    bass_octave: Annotated[int | None, Field(ge=0, le=6, description="Also add the root (or slash bass) in this octave, e.g. 2")] = None,
    velocity: Annotated[int, Field(ge=1, le=127)] = 80,
    start: Annotated[float, Field(ge=0, description="Where the first chord starts, in QN from the item start")] = 0.0,
    replace: bool = False,
) -> dict:
    """Writes block chords from chord symbols (Am7, Cmaj7/E, F#m7b5, Bbsus2, ...), with
    smooth voice leading by default. Returns the notes chosen for each chord."""
    parsed = [theory.parse_chord(c.chord) for c in chords]
    voicings = theory.voice_progression(parsed, octave=octave, voice_leading=voice_leading)
    notes, summary, pos = [], [], start
    for event, chord, voicing in zip(chords, parsed, voicings):
        at = event.start if event.start is not None else pos
        pitches = list(voicing)
        if bass_octave is not None:
            pitches.insert(0, theory.bass_note(chord, bass_octave))
        for p in pitches:
            notes.append({"pitch": p, "start": at, "length": event.length, "velocity": velocity, "channel": 1})
        summary.append({"chord": event.chord, "start": at, "notes": [theory.midi_to_note(p) for p in pitches]})
        pos = at + event.length
    result = call("add_midi_notes", item_id=item_id, notes=notes, replace=replace)
    result["chords"] = summary
    return result


@tool()
def add_drum_pattern(
    item_id: ItemId,
    pattern: Annotated[dict[str, str], Field(description=(
        "Lane name -> steps. Names are General MIDI drums (kick, snare, clap, closed hat, open hat, "
        "pedal hat, ride, crash, low/mid/high tom, floor tom, rim, shaker, tambourine...) or note "
        "names/numbers for other kits. Steps: x hit, X accent, o ghost, 1-9 velocity level, . rest; "
        "spaces and | are ignored. Example: {'kick': 'x...x...x...x...', 'snare': '....x.......x...'}"
    ))],
    step: Annotated[float, Field(gt=0, description="Length of one step in QN: 0.25 = 16ths, 0.5 = 8ths, 1/3 = 8th triplets")] = 0.25,
    repeats: Annotated[int, Field(ge=1, le=256, description="How many times to play the pattern back to back")] = 1,
    swing: Annotated[float, Field(ge=50, le=75, description="50 = straight, ~58 = light swing, ~66 = triplet shuffle")] = 50,
    humanize: Annotated[float, Field(ge=0, le=1, description="Random velocity variation, 0-1")] = 0,
    start: Annotated[float, Field(ge=0, description="Start in QN from the item start")] = 0.0,
    channel: Annotated[int, Field(ge=1, le=16, description="MIDI channel; GM drums use 10")] = 10,
    replace: bool = False,
) -> dict:
    """Programs drums step-sequencer style."""
    notes = theory.drum_pattern_notes(pattern, step=step, repeats=repeats, swing=swing,
                                      start=start, channel=channel, humanize=humanize)
    return call("add_midi_notes", item_id=item_id, notes=notes, replace=replace)


@tool(annotations=DESTRUCTIVE)
def delete_midi_notes(
    item_id: ItemId,
    start: Annotated[float | None, Field(description="Only notes starting at or after this QN position")] = None,
    end: Annotated[float | None, Field(description="Only notes starting before this QN position")] = None,
    pitch: Annotated[str | int | None, Field(description="Only this pitch")] = None,
) -> dict:
    """Deletes notes from a MIDI item; with no filters, all of them."""
    return call("delete_midi_notes", item_id=item_id, start=start, end=end,
                pitch=theory.note_to_midi(pitch) if pitch is not None else None)


@tool()
def add_midi_cc(
    item_id: ItemId,
    events: list[CCEvent],
    channel: Annotated[int, Field(ge=1, le=16)] = 1,
) -> dict:
    """Adds controller events: sustain pedal, mod wheel, expression swells, pitch bend."""
    return call("add_midi_cc", item_id=item_id, channel=channel, events=[e.model_dump() for e in events])


# ------------------------------------------------------------------- mixing


@tool()
def add_fx(
    track: TrackRef,
    fx_name: Annotated[str, Field(description="Plugin name, e.g. 'ReaEQ', 'ReaComp', 'Pro-Q 3'")],
    position: Annotated[int | None, Field(ge=1, description="Chain position (1 = first); default: end")] = None,
) -> dict:
    """Adds a plugin to a track's FX chain (use 'master' for the master bus)."""
    return call("add_fx", track=track, name=fx_name, position=position)


@tool()
def set_fx_parameter(
    track: TrackRef,
    fx: FxRef,
    parameter: Annotated[str | int, Field(description="Parameter number (from get_fx_parameters) or name, e.g. 'Threshold'")],
    display_value: Annotated[float | None, Field(description="Target in the plugin's displayed units: -18 for '-18 dB', 4 for '4:1', 2500 for '2.5 kHz'")] = None,
    value: Annotated[float | None, Field(ge=0, le=1, description="Raw normalized value 0-1, instead of display_value")] = None,
) -> dict:
    """Sets one FX parameter. display_value is usually easiest; creaper searches for the
    setting that shows that number. Returns what the plugin now displays."""
    return call("set_fx_parameter", track=track, fx=fx, parameter=parameter, value=value, display_value=display_value)


@tool()
def update_fx(
    track: TrackRef,
    fx: FxRef,
    enabled: Annotated[bool | None, Field(description="False bypasses the FX")] = None,
    preset: Annotated[str | None, Field(description="Preset name to load")] = None,
    show: Annotated[bool | None, Field(description="Open (true) or close (false) the plugin window")] = None,
) -> dict:
    """Bypasses or enables an FX, loads a preset, or opens its window for the user."""
    return call("update_fx", track=track, fx=fx, enabled=enabled, preset=preset, show=show)


@tool(annotations=DESTRUCTIVE)
def remove_fx(track: TrackRef, fx: FxRef) -> dict:
    """Removes an FX from a track's chain."""
    return call("remove_fx", track=track, fx=fx)


@tool()
def set_send(
    source: TrackRef,
    destination: TrackRef,
    volume_db: float | None = None,
    pan: Annotated[float | None, Field(ge=-1, le=1)] = None,
    mute: bool | None = None,
    mode: Literal["post-fader", "pre-fx", "post-fx"] | None = None,
    remove: bool = False,
) -> dict:
    """Creates or adjusts a send (e.g. vocals to a reverb bus), or removes it."""
    return call("set_send", source=source, destination=destination, volume_db=volume_db,
                pan=pan, mute=mute, mode=mode, remove=remove)


# ----------------------------------------------------------------- analysis


@tool(annotations=READ_ONLY)
def analyze_audio(
    track: Annotated[str | int, Field(description='"master" for the full mix, or a track to measure on its own (post-FX, post-fader)')] = "master",
    start_bar: Bar = None,
    end_bar: Annotated[float | None, Field(description="Bar to stop at; default: end of project")] = None,
) -> dict:
    """Renders the mix or one track and measures it: integrated/short-term loudness
    (LUFS), loudness range, true peak, RMS, crest factor, clipping, stereo correlation
    (including the low end), and frequency balance by band and octave. Rendering runs
    faster than real time but takes a moment for long ranges."""
    render = call("render_audio", timeout=900.0, track=track, start_bar=start_bar, end_bar=end_bar)
    path = Path(render["files"][0])
    try:
        result = analysis.analyze_file(path)
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in render["files"]:
                Path(f).unlink(missing_ok=True)
    offset = render["start"]["seconds"]
    timeline = result.get("short_term_timeline")
    if timeline:
        positions = call("time_to_positions", times=[offset + p["t"] for p in timeline])
        for point, pos in zip(timeline, positions):
            point["bar"], point["beat"] = pos["bar"], pos["beat"]
            del point["t"]
    return {"measured": render["track"], "range": {"start": render["start"], "end": render["end"]}, **result}


def run() -> None:
    mcp.run()
