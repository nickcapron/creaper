"""Sound design on plugin synths: a sound_design blueprint (milliseconds, hertz, cents,
octaves) turned into one plugin's own parameter values, the way microkorg.from_design
does it for the hardware synth.

A plugin shows some controls in real units (Prophet-5 V's filter frequency is hertz, its
envelope times seconds) and the rest on a 0-10 dial. What a dial does was measured
offline on 2026-11-18: one held note rendered per setting, the resonant peak, the pitch
or the envelope read from the audio. That is the microKORG's ten minutes of calibration
tones done in two minutes with no cables, which is the case for doing it per plugin.

Each profile: the plugin's plain sound (every control that colours it set to nothing, its
built-in effects off), and `from_design`, which returns the changes for
set_fx_parameters, what was set by rule of thumb and what the plugin can't do. Effects
in a blueprint are not the plugin's own (their type isn't a parameter): they go on the
track after it.
"""

from __future__ import annotations

from typing import Any


def _on(name: str, yes: bool) -> dict:
    return {"parameter": name, "display_text": "On" if yes else "Off"}


def _num(name: str, value: float, places: int = 3) -> dict:
    return {"parameter": name, "display_value": round(float(value), places)}


def _dial(name: str, zero_to_one: float) -> dict:
    return {"parameter": name, "value": round(max(0.0, min(1.0, float(zero_to_one))), 4)}


# ------------------------------------------------------------------ Prophet-5 V (Arturia)
# Measured 2026-11-18 at 120 BPM, effects off, one saw:
P5 = {
    "cutoff_max_hz": 6214.0,            # the frequency dial's top; what it shows is where the resonant peak is (C2, key follow off)
    "key_follow_reference": "C2",       # key follow on: the shown cutoff holds at C2 and doubles every octave up
    "env_octaves_per_unit": 1.112,      # Filter Envelope Modulation 1.00 opens the filter 1.11 octaves (2.00: 2.22 ... 5.00: 5.56)
    "attack_s_per_shown": 0.6,          # time to 90% of the level, against the seconds shown
    "decay_20db_per_shown": 0.33,       # time to fall 20 dB, against the seconds shown (0.5 shown: 0.158 s)
    "release_20db_per_shown": 0.48,
    "fine_tune_cents_per_unit": 100.0,  # VCO 2 Fine Tune 0.300 = 30 cents; its range is +-0.6
    "lfo_pitch_semitones_at_full": 9.13,   # peak to peak, Mod Wheel 1.0, square LFO
    "lfo_cutoff_octaves_at_full": 10.0,    # from one clean reading (2.5 octaves at 0.25): rule of thumb
    "polymod_semitones_per_unit": 3.66,    # Poly-Mod Filter Envelope 1.00 raises VCO 1 by 3.66 semitones
    "plain_level_dbfs": -22.5,          # one saw at C3 with Master Volume at -12
}

P5_PLAIN: list[dict] = [
    _on("SawOn1", True), _on("VCO 1 Square", False), _on("VCO 1 Sync", False), _num("VCO 1 Frequency", 0),
    _dial("VCO 1 Pulse Width", 0.5), _num("VCO 2 Frequency", 0), _dial("VCO 2 Fine Tune", 0.5), _dial("VCO 2 Pulse Width", 0.5),
    _on("VCO 2 Saw", False), _on("VCO 2 Triangle", False), _on("VCO 2 Square", False), _on("VCO 2 LFO Mode", False),
    _on("VCO 2 Key Follow", True), _dial("VCO 1 Level", 1.0), _dial("VCO 2 Level", 0.0), _dial("Noise Level", 0.0),
    _on("MW/LFO VCO 1 Pulse Width Modulation", False), _on("MW/LFO VCO 2 Pulse Width Modulation", False),
    _on("MW/LFO VCO 1 Frequency Modulation", False), _on("MW/LFO VCO 2 Frequency Modulation", False),
    _num("Filter Frequency", P5["cutoff_max_hz"], 0), _dial("Filter Resonance", 0.0), _on("Filter Key Follow", True),
    _on("Filter LFO Modulation", False), _dial("Filter Envelope Modulation", 0.0),
    _dial("VCF Attack", 0.0), _dial("VCF Decay", 0.0), _dial("VCF Sustain", 1.0), _num("VCF Release", 0.1),
    _dial("VCA Attack", 0.0), _dial("VCA Decay", 0.0), _dial("VCA Sustain", 1.0), _num("VCA Release", 0.1),
    {"parameter": "LFO Rate Type", "display_text": "Hz"}, _num("LFO Rate Unsynced", 5.0), _on("LFO Ramp", False),
    _on("LFO Triangle", True), _on("LFO Square", False), _dial("LFO ModWheel Modulation Source", 0.0), _dial("Mod Wheel", 0.0),
    _dial("Filter Envelope", 0.0), _dial("Osc 2", 0.0), _on("Freq 1", False), _on("Pulse Width 1", False),
    _on("Filter (Cutoff)", False), _on("Unison", False), _dial("Detune", 0.0), _on("Legato", False), _dial("Glide", 0.0),
    _on("Arp On/Off", False), _on("Hold", False), _on("Chord Mode ON/OFF", False),
    # "Bypass Off" is the effect OFF on this plugin (measured: its reverb tail goes with it).
    _on("FX1 Bypass", False), _on("FX2 Bypass", False), _on("FX3 Bypass", False),
    _dial("Oscillators Pitch Dispersion", 0.0), _dial("Oscillators Pulse Width Dispersion", 0.0),
    _dial("Filter Cutoff Dispersion", 0.0), _dial("Filter Resonance Dispersion", 0.0), _dial("Envelope Times Dispersion", 0.0),
    _dial("Modulations Dispersion", 0.0), _dial("Level Dispersion", 0.0), _dial("Lfo2 Dest 1 Amount", 0.5),
    _dial("Lfo2 Dest 2 Amount", 0.5), _num("Master Volume", -12.0, 1),
]

_SYNC_TEXT = {"1/1": "1", "1/2": "1/2", "1/4": "1/4", "1/8": "1/8", "1/16": "1/16", "1/32": "1/32", "2/1": "2", "4/1": "4"}


def _p5_envelope(prefix: str, env: dict) -> list[dict]:
    out = []
    if env.get("attack_ms") is not None:
        out.append(_num(f"{prefix} Attack", max(0.001, env["attack_ms"] / 1000 / P5["attack_s_per_shown"])))
    if env.get("decay_ms") is not None:
        out.append(_num(f"{prefix} Decay", max(0.005, env["decay_ms"] / 1000 / P5["decay_20db_per_shown"])))
    if env.get("sustain") is not None:
        out.append(_num(f"{prefix} Sustain", max(0.0, min(1.0, env["sustain"])), 2))
    if env.get("release_ms") is not None:
        out.append(_num(f"{prefix} Release", max(0.005, env["release_ms"] / 1000 / P5["release_20db_per_shown"])))
    return out


def _p5_from_design(bp: dict) -> dict:
    changes: list[dict] = []
    approximate: list[str] = []
    left_out: list[str] = []
    effects: list[dict] = []

    voices = bp.get("voices")
    if voices in ("mono", "unison"):
        changes.append(_on("Unison", True))
        cents = float(bp.get("unison_cents") or 0) if voices == "unison" else 0.0
        changes.append(_num("Detune", max(0.5, min(10.0, cents / 3)), 2))
        # Every voice sounds on the one note: measured 12-13 dB over the plain sound, so the output comes down.
        changes.append(_num("Master Volume", -24.0, 1))
        approximate.append("Unison stacks every voice on the note: its Detune dial is set at a third of the cents asked "
                           "(not measured), and a mono sound gets the dial's lowest setting, which still spreads a little")
    elif voices == "poly":
        changes.append(_on("Unison", False))
    if bp.get("legato") is not None:
        changes.append(_on("Legato", bool(bp["legato"])))
    if bp.get("glide_ms"):
        changes.append(_num("Glide", min(2.0, bp["glide_ms"] / 1000)))
        approximate.append("Glide is shown in seconds and taken as the time per octave (not measured)")

    o1, o2 = dict(bp.get("osc1") or {}), dict(bp.get("osc2") or {})
    swapped = False
    if o1.get("wave") in ("triangle", "sine"):
        # VCO 1 has saw and pulse only: the triangle lives on VCO 2.
        if o2:
            left_out.append(f"osc2 ({o2.get('wave', 'saw')}): VCO 2 is used for osc1's {o1['wave']}, which VCO 1 doesn't have")
        o2, o1, swapped = {"wave": o1["wave"], "level": o1.get("level", 1.0)}, {"level": 0.0}, True
    wave = o1.get("wave")
    if wave == "noise":
        changes += [_dial("VCO 1 Level", 0.0), _dial("Noise Level", o1.get("level", 1.0))]
    else:
        if wave in ("saw", "pulse", "square"):
            changes += [_on("SawOn1", wave == "saw"), _on("VCO 1 Square", wave != "saw")]
        if o1.get("width") is not None or wave == "square":
            changes.append(_num("VCO 1 Pulse Width", 100 * (0.5 if wave == "square" else 1 - float(o1.get("width", 0.5))), 1))
        if o1.get("level") is not None:
            changes.append(_num("VCO 1 Level", 10 * float(o1["level"]), 2))
        if o1.get("pwm"):
            changes.append(_on("MW/LFO VCO 1 Pulse Width Modulation", True))
            changes.append(_dial("Mod Wheel", min(1.0, float(o1["pwm"]))))
            approximate.append("pulse-width movement is the LFO through the Mod Wheel control: its depth is by rule of thumb")
    if o2:
        w2 = o2.get("wave", "saw")
        if w2 == "sine":
            approximate.append("no sine on this synth: a triangle, the nearest it has (lower the filter to round it)")
        if w2 == "noise":
            changes.append(_dial("Noise Level", o2.get("level", 1.0)))
        else:
            changes += [_on("VCO 2 Saw", w2 == "saw"), _on("VCO 2 Triangle", w2 in ("triangle", "sine")),
                        _on("VCO 2 Square", w2 in ("square", "pulse")), _num("VCO 2 Level", 10 * float(o2.get("level", 1.0)), 2)]
            semis = int(round(o2.get("semitones", 0)))
            changes.append(_num("VCO 2 Frequency", max(-24, min(36, semis)), 0))
            cents = float(o2.get("cents", 0))
            if abs(cents) > 60:
                left_out.append(f"osc2 {cents:g} cents: the fine tune reaches 60; set to its end")
            changes.append(_num("VCO 2 Fine Tune", max(-0.6, min(0.6, cents / P5["fine_tune_cents_per_unit"]))))
    elif not swapped and bp.get("osc1") is not None:
        changes.append(_dial("VCO 2 Level", 0.0))
    if bp.get("osc_mod") == "sync":
        changes.append(_on("VCO 1 Sync", True))
        approximate.append("sync: VCO 1 is locked to VCO 2, so the sweep comes from moving VCO 1's pitch (pitch_env, or "
                           "VCO 1 Frequency), not VCO 2's")
    elif bp.get("osc_mod"):
        left_out.append(f"osc_mod {bp['osc_mod']}: no ring modulator")
    if bp.get("noise") is not None:
        changes.append(_num("Noise Level", 10 * float(bp["noise"]), 2))

    flt = bp.get("filter") or {}
    if flt.get("type") in ("bp", "hp"):
        left_out.append(f"filter type {flt['type']}: this synth has one 24 dB low pass; put a filter on the track after it "
                        "(ReaEQ's high pass or band)")
    elif flt.get("type") == "lp12":
        approximate.append("its low pass is 24 dB per octave, steeper than the 12 asked: raise the cutoff a little")
    follow = None
    if flt.get("key_track") is not None:
        follow = float(flt["key_track"]) >= 0.5
        changes.append(_on("Filter Key Follow", follow))
        approximate.append("key follow is a switch here (all or nothing): on from 0.5 up")
    if flt.get("cutoff_hz") is not None:
        hz = float(flt["cutoff_hz"])
        if hz > P5["cutoff_max_hz"]:
            approximate.append(f"cutoff {hz:g} Hz: the dial tops out at {P5['cutoff_max_hz']:g} Hz, which is fully open")
        changes.append(_num("Filter Frequency", min(hz, P5["cutoff_max_hz"]), 0))
        if follow:
            approximate.append(f"with key follow on, the cutoff is {min(hz, P5['cutoff_max_hz']):g} Hz at "
                               f"{P5['key_follow_reference']} and doubles every octave up")
    if flt.get("resonance") is not None:
        changes.append(_num("Filter Resonance", 10 * float(flt["resonance"]), 2))
    if flt.get("env_octaves") is not None:
        octaves = float(flt["env_octaves"])
        if octaves < 0:
            left_out.append("a filter envelope that closes the filter: its amount only opens it")
        else:
            changes.append(_num("Filter Envelope Modulation", min(10.0, octaves / P5["env_octaves_per_unit"]), 2))
    if flt.get("velocity"):
        left_out.append("velocity to the filter: its modulation routing isn't reachable from here")
    changes += _p5_envelope("VCF", bp.get("filter_env") or {}) + _p5_envelope("VCA", bp.get("amp_env") or {})

    pe = bp.get("pitch_env") or {}
    if pe.get("semitones"):
        if pe["semitones"] < 0:
            left_out.append("a pitch envelope that rises to the note: Poly-Mod only raises the pitch")
        else:
            changes += [_on("Freq 1", True), _num("Filter Envelope", min(10.0, pe["semitones"] / P5["polymod_semitones_per_unit"]), 2)]
            approximate.append("the pitch envelope is Poly-Mod from the FILTER envelope to VCO 1: it shares that envelope's "
                               "decay, and VCO 2 doesn't move")
            if pe.get("decay_ms") is not None and not (bp.get("filter_env") or {}).get("decay_ms"):
                changes += _p5_envelope("VCF", {"decay_ms": pe["decay_ms"], "sustain": 0.0})

    lfo = bp.get("lfo1") or {}
    if lfo:
        shape = lfo.get("shape", "triangle")
        if shape == "random":
            left_out.append("a random LFO: the main LFO has ramp, triangle and square")
        changes += [_on("LFO Ramp", shape == "saw"), _on("LFO Triangle", shape in ("triangle", "sine")), _on("LFO Square", shape == "square")]
        if lfo.get("sync") in _SYNC_TEXT:
            changes += [{"parameter": "LFO Rate Type", "display_text": "Sync Binary"},
                        {"parameter": "LFO Rate Synced", "display_text": _SYNC_TEXT[lfo["sync"]]}]
        elif lfo.get("hz") is not None:
            changes += [{"parameter": "LFO Rate Type", "display_text": "Hz"}, _num("LFO Rate Unsynced", max(0.015, min(30.0, lfo["hz"])))]
        to, depth = lfo.get("to"), float(lfo.get("depth", 0))
        if to == "pitch":
            changes += [_on("MW/LFO VCO 1 Frequency Modulation", True), _on("MW/LFO VCO 2 Frequency Modulation", True),
                        _dial("Mod Wheel", 2 * depth / P5["lfo_pitch_semitones_at_full"])]
        elif to == "cutoff":
            changes += [_on("Filter LFO Modulation", True), _dial("Mod Wheel", 2 * depth / P5["lfo_cutoff_octaves_at_full"])]
            approximate.append("LFO to cutoff: its depth is from one measurement")
        elif to == "width":
            changes += [_on("MW/LFO VCO 1 Pulse Width Modulation", True), _on("MW/LFO VCO 2 Pulse Width Modulation", True),
                        _dial("Mod Wheel", depth)]
            approximate.append("LFO to pulse width: its depth is by rule of thumb")
        elif to:
            left_out.append(f"LFO to {to}: the main LFO reaches pitch, cutoff and pulse width")
        if to in ("pitch", "cutoff", "width"):
            approximate.append("the LFO's depth is the plugin's Mod Wheel control: a part with mod-wheel data (CC 1) moves it")
    if bp.get("lfo2"):
        left_out.append("lfo2: its destinations aren't reachable from here; set it in the plugin's window")
    if bp.get("velocity_to_amp"):
        left_out.append("velocity to level: its modulation routing isn't reachable from here")

    fx = bp.get("fx") or {}
    if fx.get("distortion"):
        effects.append({"add": "JS: Saturation", "set": [{"parameter": "Amount (%)", "display_value": 45}], "for": "distortion"})
    for kind in ("chorus", "ensemble", "phaser"):
        if fx.get(kind):
            effects.append({"with": "add_part_fx(track)", "for": kind})
    if fx.get("delay"):
        effects.append({"with": "a send to the song's delay return (auto_mix makes it; add_part_fx sends to it)", "for": "delay"})
    return {"changes": changes, "approximate": approximate, "left_out": left_out, "effects": effects}


PROFILES: dict[str, dict[str, Any]] = {
    "Prophet-5 V": {
        "maker": "Arturia", "plain": P5_PLAIN, "from_design": _p5_from_design, "calibration": P5,
        "what": "two oscillators (saw and pulse; a triangle on the second), noise, a 24 dB low pass, two envelopes, one LFO, "
                "Poly-Mod, unison and glide: the classic poly for basses, leads, pads, sync sweeps and brass",
        "cannot": "sine waves, high-pass and band-pass filters, a ring modulator, velocity routing, a second LFO from here",
    },
}


def find(plugin: str | None) -> tuple[str, dict] | None:
    """A profile by the plugin's name, or the name inside an FX name ('VST3i: Prophet-5 V (Arturia)')."""
    if not plugin:
        return None
    wanted = plugin.lower()
    for name, profile in PROFILES.items():
        if name.lower() in wanted or wanted in name.lower():
            return name, profile
    return None
