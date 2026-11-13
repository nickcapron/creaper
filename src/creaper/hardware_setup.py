"""Whether REAPER is set up for a hardware synth, checked before creaper plays or records
one: the audio device REAPER has open (the interface, or the laptop microphone?), whether
it runs, whether the synth's MIDI ports are enabled and not just plugged in, and the two
REAPER settings that get in the way of driving it from another app.

Every hardware tool runs preflight() first, so a wrong setup is named with its fix instead
of showing up as a silent recording. The interface a synth's audio comes back through is
worked out once (from its MIDI port's name, Windows' audio endpoints and the ASIO drivers
in the registry) and kept in the hardware map.

Nothing here changes REAPER's audio or MIDI settings: the user picks them in REAPER's
own windows, which creaper opens at the right page and then watches. REAPER's files are
only read, and only by the bridge inside REAPER (a tool process's view of AppData can be
a virtualized copy). Hooks for a later "do it for me" step: guided_fix() is the one place
that knows what has to change, and a problem's 'page' and 'pick' say where and to what."""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import jsonstore, server
from .bridge import BridgeError

FIX_WAIT_S = 120.0        # how long guided_fix watches for the user's change
FIX_POLL_S = 2.0
_sleep = time.sleep       # tests replace these
_now = time.monotonic

AUDIO_PREFS = "Options > Preferences > Audio > Device"
# REAPER 7 has a page each for MIDI outputs and inputs; before that, one "MIDI Devices" page.
MIDI_PREFS = ("Options > Preferences > Audio > MIDI Outputs and MIDI Inputs (one page, 'MIDI Devices', on older "
              "REAPER)")
CLOSE_INACTIVE_FIX = ("Options > Preferences > Audio: untick 'Close audio device when stopped and application is "
                      "inactive'")
STOP_PROMPT_FIX = ("Options > Preferences > Media > Recording: untick 'Prompt to save/delete/rename new files on "
                   "stop'")

# Words in a device name that say what it is, not whose it is.
_GENERIC = {"usb", "audio", "midi", "device", "interface", "driver", "asio", "in", "out", "input", "output", "port",
            "din", "the"}
# Inputs that are part of the computer: no synth is plugged into these.
_BUILT_IN = ("microphone array", "smart sound", "realtek", "built-in", "builtin", "macbook", "internal microphone",
             "webcam", "hands-free", "stereo mix", "nvidia", "high definition audio")
# Windows device enumerators of audio hardware that isn't part of the computer.
_INTERNAL_BUSES = ("INTELAUDIO", "HDAUDIO", "BTHENUM", "BTHHFENUM", "ROOT", "SWD")
# ASIO entries that wrap other devices rather than being an interface's own driver.
_WRAPPER_ASIO = ("asio4all", "flexasio", "fl studio asio", "generic low latency", "realtek asio", "voicemeeter",
                 "reaper", "magix low latency")


# ----------------------------------------------------------- REAPER's state

def status(session: str | None = None, open_audio: bool = False) -> dict | None:
    """The bridge's hardware_status, or None from a bridge too old to have it (the checks
    are then skipped: the tools work as they did)."""
    try:
        return server.call("hardware_status", session=session, open_audio=open_audio or None)
    except BridgeError as e:
        if "doesn't know" in str(e):
            return None
        raise


def signature(st: dict | None) -> str | None:
    """What a measured latency belongs to: audio system, input device, sample rate, block size."""
    audio = (st or {}).get("audio") or {}
    if not audio.get("input"):
        return None
    return "|".join(str(audio.get(k) or "") for k in ("mode", "input", "sample_rate", "block_size"))


def _port(st: dict, kind: str, name: str | None) -> dict | None:
    if not name:
        return None
    return next((p for p in (st.get("midi") or {}).get(kind) or [] if p.get("name") == name), None)


# ------------------------------------------------- which interface is the synth's

def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+]+", text.lower())


def _own_words(text: str) -> list[str]:
    """The words of a device name that identify it: 'SSL 2+ MIDI' -> ['ssl', '2+']."""
    return [w for w in _words(text) if w not in _GENERIC]


def product_of(port_name: str) -> str:
    """'SSL 2+ MIDI' -> 'SSL 2+'; 'MIDIIN2 (UM-ONE)' -> 'UM-ONE'."""
    inner = re.search(r"\(([^)]+)\)\s*$", port_name)
    name = inner.group(1) if inner and re.match(r"\s*MIDI(IN|OUT)\d*\s*\(", port_name, re.I) else port_name
    name = re.sub(r"\b(MIDI|DIN)(\s+(IN|OUT|PORT))?(\s*\d+)?\s*$", "", name.strip(), flags=re.I)
    return name.strip(" -:") or port_name.strip()


def _names(words: list[str]) -> list[str]:
    """Words that name a maker or product (letters, 3 or more), for matching across names."""
    return [w for w in words if len(w) >= 3 and re.search(r"[a-z]", w)]


def _subkeys(key: Any) -> list[str]:
    import winreg
    out, i = [], 0
    while True:
        try:
            out.append(winreg.EnumKey(key, i))
        except OSError:
            return out
        i += 1


def _value(key: Any, name: str) -> Any:
    import winreg
    try:
        return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None


def windows_audio() -> dict:
    """What Windows knows about audio hardware, read from the registry (reads only):
    asio = the ASIO drivers ({name, dll}: HKLM\\SOFTWARE\\ASIO and each CLSID's DLL), and
    inputs = the capture endpoints ({name, device, bus, active}). Empty off Windows."""
    out: dict[str, list[dict]] = {"asio": [], "inputs": []}
    if sys.platform != "win32":
        return out
    import winreg
    hklm, read = winreg.HKEY_LOCAL_MACHINE, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
    try:
        with winreg.OpenKey(hklm, r"SOFTWARE\ASIO", 0, read) as root:
            for name in _subkeys(root):
                dll = None
                try:
                    with winreg.OpenKey(root, name) as entry:
                        clsid = _value(entry, "CLSID")
                    with winreg.OpenKey(hklm, rf"SOFTWARE\Classes\CLSID\{clsid}\InprocServer32", 0, read) as server_key:
                        dll = _value(server_key, "")
                except OSError:
                    pass
                out["asio"].append({"name": name, "dll": dll})
    except OSError:
        pass
    try:
        with winreg.OpenKey(hklm, r"SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture", 0, read) as root:
            for guid in _subkeys(root):
                try:
                    with winreg.OpenKey(root, guid) as entry:
                        state = _value(entry, "DeviceState")
                    with winreg.OpenKey(root, guid + r"\Properties") as props:
                        name = _value(props, "{a45c254e-df1c-4efd-8020-67d146a850e0},2")        # "Input 1"
                        device = _value(props, "{b3f8fa53-0004-438e-9003-51a46e139bfc},6")      # "SSL 2+ USB Audio Device"
                        bus = _value(props, "{a45c254e-df1c-4efd-8020-67d146a850e0},24")        # "USB", "INTELAUDIO"
                except OSError:
                    continue
                if isinstance(name, str) and isinstance(device, str):
                    out["inputs"].append({"name": name, "device": device, "bus": bus if isinstance(bus, str) else None,
                                          "active": state == 1})
    except OSError:
        pass
    return out


def _external(endpoint: dict) -> bool:
    return (endpoint.get("bus") or "").upper() not in _INTERNAL_BUSES


def _asio_for(product: str, drivers: list[dict]) -> list[str]:
    """The ASIO drivers that belong to a product. A driver often shares only the maker with
    it ('SSL ASIO Driver 1' for the SSL 2+), so its DLL's folder counts too: the words of
    the path, and their initials ('Solid State Logic' -> ssl)."""
    wanted = _names(_own_words(product))
    if not wanted:
        return []
    scored = []
    for d in drivers:
        name = d.get("name") or ""
        if any(w in name.lower() for w in _WRAPPER_ASIO):
            continue
        in_name = set(_words(name))
        in_path: set[str] = set()
        for part in re.split(r"[\\/]", (d.get("dll") or "").lower()):
            words = _words(part)
            in_path.update(words)
            in_path.add("".join(w[0] for w in words))                 # 'solid state logic' -> ssl
            in_path.update(w for w in wanted if part.startswith(w))   # sslusbdriverasio_x64.dll
        hits_name = sum(w in in_name for w in wanted)
        hits = sum(w in in_name or w in in_path for w in wanted)
        if hits:
            scored.append((-hits_name, -hits, len(name), name))
    if not scored:
        return []
    best = min((s[0], s[1]) for s in scored)
    return [s[3] for s in sorted(scored) if (s[0], s[1]) == best]


def detect_interface(midi_port: str, audio: dict | None = None) -> dict | None:
    """The audio interface a MIDI port belongs to, when the names tie them together:
    {name, match, asio_driver?, asio_drivers?, windows_inputs?}. None when nothing ties
    them (a USB synth has its own MIDI port and no link to the interface its audio is
    plugged into), and off Windows. The names give a default; hearing the synth proves it."""
    audio = windows_audio() if audio is None else audio
    product = product_of(midi_port)
    wanted = _names(_own_words(product))
    if not wanted:
        return None
    inputs = []
    for e in audio.get("inputs") or []:
        device = e.get("device") or ""
        if not _external(e) or not e.get("active"):
            continue
        if product.lower() in device.lower() or all(w in _words(device) for w in wanted):
            inputs.append(e)
    asio = _asio_for(product, audio.get("asio") or [])
    if not inputs and not asio:
        return None
    out: dict[str, Any] = {"name": product, "match": [product.lower()], "words": wanted,
                           "found_by": "MIDI port name"}
    if asio:
        out["asio_driver"] = asio[0]
        if len(asio) > 1:
            out["asio_drivers"] = asio
        out["match"] += sorted({re.sub(r"\s*\d+$", "", a).lower() for a in asio})
    if inputs:
        # The endpoint with the plainest name is the one carrying every channel ("Input"
        # before "Input 1").
        inputs.sort(key=lambda e: (len(e["name"]), e["name"]))
        out["windows_inputs"] = [f"{e['name']} ({e['device']})" for e in inputs]
        out["match"] += sorted({e["device"].lower() for e in inputs})
    return out


def on_interface(ident: str | None, interface: dict | None) -> bool | None:
    """Whether REAPER's input device is this interface; None when that can't be told."""
    if not ident or not interface:
        return None
    low = ident.lower()
    known = (interface.get("audio") or {}).get("input")
    if known and known == ident:
        return True
    keys = [k for k in interface.get("match") or [] if k]
    if not keys:
        return None
    # REAPER's wording for an ASIO device isn't known for every driver: the maker's or
    # product's own word in it is enough ('ssl').
    return any(k in low for k in keys) or any(w in _words(ident) for w in interface.get("words") or [])


def looks_built_in(ident: str | None) -> bool:
    return bool(ident) and any(w in ident.lower() for w in _BUILT_IN)


def _plain(ident: str) -> str:
    """REAPER's device name without the audio system in front: 'WASAPI Microphone Array (..)'."""
    return re.sub(r"^(WASAPI|ASIO|WaveOut|DirectSound|WDM Kernel Streaming|CoreAudio|ALSA|JACK|PulseAudio)\s+", "",
                  ident).strip()


def _store() -> Path:
    return Path(server.bridge.directory) / "hardware.json"


def _update(name: str, change) -> None:
    with jsonstore.updating(_store(), lambda: {"version": 1, "devices": {}}, indent=2) as data:
        entry = data.get("devices", {}).get(name)
        if entry is not None:
            change(entry)


def interface_of(name: str | None, device: dict | None) -> dict | None:
    """The interface saved for a device; worked out from its MIDI port's name and saved the
    first time it's needed."""
    if not device:
        return None
    if device.get("interface"):
        return device["interface"]
    found = detect_interface(device.get("midi_output") or "")
    if found and name:
        device["interface"] = found
        _update(name, lambda entry: entry.setdefault("interface", found))
    return found


def remember_audio(name: str, device: dict, st: dict | None, heard: bool = False) -> None:
    """Keeps REAPER's audio device as the one this synth is recorded through, once it's known
    to be right: its input matches the interface, or (heard) the synth was just recorded
    through it."""
    audio = (st or {}).get("audio") or {}
    if not audio.get("input") or not audio.get("running"):
        return
    interface = dict(device.get("interface") or {})
    if on_interface(audio["input"], interface) is False:
        return
    if not interface:
        if not heard:
            return
        interface = {"name": _plain(audio["input"]), "match": [audio["input"].lower()], "found_by": "heard"}
    seen = {k: audio.get(k) for k in ("mode", "input", "output", "sample_rate", "block_size") if audio.get(k)}
    if interface.get("audio") == seen:
        return
    interface["audio"] = seen
    device["interface"] = interface
    _update(name, lambda entry: entry.__setitem__("interface", interface))


# ----------------------------------------------------------------- problems

def _audio_pick(device: dict | None, interface: dict | None) -> str:
    """What to choose on REAPER's audio device page, in the page's own words."""
    first = (device or {}).get("audio_input")
    last = first + 1 if first and (device or {}).get("stereo") else first
    span = (f"input {first}" if first == last else f"inputs {first}-{last}") if first else None
    if not interface:
        return ("Under 'Audio system' and the device lists, choose the audio interface the synth is plugged into "
                "(not the computer's own microphone), then OK.")
    ways = []
    if interface.get("asio_driver"):
        others = [a for a in interface.get("asio_drivers") or [] if a != interface["asio_driver"]]
        ways.append(f"Audio system: ASIO; ASIO driver: {interface['asio_driver']}"
                    + (f" (if another app holds it, {others[0]})" if others else "")
                    + (f"; tick 'Enable inputs' with a range that includes {span}" if span else "") + "; OK")
    if interface.get("windows_inputs"):
        ways.append(f"{'or keep ' if ways else 'Audio system: '}WASAPI and set Input device: "
                    f"{interface['windows_inputs'][0]}; OK")
    if not ways:
        ways.append(f"choose the {interface['name']} as the input device; OK")
    return ". ".join(w[0].upper() + w[1:] for w in ways) + "."


def _midi_pick(inputs: list[str], outputs: list[str]) -> str:
    steps = []
    if inputs:
        steps.append("on MIDI Inputs double-click " + " and ".join(f"'{n}'" for n in inputs)
                     + " and tick 'Enable input from this device'")
    if outputs:
        steps.append("on MIDI Outputs double-click " + " and ".join(f"'{n}'" for n in outputs)
                     + " and tick 'Enable output to this device'")
    return "; ".join(steps) + "; OK."


def find_problems(name: str | None, device: dict | None, st: dict, record: bool = True) -> list[dict]:
    """What's wrong with REAPER's setup for this device (or, without one, for finding
    devices), most basic first. Each: {problem, what, fix, blocks, page?, pick?}. 'blocks'
    = the hardware tools would fail or record the wrong thing; the rest are warnings.
    'page' = the settings page the fix is on ('audio' or 'midi'); 'pick' = what to choose."""
    audio, settings = st.get("audio") or {}, st.get("settings") or {}
    interface = interface_of(name, device)
    who = name or "the synth"
    out: list[dict] = []

    ident = audio.get("input")
    if not audio.get("running"):
        out.append({"problem": "audio device closed", "blocks": True, "page": "audio",
                    "what": "REAPER's audio device is closed and wouldn't open (REAPER takes in MIDI and audio "
                            "only while it runs).",
                    "fix": f"{AUDIO_PREFS}: " + _audio_pick(device, interface),
                    "pick": _audio_pick(device, interface)})
    elif record and ident:
        right = on_interface(ident, interface)
        if right is False:
            out.append({"problem": "wrong input device", "blocks": True, "page": "audio",
                        "what": f"REAPER is recording from '{_plain(ident)}', not the {interface['name']} that "
                                f"{who} is plugged into"
                                + (" (that's the computer's own microphone)." if looks_built_in(ident) else "."),
                        "fix": f"{AUDIO_PREFS}: " + _audio_pick(device, interface)
                               + f" (If {who}'s audio really comes in through '{_plain(ident)}', save_hardware it "
                                 "again with interface='current'.)",
                        "pick": _audio_pick(device, interface)})
        elif right is None and looks_built_in(ident):
            out.append({"problem": "input looks built in", "blocks": False, "page": "audio",
                        "what": f"REAPER is recording from '{_plain(ident)}', which looks like the computer's own "
                                "microphone, not an audio interface.",
                        "fix": f"If {who} is plugged into an interface: {AUDIO_PREFS}. " + _audio_pick(device, None),
                        "pick": _audio_pick(device, None)})

    midi = st.get("midi") or {}
    off_in, off_out, gone = [], [], []
    if device:
        for kind, key, off in (("outputs", "midi_output", off_out), ("inputs", "midi_input", off_in)):
            port = _port(st, kind, device.get(key))
            if not device.get(key):
                continue
            if port is None or not port.get("present"):
                gone.append(device[key])
            elif port.get("enabled") is False:
                off.append(device[key])
    else:
        outs = midi.get("outputs") or []
        if midi.get("output_enables_known") and not any(p.get("enabled") and p.get("present") for p in outs):
            off_out = [p["name"] for p in outs if p.get("present") and "wavetable" not in p["name"].lower()]
            off_in = [p["name"] for p in midi.get("inputs") or [] if p.get("present") and p.get("enabled") is False
                      and p["name"] in off_out]
    if gone:
        out.append({"problem": "MIDI port not connected", "blocks": True,
                    "what": f"{who}'s MIDI port '{gone[0]}' isn't connected: REAPER doesn't see it.",
                    "fix": "Plug in and switch on the MIDI interface (or the synth, if it's on USB). If REAPER was "
                           "already running, Preferences > Audio > MIDI Outputs (or MIDI Inputs) > 'Reset all MIDI devices' "
                           "finds it."})
    if off_in or off_out:
        ports = sorted(set(off_in + off_out))
        # Outputs first: without one nothing reaches the synth at all. guided_fix moves on to the
        # inputs page once the output is enabled.
        out.append({"problem": "MIDI port disabled", "blocks": True, "page": "midi_outputs" if off_out else "midi_inputs",
                    "what": ("MIDI port " + " and ".join(f"'{p}'" for p in ports)
                             + (" is" if len(ports) == 1 else " are") + " plugged in but not enabled in REAPER"
                             + (" for " + " or ".join(k for k, v in (("input", off_in), ("output", off_out)) if v))
                             + ": nothing goes out to the synth or comes back from it, without any error."),
                    "fix": f"{MIDI_PREFS}: " + _midi_pick(off_in, off_out), "pick": _midi_pick(off_in, off_out)})

    changed = settings.get("changed_for_session") or {}
    if settings.get("audiocloseinactive") and "audiocloseinactive" not in changed:
        out.append({"problem": "audio closes in the background", "blocks": False,
                    "what": "REAPER closes its audio device whenever it's stopped and another app is in front, "
                            "which is always the case while it's driven from a chat: MIDI stops with it, so a "
                            "synth's answers can be missed.",
                    "fix": CLOSE_INACTIVE_FIX + _cant_change(st)})
    if record and settings.get("promptendrec") and "promptendrec" not in changed:
        out.append({"problem": "save/delete window after recording", "blocks": False,
                    "what": "REAPER asks what to save after every recording, and waits for the user to click "
                            "(Save all) each time creaper records the synth.",
                    "fix": STOP_PROMPT_FIX + _cant_change(st)})

    measured_at = (device or {}).get("latency_at")
    now = signature(st)
    if record and measured_at and now and measured_at != now and now not in ((device or {}).get("latencies") or {}):
        out.append({"problem": "latency measured on other audio settings", "blocks": False,
                    "what": f"{who}'s latency was measured with other audio settings ({_readable(measured_at)}); "
                            f"REAPER now runs {_readable(now)}, so recordings may sit early or late.",
                    "fix": "calibrate_hardware_latency measures it again (20 seconds)."})
    return out


def _cant_change(st: dict) -> str:
    if (st.get("settings") or {}).get("can_change"):
        return ""
    return (f" (creaper turns this off by itself during hardware work, and back on after, from REAPER 7.74; this is "
            f"REAPER {st.get('reaper_version') or '?'}.)")


def _readable(sig: str) -> str:
    mode, ident, rate, block = (sig.split("|") + ["", "", "", ""])[:4]
    return f"{mode or 'audio'} at {rate or '?'} Hz, block {block or '?'}"


def latency_ms(device: dict, st: dict | None) -> float:
    """The device's measured latency for the audio settings REAPER runs now (the last one
    measured, when none was measured on these)."""
    now = signature(st)
    per = device.get("latencies") or {}
    if now and now in per:
        return float(per[now])
    return float(device.get("latency_ms") or 0.0)


# ---------------------------------------------------------------- preflight

@dataclass
class Checked:
    status: dict | None = None
    warnings: list[str] = field(default_factory=list)

    def onto(self, out: dict) -> dict:
        """Adds the warnings to a tool's result."""
        if self.warnings:
            out["setup_warnings"] = self.warnings
        return out


def preflight(name: str | None = None, device: dict | None = None, record: bool = True) -> Checked:
    """Run at the start of every hardware tool. Opens the audio device if it's closed,
    turns off REAPER's two in-the-way settings for the session where REAPER allows, and
    raises with the cause and the fix when the tool couldn't work (wrong input device,
    closed device, disabled or missing MIDI port). Lesser things come back as warnings."""
    st = status(session="begin", open_audio=True)
    if st is None:
        return Checked()
    problems = find_problems(name, device, st, record)
    blocking = next((p for p in problems if p["blocks"]), None)
    if blocking:
        fix = f" {blocking['fix']}"
        if blocking.get("page"):
            fix += (f" setup_hardware({f'name={name!r}, ' if name else ''}action='fix') opens that page, waits for "
                    "the change and says when it's right.")
        raise ValueError(blocking["what"] + fix)
    if name and device and record:
        remember_audio(name, device, st)
    return Checked(st, [f"{p['what']} {p['fix']}" for p in problems])


def guided_fix(name: str | None, device: dict | None) -> dict:
    """Opens the settings page of the first problem that has one, then watches REAPER until
    that problem is gone (or FIX_WAIT_S passes)."""
    st = status(open_audio=True)
    if st is None:
        raise ValueError("this needs the current creaper bridge in REAPER: run `creaper install-bridge`, then run "
                         "the creaper_bridge action again")
    record = bool(device)
    problems = find_problems(name, device, st, record)
    target = next((p for p in problems if p.get("page") and p["blocks"]), None) \
        or next((p for p in problems if p.get("page")), None)
    if target is None:
        return {"fixed": True, "note": "Nothing to fix in REAPER's audio or MIDI settings.",
                **_report(name, device, st, problems)}
    started = _now()
    opened: list[str] = []

    def open_page(page: str) -> None:
        try:
            # If the settings window holds REAPER's scripts while it's open, this answers when
            # the user closes it; if it doesn't, at once. Either way the watching below decides.
            how = server.call("hardware_open_prefs", timeout=FIX_WAIT_S + 30.0, page=page).get("opened")
        except BridgeError:
            how = None
        opened.append(how or page)

    page = target["page"]
    open_page(page)
    while True:
        try:
            st = status() or st     # not opening the device here: the user is choosing it
        except BridgeError:
            pass
        problems = find_problems(name, device, st, record)
        same = next((p for p in problems if p["problem"] == target["problem"]), None)
        if same and same.get("page") and same["page"] != page:
            # Half done (the MIDI output is enabled, the input isn't yet): its page is another one.
            page = same["page"]
            open_page(page)
        # Done when the problem is gone and, for a blocking one, nothing else blocks either:
        # while the user switches devices REAPER closes the old one for a moment, and a
        # closed device is not a fixed one.
        left = (any(p["problem"] == target["problem"] for p in problems)
                or (target["blocks"] and any(p["blocks"] for p in problems)))
        if not left or _now() - started >= FIX_WAIT_S:
            break
        _sleep(FIX_POLL_S)
    out = {"fixed": not left, "was": target["what"], **_report(name, device, st, problems)}
    if left and "preferences" in opened:
        # This REAPER's page numbers aren't known: Preferences opened wherever it was last.
        out["opened"] = ("REAPER's Preferences window, on the page it was last on, not the one to change: the user "
                         "goes to the page the problem's 'fix' names.")
    if left:
        out["note"] = ("Still the same after two minutes. Tell the user what to choose (the problem's 'fix'), and "
                       "call this again when they're ready.")
    else:
        if name and device:
            remember_audio(name, device, st)
        more = [p for p in problems if p.get("page")]
        out["note"] = ("That's right now." + (" One more thing needs changing: call this again for it."
                                              if more else " Carry on with what you were doing."))
    return out


def _report(name: str | None, device: dict | None, st: dict, problems: list[dict]) -> dict:
    audio, midi, settings = st.get("audio") or {}, st.get("midi") or {}, st.get("settings") or {}
    interface = interface_of(name, device)
    out: dict[str, Any] = {
        "ready": not any(p["blocks"] for p in problems),
        "problems": [{k: p[k] for k in ("problem", "what", "fix") if k in p} | {"blocks": p["blocks"]} for p in problems],
        "audio": {k: audio.get(k) for k in ("running", "mode", "input", "output", "sample_rate", "block_size")},
        "midi_outputs_enabled": [p["name"] for p in midi.get("outputs") or [] if p.get("enabled") and p.get("present")],
        "midi_inputs_enabled": [p["name"] for p in midi.get("inputs") or [] if p.get("enabled") and p.get("present")],
        "reaper_version": st.get("reaper_version"),
    }
    off = sorted({p["name"] for k in ("inputs", "outputs") for p in midi.get(k) or []
                  if p.get("present") and p.get("enabled") is False})
    if off:
        out["midi_ports_plugged_in_but_disabled"] = off
    unknown = sorted({p["name"] for k in ("inputs", "outputs") for p in midi.get(k) or []
                      if p.get("present") and p.get("enabled") is None})
    if unknown:
        out["midi_ports_creaper_cannot_tell"] = unknown
    if interface:
        out["interface"] = {k: interface[k] for k in ("name", "asio_driver", "windows_inputs", "found_by")
                            if interface.get(k)}
    if settings.get("changed_for_session"):
        out["settings_off_for_this_session"] = sorted(settings["changed_for_session"])
    return out


def check(name: str | None, device: dict | None) -> dict:
    """The whole setup, read without changing anything."""
    st = status(open_audio=True)
    if st is None:
        raise ValueError("this needs the current creaper bridge in REAPER: run `creaper install-bridge`, then run "
                         "the creaper_bridge action again")
    problems = find_problems(name, device, st, record=bool(device))
    out = _report(name, device, st, problems)
    if not device:
        # No device saved yet: say which interfaces the MIDI ports point to.
        audio = windows_audio()
        found = {}
        for p in (st.get("midi") or {}).get("outputs") or []:
            guess = detect_interface(p["name"], audio) if p.get("present") else None
            if guess:
                found[p["name"]] = {k: guess[k] for k in ("name", "asio_driver", "windows_inputs") if guess.get(k)}
        if found:
            out["interfaces_by_midi_port"] = found
    if any(p.get("page") for p in problems):
        out["next"] = ("Tell the user the first problem's fix in plain words, then call setup_hardware with "
                       "action='fix': it opens that settings page and waits until the change is made.")
    elif out["ready"]:
        out["next"] = ("REAPER is set up." if device else
                       "REAPER is set up: scan_hardware finds the synths, save_hardware keeps them.")
    return out


def finish() -> dict:
    """Ends the hardware session: REAPER's settings turned off for it go back."""
    st = status(session="end")
    if st is None:
        return {"restored": [], "note": "Nothing was changed."}
    restored = st.get("restored") or {}
    return {"restored": sorted(restored),
            "note": ("REAPER's settings are as the user had them." if restored else
                     "creaper hadn't changed any REAPER settings.")}
