"""MCP tools for recording (inputs, arming, monitoring, recording a range, takes) and
the editing basics around it: time selection and loop points, editing and deleting
markers and regions, track templates, freezing tracks."""

from __future__ import annotations

import re
from typing import Annotated, Literal

from pydantic import Field

from .bridge import STOP_PROMPT_WAIT
from .server import DESTRUCTIVE, READ_ONLY, ItemId, bridge, call, confirm_with_user, tool

Bar = Annotated[float | None, Field(ge=1, description="Bar, 1-based")]

STOP_PROMPT_NOTE = (
    "When recording stops, REAPER will open a window asking the user which new files to "
    "save or delete (a REAPER preference, on by default). Tell the user it's coming and to "
    "answer it: REAPER can't do anything else until they do, so tools wait for them (up to "
    f"{STOP_PROMPT_WAIT / 60:.0f} minutes). They can turn it off in Preferences > Recording "
    "(\"Prompt to save/delete/rename new files\")."
)


# ---------------------------------------------------------------- recording

@tool(annotations=READ_ONLY)
def list_inputs() -> dict:
    """The audio inputs of the user's audio interface (as REAPER names them) and the MIDI
    input devices, for setting what a track records from."""
    return call("list_inputs")


@tool()
def set_record_settings(
    track: Annotated[str | int, Field(description="Track number or name")],
    arm: Annotated[bool | None, Field(description="Arm (or disarm) the track for recording")] = None,
    audio_input: Annotated[int | None, Field(ge=1, description="Record audio from this interface input (see list_inputs)")] = None,
    stereo: Annotated[bool, Field(description="With audio_input: record that input and the next as a stereo pair")] = False,
    midi_device: Annotated[int | Literal["all"] | None, Field(description="Record MIDI from this device number (list_inputs) or 'all'")] = None,
    midi_channel: Annotated[int, Field(ge=0, le=16, description="MIDI channel to record, 0 = all")] = 0,
    no_input: Annotated[bool, Field(description="Clear the track's input")] = False,
    monitor: Annotated[Literal["off", "on", "auto"] | None, Field(description="Hear the input through the track: on, off, or auto (only while recording/stopped)")] = None,
    mode: Annotated[Literal["input", "output", "none", "midi overdub", "midi replace"] | None, Field(description=(
        "What gets recorded: the input (default), the track's output (resampling), nothing (monitor only), "
        "or MIDI merged into / replacing existing notes"))] = None,
) -> dict:
    """Sets what a track records and whether it's armed: an audio input (a mic, a
    guitar, a hardware synth's outputs on the interface) or a MIDI device (a keyboard,
    a hardware synth's MIDI out), input monitoring, and the record mode."""
    return call("set_record_settings", track=track, arm=arm, audio_input=audio_input, stereo=stereo,
                midi_device=midi_device, midi_channel=midi_channel, no_input=no_input, monitor=monitor, mode=mode)


@tool()
def record(
    start_bar: Bar = None,
    start_beat: Annotated[float | None, Field(ge=1)] = None,
    end_bar: Annotated[float | None, Field(ge=1, description="Stop recording automatically at this bar")] = None,
    bars: Annotated[float | None, Field(gt=0, description="Or record this many bars")] = None,
) -> dict:
    """Starts recording on every armed track, from a bar (default: the edit cursor),
    optionally stopping by itself at a bar. Without an end it records until stopped
    (transport stop). The performer hears the count-in and metronome as set in REAPER."""
    if bars and start_bar:
        end_bar = start_bar + bars
    elif bars:
        position = call("get_project_overview")["edit_cursor"]
        end_bar = position["bar"] + bars
    confirm_with_user("start recording on the armed tracks")
    result = call("record", start_bar=start_bar, start_beat=start_beat, end_bar=end_bar)
    if result.pop("stop_prompt", None):
        result["note"] = STOP_PROMPT_NOTE
    return result


@tool(annotations=READ_ONLY)
def recording_status() -> dict:
    """Whether REAPER is recording or playing, where the playhead is, and when it'll stop.
    If recording just stopped and REAPER is asking the user which files to keep, this
    waits for them to answer."""
    waited: list[bool] = []
    result = bridge.call("recording_status", on_user_wait=lambda: waited.append(True))
    if waited:
        result["note"] = ("Recording stopped and REAPER asked the user which new files to keep; they've "
                          "answered. Check the recorded items (get_track_details): they may have deleted some.")
    elif result.pop("stop_prompt", None):
        result["note"] = "When this recording stops, REAPER will ask the user which new files to keep."
    return result



@tool(annotations=READ_ONLY)
def list_takes(item_id: ItemId) -> dict:
    """The takes in an item (each recording pass over the same spot), and which is active."""
    return call("list_takes", item_id=item_id)


@tool()
def choose_take(
    item_id: ItemId,
    take: Annotated[int | None, Field(ge=1, description="Take number from list_takes")] = None,
    name: Annotated[str | None, Field(description="Or the take's name")] = None,
) -> dict:
    """Makes a take the one that plays (for picking the best performance)."""
    if take is None and not name:
        raise ValueError("give a take number or name")
    return call("set_active_take", item_id=item_id, take=take, name=name)


@tool()
def explode_takes(item_id: ItemId) -> dict:
    """Puts each take of an item on its own new track, to compare or comp them side by side."""
    return call("explode_takes", item_id=item_id)


# ---------------------------------------------------------- time and loops

@tool()
def set_time_selection(
    start_bar: Bar = None,
    end_bar: Bar = None,
    start_beat: Annotated[float | None, Field(ge=1)] = None,
    end_beat: Annotated[float | None, Field(ge=1)] = None,
    loop: Annotated[bool, Field(description="Also set the loop points to the same range")] = False,
    repeat: Annotated[bool | None, Field(description="Turn loop playback (repeat) on or off")] = None,
    clear: Annotated[bool, Field(description="Clear the time selection (and loop points)")] = False,
) -> dict:
    """Sets or clears the time selection and loop points, and turns repeat on/off: for
    looping a section while working on it, or for actions that use the selection."""
    return call("set_time_selection", start_bar=start_bar, start_beat=start_beat, end_bar=end_bar,
                end_beat=end_beat, loop=loop, **{"repeat": repeat}, clear=clear)


# ------------------------------------------------------- markers, regions

MarkerRef = Annotated[str | int, Field(description="The marker's or region's name, or its number")]


def _marker_ref(ref: str | int) -> dict:
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        return {"number": int(ref)}
    return {"name": ref}


@tool()
def edit_marker(
    marker: MarkerRef,
    region: Annotated[bool | None, Field(description="True for a region, False for a marker, when names clash")] = None,
    new_name: str | None = None,
    start_bar: Bar = None,
    start_beat: Annotated[float | None, Field(ge=1)] = None,
    end_bar: Annotated[float | None, Field(ge=1, description="Regions: new end bar")] = None,
    end_beat: Annotated[float | None, Field(ge=1)] = None,
    color: Annotated[str | None, Field(description="#RRGGBB")] = None,
) -> dict:
    """Renames, moves, resizes or recolors a marker or region (e.g. rename 'Chorus' to
    'Chorus 1', or extend the bridge region to bar 49)."""
    return call("edit_marker", **_marker_ref(marker), region=region, new_name=new_name, start_bar=start_bar,
                start_beat=start_beat, end_bar=end_bar, end_beat=end_beat, color=color)


@tool(annotations=DESTRUCTIVE)
def delete_marker(marker: MarkerRef, region: Annotated[bool | None, Field()] = None) -> dict:
    """Deletes a marker or region (not the audio or MIDI under it)."""
    return call("delete_marker", **_marker_ref(marker), region=region)


# ------------------------------------------- track templates and freezing

def _template_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"\\|?*\x00-\x1f]+', " ", name).strip(" ./")
    if not cleaned or ".." in cleaned:
        raise ValueError("give a plain template name")
    return cleaned


@tool()
def save_track_template(
    name: Annotated[str, Field(description="e.g. 'Vocal chain', 'Drum bus' (a/b makes a subfolder)")],
    tracks: Annotated[list[str | int], Field(min_length=1)],
) -> dict:
    """Saves tracks (with their plugins, sends between them, settings and items) as a
    REAPER track template, to reuse in any project."""
    return call("save_track_template", name=_template_name(name), tracks=tracks)


@tool(annotations=READ_ONLY)
def list_track_templates() -> dict:
    """The user's REAPER track templates."""
    return call("list_track_templates")


@tool()
def apply_track_template(name: Annotated[str, Field(description="A name from list_track_templates")]) -> dict:
    """Adds a track template's tracks to the project."""
    return call("apply_track_template", name=_template_name(name))


@tool()
def freeze_tracks(
    tracks: Annotated[list[str | int], Field(min_length=1)],
    unfreeze: Annotated[bool, Field(description="Undo a freeze: bring back the original items and plugins")] = False,
    mono: bool = False,
) -> dict:
    """Freezes tracks: renders them to audio and takes their plugins offline to save CPU
    (heavy synths, long effect chains), or unfreezes them to edit again."""
    return call("freeze_tracks", timeout=600.0, tracks=tracks, unfreeze=unfreeze, mono=mono)
