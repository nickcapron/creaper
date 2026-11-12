"""MCP tools for hardware synths and drum machines on MIDI: find what's connected (the
standard MIDI identity request), keep a map of each device (its MIDI ports, channel and
the interface inputs its audio comes back on), play a test note, and a panic button.

Safety: creaper only sends fixed, harmless messages here (the identity request, notes,
all-notes-off). Nothing that writes a device's memory is sent from this module. Ports
are saved by name, not number: REAPER renumbers MIDI devices when they're replugged."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field

from . import hardware_setup as setup
from . import jsonstore
from .server import DESTRUCTIVE, READ_ONLY, bridge, call, confirm_with_user, tool

IDENTITY_REQUEST = "F0 7E 7F 06 01 F7"   # Universal Non-Realtime, General Information, Identity Request, any device
REPLY_WAIT_S = 0.6                       # how long a device gets to answer the identity request
_sleep = time.sleep                      # tests replace it

# Manufacturer IDs (MIDI Manufacturers Association), for naming what answers.
MAKERS = {
    "01": "Sequential", "04": "Moog", "33": "Clavia (Nord)", "3E": "Waldorf", "40": "Kawai", "41": "Roland",
    "42": "Korg", "43": "Yamaha", "44": "Casio", "47": "Akai",
    "002029": "Novation", "002032": "Behringer", "002033": "Access", "00203C": "Elektron", "00206B": "Arturia",
}

# Models identified from their identity reply, from each maker's MIDI implementation.
# Key: (manufacturer hex, family code, member code); codes are LSB-first 14-bit numbers.
KNOWN_MODELS: dict[tuple[str, int, int], dict[str, Any]] = {
    ("42", 0x0058, 0x0011): {
        "model": "Korg microKORG", "kind": "synth", "device_id_is_channel": True,
        "setup": ("Its audio comes from the L/MONO and R outputs on the back: plug them into two interface inputs "
                  "(L/MONO alone gives mono). On the microKORG's MIDI settings: 'CtrlChg' filter ENA lets creaper "
                  "turn its knobs over MIDI, and 'SystemEx' filter ENA lets it read and load patches. "
                  "It's 4-voice, one patch at a time (two timbres in a layer or split patch)."),
    },
}


def _store_path() -> Path:
    return Path(bridge.directory) / "hardware.json"


def _devices() -> dict[str, dict]:
    return jsonstore.read(_store_path(), dict).get("devices", {})


def _ports() -> dict:
    """The MIDI ports REAPER has enabled, and apart from them the ones that are plugged in
    but switched off in REAPER (nothing goes through those, without any error)."""
    ports = call("list_inputs")
    outs, ins = ports.get("midi_outputs") or [], ports.get("midi_inputs") or []
    return {"outputs": [p for p in outs if p.get("enabled") is not False],
            "inputs": [p for p in ins if p.get("enabled") is not False],
            "disabled_outputs": [p for p in outs if p.get("enabled") is False],
            "disabled_inputs": [p for p in ins if p.get("enabled") is False],
            "audio_inputs": ports.get("audio_inputs") or []}


def _port_number(ports: list[dict], ref: str | int | None, kind: str,
                 disabled: list[dict] | None = None) -> tuple[int, str] | None:
    """(device number, name) for a port given by number or name (exact, else a unique part).
    `disabled` = ports that are plugged in but not enabled, to say so instead of 'no such port'."""
    if ref is None:
        return None

    def switched_off(match) -> None:
        p = next((p for p in disabled or [] if match(p)), None)
        if p is not None:
            raise ValueError(
                f"MIDI {kind} '{p['name']}' is plugged in but not enabled in REAPER, so nothing "
                f"{'sent to it arrives' if kind == 'output' else 'it sends comes in'}. {setup.MIDI_PREFS}: "
                + setup._midi_pick([p["name"]] if kind == "input" else [], [p["name"]] if kind == "output" else [])
                + " setup_hardware(action='fix') opens that page and waits for the change.")

    if isinstance(ref, int) or (isinstance(ref, str) and ref.strip().isdigit()):
        for p in ports:
            if p["device"] == int(ref):
                return p["device"], p["name"]
        switched_off(lambda p: p["device"] == int(ref))
        raise ValueError(f"there's no MIDI {kind} {ref}; list_hardware names the ports")
    exact = [p for p in ports if p["name"].lower() == ref.lower()]
    near = exact or [p for p in ports if ref.lower() in p["name"].lower()]
    if len(near) == 1:
        return near[0]["device"], near[0]["name"]
    if not near:
        switched_off(lambda p: ref.lower() in p["name"].lower())
        listed = ", ".join(p["name"] for p in ports) or "none"
        raise ValueError(f"no MIDI {kind} is named like '{ref}'; the {kind}s REAPER has enabled: {listed}")
    raise ValueError(f"'{ref}' matches several MIDI {kind}s: " + ", ".join(p["name"] for p in near))


def _bytes(hexstr: str) -> list[int]:
    return [int(hexstr[i:i + 2], 16) for i in range(0, len(hexstr), 2)]


def decode_identity_reply(hexstr: str) -> dict | None:
    """The identity reply's fields, or None if the message isn't one.
    F0 7E <device id> 06 02 <maker: 1 byte, or 00 + 2> <family: 2> <member: 2> <version: 4> F7"""
    b = _bytes(hexstr.replace(" ", "").upper())
    if len(b) < 15 or b[0] != 0xF0 or b[1] != 0x7E or b[3] != 0x06 or b[4] != 0x02 or b[-1] != 0xF7:
        return None
    i = 5
    if b[i] == 0x00:
        maker, i = "".join(f"{x:02X}" for x in b[i:i + 3]), i + 3
    else:
        maker, i = f"{b[i]:02X}", i + 1
    if len(b) < i + 8 + 1:
        return None
    family = b[i] | (b[i + 1] << 7)
    member = b[i + 2] | (b[i + 3] << 7)
    version = b[i + 4:i + 8]
    out: dict[str, Any] = {"device_id": b[2], "maker_id": maker, "maker": MAKERS.get(maker),
                           "family": family, "member": member, "version": " ".join(f"{x:02X}" for x in version)}
    known = KNOWN_MODELS.get((maker, family, member))
    if known:
        out["model"] = known["model"]
        out["kind"] = known["kind"]
        if known.get("device_id_is_channel") and b[2] < 16:
            out["channel"] = b[2] + 1
        out["setup"] = known["setup"]
    return out


def _replies_since(after: int, limit: int = 64) -> tuple[int, list[dict]]:
    got = call("recent_midi_input", after=after, limit=limit)
    return int(got.get("latest") or after), got.get("events") or []


@tool()
def scan_hardware() -> dict:
    """Finds the hardware synths and drum machines on the MIDI ports: sends the standard
    MIDI identity request out of each MIDI output and listens on the inputs for the answer
    (maker, model, firmware, and for some the MIDI channel). It asks the user first. A
    device can only answer if its MIDI OUT is connected back to the computer and that
    input is enabled in REAPER (Preferences > MIDI Devices); devices that don't answer
    show up as silent ports. Then save_hardware with what was found plus which interface
    inputs its audio comes back on (ask the user; list_inputs names them). REAPER's
    setup is checked first: a closed audio device or MIDI ports that are plugged in but
    not enabled are named with their fix (setup_hardware walks the user through it)."""
    checked = setup.preflight(record=False)
    ports = _ports()
    if not ports["outputs"]:
        off = [p["name"] for p in ports["disabled_outputs"]]
        return {"found": [], "midi_inputs": ports["inputs"], "note": (
            "REAPER has no MIDI outputs enabled. In REAPER: Options > Preferences > Audio > MIDI Devices, "
            "double-click the MIDI interface under 'MIDI outputs' and choose Enable output (and enable its input "
            "under 'MIDI inputs'); setup_hardware(action='fix') opens that page and waits for the change."
            + (f" Plugged in but not enabled: {', '.join(off)}." if off else ""))}
    names = ", ".join(p["name"] for p in ports["outputs"])
    confirm_with_user(f"send a MIDI identity request (asks a device what it is; changes nothing) to: {names}")
    latest, _ = _replies_since(0, limit=1)   # only the newest sequence number: replies come after it
    found, silent = [], []
    for out in ports["outputs"]:
        call("send_midi", device=out["device"], messages=[IDENTITY_REQUEST])
        _sleep(REPLY_WAIT_S)
        latest_now, events = _replies_since(latest)
        latest = latest_now
        answers = []
        for e in events:
            reply = decode_identity_reply(e.get("hex", ""))
            if reply:
                inp = next((p["name"] for p in ports["inputs"] if p["device"] == e.get("device")), None)
                answers.append({"midi_output": out["name"], "midi_input": inp, **reply})
        if answers:
            found.extend(answers)
        else:
            silent.append(out["name"])
    saved = _devices()
    for f in found:
        f["saved_as"] = next((n for n, d in saved.items() if d.get("midi_output") == f["midi_output"]
                              and d.get("model") == f.get("model")), None)
    out: dict[str, Any] = checked.onto({"found": found, "silent_outputs": silent})
    if ports["disabled_outputs"]:
        out["not_enabled_in_reaper"] = [p["name"] for p in ports["disabled_outputs"]]
    if not found and not ports["audio_inputs"]:
        out["note"] = (
            "No device answered, and REAPER's audio device looks closed (it lists no audio inputs). REAPER takes "
            "in MIDI through its audio engine, so nothing arrives until the audio device runs: Options > "
            "Preferences > Audio > Device, choose the audio interface (ASIO), OK, then scan again.")
    elif not found:
        out["note"] = (
            "No device answered. Check: the synth's MIDI OUT goes to the interface's MIDI IN (not only computer -> "
            "synth); the interface's MIDI input is enabled in REAPER (Preferences > MIDI Devices); the synth is on. "
            "Some devices never answer identity requests: save_hardware still works, from the port names.")
    elif silent:
        out["note"] = ("Silent outputs either have nothing on them, a device that doesn't answer identity requests, "
                       "or no MIDI cable back to the computer.")
    return out


@tool()
def save_hardware(
    name: Annotated[str, Field(min_length=1, max_length=60, description="What to call it, e.g. 'microKORG'")],
    midi_output: Annotated[str | int, Field(description="MIDI output it's played from: port name (or number, from scan_hardware/list_hardware)")],
    midi_input: Annotated[str | int | None, Field(description="MIDI input its MIDI OUT comes back on, if connected")] = None,
    channel: Annotated[int, Field(ge=1, le=16, description="MIDI channel it listens on")] = 1,
    audio_input: Annotated[int | None, Field(ge=1, description="First interface input its audio comes back on (list_inputs)")] = None,
    stereo: Annotated[bool, Field(description="Its audio uses audio_input and the next one as a stereo pair")] = True,
    kind: Annotated[Literal["synth", "drum machine", "multitimbral", "other"], Field()] = "synth",
    model: Annotated[str | None, Field(description="Make and model, e.g. from scan_hardware")] = None,
    notes: Annotated[str | None, Field(max_length=300, description="Anything worth remembering, e.g. 'patch A.11 is my lead'")] = None,
    interface: Annotated[str | None, Field(max_length=120, description=(
        "The audio interface its audio comes back through. Leave out: creaper works it out from the MIDI port's "
        "name. 'current' = the input device REAPER uses right now. Or its name as REAPER's audio settings show it"))] = None,
) -> dict:
    """Saves (or updates) a hardware synth or drum machine in creaper's hardware map:
    which MIDI output plays it, the MIDI input its replies come back on, its channel, and
    the interface inputs its audio returns on. Ports are kept by name so the map still
    works after replugging. creaper also keeps which audio interface the synth comes
    back through, and from then on refuses to record it while REAPER listens to another
    device (the laptop microphone, say). Give interface only when creaper's guess is
    wrong or it has none: ask the user which interface, by name. Returns the saved entry."""
    ports = _ports()
    out = _port_number(ports["outputs"], midi_output, "output", ports["disabled_outputs"])
    inp = _port_number(ports["inputs"], midi_input, "input", ports["disabled_inputs"])
    if audio_input is not None and ports["audio_inputs"] and audio_input + (1 if stereo else 0) > len(ports["audio_inputs"]):
        raise ValueError(f"the audio interface has {len(ports['audio_inputs'])} inputs; "
                         f"input {audio_input}{' and the next' if stereo else ''} isn't there")
    entry = {"midi_output": out[1], "midi_input": inp[1] if inp else None, "channel": channel,
             "audio_input": audio_input, "stereo": stereo if audio_input else None, "kind": kind,
             "model": model, "notes": notes}
    entry = {k: v for k, v in entry.items() if v is not None}
    st = setup.status()
    ident = ((st or {}).get("audio") or {}).get("input")
    if interface is None:
        found = setup.detect_interface(out[1])
    elif interface.strip().lower() == "current":
        if not ident:
            raise ValueError("REAPER has no audio device open, so there's no current input device to keep: "
                             "setup_hardware shows what to fix")
        found = {"name": setup._plain(ident), "match": [ident.lower()], "found_by": "user"}
    else:
        found = {"name": interface.strip(), "match": [interface.strip().lower()], "found_by": "user"}
    with jsonstore.updating(_store_path(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        before = data.setdefault("devices", {}).get(name.strip()) or {}
        if before.get("midi_output") == entry["midi_output"]:
            # The same device, saved again: what creaper measured and read from it stays.
            for key in ("midi_setup", "latency_ms", "latency_at", "latencies"):
                if key in before:
                    entry[key] = before[key]
            if interface is None and before.get("interface"):
                found = before["interface"]
        if found:
            entry["interface"] = found
        data["devices"][name.strip()] = entry
    setup.remember_audio(name.strip(), entry, st)
    saved = {"saved": name.strip(), **entry}
    if not found:
        saved["note"] = ("creaper couldn't tell which audio interface this comes back through (its MIDI port's name "
                         "doesn't match one). Ask the user, and save it again with interface=<its name>, or "
                         "interface='current' if REAPER's input device is already the right one"
                         + (f" ({setup._plain(ident)})." if ident else "."))
    elif setup.on_interface(ident, found) is False:
        saved["note"] = (f"REAPER's input device is '{setup._plain(ident)}', not the {found['name']}: "
                         f"setup_hardware(name={name.strip()!r}) says what to change before recording it.")
    return saved


@tool(annotations=READ_ONLY)
def list_hardware() -> dict:
    """The hardware synths and drum machines in creaper's map, whether each one's MIDI
    ports are connected right now, and every MIDI port REAPER has enabled."""
    ports = _ports()
    outs = {p["name"] for p in ports["outputs"]}
    ins = {p["name"] for p in ports["inputs"]}
    devices = []
    for name, d in _devices().items():
        devices.append({"name": name, **d, "connected": d.get("midi_output") in outs,
                        **({"midi_input_connected": d["midi_input"] in ins} if d.get("midi_input") else {})})
    out = {"devices": devices, "midi_outputs": ports["outputs"], "midi_inputs": ports["inputs"]}
    off = sorted({p["name"] for p in ports["disabled_outputs"] + ports["disabled_inputs"]})
    if off:
        out["plugged_in_but_not_enabled"] = off
    if not devices:
        out["note"] = "No hardware saved yet: scan_hardware finds what's connected."
    return out


@tool(annotations=DESTRUCTIVE)
def forget_hardware(name: Annotated[str, Field(description="Name in the hardware map")]) -> dict:
    """Removes a device from creaper's hardware map (the device itself is untouched)."""
    with jsonstore.updating(_store_path(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        devices = data.setdefault("devices", {})
        key = next((k for k in devices if k.lower() == name.strip().lower()), None)
        if key is None:
            raise ValueError(f"no hardware named '{name}'; saved: {', '.join(devices) or 'none'}")
        del devices[key]
    return {"forgotten": key}


def _device(name: str) -> tuple[str, dict]:
    devices = _devices()
    key = next((k for k in devices if k.lower() == name.strip().lower()), None)
    if key is None:
        raise ValueError(f"no hardware named '{name}'; saved: {', '.join(devices) or 'none'} (save_hardware)")
    return key, devices[key]


def _output_of(device: dict) -> int:
    ports = _ports()
    found = _port_number(ports["outputs"], device["midi_output"], "output", ports["disabled_outputs"])
    return found[0]


@tool()
def setup_hardware(
    name: Annotated[str | None, Field(description="A device in the hardware map; leave out before any is saved")] = None,
    action: Annotated[Literal["check", "fix", "finish"], Field(description=(
        "check = what's set up and what isn't (changes nothing); fix = open the REAPER settings page of the first "
        "problem and wait until the user has changed it; finish = hardware work is over, put REAPER's settings back"))] = "check",
) -> dict:
    """Gets REAPER ready for hardware synths, and is where to go whenever a hardware
    tool says the setup is wrong. Start a "set up my synth" request here.

    check reads the state: the audio device REAPER has open and whether it's the
    interface the synth is plugged into (not the laptop microphone), whether its MIDI
    ports are enabled and not just plugged in, and each problem with its fix in the
    words of REAPER's own windows (e.g. "Audio system: ASIO, ASIO driver: SSL ASIO
    Driver 1"). creaper can't change the audio device or enable a MIDI port itself.
    So: tell the user the fix in plain words, then call fix. It opens that settings
    page in REAPER and watches for up to two minutes; the moment the change is made
    it returns, so carry straight on without waiting for the user to say so. Call fix
    again while it reports another problem. Then scan_hardware, save_hardware,
    calibrate_hardware_latency.

    While hardware is worked on, creaper turns off two REAPER settings that get in the
    way (the save/delete window after each recording, and closing the audio device
    when REAPER is in the background) on REAPER 7.74 and later, and puts them back
    after half an hour without hardware work or when REAPER closes; call finish when
    the user says they're done with the synth, to put them back at once. On older
    REAPER, check names the two settings and where to untick them."""
    key, device = _device(name) if name else (None, None)
    if action == "finish":
        return setup.finish()
    if action == "fix":
        return setup.guided_fix(key, device)
    return setup.check(key, device)


@tool()
def test_hardware(
    name: Annotated[str, Field(description="Name in the hardware map")],
    note: Annotated[int, Field(ge=0, le=127, description="MIDI note, 60 = middle C")] = 60,
    velocity: Annotated[int, Field(ge=1, le=127)] = 100,
    seconds: Annotated[float, Field(gt=0, le=5)] = 1.0,
) -> dict:
    """Plays one note on a saved hardware device, so the user can check it's connected
    (they should hear it, and see their interface's input meter move). Ask them what
    they heard: creaper can't hear hardware until it records it."""
    key, device = _device(name)
    port = _output_of(device)
    ch = device.get("channel", 1) - 1
    call("send_midi", device=port, messages=[f"{0x90 | ch:02X} {note:02X} {velocity:02X}"])
    try:
        _sleep(seconds)
    finally:
        call("send_midi", device=port, messages=[f"{0x80 | ch:02X} {note:02X} 40"])
    return {"played": key, "note": note, "channel": ch + 1, "midi_output": device["midi_output"],
            "ask": "Ask the user whether they heard it and whether the interface input meter moved."}


@tool()
def midi_panic(name: Annotated[str | None, Field(description="One saved device; default every MIDI output")] = None) -> dict:
    """Silences hardware: All Notes Off and All Sound Off on all 16 channels of every
    MIDI output (or one saved device's). Use it whenever a hardware note hangs."""
    ports = _ports()["outputs"]
    if name:
        _, device = _device(name)
        targets = [p for p in ports if p["name"] == device["midi_output"]]
        if not targets:
            raise ValueError(f"{name}'s MIDI output '{device['midi_output']}' isn't connected")
    else:
        targets = ports
    messages = [f"{0xB0 | ch:02X} {cc:02X} 00" for ch in range(16) for cc in (0x7B, 0x78)]
    for p in targets:
        call("send_midi", device=p["device"], messages=messages)
    return {"silenced": [p["name"] for p in targets]}
