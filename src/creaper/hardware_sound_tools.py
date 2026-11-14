"""MCP tools for sound design and recording on hardware synths: read and load patches,
set parameters by name, audition (play a phrase, record it, measure it), keep sounds in
the sound library, write them into the song, and print hardware parts to audio.

A device model can have a profile module (microkorg.py is the first) that knows its
patch format and parameters. Everything device-specific here goes through the profile,
by the interface written down in hardware_profiles.Profile, so another synth is another
profile. A device without a profile still gets a track pair, auditions, prints and a
latency measurement: only reading, loading and editing its sound need the profile.

Safety: only the device's EDIT BUFFER is changed, and the sound it held is kept as a
backup first. A stored program is written by one tool only, after asking the user, every
time. Hardware can't be rendered offline: it's heard by recording it, in real time."""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

import numpy as np
import soundfile as sf
from pydantic import BaseModel, Field

from . import convstate, hardware_profiles, jsonstore, listen, server, sound_design
from . import hardware_setup as setup
from . import hardware_tools as hw
from .bridge import STOP_PROMPT_WAIT, BridgeError
from .server import DESTRUCTIVE, READ_ONLY, call, confirm_with_user, tool
from .theory import midi_to_note

PROFILES = hardware_profiles.PROFILES
REPLY_WAIT_S = 2.5        # a patch is ~300 bytes: 0.1 s on a MIDI cable, plus the synth's own time
POLL_S = 0.1
BACKUPS_KEPT = 30
SILENT_DBFS = -60.0
# Under this a "silent" recording isn't a quiet synth but no signal at all: an open analog
# input idles around -90 to -110 dBFS, a stream nothing feeds reads as digital zero (the
# laptop microphone REAPER was recording by mistake read -138). From a few readings, not
# yet a measured threshold.
DEAD_DBFS = -125.0
HOT_DBFS = -0.3
PATCH_LEAD_S = 0.5        # a sound written into the song is sent this long before its part
_asked: set[str] = set()  # standing questions the user said yes to, in this server's lifetime


def _was_asked(key: str) -> bool:
    """Whether the user already said yes to this standing question (the device's name:
    load sounds; 'record:<name>': record test clips). One key per question. In the chat
    panel the answer is kept for the conversation (a new server starts with every
    message there), lapsing an hour after it was last relied on."""
    return key in _asked or convstate.allowed('hardware:' + key)


def _mark_asked(key: str) -> None:
    _asked.add(key)
    convstate.allow('hardware:' + key)


@dataclass
class Link:
    name: str
    device: dict
    out: int
    inp: int | None
    channel: int
    profile: Any            # a hardware_profiles.Profile, or None: the device is played and recorded only


def _link(name: str) -> Link:
    key, device = hw._device(name)
    ports = hw._ports()
    out = hw._port_number(ports["outputs"], device["midi_output"], "output", ports["disabled_outputs"])[0]
    inp = (hw._port_number(ports["inputs"], device["midi_input"], "input", ports["disabled_inputs"])[0]
           if device.get("midi_input") else None)
    return Link(key, device, out, inp, hw.midi_channel(key, device), PROFILES.get(device.get("model") or ""))


def _profile(link: Link, to: str) -> Any:
    """The device's profile, for a tool that can't work without one (`to` = what it does)."""
    if link.profile is None:
        raise ValueError(
            f"creaper has no sound-design profile for {link.name} ({link.device.get('model') or 'model unknown'}), "
            f"so it can't {to}; it has profiles for: {', '.join(PROFILES)}. The user sets the sound on the synth "
            "itself. Everything else works: create_hardware_track, audition_hardware (hear and measure it), "
            "print_hardware, calibrate_hardware_latency.")
    return link.profile


def _reads(link: Link) -> bool:
    """Whether creaper can ask this device for its current sound."""
    return link.profile is not None and link.profile.READS_PATCH


def _ask(link: Link, request: tuple[list[str], set[int]], what: str, wait: float = REPLY_WAIT_S) -> tuple[int, bytes]:
    """Sends a profile's request and returns the device's answer (reply code, payload)."""
    messages, want = request
    if link.inp is None:
        raise ValueError(f"{link.name} can't answer creaper: no MIDI input is saved for it. Cable its MIDI OUT to the "
                         "interface's MIDI IN and save_hardware it again with midi_input.")
    latest = int(call("recent_midi_input", after=0, limit=1).get("latest") or 0)
    sent = call("send_midi", device=link.out, messages=messages, open_audio=True)
    waited = 0.0
    while waited <= wait:
        hw._sleep(POLL_S)
        waited += POLL_S
        got = call("recent_midi_input", after=latest, limit=64)
        for event in got.get("events") or []:
            parsed = link.profile.parse_message(event.get("hex", "")) if event.get("device") == link.inp else None
            if parsed and parsed[0] in want:
                return parsed
        latest = max(latest, int(got.get("latest") or 0))
    if sent.get("audio_running") is False:
        raise ValueError("REAPER's audio device is closed and wouldn't open, and REAPER only takes in MIDI while it "
                         "runs: Options > Preferences > Audio > Device, choose the interface, then try again.")
    raise ValueError(f"{link.name} didn't answer ({what}). Is it switched on? {link.profile.SETUP_HELP}")


def _read_program(link: Link) -> bytes:
    p = _profile(link, "read its sound")
    if not p.READS_PATCH:
        raise ValueError(f"a {p.MODEL} can't send its current sound over MIDI, so creaper can't read it from "
                         f"{link.name}")
    function, payload = _ask(link, p.read_request(link.channel), "asked for its current sound")
    data = p.patch_reply(function, payload) or b""
    if len(data) != p.PROGRAM_BYTES:
        raise ValueError(f"{link.name} answered, but not with a whole patch; try again")
    return data


def _read_setup(link: Link) -> dict:
    """The device's global MIDI settings, read now and remembered in the hardware map."""
    p = _profile(link, "read its MIDI settings")
    function, payload = _ask(link, p.setup_request(link.channel), "asked for its settings")
    setup = p.setup_reply(function, payload)
    with jsonstore.updating(hw._store_path(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        if link.name in data.get("devices", {}):
            data["devices"][link.name]["midi_setup"] = setup
    link.device["midi_setup"] = setup
    return setup


def _backups_path() -> Path:
    return Path(server.bridge.directory) / "hardware_backups.json"


def _backups(link: Link) -> list[dict]:
    return jsonstore.read(_backups_path(), dict).get("devices", {}).get(link.name, [])


def _backup(link: Link, data: bytes, why: str) -> None:
    """Keeps a sound the device held (newest first), unless it's the one kept last."""
    with jsonstore.updating(_backups_path(), lambda: {"version": 1, "devices": {}}, indent=None) as store:
        kept = store.setdefault("devices", {}).setdefault(link.name, [])
        if kept and kept[0]["patch"] == data.hex():
            return
        kept.insert(0, {"time": dt.datetime.now().isoformat(timespec="seconds"), "why": why, "patch": data.hex()})
        del kept[BACKUPS_KEPT:]


def _load(link: Link, data: bytes, label: str, current: bytes | None = None, keep: bool = True,
          ask: bool = True) -> None:
    """Loads a patch into the device's edit buffer, keeping what was there (keep=False
    only for a sound creaper put there itself a moment ago). ask=False only for putting
    back a sound the synth itself held a moment ago."""
    p = _profile(link, "load a sound into it")
    # Whatever the source (the library, a backup, a project someone else made), only a
    # whole patch is sent: these files can be edited, and a short one is a malformed dump.
    if not isinstance(data, (bytes, bytearray)) or len(data) != p.PROGRAM_BYTES:
        raise ValueError(f"'{label}' isn't a whole {p.MODEL} patch ({len(data) if hasattr(data, '__len__') else 0} "
                         f"bytes, a patch is {p.PROGRAM_BYTES}), so it wasn't sent to {link.name}")
    if current is None and p.READS_PATCH:
        current = _read_program(link)   # no backup, no load
    if ask and not _was_asked(link.name):
        confirm_with_user(f"load sounds into the {link.name}'s edit buffer during this session (its stored programs "
                          "aren't changed, and the sound it has now is kept as a backup)")
        _mark_asked(link.name)
    if keep and current is not None and current != data:
        _backup(link, current, f"before loading {label}")
    request = p.load_request(link.channel, data)
    if not p.ACKS_LOAD:
        # A device that confirms nothing: the sound is sent, and audition_hardware is the check.
        call("send_midi", device=link.out, messages=request[0], open_audio=True)
        return
    function, _ = _ask(link, request, "sent it a sound", wait=4.0)
    error = p.load_error(function)
    if error:
        raise ValueError(f"{link.name} refused the sound ({error}); its edit buffer is as it was")


def _summary(link: Link, data: bytes) -> dict:
    prog = link.profile.decode_program(data)
    return {"device": link.name, **prog}


def _project_tempo(bar: float | None) -> tuple[float, bool] | None:
    """(the project's tempo at a bar, whether the tempo changes during the project); the
    opening tempo when no bar is given. None when REAPER can't be asked."""
    try:
        tempo_map = call("get_tempo_map")
        bpm = opening = float(tempo_map["start_tempo_bpm"])
        tempos = {round(opening, 3)}
        for change in tempo_map.get("changes") or []:
            at = change.get("position") or {}
            tempos.add(round(float(change["bpm"]), 3))
            # A change counts from its bar on; one inside a bar, for a part that starts inside that bar too.
            before = at.get("bar", 1) < int(bar or 1) or (at.get("bar", 1) == int(bar or 1) and (
                at.get("beat", 1) <= 1.001 or (bar or 1) > int(bar or 1)))
            if bar is not None and before:
                bpm = float(change["bpm"])
    except (BridgeError, KeyError, TypeError, ValueError):
        return None
    return bpm, len(tempos) > 1


def _match_tempo(link: Link, data: bytes, bar: float | None) -> tuple[bytes, dict | None]:
    """A patch that runs at a tempo of the synth's own (an arpeggiator, a synced delay or
    LFO) set to the project's tempo, and what to tell about it. The patch comes back
    unchanged, with nothing to tell, when nothing in it runs at the tempo."""
    p = link.profile
    uses = p.tempo_features(data)
    if not uses:
        return data, None
    told: dict[str, Any] = {"runs_at_the_tempo": uses, "patch_tempo_bpm": p.tempo(data)}
    found = _project_tempo(bar)
    if found is None:
        told["note"] = "REAPER's tempo couldn't be read, so the patch's tempo was left as it was."
    else:
        bpm, varies = found
        was = p.tempo(data)
        data, now = p.with_tempo(data, bpm)
        told["patch_tempo_bpm"] = now
        said = [f"The patch's tempo was set to {now} BPM (it was {was}) to match the project"
                + (f" at bar {bar:g}" if bar is not None else "") + "." if now != was else
                f"The patch's tempo already matches the project ({now} BPM)."]
        if abs(now - bpm) > 0.01:
            lo, hi = p.TEMPO_RANGE
            said.append(f"The project runs at {bpm:g} BPM and the synth's tempo is a whole number from {lo} to {hi}, "
                        "so the two drift apart over a long part: keep such parts short, or sync the synth to MIDI "
                        "clock.")
        if varies:
            said.append("The project's tempo changes"
                        + (": this is the tempo at that bar, so write the sound again (load_hardware_sound with "
                           "track and bar) where a part starts at another tempo." if bar is not None else
                           ": this is its opening tempo."))
        told["note"] = " ".join(said)
    if bar is not None:
        # In the song the part has to sit on the grid: a print of an arpeggio that waits for the
        # synth's own clock lands late (live-measured). Played by hand, the patch stays as it is.
        data, synced = p.start_on_the_note(data)
        if synced:
            told["arpeggiator"] = synced
    try:
        settings = _read_setup(link)       # the Clock setting is the user's to change on the synth: read now
    except ValueError:
        settings = link.device.get("midi_setup")
    told["clock"] = p.clock_note(settings)
    return data, told


# ------------------------------------------------------------ profile, patches

@tool(annotations=READ_ONLY)
def hardware_profile(
    name: Annotated[str, Field(description="Name in the hardware map (list_hardware)")],
    show: Annotated[Literal["parameters", "recipes", "setup"], Field(description=(
        "parameters = every sound parameter by name with its values; recipes = ready starting points (artist-style "
        "sounds, game sound effects) and the maker's presets worth knowing; setup = the synth's MIDI settings, read "
        "from it now"))] = "parameters",
    kind: Annotated[Literal["artist", "sfx", "song"] | None, Field(description="With show='recipes': only this kind")] = None,
) -> dict:
    """What creaper knows about a hardware synth: its sound parameters (the names
    set_hardware_params takes), its recipes (load_hardware_sound recipe=...), or its
    MIDI setup. Read 'parameters' once before designing a sound on it, and 'recipes'
    when the user asks for a known sound ("that Killers lead", a laser, an alarm, a
    robot voice): recipes say what they're based on and how to play them. 'setup'
    asks the synth which MIDI messages it accepts, whether its memory is protected,
    and which control change each knob uses (for add_midi_cc sweeps in a part)."""
    link = _link(name)
    p = _profile(link, "list its parameters, recipes or MIDI settings")
    if show == "recipes":
        return {"device": link.name, "recipes": p.describe_recipes(kind),
                "factory_programs": p.FACTORY_NOTES,
                "note": "Recipes are creaper's own starting points, written from published descriptions; each "
                        "was played and measured on one microKORG, not matched to its source by ear: load one, "
                        "audition_hardware, and tune it with the user. A "
                        "factory_program is selected with load_hardware_sound program=...; it's the maker's preset "
                        "only if that slot was never overwritten."}
    if show == "setup":
        setup = _read_setup(link)
        problems = p.setup_problems(setup)
        return {"device": link.name, **setup, **({"to_fix": problems} if problems else {})}
    return {"device": link.name, **p.describe(), "live_control": (
        "set_hardware_params live=true moves knob parameters with control changes (no gap in the sound); everything "
        "else is set by loading the whole patch into the edit buffer.")}


@tool(annotations=READ_ONLY)
def sound_design_guide(
    sound: Annotated[str | None, Field(description=(
        "A kind of sound ('string pad', 'acid bass', 'sync lead', 'bell', 'riser', 'synth kick'...) or a technique "
        "('detune', 'glide', 'pulse width', 'key tracking'...); leave out for the method and the list of both"))] = None,
    synth: Annotated[str | None, Field(description=(
        "A hardware synth from list_hardware: with a profile (hardware_profile works on it) the blueprint also "
        "comes as that synth's own parameter values"))] = None,
    blueprint: Annotated[dict | None, Field(description=(
        "With synth: a blueprint of your own in the same fields and real units (a built-in one changed, or built "
        "from techniques), e.g. {'voices': 'mono', 'glide_ms': 90, 'osc2': {'wave': 'saw', 'cents': 12}, 'filter': "
        "{'cutoff_hz': 1800, 'env_octaves': 2.5}, 'amp_env': {'attack_ms': 5, 'release_ms': 200}}: it comes back as "
        "that synth's parameter values"))] = None,
) -> dict:
    """How to design a sound on a synthesizer: creaper's sound-design knowledge. Read it
    before building or changing a patch on ANY synth, hardware or plugin, instead of
    guessing values.

    With no sound: the method (design against numbers that can be measured, in what
    order to build, how to check) and the names of every blueprint and technique.
    With a sound: what it is, its blueprint in real units (milliseconds, hertz, cents,
    octaves: oscillators, filter, envelopes, modulation, effects), how to play it,
    what a recording of it should measure, and what to change when it doesn't.
    With a technique: what it does and the amounts that work. With a family ('pad',
    'bass', 'lead', 'keys', 'fx', 'drums'): its sounds and what each is.
    With synth: the blueprint translated into that synth's parameter values through
    its measured calibration ('on_this_synth': pass params to set_hardware_params with
    start_from='init', then audition_hardware with the 'play' phrase and compare with
    'check'), what was set by rule of thumb, what the synth can't do, and the synth's
    calibration (what its 0-127 values are in real units) for working out any other
    value. For a plugin synth, set the nearest controls by name (get_fx_parameters,
    set_fx_parameters display_value takes real units) and measure with
    audition_instrument. An advanced patch is a blueprint plus techniques: start from
    the nearest sound, change its blueprint in real units, and pass it as blueprint=
    with synth= for the values (don't work out 0-127 values by eye: the controls aren't
    even), one step at a time."""
    if blueprint is not None:
        if synth is None:
            raise ValueError("blueprint needs synth: the hardware synth whose parameter values it should become")
        unknown = sound_design.unknown_fields(blueprint)
        if unknown:
            raise ValueError(f"not blueprint fields: {', '.join(unknown)}. The fields: "
                             + "; ".join(f"{part or 'top level'}: {', '.join(sorted(names))}"
                                         for part, names in sound_design.FIELDS.items()))
        return {"blueprint": blueprint, "on_this_synth": _on_synth(synth, blueprint)}
    if sound is None:
        out = sound_design.index()
        out["next"] = ("sound_design_guide(sound=...) for a blueprint or a technique; add synth=<a hardware synth> "
                       "for its own parameter values.")
        return out
    technique = sound_design.find_technique(sound)
    found = sound_design.find(sound)
    asked = " ".join(sound.lower().replace("-", " ").split())
    if technique is not None and technique[0] == asked and (found is None or found[0] != asked):
        found = None          # "detune" is the technique, not the detuned bass that mentions it
    listed = sound_design.family(sound) if found is None and technique is None else None
    if listed is not None:
        return {"family": listed[0], "sounds": listed[1], "next": "sound_design_guide(sound=<one of these>) for its blueprint"}
    if found is None and technique is None:
        raise ValueError(f"no blueprint or technique named '{sound}'. Sounds: {', '.join(sound_design.SOUNDS)}. "
                         f"Techniques: {', '.join(sound_design.TECHNIQUES)}. For anything else, start from the "
                         "nearest sound and apply techniques to it.")
    if found is None:
        return {"technique": technique[0], "how": technique[1]}
    name, entry = found
    out = {"sound": name, **{k: v for k, v in entry.items() if k != "aka"}, "also_known_as": entry.get("aka")}
    if technique is not None:
        out["technique"] = {technique[0]: technique[1]}
    if synth is not None:
        out["on_this_synth"] = _on_synth(synth, entry["blueprint"])
    return out


def _on_synth(synth: str, blueprint: dict) -> dict | str:
    """A blueprint as one hardware synth's parameter values, or why creaper can't say."""
    link = _link(synth)
    p = link.profile
    if p is None or not hasattr(p, "from_design"):
        return (f"creaper has no profile for {link.name}, so it can't set these values on it: the user sets the sound "
                "on the synth from the blueprint, and audition_hardware measures the result against 'check'.")
    made = p.from_design(blueprint)
    return {
        "device": link.name, **made,
        "how": (f"set_hardware_params(name={link.name!r}, params=<these>, start_from='init'), then "
                "audition_hardware with a phrase from 'play', and compare with 'check'. These values come "
                "from this model's measured calibration: a starting point, tuned by measuring."),
        "calibration": p.calibration_summary(),
    }


@tool(annotations=READ_ONLY)
def read_hardware_patch(
    name: Annotated[str, Field(description="Name in the hardware map")],
    backups: Annotated[bool, Field(description="Also list the sounds creaper has kept as backups")] = False,
) -> dict:
    """Reads the sound a hardware synth has right now (its edit buffer, including knob
    moves the user made by hand) as named parameters. Use it to see what a sound is
    made of before changing it, to learn from a preset the user likes, or to check a
    change arrived. Nothing on the synth changes. backups=true also lists the sounds
    creaper kept before each load (load_hardware_sound backup=N brings one back)."""
    link = _link(name)
    out = _summary(link, _read_program(link))
    if backups:
        out["backups"] = [{"backup": i + 1, "time": b["time"], "kept": b["why"]} for i, b in enumerate(_backups(link))]
    return out


@tool()
def set_hardware_params(
    name: Annotated[str, Field(description="Name in the hardware map")],
    params: Annotated[dict[str, Any], Field(description=(
        "Parameter names and values from hardware_profile, e.g. {'cutoff': 60, 'osc1_wave': 'pulse', "
        "'patch1_source': 'lfo1', 'patch1_dest': 'pitch', 'patch1_int': 20}"))],
    timbre: Annotated[Literal[1, 2, "both"], Field(description="Which timbre of a layer program the sound parameters go to")] = 1,
    start_from: Annotated[Literal["current", "init"], Field(description=(
        "current = change the sound the synth has now; init = start from creaper's plain sound (one saw, filter "
        "open, no effects) and apply params to that"))] = "current",
    live: Annotated[bool, Field(description=(
        "Send control changes instead of reloading the patch: no gap in a sounding note, but only knob parameters "
        "work and nothing confirms they arrived"))] = False,
) -> dict:
    """Sets sound parameters on a hardware synth by name. By default it reads the
    synth's current sound, changes the named parameters and loads the result into the
    EDIT BUFFER (stored programs are untouched; the previous sound is kept as a
    backup), and the synth confirms. This is the step of the sound-design loop:
    set, audition_hardware (records and measures it), compare with what was wanted,
    set again. Change a few things at a time so the measurement shows what each did.
    live=true is for small moves while the user listens to a held note."""
    link = _link(name)
    p = _profile(link, "set its parameters by name")
    if not params:
        raise ValueError("give at least one parameter to set")
    if live:
        setup = link.device.get("midi_setup") or _read_setup(link)
        blocked = p.live_blocked(setup)
        if blocked:
            raise ValueError(f"{link.name} {blocked} Or leave live off.")
        messages, cant = p.live(params, timbre, link.channel, setup)
        if cant:
            raise ValueError(f"these can't be set live on the {link.name} (no knob or NRPN reaches them): "
                             f"{', '.join(cant)}. Set them with live=false.")
        call("send_midi", device=link.out, messages=messages, open_audio=True)
        return {"device": link.name, "sent_live": sorted(params), "note": (
            "Sent as control changes; the synth doesn't confirm them. read_hardware_patch shows the result.")}
    current = _read_program(link)
    base = p.init_program(current) if start_from == "init" else current
    new = p.apply(base, params, timbre=timbre)
    _load(link, new, "new parameter values", current=current)
    before, after = p.flat(p.decode_program(base)), p.flat(p.decode_program(new))
    return {"device": link.name, "loaded": True, **p.brief(new),
            "set": {k: v for k, v in after.items() if k.split(".")[-1] in params and k != "name"},
            **({"started_from": "creaper's plain sound"} if start_from == "init" else
               {"was": {k: v for k, v in before.items() if k.split(".")[-1] in params and after.get(k) != v}})}


def _part_notes(track: str | int, written: dict) -> list[dict]:
    """The notes a sound written into the song will play: from its bar to the part's next
    sound (or the end), positions in quarter notes of the song."""
    try:
        part = call("hardware_tracks", track=track)["hardware_tracks"][0]
        start = float(written["part_starts"]["qn"])
        later = [float(s["start"]["qn"]) for s in part.get("sounds") or [] if float(s["start"]["qn"]) > float(written["sends_at"]["qn"]) + 0.01]
        end = min(later) if later else float("inf")
        notes = []
        for item in part.get("parts") or []:
            at = float(item["start"]["qn"])
            for n in call("get_midi_notes", item_id=item["id"]).get("notes", []):
                if start - 0.01 <= at + n["start"] < end:
                    notes.append({"pitch": n["pitch"], "start": at + n["start"], "length": n["length"]})
        return notes
    except (BridgeError, KeyError, TypeError, ValueError):
        return []     # the fit is advice: a part that can't be read just gets none


Tags = Annotated[list[str] | None, Field(description="Role and character, e.g. ['lead', 'glide'] or ['sfx', 'laser']")]


@tool()
def save_hardware_sound(
    name: Annotated[str, Field(description="Name in the hardware map")],
    sound: Annotated[str, Field(min_length=1, max_length=60, description="What to call the sound, e.g. 'Plasma Rifle'")],
    tags: Tags = None,
    description: Annotated[str | None, Field(max_length=server.MAX_DESCRIPTION_CHARS, description=(
        "What it sounds like, what it's for and how to play it, in a sentence or two"))] = None,
    overwrite: Annotated[bool, Field(description="Replace a saved sound with the same name")] = False,
) -> dict:
    """Saves the sound a hardware synth has right now to the user's sound library (the
    whole patch, read from the synth), so load_hardware_sound can bring it back in any
    project. Hardware forgets its edit buffer when another program is selected or the
    power goes off: save every sound the user likes, and every sound a song or a game
    effect uses. list_sounds kind='hardware' shows them."""
    link = _link(name)
    data = _read_program(link)
    entry = server.sound_library.save_hardware(sound, link.profile.MODEL, data.hex(), link.profile.decode_program(data),
                                               tags=tags, description=description, overwrite=overwrite)
    return {"saved": entry["name"], "device": link.name, "tags": entry["tags"]}


@tool()
def load_hardware_sound(
    name: Annotated[str, Field(description="Name in the hardware map")],
    sound: Annotated[str | None, Field(description="A sound saved with save_hardware_sound (list_sounds kind='hardware')")] = None,
    recipe: Annotated[str | None, Field(description="A recipe from hardware_profile show='recipes', e.g. 'laser zap'")] = None,
    program: Annotated[str | None, Field(description="One of the synth's own stored programs, e.g. 'b.14' on a microKORG")] = None,
    backup: Annotated[int | None, Field(ge=1, description="A sound creaper kept: 1 = the one replaced by the latest load")] = None,
    track: Annotated[str | int | None, Field(description=(
        "Also write the sound into the song on this hardware part (a track from create_hardware_track), so the "
        "part recalls it"))] = None,
    bar: Annotated[float | None, Field(ge=1, description="With track: the bar where the part using this sound starts")] = None,
) -> dict:
    """Puts a sound on a hardware synth: one from the sound library, one of creaper's
    recipes, one of the synth's own stored programs, or a backup. It goes into the
    EDIT BUFFER only; the sound that was there is kept as a backup (backup=1 undoes
    the latest load). With track and bar the sound is also written into the song, sent
    half a second before that bar: do this for EVERY hardware part, because the synth
    holds one sound at a time and the project doesn't store it otherwise. Leave room
    before a part that starts at bar 1. Give exactly one of sound, recipe, program,
    backup.
    A sound with an arpeggiator, a tempo-synced delay or a tempo-synced LFO runs at a
    tempo stored in the patch: it's set to the project's tempo (at that bar, when the
    sound is written into the song) and the result says so under 'tempo', with what
    the synth's clock setting means for it. An arpeggio written into the song also gets
    its key sync turned on, so it starts with the part's first note.
    A recipe written into the song is checked against the part's notes from that bar
    to the part's next sound: 'fit' says when notes lie outside the register the sound
    works in or the part plays more notes at once than the sound has voices. A recipe that names its own tempo (an
    effect's speed) and a backup loaded without a track keep theirs."""
    if sum(x is not None for x in (sound, recipe, program, backup)) != 1:
        raise ValueError("give exactly one of sound, recipe, program or backup")
    if (track is None) != (bar is None):
        raise ValueError("to write the sound into the song give both track and bar")
    link = _link(name)
    p = _profile(link, "load sounds into it or write them into the song")
    current = _read_program(link) if p.READS_PATCH else None   # a synth that can't send its sound: nothing to keep
    out: dict[str, Any] = {"device": link.name}
    own_tempo = backup is not None and track is None      # an undo brings back exactly what was there
    if program is not None:
        number = p.program_number(program)
        if not _was_asked(link.name):
            confirm_with_user(f"change the sound on the {link.name} during this session (its stored programs aren't "
                              "changed, and the sound it has now is kept as a backup)")
            _mark_asked(link.name)
        if not p.READS_PATCH:
            # It can be told to change program, but not asked what the program holds.
            if track is not None:
                raise ValueError(f"a {p.MODEL} can't send its sounds over MIDI, so creaper can't write one of its "
                                 "stored programs into the song; the user selects it on the synth before printing")
            call("send_midi", device=link.out, messages=p.select_program(link.channel, number), open_audio=True)
            return {"device": link.name, "loaded": f"program {p.program_name(number)}",
                    "note": "Sent as a program change; this synth can't confirm it or send back what it holds. "
                            "audition_hardware hears the result."}
        _backup(link, current, f"before selecting program {p.program_name(number)}")
        call("send_midi", device=link.out, messages=p.select_program(link.channel, number), open_audio=True)
        hw._sleep(0.3)
        data = _read_program(link)
        label = f"program {p.program_name(number)}"
        if data == current:
            out["note"] = (f"The sound didn't change: either {p.program_name(number)} was already selected, or the "
                           "synth ignores program changes (hardware_profile show='setup' tells).")
        if p.FACTORY_NOTES.get(p.program_name(number)):
            out["factory_preset"] = p.FACTORY_NOTES[p.program_name(number)] + " (if the slot was never overwritten)"
        stored = data
        data, tempo = _match_tempo(link, data, bar)
        if data != stored:
            # The stored program stays as it is; the edit buffer gets it at the project's tempo.
            _load(link, data, label, current=stored, keep=False, ask=False)
    else:
        if sound is not None:
            _, entry = server.sound_library.find(sound)
            state = server.sound_library.state(entry) if entry.get("source") == "hardware" else {}
            if state.get("model") != p.MODEL:
                raise ValueError(f"'{entry['name']}' isn't a {p.MODEL} sound (it's from {entry.get('plugin_name')})")
            data, label = bytes.fromhex(state["patch"]), entry["name"]
        elif recipe is not None:
            key, made = p.find_recipe(recipe)
            data, label = p.build({**made, "name": key}, template=current), key
            out["how_to_play"] = made["play"]
            for field in ("style_of", "evidence"):
                if made.get(field):
                    out[field] = made[field]
            if made.get("factory"):
                out["factory_program"] = f"{made['factory']} (load_hardware_sound program='{made['factory']}')"
            own_tempo = p.TEMPO_PARAM in made.get("params", {})   # an effect whose speed is the recipe
        else:
            kept = _backups(link)
            if backup > len(kept):
                raise ValueError(f"there {'is' if len(kept) == 1 else 'are'} {len(kept)} backup(s) for {link.name}"
                                 " (read_hardware_patch backups=true lists them)")
            data, label = bytes.fromhex(kept[backup - 1]["patch"]), f"backup {backup} ({kept[backup - 1]['time']})"
        tempo = None
        if len(data) == p.PROGRAM_BYTES:      # anything else is refused by _load, by name
            if own_tempo and p.tempo_features(data):
                tempo = {"runs_at_the_tempo": p.tempo_features(data), "patch_tempo_bpm": p.tempo(data),
                         "note": ("Kept at its own tempo, not the project's: " + (
                             "the recipe's speed is part of the effect." if recipe is not None else
                             "a backup comes back exactly as it was.")
                             + f" set_hardware_params {p.TEMPO_PARAM}=... changes it."),
                         "clock": p.clock_note(link.device.get("midi_setup"))}
            elif not own_tempo:
                data, tempo = _match_tempo(link, data, bar)
        _load(link, data, label, current=current)
    out.update({"loaded": label, **p.brief(data), "tempo": tempo,
                "undo": ("load_hardware_sound backup=1 brings back the sound it replaced"
                         if current is not None and data != current else None)})
    if track is not None:
        written = call("hardware_patch_item", track=track, start_bar=bar, name=label, lead_seconds=PATCH_LEAD_S,
                       sysex=p.program_dump(link.channel, data))
        out["written_into_song"] = written
        if recipe is not None and hasattr(p, "part_fit"):
            fit = p.part_fit(made, _part_notes(track, written))
            if fit:
                out["fit"] = fit
        if not written.get("loads_before_the_part"):
            out["warning"] = ("The part starts at the very beginning of the project, so on playback the sound loads "
                              "as the first note plays. print_hardware sends it ahead and isn't affected; for live "
                              "playback, start the part a bar later.")
    return {k: v for k, v in out.items() if v is not None}


@tool(annotations=DESTRUCTIVE)
def write_hardware_program(
    name: Annotated[str, Field(description="Name in the hardware map")],
    program: Annotated[str, Field(description="The program to overwrite, e.g. 'A.11' on a microKORG")],
) -> dict:
    """Stores the sound in a hardware synth's edit buffer into one of its programs,
    OVERWRITING what's stored there. Only when the user asks for a sound to live on
    the synth itself, and names the slot (or agrees to one). In creaper's chat panel
    it asks the user every time, naming the slot. In other apps (Claude Desktop,
    Claude Code) creaper can't ask, so it refuses, unless the user has set
    CREAPER_ALLOW_UNCONFIRMED=1: then confirm the slot with the user in the chat
    yourself first. creaper keeps a copy of the program being replaced (as a backup)
    when the synth lets it. Sounds are safe in the sound library without this
    (save_hardware_sound)."""
    link = _link(name)
    p = _profile(link, "write its stored programs")
    number = p.program_number(program)
    slot = p.program_name(number)
    # Before anything is sent to the synth: where creaper can't ask, nothing is touched.
    server.require_asking(f"OVERWRITE program {slot} on the {link.name}")
    setup = _read_setup(link)
    if setup["memory_protect"]:
        raise ValueError(f"{link.name}'s memory protect is on, so it would refuse. The user turns it off on the synth "
                         f"({p.PROTECT_HELP}), then try again.")
    wanted = _read_program(link)
    kept = False
    if setup["program_change_enabled"]:
        # Look at what's in the slot (select it, read it), then put the sound back in the buffer.
        call("send_midi", device=link.out, messages=p.select_program(link.channel, number), open_audio=True)
        hw._sleep(0.3)
        stored = _read_program(link)
        _backup(link, stored, f"program {slot} before it was overwritten")
        kept = True
        _load(link, wanted, f"the sound to store in {slot}", current=stored, ask=False)
    confirm_with_user(f"OVERWRITE program {slot} on the {link.name} with the sound in its edit buffer ("
                      + ("creaper has kept a copy of the program that's there now" if kept else
                         "the program that's there now can't be backed up and will be lost") + ")",
                      irreversible=True)
    _mark_asked(link.name)   # only now: a Deny above leaves later loads still to be asked
    function, _ = _ask(link, p.write_request(link.channel, number), f"asked it to write program {slot}", wait=4.0)
    if p.write_error(function):
        raise ValueError(f"{link.name} reported a {p.write_error(function)}: program {slot} was not changed")
    return {"device": link.name, "written": slot, "program_change_number": number,
            "previous_program": "kept: read_hardware_patch backups=true lists it" if kept else "not backed up"}


# ------------------------------------------------------- recording passes

class PhraseNote(BaseModel):
    pitch: Annotated[int, Field(ge=0, le=127, description="MIDI note, 60 = middle C")]
    at: Annotated[float, Field(ge=0, le=60, description="Seconds from the start")] = 0.0
    length: Annotated[float, Field(gt=0, le=60, description="Seconds held")] = 1.0
    velocity: Annotated[int, Field(ge=1, le=127)] = 100


def _wait_for_stop(seconds: float) -> None:
    hw._sleep(seconds + 0.3)
    waited = 0.0
    while waited < 15.0:
        status = server.bridge.call("recording_status", on_user_wait=lambda: None)
        if not status.get("recording"):
            return
        hw._sleep(0.25)
        waited += 0.25


def _take(start: dict, finish: dict) -> tuple[list[dict], bool]:
    """One recording pass: (the items recorded, whether REAPER's save/delete prompt is on)."""
    started = call("hardware_take_start", **start)
    try:
        _wait_for_stop(started["end_seconds"] - started["start_seconds"])
    finally:
        done = call("hardware_take_finish", timeout=STOP_PROMPT_WAIT + 60.0, **finish)
    return done.get("items") or [], bool(started.get("stop_prompt"))


def _audio_of(items: list[dict], link: Link) -> tuple[np.ndarray, int, float, str]:
    """(audio, sample rate, where the file starts against the pass start, file path)."""
    item = next((i for i in items if i.get("file")), None)
    if item is None:
        raise ValueError("Nothing was recorded: REAPER has no new recording (if its save/delete window came up, the "
                         "take was deleted there). Ask the user to choose 'Save all' next time, or to turn the "
                         "window off in Preferences > Recording.")
    audio, fs = sf.read(item["file"], dtype="float32", always_2d=True)
    return audio, int(fs), float(item.get("file_starts_at_seconds") or 0.0), item["file"]


def _discard(path: str) -> None:
    # REAPER keeps a recording's peaks beside it or in a "peaks" folder there (seen live: one
    # stray .reapeaks per audition), depending on the user's settings.
    for f in (Path(path), Path(path + ".reapeaks"), Path(path).parent / "peaks" / (Path(path).name + ".reapeaks")):
        try:
            f.unlink(missing_ok=True)
        except OSError:
            pass   # REAPER may still hold it; a stray scratch file does no harm


def _answers(link: Link) -> bool | None:
    """Whether the synth answers over MIDI right now; None when it has no way to (no MIDI
    input saved, or no profile that knows a question it answers)."""
    if link.inp is None or not _reads(link):
        return None
    try:
        _read_program(link)
        return True
    except ValueError:
        return False


def _silence_cause(link: Link, peak_db: float) -> str:
    """Why a recording of the synth came out silent, most basic cause first: REAPER's
    device before the synth, the synth before its cables."""
    first = link.device.get("audio_input")
    where = f"interface input {first}" + (f" and {first + 1}" if link.device.get("stereo") else "")
    st = setup.status()
    if st is not None:
        setup_problem = next((p for p in setup.find_problems(link.name, link.device, st)
                              if p["blocks"] or p["problem"] == "input looks built in"), None)
        if setup_problem:
            return (f"Nothing came in on {where}, and the cause is REAPER's setup, not the synth: "
                    f"{setup_problem['what']} {setup_problem['fix']} setup_hardware(name={link.name!r}, "
                    "action='fix') opens that page and waits for the change.")
    device = setup._plain(((st or {}).get("audio") or {}).get("input") or "") or "REAPER's audio device"
    if peak_db < DEAD_DBFS:
        return (f"Nothing at all came in on {where}: the recording is digital silence, not even the faint noise an "
                f"open input has. So no signal reaches REAPER from '{device}' on that input: it's the wrong input "
                "device or a muted one (setup_hardware shows which device REAPER uses), Windows is blocking it "
                "(Settings > Privacy & security > Microphone: let desktop apps use it), or the synth's audio is on "
                "another input pair than the one saved. Not the synth's volume.")
    answers = _answers(link)
    if answers:
        return (f"Nothing came in on {where}, but the input is live (its noise floor is there) and {link.name} "
                "answers over MIDI, so it's on and listening. In this order: its volume knob, the audio cables "
                f"from its outputs to {where}, the interface's input gain for those inputs.")
    if answers is False:
        return (f"Nothing came in on {where}, and {link.name} doesn't answer over MIDI either, so the note probably "
                f"never reached it: is it switched on, is the MIDI cable from the interface's MIDI OUT in its MIDI "
                f"IN, and is it on channel {link.channel}? (test_hardware plays one note to listen for.)")
    return (f"Nothing came in on {where}: the input is live but silent. Check that a note sounds at all "
            f"(test_hardware), then {link.name}'s volume knob, its audio cables, and the interface's input gain.")


# Where the test sound should peak: noise far below, and room above for the sounds that
# are louder than it (live, 2026-11-13: with the test sound at -12.6 dBFS a distorted lead
# printed at -5.5, 7 dB hotter). Wide on purpose: the same setting read 1-2 dB apart from one
# test note to the next (detuned saws beat), and a user sent back to the knobs for half a dB
# stops trusting the check.
LEVEL_WINDOW = (-20.0, -12.0)
LEVEL_AIM = -16.0
NOTHING_DBFS = -50.0           # a channel under this while the test sound plays gets next to nothing
ONE_SIDED_DB = 12.0            # two inputs of a stereo pair this far apart: the part sits in one ear
MATCH_DB = 1.5


def _peaks_db(audio: np.ndarray) -> list[float]:
    """Each channel's peak in dBFS."""
    if not audio.size:
        return []
    return [round(20 * math.log10(p), 1) if p > 0 else -200.0 for p in np.max(np.abs(audio), axis=0)]


def _level_problem(audio: np.ndarray, link: Link) -> str | None:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    peak_db = 20 * math.log10(peak) if peak > 0 else -200.0
    if peak_db < SILENT_DBFS:
        return _silence_cause(link, peak_db)
    if peak_db > HOT_DBFS:
        return ("The recording clips: the interface's input gain is too high for this sound. Ask the user to turn "
                f"it down and record again; setup_hardware(name={link.name!r}, action='level') measures how far.")
    peaks = _peaks_db(audio)
    if link.device.get("stereo") and len(peaks) == 2 and abs(peaks[0] - peaks[1]) > ONE_SIDED_DB:
        first = int(link.device.get("audio_input") or 1)
        quiet = first + (0 if peaks[0] < peaks[1] else 1)
        return (f"The recording is one-sided: interface input {first} peaks at {peaks[0]:.0f} dBFS and input "
                f"{first + 1} at {peaks[1]:.0f}, so it plays from one speaker (unless the sound is panned hard on "
                f"purpose). Input {quiet}'s gain is far below the other's, or its cable is loose. "
                f"setup_hardware(name={link.name!r}, action='level') measures both inputs and says how far to turn "
                "each; then record this again.")
    return None


def level_advice(peaks: list[float], first_input: int, synth: str) -> list[str]:
    """What to turn, from each input's peak while the synth plays about its loudest sound.
    Nothing to say = the level is right."""
    said = []
    lo, hi = LEVEL_WINDOW
    for i, peak in enumerate(peaks):
        n = first_input + i
        if peak > HOT_DBFS:
            said.append(f"Input {n} clips: turn its gain down about a quarter turn.")
        elif peak < NOTHING_DBFS or (len(peaks) == 2 and peak < max(peaks) - 20):
            # Dead, or far under its partner: not a matter of a few dB on the knob.
            jack = ("L/MONO" if i == 0 else "R") if len(peaks) == 2 else "output"
            said.append(f"Input {n} gets next to nothing (peak {peak:.0f} dBFS): its gain knob is at the bottom, the "
                        f"cable from the {synth}'s {jack} jack is loose or missing, or the input is switched to the "
                        "wrong kind (LINE for a synth, not instrument/Hi-Z, and no pad).")
        elif peak < lo:
            said.append(f"Input {n} is low (peak {peak:.0f} dBFS): turn its gain up about {LEVEL_AIM - peak:.0f} dB.")
        elif peak > hi:
            said.append(f"Input {n} is hot (peak {peak:.0f} dBFS): turn its gain down about {peak - LEVEL_AIM:.0f} dB.")
    if len(peaks) == 2 and not said and abs(peaks[0] - peaks[1]) > MATCH_DB:
        low = first_input + (0 if peaks[0] < peaks[1] else 1)
        said.append(f"Input {low} is {abs(peaks[0] - peaks[1]):.0f} dB under the other: nudge its gain up to match, "
                    "or the synth leans to one side.")
    if said and peaks and max(peaks) < -30:
        said.insert(0, f"First turn the {synth}'s own volume knob up to about three quarters: a quiet synth into a "
                       "lot of gain is noisier than a loud synth into a little.")
    return said


def check_input_level(name: str) -> dict:
    """setup_hardware's 'level' action: plays the synth's loudest sound (or, without a
    profile, the sound it has), records it and says how far to turn each input's gain."""
    link = _link(name)
    if not link.device.get("audio_input"):
        raise ValueError(f"creaper doesn't know which interface inputs {link.name}'s audio comes back on: "
                         "save_hardware it again with audio_input (list_inputs names them)")
    checked = setup.preflight(link.name, link.device)
    own = _reads(link)
    confirm_with_user(f"play a loud two-second test note on the {link.name} and record it to check the interface's "
                      "input level" + (" (its sound is put back afterwards)" if own else ""))
    notes = [{"pitch": 48, "at": 0.3, "length": 2.0, "velocity": 127}]
    current = _read_program(link) if own else None
    if own:
        loud = link.profile.level_patch(current)
        _load(link, loud, "the level test sound", current=current, ask=False)
    try:
        items, _ = _take(_scratch(link, notes, 3.8), {})
    finally:
        if own:
            _load(link, current, "the sound from before the level test", current=loud, keep=False, ask=False)
    audio, fs, _, path = _audio_of(items, link)
    _discard(path)
    peaks = _peaks_db(audio)
    first = int(link.device["audio_input"])
    advice = level_advice(peaks, first, link.name)
    # Well after the note: what the input does with nothing playing. Only with the test sound,
    # which stops dead: a sound of the user's may still be ringing or echoing there.
    quiet = audio[-int(0.6 * fs):] if own else audio[:0]
    floor = round(20 * math.log10(max(1e-9, float(np.sqrt(np.mean(quiet ** 2))))), 1) if quiet.size else None
    measured_at = setup.signature(checked.status)
    with jsonstore.updating(hw._store_path(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        data["devices"][link.name]["input_level"] = {
            "peaks_dbfs": peaks, "ok": not advice, "at": measured_at,
            "time": dt.datetime.now().isoformat(timespec="seconds")}
    out: dict[str, Any] = {
        "device": link.name, "level_ok": not advice,
        "inputs": {f"input {first + i}": f"{p:.1f} dBFS peak" for i, p in enumerate(peaks)},
        "aim": (f"this test sound peaking between {LEVEL_WINDOW[0]:.0f} and {LEVEL_WINDOW[1]:.0f} dBFS on every input: "
                "distorted and resonant sounds come out up to 8 dB louder, and still must not clip"),
        "noise_floor_dbfs": floor,
        "measured_with": ("a loud plain sound (four saws in unison, filter open)" if own else
                          "the sound the synth had (creaper has no profile to set a loud one): have the user "
                          "choose its loudest sound first, or leave a few dB more room"),
    }
    if advice:
        out["turn"] = advice
        out["next"] = ("Tell the user exactly these, one knob at a time, on the interface's front panel; when they "
                       "say it's done, call this again. Repeat until level_ok (usually two or three rounds).")
    else:
        out["next"] = "The input level is right; it's kept with the device. Carry on."
    return checked.onto(out)


def level_note(link: Link, st: dict | None) -> str | None:
    """A reminder when this device's input level was never set on these audio settings."""
    kept = link.device.get("input_level") or {}
    if kept.get("ok") and kept.get("at") == setup.signature(st):
        return None
    return (f"The interface's input level for {link.name} hasn't been set"
            + (" (the last check found it off)" if kept and not kept.get("ok") else "")
            + f": setup_hardware(name={link.name!r}, action='level') plays a test note and says how far to turn each "
            "gain knob. Do it with the user before recording parts, so prints aren't quiet, clipped or one-sided.")


def _scratch(link: Link, notes: list[dict], seconds: float) -> dict:
    if not link.device.get("audio_input"):
        raise ValueError(f"creaper doesn't know which interface inputs {link.name}'s audio comes back on: "
                         "save_hardware it again with audio_input (list_inputs names them)")
    return {"scratch": True, "midi_device": link.out, "channel": link.channel,
            "audio_input": link.device["audio_input"], "stereo": bool(link.device.get("stereo")), "notes": notes,
            "seconds": seconds}


MEASURED = ("level_db", "peak_db", "attack_ms", "decay_s", "sustain_db", "release_s", "centroid_hz", "pitch_hz",
            "cents_off", "semitones_off", "octave_offset", "pitch_glide", "clarity", "silent")


def _pitch_path(mono: np.ndarray, fs: int, points: int = 10) -> list[float | None]:
    """The pitch heard at evenly spaced moments while the sound lasts (None = no clear pitch)."""
    env = np.abs(mono)
    loud = np.where(env > 0.03 * (env.max() or 1.0))[0]
    if loud.size < fs * 0.1:
        return []
    a, b = int(loud[0]), int(loud[-1])
    win = int(0.06 * fs)
    out: list[float | None] = []
    for start in np.linspace(a, max(a, b - win), points).astype(int):
        hz, clarity = listen._pitch(mono[start:start + win], fs)
        out.append(round(hz) if hz and clarity > 0.6 else None)
    return out


def measure_take(audio: np.ndarray, fs: int, notes: list[dict], file_offset: float, latency: float) -> dict:
    """What a recorded test phrase sounds like, note by note and as a whole."""
    mono = audio.mean(axis=1).astype(np.float64)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    out: dict[str, Any] = {"peak_dbfs": round(20 * math.log10(peak), 1) if peak > 0 else None}
    if peak <= 0 or 20 * math.log10(peak) < SILENT_DBFS:
        out["silent"] = True
        return out
    env = np.abs(mono)
    sounding = np.where(env > peak * 0.01)[0]
    out["sounds_for_seconds"] = round((sounding[-1] - sounding[0]) / fs, 2)
    width = listen.width_db(audio, fs, len(audio) / fs)
    if width is not None:
        out["stereo_width_db"] = width
    measured = []
    ordered = sorted(notes, key=lambda n: n["at"])
    for i, n in enumerate(ordered[:8]):
        a = int((n["at"] - file_offset + latency) * fs)
        end = ordered[i + 1]["at"] if i + 1 < len(ordered) else len(mono) / fs + file_offset
        seg = mono[max(0, a): max(0, int((end - file_offset + latency) * fs))]
        if seg.size < fs * 0.05:
            continue
        f = listen.features(seg, fs, note_off=min(n["length"], seg.size / fs), expected_hz=listen.note_freq(n["pitch"]))
        measured.append({"note": midi_to_note(n["pitch"]), **{k: f[k] for k in MEASURED if f.get(k) is not None}})
    out["notes"] = measured
    path = _pitch_path(mono, fs)
    if any(path):
        out["pitch_over_time_hz"] = path
    return out


AUDITION_LEGEND = (
    "level_db = loudness while held; attack_ms = time to reach full level; decay_s = time to fall 30 dB while held "
    "(none = it sustains); release_s = ring-out after the note-off; centroid_hz = brightness (higher is brighter); "
    "cents_off / semitones_off = tuning against the note played; pitch_glide above 1 = the pitch starts high and "
    "falls (zaps, kicks); clarity near 0 = noise, near 1 = a clear pitch; pitch_over_time_hz = the pitch at ten "
    "moments across the sound (sweeps, sirens, arpeggios); stereo_width_db about -40 = mono, above -10 = wide.")


@tool()
def audition_hardware(
    name: Annotated[str, Field(description="Name in the hardware map")],
    notes: Annotated[list[PhraseNote] | None, Field(max_length=32, description=(
        "The test phrase; default one middle C held for 1.5 s. Play what the sound is for: a low note for a bass, "
        "a short high note for a blip, a held chord for an arpeggio or a pad"))] = None,
    tail_seconds: Annotated[float, Field(ge=0.2, le=20, description="Recorded after the last note ends, for the release and echoes")] = 1.5,
    keep_file: Annotated[bool, Field(description="Keep the recording and return its path (e.g. for insert_audio_file)")] = False,
) -> dict:
    """Hears a hardware synth: plays a test phrase to it, records its audio from the
    interface for a few seconds on temporary tracks past the end of the project
    (removed again afterwards), and measures the recording: level, attack, decay,
    release, brightness, pitch and tuning per note, and the pitch over time. This is
    creaper's only ear for hardware, so use it after every change in a sound-design
    loop instead of guessing, and tell the user what was measured. It takes real
    time (the phrase plus the tail). In creaper's chat panel it asks the user once per
    session (elsewhere the app's own approval of the tool call is the question). REAPER's
    'save or delete new files' window is turned off for the session where REAPER
    allows (7.74 and later); on older REAPER it appears after every recording and the
    user must click Save: setup_warnings says where to turn it off. The synth plays
    its current sound: load or set one first.
    REAPER's setup is checked first: it refuses, with the fix, when REAPER is recording
    another device than the synth's interface or its MIDI port is disabled, and a silent
    recording comes back with its cause ('problem'): act on that, don't guess cables."""
    link = _link(name)
    checked = setup.preflight(link.name, link.device)
    phrase = [n.model_dump() for n in notes] if notes else [{"pitch": 60, "at": 0.0, "length": 1.5, "velocity": 100}]
    phrase = [{**n, "at": n["at"] + 0.25} for n in phrase]      # a moment for the transport to start
    seconds = max(n["at"] + n["length"] for n in phrase) + tail_seconds
    start = _scratch(link, phrase, seconds)
    if not _was_asked(f"record:{link.name}"):
        confirm_with_user(f"record short test clips from the {link.name} during this session (temporary tracks at the "
                          "end of the project, removed after each one)")
        _mark_asked(f"record:{link.name}")
    items, prompt = _take(start, {})
    audio, fs, offset, path = _audio_of(items, link)
    try:
        latency = setup.latency_ms(link.device, checked.status) / 1000
        out: dict[str, Any] = {"device": link.name, "recorded_seconds": round(len(audio) / fs, 2),
                               **measure_take(audio, fs, phrase, offset, latency)}
    finally:
        if not keep_file:
            _discard(path)
    problem = _level_problem(audio, link)
    if problem:
        out["problem"] = problem
    else:
        out["legend"] = AUDITION_LEGEND
        setup.remember_audio(link.name, link.device, checked.status, heard=True)
    checked.onto(out)
    if keep_file:
        out["file"] = path
    if prompt and not any("after every recording" in w for w in checked.warnings):
        out["note"] = ("REAPER asked the user to save or delete the recording. For a sound-design session, suggest "
                       "turning that window off: " + setup.STOP_PROMPT_FIX + ".")
    return out


CLICKS = 5
CLICK_NOTE_S = 0.1        # short, so a sound the user chose (no profile to set a click) can't smear into the next


@tool()
def calibrate_hardware_latency(name: Annotated[str, Field(description="Name in the hardware map")]) -> dict:
    """Measures how late a hardware synth's audio arrives after REAPER sends it a note
    (MIDI interface, the synth's own response, audio conversion), and saves it in the
    hardware map. print_hardware then shifts every recording by that much, so
    hardware parts line up with plugin parts, and audition_hardware measures from
    the right moment. Run it once per device, and again after changing the audio
    buffer size or interface. It plays five short clicks: for those few seconds it
    puts a click sound in the synth's edit buffer, then puts the user's sound back.
    It records, so in creaper's chat panel the user is asked (and REAPER's save/delete
    window may appear).
    On a synth creaper has no profile for (hardware_profile refuses it), creaper can't
    set the click: FIRST ask the user to put a short, percussive sound on the synth
    (instant attack, no delay or reverb), then call this. It plays five short notes
    with whatever sound is there; a slow attack would be measured as latency."""
    link = _link(name)
    p = link.profile
    own_click = _reads(link)   # creaper can set a click and put the user's sound back; else the user sets one
    checked = setup.preflight(link.name, link.device)
    if own_click:
        confirm_with_user(f"play five test clicks on the {link.name} and record them to measure its latency (its current "
                          "sound is put back afterwards)")
    else:
        confirm_with_user(f"play five short test notes on the {link.name} and record them to measure its latency. "
                          "creaper can't set a sound on this synth, so put a short, percussive one on it first "
                          "(instant attack, no delay or reverb)")
    current = _read_program(link) if own_click else None
    notes = [{"pitch": 72, "at": 0.5 + 0.5 * i, "length": CLICK_NOTE_S, "velocity": 127} for i in range(CLICKS)]
    if own_click:
        click = p.click_patch(current)
        # ask=False: the question above covers the click and putting the sound back, and only
        # those. It isn't a yes to loading sounds from then on, which stays its own question.
        _load(link, click, "the calibration click", current=current, ask=False)
    try:
        items, _ = _take(_scratch(link, notes, notes[-1]["at"] + 1.0), {})
    finally:
        if own_click:
            _load(link, current, "the sound from before the calibration", current=click, keep=False, ask=False)
    audio, fs, offset, path = _audio_of(items, link)
    try:
        problem = _level_problem(audio, link)
        if problem:
            raise ValueError(problem)
        mono = np.abs(audio.mean(axis=1))
        delays = []
        for n in notes:
            a = int((n["at"] - offset) * fs)
            window = mono[max(0, a): a + int(0.4 * fs)]
            if window.size and window.max() > 0:
                onset = int(np.argmax(window >= 0.25 * window.max()))
                delays.append(onset / fs * 1000)
    finally:
        _discard(path)
    if len(delays) < 3:
        raise ValueError("couldn't find the clicks in the recording; check that the synth sounded (test_hardware)")
    latency = float(np.median(delays))
    spread = float(max(delays) - min(delays))
    measured_at = setup.signature(checked.status)
    with jsonstore.updating(hw._store_path(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        entry = data["devices"][link.name]
        entry["latency_ms"] = round(latency, 1)
        if measured_at:
            # Latency belongs to the audio settings it was measured on (WASAPI and ASIO differ
            # by tens of milliseconds): kept per setting, so switching back needs no new measurement.
            entry["latency_at"] = measured_at
            entry.setdefault("latencies", {})[measured_at] = round(latency, 1)
    setup.remember_audio(link.name, link.device, checked.status, heard=True)
    out = {"device": link.name, "latency_ms": round(latency, 1), "clicks_measured": len(delays),
           "spread_ms": round(spread, 1), "saved": True}
    if measured_at:
        out["measured_on"] = setup._readable(measured_at)
    if spread > 8:
        out["note"] = ("The clicks arrived unevenly (MIDI timing jitter): the saved value is the middle one. A "
                       "smaller audio buffer in REAPER usually tightens it.")
    if not own_click:
        out["measured_with"] = ("the sound the synth had (creaper has no profile to set a click on it). The value is "
                                "right only if that sound starts at once: a slow attack is measured as latency. If "
                                "it looks high, have the user set a sharper sound and measure again.")
    return out


# ------------------------------------------------------- tracks and printing

def _item_label(item: dict) -> str:
    name = hw.one_line(item.get("sound") or item.get("name") or "", 60)
    where = (item.get("start") or {}).get("bar")
    return (f"'{name}' " if name else "") + (f"at bar {where}" if where else f"at {item.get('start_seconds', 0):.1f} s")


def _sound_patch(link: Link, sysex: Any, label: str) -> bytes:
    """The patch in a sound item's SysEx, or a refusal: only the device's own
    current-program dump of a whole patch is ever played or sent. A project from
    someone else can hold anything here (a write request stores the edit buffer over
    a program)."""
    p = link.profile
    if p is None:
        # creaper never writes a sound for a device it has no profile for, so it can't vouch for this one.
        raise ValueError(f"not recorded: the sound item {label} on this part holds SysEx that would be sent to "
                         f"{link.name}, and creaper has no profile for that synth to check it with (SysEx can "
                         "overwrite a synth's stored programs). Delete that item; the user sets the sound on the "
                         "synth itself.")
    try:
        data = p.patch_in_message(sysex) if isinstance(sysex, str) else None
    except (ValueError, TypeError, IndexError):
        data = None
    if data is None or len(data) != p.PROGRAM_BYTES:
        raise ValueError(f"not recorded: the sound item {label} on this part doesn't hold a {p.MODEL} sound as "
                         f"creaper writes them (a current-program dump of {p.PROGRAM_BYTES} bytes), and it would be "
                         f"sent to {link.name}. Delete that item and write the sound again with load_hardware_sound "
                         "track=..., bar=....")
    return data


def _check_part_sysex(link: Link, part: dict) -> None:
    """Refuses to play a hardware part whose MIDI track would send SysEx creaper didn't
    write: notes and control changes can't hurt a synth, SysEx can rewrite its memory.
    Allowed: creaper's sound items, each holding only whole current-program dumps."""
    items = [(i, False) for i in part.get("parts") or []] + [(i, True) for i in part.get("sounds") or []]
    if any("sysex_count" not in i for i, _ in items):
        raise ValueError("not recorded: the creaper bridge in REAPER is older than this server and can't show what "
                         "the part would send to the synth. The user updates it with `creaper install-bridge` and "
                         "restarts the bridge script in REAPER.")
    for item, is_sound in items:
        count, events = int(item.get("sysex_count") or 0), list(item.get("sysex_events") or [])
        if not is_sound:
            if count:
                raise ValueError(f"not recorded: the MIDI item {_item_label(item)} on {part['midi_track']['name']} "
                                 f"holds {count} SysEx message(s) that creaper didn't write, and playing it would "
                                 f"send them to {link.name} (SysEx can overwrite a synth's stored programs). The "
                                 "user removes them in REAPER's MIDI editor (the event list shows them), or the "
                                 "item is deleted and the part written again.")
            continue
        label = _item_label(item)
        if count > len(events):
            raise ValueError(f"not recorded: the sound item {label} holds {count} SysEx messages, more than a sound "
                             f"creaper wrote has, and they would be sent to {link.name}. Delete that item and write "
                             "the sound again with load_hardware_sound track=..., bar=....")
        for event in events:
            _sound_patch(link, event, label)
        if item.get("sysex"):
            _sound_patch(link, item["sysex"], label)


@tool()
def create_hardware_track(
    name: Annotated[str, Field(description="Name in the hardware map")],
    part: Annotated[str, Field(min_length=1, max_length=40, description="What the part is, e.g. 'MK Lead', 'MK Bass'")],
    monitor: Annotated[bool, Field(description=(
        "Hear the synth through REAPER while writing the part. Turn off if the user hears the synth directly from "
        "the interface (direct monitoring), or it sounds doubled"))] = True,
) -> dict:
    """Sets up a part for a hardware synth as two tracks: '<part> (MIDI)', whose notes
    REAPER sends to the synth's MIDI port, and '<part>', an audio track that records
    the synth's interface inputs. Write the part on the MIDI track like any other
    (create_midi_item, add_midi_notes, add_midi_cc for knob sweeps), give it its sound
    with load_hardware_sound track=..., bar=..., then print_hardware records it to
    audio, after which mixing, mastering and exporting treat it like any audio track.
    One pair per part (lead, bass, each sound effect): the synth plays one sound at a
    time, so parts are printed one after another. (Two tracks rather than ReaInsert:
    ReaInsert forces every render to run in real time, and creaper measures and mixes
    with offline renders.) Any saved MIDI device gets a pair; on one creaper has no
    profile for, the user sets the sound on the synth before the print.
    A whole song with the synth: set_tempo first (sounds take the tempo), then a pair
    for every part it plays, named Bass, Pad, Lead and Counter, BEFORE build_song, which
    then writes those parts onto them. hardware_profile show='recipes' lists sounds by
    role with the register each works in and the notes it plays at once; give each
    part one at its first bar, and another at any section where the sound should
    change (a darker bass under the verse, a solo sound for the instrumental), and act
    on the 'fit' each load reports. Print the parts one after another, then mix as
    usual: the printed audio tracks are the parts."""
    link = _link(name)
    if not link.device.get("audio_input"):
        raise ValueError(f"creaper doesn't know which interface inputs {link.name}'s audio comes back on: "
                         "save_hardware it again with audio_input (list_inputs names them)")
    checked = setup.preflight(link.name, link.device)
    made = call("create_hardware_tracks", name=part.strip(), device=link.name, midi_device=link.out,
                channel=link.channel, audio_input=link.device["audio_input"], stereo=bool(link.device.get("stereo")),
                monitor=monitor)
    made["next"] = ("Write the part on the MIDI track, then load_hardware_sound with track and bar, then "
                    "print_hardware." if link.profile is not None else
                    f"Write the part on the MIDI track. creaper has no profile for {link.name}, so it can't load or "
                    "store its sound: the user sets the sound on the synth, audition_hardware hears it, then "
                    "print_hardware records the part with it.")
    if not link.device.get("latency_ms"):
        made["note"] = (f"{link.name}'s latency hasn't been measured: calibrate_hardware_latency once, so prints "
                        "line up with the other tracks.")
    level = level_note(link, checked.status)
    if level:
        made["input_level"] = level
    return checked.onto(made)


@tool()
def print_hardware(
    track: Annotated[str | int, Field(description="A hardware part: either of its two tracks, by name or number")],
    start_bar: Annotated[float | None, Field(ge=1, description="Default: where the part's first MIDI item starts")] = None,
    end_bar: Annotated[float | None, Field(ge=1, description="Default: where its last MIDI item ends")] = None,
    tail_seconds: Annotated[float, Field(ge=0, le=30, description="Extra time recorded after the end for releases and echoes")] = 2.0,
) -> dict:
    """Records a hardware part to audio in real time: plays its MIDI track to the
    synth and records the synth onto the part's audio track, shifted by the device's
    measured latency. Before the pass it sends the part's sound (the one written into
    the song with load_hardware_sound track=...) and mutes other tracks that play the
    same synth; after it, the MIDI track is muted so the synth doesn't play over its
    own recording, and an older print over the same bars is replaced. Then the part is
    ordinary audio: measure_tracks, auto_mix, mastering, export_mix and export_regions
    (sound effects) all work on it. Print again after changing the notes or the
    sound. It takes as long as the part lasts; in creaper's chat panel the user is
    asked first, and REAPER's save/delete window may appear when it stops (they choose
    Save). It refuses a part whose MIDI track holds SysEx creaper didn't write (only a
    sound from load_hardware_sound track=... may be there): SysEx can overwrite the
    synth's stored programs."""
    found = call("hardware_tracks", track=track, start_bar=start_bar, end_bar=end_bar)
    part = found["hardware_tracks"][0]
    link = _link(part["device"])
    checked = setup.preflight(link.name, link.device)
    parts = part.get("parts") or []
    if not parts:
        raise ValueError(f"{part['midi_track']['name']} has no MIDI items yet: write the part first")
    start = found.get("start_seconds", min(i["start_seconds"] for i in parts))
    end = found.get("end_seconds", max(i["end_seconds"] for i in parts))
    if end <= start:
        raise ValueError("end_bar must be after start_bar")
    length = end - start + tail_seconds
    _check_part_sysex(link, part)   # before the user is asked: nothing foreign is played to the synth
    confirm_with_user(f"record '{part['audio_track']['name']}' from the {link.name} in real time ({length:.0f} seconds)")
    earlier = [s for s in part.get("sounds") or [] if s["start_seconds"] <= start + 0.01 and s.get("sysex")]
    out: dict[str, Any] = {"device": link.name}
    mute_items = []
    if earlier:
        sound = max(earlier, key=lambda s: s["start_seconds"])
        # ask=False: the print was just allowed, and the part's own sound is part of it.
        _load(link, _sound_patch(link, sound["sysex"], _item_label(sound)), sound["sound"], ask=False)
        out["sound"] = sound["sound"]
        if sound["end_seconds"] > start:
            mute_items.append(sound["id"])
    elif link.profile is None:
        out["warning"] = (f"creaper has no profile for {link.name}, so the song doesn't hold this part's sound: it "
                          "was recorded with whatever the synth had. Before printing it again, the user puts the "
                          "right sound on the synth.")
    else:
        out["warning"] = ("No sound is written into the song for this part, so it was recorded with whatever the "
                          "synth had. load_hardware_sound with track and bar fixes that for good.")
    latency = setup.latency_ms(link.device, checked.status) / 1000
    items, prompt = _take({"track": track, "start_seconds": start, "end_seconds": end + tail_seconds,
                           "mute_items": mute_items},
                          {"latency_seconds": latency, "replace": True, "mute_midi": True,
                           "take_name": f"{part['audio_track']['name']} (printed)"})
    audio, fs, _, _ = _audio_of(items, link)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    shown = sum(float(i.get("length_seconds") or 0) for i in items)
    if shown < 0.9 * length - latency:
        # Live, 2026-11-13: the recordings were whole and the items 10 ms long, so the mix had no bass.
        out["problem"] = (f"The recording is {length:.0f} seconds long but its item in the project shows only "
                          f"{shown:.1f}: the part will be missing from the song. Look at the item on "
                          f"'{part['audio_track']['name']}' (get_track_details), delete it and print again; if it "
                          "happens again, tell the user: something in REAPER trims new recordings.")
    out.update({"printed": part["audio_track"], "items": [{k: i[k] for k in ("id", "start", "length_seconds")} for i in items],
                "peak_dbfs": round(20 * math.log10(peak), 1) if peak > 0 else None,
                "latency_compensated_ms": round(latency * 1000, 1), "midi_track": "muted (unmute it to edit and reprint)"})
    out["peaks_dbfs"] = _peaks_db(audio)
    problem = out.get("problem") or _level_problem(audio, link)
    if problem:
        out["problem"] = problem
    level = level_note(link, checked.status)
    if level and not problem:
        out["input_level"] = level
    if not latency:
        out["note"] = "This device's latency isn't measured (calibrate_hardware_latency), so the print may sit late."
    if prompt:
        from .record_tools import STOP_PROMPT_NOTE   # here, not at the top: record_tools may still be loading
        out["stop_prompt"] = STOP_PROMPT_NOTE
    return checked.onto(out)
