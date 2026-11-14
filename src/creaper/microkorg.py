"""The Korg microKORG (2002) as creaper sees it: its patch format, its parameters by name,
how each one is reached over MIDI, and starting-point recipes.

Written from Korg's MIDI implementation (rev 1.4) and checked against the dumps a real
microKORG sent. What the synth offers over MIDI:

- No "set one parameter" SysEx. A whole patch (254 bytes, sent 7 bits at a time as 291)
  is read from and loaded into the EDIT BUFFER; a separate request writes the buffer to
  one of the 128 programs.
- The panel knobs as control changes. Which CC each knob uses is a setting on the synth
  (the Global dump carries the map), so nothing here assumes the numbers.
- NRPNs for the arpeggiator, the four modulation patches and the vocoder bands.

A parameter here has a plain name and a plain value: 0-127 where the synth shows 0-127,
-63..63 where it shows a signed amount, a word where it shows a choice ("saw", "24lpf").
Nothing in this module talks to REAPER: hardware_sound_tools does."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

MODEL = "Korg microKORG"
PROGRAM_BYTES = 254
GLOBAL_BYTES = 200
TIMBRE1, TIMBRE2, TIMBRE_SIZE = 38, 146, 108

# SysEx function codes (after the header F0 42 3g 58, g = the global MIDI channel).
F_CURRENT_REQUEST, F_GLOBAL_REQUEST, F_WRITE_REQUEST = 0x10, 0x0E, 0x11
F_CURRENT_DUMP, F_GLOBAL_DUMP = 0x40, 0x51
F_LOAD_OK, F_LOAD_ERROR, F_FORMAT_ERROR, F_WRITE_OK, F_WRITE_ERROR = 0x23, 0x24, 0x26, 0x21, 0x22

SETUP_HELP = (
    "On the microKORG, hold SHIFT and press the program key labelled MIDI FILTER, then set 'SystemEx' to ENA "
    "(patches) and 'CtrlChg' to ENA (knobs) with the knobs under the display; its MIDI OUT must be cabled back "
    "to the interface's MIDI IN.")


# ------------------------------------------------------------------ bytes

def header(channel: int, function: int) -> list[int]:
    return [0xF0, 0x42, 0x30 | ((channel - 1) & 0x0F), 0x58, function]


def message(channel: int, function: int, payload: bytes | list[int] = b"") -> str:
    """A microKORG SysEx message as hex, the way the bridge's send_midi takes it."""
    return " ".join(f"{b:02X}" for b in [*header(channel, function), *payload, 0xF7])


def unpack(midi: bytes) -> bytes:
    """MIDI data (7 bits a byte) -> the 8-bit data. Every 8 MIDI bytes carry 7 data bytes:
    the first holds their top bits (bit 0 for the first of the seven)."""
    out = bytearray()
    for i in range(0, len(midi), 8):
        group = midi[i:i + 8]
        for k, b in enumerate(group[1:]):
            out.append(b | (((group[0] >> k) & 1) << 7))
    return bytes(out)


def pack(data: bytes) -> bytes:
    out = bytearray()
    for i in range(0, len(data), 7):
        group = data[i:i + 7]
        out.append(sum(((b >> 7) & 1) << k for k, b in enumerate(group)))
        out.extend(b & 0x7F for b in group)
    return bytes(out)


def parse_message(hexstr: str) -> tuple[int, bytes] | None:
    """(function code, payload) of a microKORG SysEx message, or None for anything else."""
    h = hexstr.replace(" ", "").upper()
    if len(h) < 12 or not h.startswith("F042") or h[4] != "3" or h[6:8] != "58" or not h.endswith("F7"):
        return None
    raw = bytes.fromhex(h)
    return raw[4], raw[5:-1]


def program_number(ref: str | int) -> int:
    """'A.11' .. 'b.88' (as the display shows them) or 1-128 -> the program change number 0-127."""
    if isinstance(ref, int) or str(ref).strip().isdigit():
        n = int(ref)
        if not 1 <= n <= 128:
            raise ValueError("microKORG programs are numbered 1-128, or named A.11 to b.88")
        return n - 1
    s = str(ref).strip().replace(" ", "").replace(".", "")
    if len(s) == 3 and s[0] in "AaBb" and s[1] in "12345678" and s[2] in "12345678":
        return (64 if s[0] in "Bb" else 0) + (int(s[1]) - 1) * 8 + int(s[2]) - 1
    raise ValueError(f"'{ref}' isn't a microKORG program: they run A.11-A.88 and b.11-b.88 (two digits, each 1-8)")


def program_name(number: int) -> str:
    return f"{'b' if number >= 64 else 'A'}.{(number % 64) // 8 + 1}{number % 8 + 1}"


# -------------------------------------------------------------- parameters

@dataclass(frozen=True)
class Param:
    name: str
    offset: int                      # byte in the program (common) or in the timbre / vocoder block
    help: str = ""
    lo: int = 0
    hi: int = 127
    shift: int = 0                   # for values packed into part of a byte
    bits: int = 8
    center: int | None = None        # stored as value + center
    choices: tuple[str | None, ...] | None = None
    signed: bool = False             # stored as a signed byte
    knob: int | None = None          # index into the Global dump's knob -> CC map
    nrpn: tuple[int, int] | None = None
    wide: bool = False               # two bytes, high first (the tempo)
    pattern: bool = False            # the arpeggiator's 8 steps

    def read(self, block: bytes | bytearray) -> Any:
        if self.wide:
            return (block[self.offset] << 8) | block[self.offset + 1]
        raw = block[self.offset]
        if self.pattern:
            return "".join("-" if (raw >> i) & 1 else "x" for i in range(8))
        if self.signed:
            return raw - 256 if raw > 127 else raw
        raw = (raw >> self.shift) & ((1 << self.bits) - 1)
        if self.choices:
            return self.choices[raw] if raw < len(self.choices) and self.choices[raw] else raw
        return raw - self.center if self.center is not None else raw

    def raw(self, value: Any) -> int:
        """The stored number for a value, refusing anything out of range by name."""
        if self.pattern:
            v = str(value).strip().lower()
            if len(v) != 8 or set(v) - set("x-."):
                raise ValueError(f"{self.name} is 8 steps, x = plays, - = rests, e.g. 'x-x-xx-x'")
            return sum(1 << i for i, c in enumerate(v) if c != "x")
        if self.choices:
            if isinstance(value, bool):
                value = "on" if value else "off"
            if isinstance(value, str):
                key = value.strip().lower().replace(" ", "")
                names = [c.lower().replace(" ", "") if c else None for c in self.choices]
                if key in names:
                    return names.index(key)
                raise ValueError(f"{self.name} is one of: {', '.join(c for c in self.choices if c)} (got '{value}')")
            raise ValueError(f"{self.name} is one of: {', '.join(c for c in self.choices if c)}")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise ValueError(f"{self.name} takes a whole number {self.lo} to {self.hi} (got {value!r})")
        value = int(value)
        if not self.lo <= value <= self.hi:
            raise ValueError(f"{self.name} runs {self.lo} to {self.hi} (got {value})")
        return value + (self.center or 0)

    def write(self, block: bytearray, value: Any) -> None:
        raw = self.raw(value)
        if self.wide:
            block[self.offset], block[self.offset + 1] = raw >> 8, raw & 0xFF
        elif self.signed or self.pattern or (self.bits == 8 and not self.shift):
            block[self.offset] = raw & 0xFF
        else:
            mask = ((1 << self.bits) - 1) << self.shift
            block[self.offset] = (block[self.offset] & ~mask & 0xFF) | ((raw << self.shift) & mask)

    def describe(self) -> dict:
        out: dict[str, Any] = {"name": self.name}
        if self.pattern:
            out["values"] = "8 steps: x plays, - rests"
        elif self.choices:
            out["values"] = [c for c in self.choices if c]
        else:
            out["range"] = [self.lo, self.hi]
        if self.help:
            out["what"] = self.help
        return out


ONOFF = ("off", "on")
NOTE_DIVS_LFO = ("1/1", "3/4", "2/3", "1/2", "3/8", "1/3", "1/4", "3/16", "1/6", "1/8", "3/32", "1/12", "1/16",
                 "1/24", "1/32")
NOTE_DIVS_DELAY = ("1/32", "1/24", "1/16", "1/12", "3/32", "1/8", "1/6", "3/16", "1/4", "1/3", "3/8", "1/2", "2/3",
                   "3/4", "1/1")
SOURCES = ("eg1", "eg2", "lfo1", "lfo2", "velocity", "kbd track", "pitch bend", "mod wheel")
DESTS = ("pitch", "osc2 pitch", "osc1 ctrl1", "noise level", "cutoff", "amp", "pan", "lfo2 freq")
WAVES = ("saw", "pulse", "triangle", "sine", "vox", "dwgs", "noise", "audio in")

# The whole program: voice mode, effects, EQ, arpeggiator.
COMMON = [
    Param("voice_mode", 16, "single = one timbre, layer = two timbres stacked (halves the 4 voices), vocoder",
          shift=4, bits=2, choices=("single", None, "layer", "vocoder")),
    Param("arp_steps", 14, "how many of the 8 arpeggiator steps are used", lo=1, hi=8, center=-1, bits=3),
    Param("arp_pattern", 15, "which steps play (step-sequencer rhythms from a held chord)", pattern=True),
    Param("delay_sync", 19, "delay time follows the tempo", shift=7, bits=1, choices=ONOFF),
    Param("delay_division", 19, "delay time when synced", bits=4, choices=NOTE_DIVS_DELAY),
    Param("delay_time", 20, "delay time when not synced", knob=39),
    Param("delay_depth", 21, "how much delay (0 = none)", knob=40),
    Param("delay_type", 22, choices=("stereo", "cross", "l/r")),
    Param("mod_speed", 23, "chorus/phaser LFO speed", knob=37),
    Param("mod_depth", 24, "how much modulation effect (0 = none)", knob=38),
    Param("mod_type", 25, choices=("chorus/flanger", "ensemble", "phaser")),
    Param("eq_high_freq", 26, "0-29 = 1 kHz to 18 kHz", hi=29),
    Param("eq_high_gain", 27, "dB", lo=-12, hi=12, center=64),
    Param("eq_low_freq", 28, "0-29 = 40 Hz to 1 kHz", hi=29),
    Param("eq_low_gain", 29, "dB", lo=-12, hi=12, center=64),
    Param("arp_tempo", 30, "BPM of the arpeggiator and synced LFOs/delay when the synth runs on its own clock",
          lo=20, hi=300, wide=True),
    Param("arp_on", 32, shift=7, bits=1, choices=ONOFF, nrpn=(0, 2)),
    Param("arp_latch", 32, "keeps arpeggiating after the keys are released", shift=6, bits=1, choices=ONOFF,
          nrpn=(0, 4)),
    Param("arp_target", 32, shift=4, bits=2, choices=("both", "timbre 1", "timbre 2")),
    Param("arp_key_sync", 32, bits=1, choices=ONOFF),
    Param("arp_type", 33, bits=4, choices=("up", "down", "alt1", "alt2", "random", "trigger"), nrpn=(0, 7)),
    Param("arp_octaves", 33, lo=1, hi=4, center=-1, shift=4, bits=4, nrpn=(0, 3)),
    Param("arp_gate", 34, "note length, % of a step", hi=100, nrpn=(0, 10)),
    Param("arp_resolution", 35, "step length", choices=("1/24", "1/16", "1/12", "1/8", "1/6", "1/4")),
    Param("arp_swing", 36, "%", lo=-100, hi=100, signed=True),
    Param("kbd_octave", 37, "the synth's own keyboard, not MIDI notes", lo=-3, hi=3, signed=True),
]


def _lfo(n: int, at: int, waves: tuple[str, ...], knob: int) -> list[Param]:
    return [
        Param(f"lfo{n}_wave", at, bits=2, choices=waves, knob=knob),
        Param(f"lfo{n}_key_sync", at, "restart the LFO at each note", shift=4, bits=2,
              choices=("off", "timbre", "voice")),
        Param(f"lfo{n}_freq", at + 1, "speed when not tempo-synced", knob=knob + 1),
        Param(f"lfo{n}_tempo_sync", at + 2, shift=7, bits=1, choices=ONOFF),
        Param(f"lfo{n}_division", at + 2, "speed when tempo-synced", bits=5, choices=NOTE_DIVS_LFO),
    ]


def _voice(at: int) -> list[Param]:
    return [
        Param("assign_mode", at + 1, "mono, poly, or unison (all 4 voices on one note, detuned: fat leads and basses)",
              shift=6, bits=2, choices=("mono", "poly", "unison")),
        Param("eg2_reset", at + 1, shift=5, bits=1, choices=ONOFF),
        Param("eg1_reset", at + 1, shift=4, bits=1, choices=ONOFF),
        Param("trigger_mode", at + 1, "mono/unison: single = legato notes don't restart the envelopes",
              shift=3, bits=1, choices=("single", "multi")),
        Param("unison_detune", at + 2, "cents, in unison mode", hi=99),
        Param("tune", at + 3, "cents", lo=-50, hi=50, center=64),
        Param("bend_range", at + 4, "semitones", lo=-12, hi=12, center=64),
        Param("transpose", at + 5, "semitones", lo=-24, hi=24, center=64),
        Param("vibrato_int", at + 6, "how much the mod wheel adds vibrato", lo=-63, hi=63, center=64),
    ]


# One synth timbre (the program has two; the second only sounds in layer mode).
TIMBRE = [
    *_voice(0),
    Param("osc1_wave", 7, "vox = vocal formants, dwgs = 64 digital waves (dwgs_wave), noise, audio in",
          choices=WAVES, knob=1),
    Param("osc1_ctrl1", 8, "wave shape: pulse width on pulse, cross-modulation depth on sine, formant on vox, "
                           "noise filter cutoff on noise", knob=2),
    Param("osc1_ctrl2", 9, "second wave control: LFO1 wave-shape depth on saw/pulse/triangle/sine, noise "
                           "resonance on noise", knob=3),
    Param("dwgs_wave", 10, "which digital wave, when osc1_wave is dwgs", lo=1, hi=64, center=-1),
    Param("osc2_wave", 12, bits=2, choices=("saw", "square", "triangle"), knob=4),
    Param("osc2_mod", 12, "ring = metallic, sync = tearing sweeps when osc2 pitch moves", shift=4, bits=2,
          choices=("off", "ring", "sync", "ring+sync"), knob=5),
    Param("osc2_semitone", 13, "osc2 pitch against osc1, semitones", lo=-24, hi=24, center=64),
    Param("osc2_tune", 14, "osc2 detune, not even steps (measured): 3 = 2 cents, 6 = 9, 9 = 25, 12 = 60, 24 = over "
                           "two semitones. 4-6 fattens and stays in tune; 9 and up sounds out of tune in chords",
          lo=-63, hi=63, center=64, knob=7),
    Param("portamento", 15, "glide time between notes", bits=7, knob=0),
    Param("osc1_level", 16, knob=8),
    Param("osc2_level", 17, knob=9),
    Param("noise_level", 18, knob=10),
    Param("filter_type", 19, choices=("24lpf", "12lpf", "12bpf", "12hpf"), knob=11),
    Param("cutoff", 20, "brightness", knob=12),
    Param("resonance", 21, knob=13),
    Param("filter_eg_int", 22, "how far EG1 opens (+) or closes (-) the filter", lo=-63, hi=63, center=64, knob=14),
    Param("filter_velocity", 23, "harder notes are brighter", lo=-63, hi=63, center=64),
    Param("filter_kbd_track", 24, "higher notes are brighter", lo=-63, hi=63, center=64, knob=15),
    Param("amp_level", 25, knob=16),
    Param("pan", 26, "-64 left .. 0 centre .. 63 right", lo=-64, hi=63, center=64),
    Param("amp_gate", 27, "off = EG2 shapes the volume; on = an organ-like on/off gate", shift=6, bits=1,
          choices=ONOFF, knob=18),
    Param("distortion", 27, bits=1, choices=ONOFF, knob=19),
    Param("amp_velocity", 28, "harder notes are louder", lo=-63, hi=63, center=64),
    Param("amp_kbd_track", 29, lo=-63, hi=63, center=64),
    Param("eg1_attack", 30, "EG1 = the filter envelope (and a modulation source)", knob=20),
    Param("eg1_decay", 31, knob=21),
    Param("eg1_sustain", 32, knob=22),
    Param("eg1_release", 33, knob=23),
    Param("eg2_attack", 34, "EG2 = the volume envelope", knob=24),
    Param("eg2_decay", 35, knob=25),
    Param("eg2_sustain", 36, knob=26),
    Param("eg2_release", 37, knob=27),
    *_lfo(1, 38, ("saw", "square", "triangle", "s/h"), 28),
    *_lfo(2, 41, ("saw", "square+", "sine", "s/h"), 30),
    *[p for n in range(4) for p in (
        Param(f"patch{n + 1}_source", 44 + 2 * n, "modulation patch: what moves", bits=4, choices=SOURCES,
              nrpn=(4, n)),
        Param(f"patch{n + 1}_dest", 44 + 2 * n, "what it moves", shift=4, bits=4, choices=DESTS, nrpn=(4, 8 + n)),
        Param(f"patch{n + 1}_int", 45 + 2 * n, "how far (negative inverts)", lo=-63, hi=63, center=64, knob=32 + n),
    )],
]

# The vocoder (replaces both timbres): the voice goes into AUDIO IN 1, the keys play the carrier.
VOCODER = [
    *_voice(0),
    Param("osc1_wave", 7, "the carrier the voice is imposed on (saw is the classic robot)", choices=WAVES),
    Param("osc1_ctrl1", 8),
    Param("osc1_ctrl2", 9),
    Param("dwgs_wave", 10, lo=1, hi=64, center=-1),
    Param("hpf_gate", 12, "let the voice's high frequencies through only while keys are held", bits=1,
          choices=("off", "on")),
    Param("portamento", 14, bits=7),
    Param("osc1_level", 15, "carrier level"),
    Param("ext1_level", 16, "level of an external carrier on AUDIO IN 2"),
    Param("noise_level", 17, "noise in the carrier (helps consonants come through)"),
    Param("hpf_level", 18, "how much of the voice's own highs (s, t) are mixed in"),
    Param("gate_sense", 19, "how quickly the voice gate closes"),
    Param("threshold", 20, "voice level under which the input is gated (cuts room noise)"),
    Param("formant_shift", 21, "moves the voice's character up or down", choices=("0", "+1", "+2", "-1", "-2")),
    Param("cutoff", 22, "fine formant offset", lo=-63, hi=63, center=64),
    Param("resonance", 23, "sharpness of the 16 bands"),
    Param("filter_mod_source", 24, choices=("off", "eg2", "lfo1", "lfo2", "velocity", "kbd track", "pitch bend",
                                           "mod wheel")),
    Param("filter_mod_int", 25, lo=-63, hi=63, center=64),
    Param("ef_sense", 26, "envelope follower: how quickly the bands follow the voice; 127 = hold (freezes the "
                          "current vowel)"),
    Param("amp_level", 27),
    Param("direct_level", 28, "the dry voice mixed in"),
    Param("distortion", 29, bits=1, choices=ONOFF),
    Param("amp_velocity", 30, lo=-63, hi=63, center=64),
    Param("amp_kbd_track", 31, lo=-63, hi=63, center=64),
    Param("eg2_attack", 36),
    Param("eg2_decay", 37),
    Param("eg2_sustain", 38),
    Param("eg2_release", 39),
    *_lfo(1, 40, ("saw", "square", "triangle", "s/h"), 28),
    *_lfo(2, 43, ("saw", "square+", "sine", "s/h"), 30),
]
VOCODER = [Param(**{**p.__dict__, "knob": None, "nrpn": None}) for p in VOCODER]
BAND_LEVEL, BAND_PAN = 46, 62     # 16 filter channels, set in pairs as 8 bands

COMMON_BY_NAME = {p.name: p for p in COMMON}
TIMBRE_BY_NAME = {p.name: p for p in TIMBRE}
VOCODER_BY_NAME = {p.name: p for p in VOCODER}
BAND_NAMES = {f"band{n}_{kind}" for n in range(1, 9) for kind in ("level", "pan")}

# A plain, bright, dry single-oscillator sound: where every recipe starts from. creaper's
# own starting point, not one of Korg's programs.
INIT_COMMON: dict[str, Any] = {
    "voice_mode": "single", "arp_steps": 8, "arp_pattern": "xxxxxxxx", "delay_sync": "off", "delay_division": "1/8",
    "delay_time": 40, "delay_depth": 0, "delay_type": "stereo", "mod_speed": 20, "mod_depth": 0,
    "mod_type": "chorus/flanger", "eq_high_freq": 20, "eq_high_gain": 0, "eq_low_freq": 14, "eq_low_gain": 0,
    "arp_tempo": 120, "arp_on": "off", "arp_latch": "off", "arp_target": "both", "arp_key_sync": "on",
    "arp_type": "up", "arp_octaves": 1, "arp_gate": 80, "arp_resolution": "1/16", "arp_swing": 0, "kbd_octave": 0,
}
INIT_TIMBRE: dict[str, Any] = {
    "assign_mode": "poly", "eg2_reset": "on", "eg1_reset": "on", "trigger_mode": "multi", "unison_detune": 0,
    "tune": 0, "bend_range": 2, "transpose": 0, "vibrato_int": 5,
    "osc1_wave": "saw", "osc1_ctrl1": 0, "osc1_ctrl2": 0, "dwgs_wave": 1,
    "osc2_wave": "saw", "osc2_mod": "off", "osc2_semitone": 0, "osc2_tune": 0, "portamento": 0,
    "osc1_level": 127, "osc2_level": 0, "noise_level": 0,
    "filter_type": "24lpf", "cutoff": 127, "resonance": 0, "filter_eg_int": 0, "filter_velocity": 0,
    "filter_kbd_track": 0, "amp_level": 127, "pan": 0, "amp_gate": "off", "distortion": "off", "amp_velocity": 0,
    "amp_kbd_track": 0,
    "eg1_attack": 0, "eg1_decay": 64, "eg1_sustain": 127, "eg1_release": 0,
    "eg2_attack": 0, "eg2_decay": 64, "eg2_sustain": 127, "eg2_release": 5,
    "lfo1_wave": "triangle", "lfo1_key_sync": "off", "lfo1_freq": 10, "lfo1_tempo_sync": "off", "lfo1_division": "1/4",
    "lfo2_wave": "sine", "lfo2_key_sync": "off", "lfo2_freq": 70, "lfo2_tempo_sync": "off", "lfo2_division": "1/8",
    "patch1_source": "lfo1", "patch1_dest": "pitch", "patch1_int": 0,
    "patch2_source": "lfo2", "patch2_dest": "cutoff", "patch2_int": 0,
    "patch3_source": "eg1", "patch3_dest": "pitch", "patch3_int": 0,
    "patch4_source": "velocity", "patch4_dest": "amp", "patch4_int": 0,
}
INIT_VOCODER: dict[str, Any] = {
    "assign_mode": "poly", "eg2_reset": "on", "eg1_reset": "off", "trigger_mode": "multi", "unison_detune": 0,
    "tune": 0, "bend_range": 2, "transpose": 0, "vibrato_int": 5,
    "osc1_wave": "saw", "osc1_ctrl1": 0, "osc1_ctrl2": 0, "dwgs_wave": 1, "hpf_gate": "on", "portamento": 0,
    "osc1_level": 127, "ext1_level": 0, "noise_level": 10, "hpf_level": 40, "gate_sense": 30, "threshold": 0,
    "formant_shift": "0", "cutoff": 0, "resonance": 30, "filter_mod_source": "eg2", "filter_mod_int": 0,
    "ef_sense": 0, "amp_level": 127, "direct_level": 0, "distortion": "off", "amp_velocity": 0, "amp_kbd_track": 0,
    "eg2_attack": 0, "eg2_decay": 64, "eg2_sustain": 127, "eg2_release": 10,
    "lfo1_wave": "triangle", "lfo1_key_sync": "off", "lfo1_freq": 10, "lfo1_tempo_sync": "off", "lfo1_division": "1/4",
    "lfo2_wave": "sine", "lfo2_key_sync": "off", "lfo2_freq": 70, "lfo2_tempo_sync": "off", "lfo2_division": "1/8",
    **{f"band{n}_level": 127 for n in range(1, 9)}, **{f"band{n}_pan": 0 for n in range(1, 9)},
}


def _name(data: bytes | bytearray) -> str:
    return bytes(data[0:12]).decode("ascii", "replace").strip("\x00 ").strip()


def voice_mode(data: bytes | bytearray) -> str:
    return str(COMMON_BY_NAME["voice_mode"].read(data))


def decode_program(data: bytes) -> dict:
    """A 254-byte program as named values: {name, voice_mode, common, timbre1[, timbre2]} or
    {..., vocoder} for a vocoder program."""
    if len(data) != PROGRAM_BYTES:
        raise ValueError(f"a microKORG program is {PROGRAM_BYTES} bytes; this is {len(data)}")
    common = {p.name: p.read(data) for p in COMMON}
    out: dict[str, Any] = {"name": _name(data), "voice_mode": common.pop("voice_mode"), "common": common}
    if out["voice_mode"] == "vocoder":
        block = data[TIMBRE1:TIMBRE1 + TIMBRE_SIZE]
        voc = {p.name: p.read(block) for p in VOCODER}
        for n in range(8):
            voc[f"band{n + 1}_level"] = block[BAND_LEVEL + 2 * n]
            voc[f"band{n + 1}_pan"] = block[BAND_PAN + 2 * n] - 64
        out["vocoder"] = voc
    else:
        out["timbre1"] = {p.name: p.read(data[TIMBRE1:TIMBRE1 + TIMBRE_SIZE]) for p in TIMBRE}
        if out["voice_mode"] == "layer":
            out["timbre2"] = {p.name: p.read(data[TIMBRE2:TIMBRE2 + TIMBRE_SIZE]) for p in TIMBRE}
    return out


def _write_block(data: bytearray, at: int, table: dict[str, Param], values: dict[str, Any]) -> None:
    block = bytearray(data[at:at + TIMBRE_SIZE])
    for name, value in values.items():
        if name in BAND_NAMES and table is VOCODER_BY_NAME:
            n, kind = int(name[4]), name[6:]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} takes a whole number")
            if kind == "level":
                if not 0 <= value <= 127:
                    raise ValueError(f"{name} runs 0 to 127")
                block[BAND_LEVEL + 2 * (n - 1)] = block[BAND_LEVEL + 2 * (n - 1) + 1] = value
            else:
                if not -63 <= value <= 63:
                    raise ValueError(f"{name} runs -63 (left) to 63 (right)")
                block[BAND_PAN + 2 * (n - 1)] = block[BAND_PAN + 2 * (n - 1) + 1] = value + 64
            continue
        table[name].write(block, value)
    data[at:at + TIMBRE_SIZE] = block


def unknown_params(names: list[str], mode: str) -> list[str]:
    table = VOCODER_BY_NAME if mode == "vocoder" else TIMBRE_BY_NAME
    extra = BAND_NAMES if mode == "vocoder" else set()
    return [n for n in names if n not in COMMON_BY_NAME and n not in table and n not in extra and n != "name"]


def apply(data: bytes, params: dict[str, Any], timbre: int | str = 1) -> bytes:
    """The program with these parameters changed. Whole-program names (voice_mode, the
    effects, EQ, arpeggiator, 'name') go where they belong; the rest go to the timbre
    asked for (1, 2 or 'both'), or to the vocoder in a vocoder program. Switching
    voice_mode to or from vocoder resets the sound block to creaper's plain starting
    point first, because the two layouts share the same bytes."""
    if len(data) != PROGRAM_BYTES:
        raise ValueError(f"a microKORG program is {PROGRAM_BYTES} bytes; this is {len(data)}")
    out = bytearray(data)
    before = voice_mode(out)
    if "voice_mode" in params:
        COMMON_BY_NAME["voice_mode"].write(out, params["voice_mode"])
    after = voice_mode(out)
    if (before == "vocoder") != (after == "vocoder"):
        out[TIMBRE1:] = bytes(PROGRAM_BYTES - TIMBRE1)
        out[TIMBRE1] = 0xFF               # the sound follows the global MIDI channel
        if after == "vocoder":
            _write_block(out, TIMBRE1, VOCODER_BY_NAME, INIT_VOCODER)
        else:
            out[TIMBRE2] = 0xFF
            for at in (TIMBRE1, TIMBRE2):
                _write_block(out, at, TIMBRE_BY_NAME, INIT_TIMBRE)
    bad = unknown_params(list(params), after)
    if bad:
        other = "synth" if after == "vocoder" else "vocoder"
        table = TIMBRE_BY_NAME if after == "vocoder" else VOCODER_BY_NAME
        hint = [n for n in bad if n in table or n in BAND_NAMES]
        raise ValueError(
            f"no microKORG {'vocoder' if after == 'vocoder' else 'synth'} parameter named: {', '.join(bad)}"
            + (f" ({', '.join(hint)} belong to {other} programs: set voice_mode first)" if hint else "")
            + "; hardware_profile lists the names")
    if "name" in params:
        text = str(params["name"]).encode("ascii", "replace")[:12].ljust(12)
        out[0:12] = text
    for name, value in params.items():
        if name in COMMON_BY_NAME and name != "voice_mode":
            COMMON_BY_NAME[name].write(out, value)
    sound = {n: v for n, v in params.items() if n not in COMMON_BY_NAME and n != "name"}
    if sound:
        if after == "vocoder":
            _write_block(out, TIMBRE1, VOCODER_BY_NAME, sound)
        else:
            if timbre not in (1, 2, "both"):
                raise ValueError("timbre is 1, 2 or 'both'")
            if timbre in (2, "both") and after != "layer":
                raise ValueError("timbre 2 only sounds in a layer program: set voice_mode to 'layer' as well")
            for at in ([TIMBRE1, TIMBRE2] if timbre == "both" else [TIMBRE2 if timbre == 2 else TIMBRE1]):
                _write_block(out, at, TIMBRE_BY_NAME, sound)
    return bytes(out)


def init_program(template: bytes | None = None, name: str = "creaper") -> bytes:
    """creaper's plain starting sound. Built on a program the synth sent when there is
    one, so bytes the documentation doesn't describe stay as the synth had them."""
    data = bytearray(template if template and len(template) == PROGRAM_BYTES else bytes(PROGRAM_BYTES))
    was_vocoder = voice_mode(data) == "vocoder"
    COMMON_BY_NAME["voice_mode"].write(data, "single")
    if was_vocoder or not template:
        data[TIMBRE1:] = bytes(PROGRAM_BYTES - TIMBRE1)
        data[TIMBRE1] = data[TIMBRE2] = 0xFF
    out = apply(bytes(data), {**INIT_COMMON, **INIT_TIMBRE, "name": name})
    both = bytearray(out)
    _write_block(both, TIMBRE2, TIMBRE_BY_NAME, INIT_TIMBRE)
    return bytes(both)


def build(recipe: dict, template: bytes | None = None) -> bytes:
    """A recipe ({params, timbre2?, name?}) as a program, starting from init_program."""
    data = init_program(template, name=recipe.get("name", "creaper")[:12])
    data = apply(data, recipe.get("params", {}))
    if recipe.get("timbre2"):
        data = apply(data, recipe["timbre2"], timbre=2)
    return data


def program_dump(channel: int, data: bytes) -> str:
    """The SysEx message that loads a program into the edit buffer."""
    return message(channel, F_CURRENT_DUMP, pack(data))


# ------------------------------------------------------------- global data

KNOBS = ["portamento", "osc1_wave", "osc1_ctrl1", "osc1_ctrl2", "osc2_wave", "osc2_mod", "osc2_semitone", "osc2_tune",
         "osc1_level", "osc2_level", "noise_level", "filter_type", "cutoff", "resonance", "filter_eg_int",
         "filter_kbd_track", "amp_level", "pan", "amp_gate", "distortion", "eg1_attack", "eg1_decay", "eg1_sustain",
         "eg1_release", "eg2_attack", "eg2_decay", "eg2_sustain", "eg2_release", "lfo1_wave", "lfo1_freq", "lfo2_wave",
         "lfo2_freq", "patch1_int", "patch2_int", "patch3_int", "patch4_int", "seq_switch", "mod_speed", "mod_depth",
         "delay_time", "delay_depth"]


def _signed(b: int) -> int:
    return b - 256 if b > 127 else b


def decode_global(data: bytes) -> dict:
    """The Global dump: MIDI channel, what the synth's MIDI filters let through, memory
    protect, clock, and which control change each panel knob sends and answers to."""
    if len(data) != GLOBAL_BYTES:
        raise ValueError(f"the microKORG's global data is {GLOBAL_BYTES} bytes; this is {len(data)}")
    ccs = {}
    for i, name in enumerate(KNOBS):
        cc = _signed(data[18 + i])
        if 0 <= cc <= 95:
            ccs[name] = cc
    timbre_select = _signed(data[11])
    return {
        "midi_channel": (data[9] & 0x0F) + 1,
        "sysex_enabled": bool(data[16] & 0x80),
        "control_change_enabled": bool(data[17] & 0x04),
        "program_change_enabled": bool(data[17] & 0x01),
        "pitch_bend_enabled": bool(data[17] & 0x40),
        "memory_protect": bool(data[5] & 0x01),
        "local_control": bool(data[5] & 0x04),
        "clock": ("internal", "external", "auto")[min(data[8] & 0x03, 2)],
        "knob_ccs": ccs,
        "timbre_select_cc": timbre_select if 0 <= timbre_select <= 95 else None,
        "program_change_map_is_default": bytes(data[72:200]) == bytes(range(128)),
    }


# ------------------------------------------------------- live control (CC, NRPN)

def _bucket(index: int, count: int) -> int:
    """A controller value in the middle of choice `index` of `count` equal slices of 0-127."""
    return min(127, int((index + 0.5) * 128 / count))


# Choices whose slices of the controller range aren't equal, from Korg's tables.
_CC_SLICES = {"osc2_wave": (0x15, 0x40, 0x6A), "arp_type": (0x0A, 0x20, 0x35, 0x4A, 0x60, 0x75)}
# Not offered live: their controller values follow long tables (or the DWGS wave number);
# a patch load sets them exactly.
PATCH_ONLY = {"osc2_semitone", "arp_gate", "pan", "amp_gate"}


def live_messages(name: str, value: Any, channel: int, knob_ccs: dict[str, int]) -> list[str] | None:
    """The control change or NRPN messages that set one parameter while the synth plays,
    or None when it can only be set by loading the patch. Synth programs only."""
    p = COMMON_BY_NAME.get(name) or TIMBRE_BY_NAME.get(name)
    if p is None or name in PATCH_ONLY or p.pattern or p.wide:
        return None
    raw = p.raw(value)                      # validates, by name
    status = 0xB0 | (channel - 1)
    if p.choices:
        count = len([c for c in p.choices if c])
        send = _CC_SLICES[name][raw] if name in _CC_SLICES else (0x7F if raw else 0) if count == 2 else _bucket(raw, count)
    else:
        send = raw                          # 0-127 as stored; signed amounts are stored +64, which is what the knob sends
    if p.nrpn:
        msb, lsb = p.nrpn
        return [f"{status:02X} 63 {msb:02X}", f"{status:02X} 62 {lsb:02X}", f"{status:02X} 06 {send:02X}"]
    cc = knob_ccs.get(name)
    if p.knob is None or cc is None:
        return None
    return [f"{status:02X} {cc:02X} {send:02X}"]


def describe() -> dict:
    """The profile as a tool shows it: every parameter by name with its values."""
    return {
        "model": MODEL,
        "programs": "128, shown as A.11-A.88 and b.11-b.88; only the edit buffer is changed unless a program is written",
        "voices": "4 (2 notes at once in a layer program); one program at a time on one MIDI channel",
        "whole_program": [p.describe() for p in COMMON],
        "timbre": [p.describe() for p in TIMBRE],
        "vocoder": [p.describe() for p in VOCODER] + [
            {"name": "band1_level .. band8_level", "range": [0, 127], "what": "level of each of the 8 band pairs"},
            {"name": "band1_pan .. band8_pan", "range": [-63, 63]}],
        "measured_on_one": [
            "one cutoff step is one semitone; filter_kbd_track +48 follows the keys exactly",
            "with resonance at 127 the filter rings as a note: at cutoff 24 on the key played, 12 more per octave",
            "portamento over about 30 hasn't reached the note an eighth note later at 120 BPM",
            "osc2_tune isn't even: 3 = 2 cents, 6 = 9, 9 = 25, 12 = 60 (a pad at 12 was heard as out of tune)",
            "an arpeggio starts with its note only with arp_key_sync on",
            "sounds differ in level by 20 dB and more: compare level_db between sounds for one song",
        ],
        "modulation": {"sources": list(SOURCES), "destinations": list(DESTS),
                       "how": "four patches: patchN_source moves patchN_dest by patchN_int. EG1 or an LFO to "
                              "pitch makes zaps, risers and sirens; LFO s/h makes random bleeps."},
    }


# ----------------------------------------------------------------- recipes

# Starting points, each a set of parameters over init_program. They're written from how
# the sounds are described in print (sources in notes/hardware/microkorg-artist-sounds.md)
# and from how the synth works; none is a copy of a Korg program. Audition and tune them.
# "factory" names the Korg preset a source connects with the song: the tool can select
# that program instead, if the slot still holds Korg's sound.
RECIPES: dict[str, dict] = {
    # ---- in the style of well-known records
    "phaser glide lead": {
        "kind": "artist", "style_of": "The Killers, \"Somebody Told Me\" intro lead", "factory": "b.14",
        "evidence": "Forum posts name factory program b.14 (Phaser Lead); Keyboard (Oct 2005) hears detuned unison "
                    "saws, heavy glide and heavy phaser. No interview confirms the preset.",
        "play": "Mono line with octave jumps so the glide is heard; overlap notes for legato.",
        "role": "lead", "range": ["C4", "C6"], "voices": 1,
        # portamento 45 was still sliding half a second into each note (measured); at 28 an
        # octave jump arrives within a tenth of a tone by the next eighth note at 120 BPM.
        "params": {"assign_mode": "unison", "unison_detune": 14, "trigger_mode": "single", "portamento": 28,
                   "osc2_level": 127, "osc2_tune": 6, "cutoff": 105, "resonance": 20, "eg2_release": 20,
                   "mod_type": "phaser", "mod_depth": 100, "mod_speed": 22, "delay_depth": 25, "delay_time": 50},
    },
    "glide distortion lead": {
        "kind": "artist", "style_of": "The Killers, \"Smile Like You Mean It\" lead riff", "factory": "A.28",
        "evidence": "Forum posts name factory program A.28 (Hard House Lead), one adding 'an octave up'; Keyboard "
                    "(Oct 2005) hears a delayed, distorted lead leaning on glide. No interview confirms the preset.",
        "play": "Mono melody written C3-C5 (it sounds an octave up), notes overlapped so they slide.",
        "role": "lead", "range": ["C3", "C5"], "voices": 1,
        "params": {"assign_mode": "mono", "trigger_mode": "single", "portamento": 35, "osc2_wave": "square",
                   "osc2_level": 110, "osc2_tune": 6, "cutoff": 85, "resonance": 30, "distortion": "on",
                   "eg2_release": 25, "delay_sync": "on", "delay_division": "1/8", "delay_depth": 55,
                   "transpose": 12},
    },
    "eighth-note saw bass": {
        "kind": "artist",
        "style_of": "The Killers, \"Mr. Brightside\" pre-chorus counter-bass (as Keyboard describes it)",
        "evidence": "Keyboard (Oct 2005): saw + pulse with a quick envelope, in eighth notes. No source says this "
                    "part was a microKORG (the band also used a Nord Lead).",
        "play": "Steady eighth notes on the chord roots, C1-C3 (fills to C4).",
        "role": "bass", "range": ["C1", "C4"], "voices": 1,
        "params": {"assign_mode": "mono", "osc2_wave": "square", "osc2_level": 100, "osc2_tune": 4, "cutoff": 62,
                   "resonance": 30, "filter_eg_int": 50, "eg1_decay": 45, "eg1_sustain": 30, "eg2_decay": 60,
                   "eg2_sustain": 90, "eg2_release": 10, "eq_low_freq": 6, "eq_low_gain": 3},
    },
    "octave unison saw solo": {
        "kind": "artist", "style_of": "The Killers, \"Mr. Brightside\" solo (as Keyboard describes it)",
        "evidence": "Keyboard (Oct 2005): unison-detuned saws stacked in octaves. No source says it was a microKORG.",
        "play": "Mono melody, C4-C7 (thin and piercing at the very top).",
        "role": "solo", "range": ["C4", "C7"], "voices": 1,
        "params": {"assign_mode": "unison", "unison_detune": 18, "osc2_level": 127, "osc2_semitone": 12,
                   "cutoff": 110, "eg2_release": 30, "mod_type": "ensemble", "mod_depth": 40, "delay_depth": 30},
    },
    "square bass": {
        "kind": "artist", "style_of": "The Killers, \"Andy, You're a Star\" bass (as Keyboard describes it)",
        "evidence": "Keyboard (Oct 2005): a bass from two square oscillators with a fast-opening filter. No source "
                    "says it was a microKORG.",
        "play": "Mono bass line, C1-C3 (fills to C4): held notes growl, short ones punch.",
        "role": "bass", "range": ["C1", "C4"], "voices": 1,
        "params": {"assign_mode": "mono", "osc1_wave": "pulse", "osc1_ctrl1": 0, "osc2_wave": "square",
                   "osc2_level": 127, "osc2_tune": 5, "cutoff": 46, "resonance": 35, "filter_eg_int": 55,
                   "eg1_decay": 55, "eg1_sustain": 50, "eg2_decay": 70, "eg2_sustain": 100, "eg2_release": 8},
    },
    "dual saw strings": {
        "kind": "artist", "style_of": "The Killers, \"Smile Like You Mean It\" string pad (as Keyboard describes it)",
        "evidence": "Keyboard (Oct 2005): a dual-saw string sound. No source says it was a microKORG.",
        "play": "Held chords of up to 4 notes (the synth has 4 voices), C2-C6; it swells in over a fifth of a second.",
        "role": "pad", "range": ["C2", "C6"], "voices": 4,
        "params": {"assign_mode": "poly", "osc2_level": 127, "osc2_tune": 6, "cutoff": 100, "resonance": 5,
                   "filter_kbd_track": 20, "eg2_attack": 40, "eg2_decay": 80, "eg2_sustain": 115, "eg2_release": 55,
                   "mod_type": "ensemble", "mod_depth": 90, "mod_speed": 20, "eq_high_freq": 16, "eq_high_gain": 3},
    },
    "saw stab chords": {
        "kind": "song",
        "play": "Short chord stabs or pumping eighth-note chords of up to 4 notes, C2-C5: it speaks at once, where "
                "the strings swell.",
        "role": "chords", "range": ["C2", "C5"], "voices": 4,
        "params": {"assign_mode": "poly", "osc2_level": 120, "osc2_tune": 5, "filter_type": "12lpf", "cutoff": 66,
                   "resonance": 15, "filter_eg_int": 40, "eg1_decay": 45, "eg1_sustain": 0, "eg1_release": 30,
                   "eg2_decay": 70, "eg2_sustain": 80, "eg2_release": 22, "mod_depth": 35, "mod_speed": 25},
    },
    "synth pluck": {
        "kind": "song",
        "play": "Sixteenth-note broken chords written as MIDI notes, C3-C6 (up to 4 ring at once); a dotted-eighth "
                "echo fills the gaps, at the song's tempo.",
        "role": "arp", "range": ["C3", "C6"], "voices": 4,
        "params": {"assign_mode": "poly", "osc1_wave": "pulse", "osc1_ctrl1": 40, "osc2_wave": "saw", "osc2_level": 80,
                   "osc2_tune": 5, "filter_type": "12lpf", "cutoff": 48, "resonance": 30, "filter_eg_int": 45,
                   "eg1_decay": 42, "eg1_sustain": 0, "eg1_release": 40, "eg2_decay": 55, "eg2_sustain": 0,
                   "eg2_release": 45, "delay_sync": "on", "delay_division": "3/16", "delay_depth": 40},
    },
    "noise helicopter": {
        "kind": "artist", "style_of": "The Killers, \"Jenny Was a Friend of Mine\" helicopter noise",
        "evidence": "Keyboard (Oct 2005): white noise with a triangle LFO on the filter cutoff.",
        "play": "Hold any note; lfo1_freq sets the rotor speed.",
        "params": {"osc1_level": 0, "noise_level": 127, "filter_type": "12lpf", "cutoff": 40, "resonance": 35,
                   "lfo1_wave": "triangle", "lfo1_freq": 60, "patch1_source": "lfo1", "patch1_dest": "cutoff",
                   "patch1_int": 50, "eg2_attack": 40, "eg2_release": 70},
    },
    "ringing filter note": {
        "kind": "artist", "style_of": "The Killers, \"All These Things That I've Done\" ringing note",
        "evidence": "Keyboard (Oct 2005): a self-oscillating, high-resonance filter note with white noise under it.",
        "play": "Hold one note, C4-C6; the filter rings an octave above the key, in tune.",
        # Measured on a microKORG (2026-11-13): one cutoff step is one semitone, keyboard track +48 is
        # exactly 1:1, and at cutoff 24 the ringing filter sits on the played note (3 cents flat);
        # every 12 more is an octave up, and above about 7 kHz it stops following. At 24 the ring
        # takes a second to build; at 36 with the noise full up it speaks in about 0.1 s.
        "params": {"osc1_level": 0, "noise_level": 127, "cutoff": 36, "resonance": 127, "filter_kbd_track": 48,
                   "eg2_attack": 20, "eg2_release": 80, "delay_depth": 40},
    },
    "sync scream": {
        "kind": "artist", "style_of": "The Killers, \"On Top\" sync sound at 3:33 (as Keyboard describes it)",
        "evidence": "Keyboard (Oct 2005): a hard-sync sound with extreme pitch movement.",
        "play": "Hold a note C3-C4: the envelope tears the pitch of the synced oscillator downwards.",
        "params": {"assign_mode": "mono", "osc2_mod": "sync", "osc1_level": 0, "osc2_level": 127, "osc2_semitone": 12,
                   "patch3_source": "eg1", "patch3_dest": "osc2 pitch", "patch3_int": 63, "eg1_decay": 85,
                   "eg1_sustain": 0, "distortion": "on", "eg2_release": 30},
    },
    "sub bass": {
        "kind": "artist",
        "style_of": "The Prodigy's use of the microKORG for sub bass (Always Outnumbered, Never Outgunned)",
        "evidence": "Liam Howlett, Korg interview 2004: sub bass on \"Memphis Bells\" and \"Wake Up\" came from a "
                    "microKORG. No preset or settings are given: this is a plain sine sub.",
        "play": "Mono, C1-C2, under another bass.",
        "role": "bass", "range": ["C1", "C2"], "voices": 1,
        "params": {"assign_mode": "mono", "trigger_mode": "single", "osc1_wave": "sine", "cutoff": 60,
                   "eg2_release": 15, "transpose": -12},
    },
    "pulse band-pass keys": {
        "kind": "artist", "style_of": "Snoop Dogg, \"Drop It Like It's Hot\" keys",
        "evidence": "Syntorial's recipe (pulse, band-pass, triangle LFO on the pulse width); whether the record "
                    "used a microKORG is disputed.",
        "play": "Short stabs, C3-C5.",
        "params": {"osc1_wave": "pulse", "osc1_ctrl1": 76, "osc1_ctrl2": 40, "filter_type": "12bpf", "cutoff": 50,
                   "resonance": 38, "lfo1_wave": "triangle", "lfo1_tempo_sync": "on", "lfo1_division": "1/8",
                   "eg2_attack": 3, "eg2_release": 8},
    },
    # ---- game sound effects
    "laser zap": {
        "kind": "sfx", "play": "Short notes, C4-C6: higher notes are thinner and quicker. Retune with patch3_int "
                                "(depth of the drop) and eg1_decay (its speed).",
        "params": {"assign_mode": "mono", "osc1_wave": "pulse", "osc1_ctrl1": 30, "osc2_mod": "sync",
                   "osc2_level": 100, "osc2_semitone": 7, "patch3_source": "eg1", "patch3_dest": "pitch",
                   "patch3_int": 63, "eg1_decay": 38, "eg1_sustain": 0, "eg1_release": 38, "filter_type": "12lpf",
                   "cutoff": 110, "resonance": 45, "eg2_decay": 45, "eg2_sustain": 0, "eg2_release": 30},
    },
    "power-up": {
        "kind": "sfx", "play": "Hold a major triad (C4 E4 G4) for 1-2 s: the arpeggiator runs it up four octaves. "
                                "arp_tempo sets the speed; arp_type 'down' makes a power-down.",
        "params": {"osc1_wave": "pulse", "osc1_ctrl1": 64, "cutoff": 115, "eg2_decay": 30, "eg2_sustain": 60,
                   "eg2_release": 20, "arp_on": "on", "arp_type": "up", "arp_octaves": 4, "arp_resolution": "1/24",
                   "arp_tempo": 200, "arp_gate": 60, "delay_depth": 35, "delay_time": 35},
    },
    "alarm": {
        "kind": "sfx", "play": "Hold a note around C5 for as long as the alarm sounds. lfo1_freq sets the rate; "
                                "lfo1_wave 'saw' turns the two-tone klaxon into a siren sweep.",
        "params": {"assign_mode": "mono", "osc1_wave": "pulse", "osc1_ctrl1": 40, "lfo1_wave": "square",
                   "lfo1_key_sync": "voice", "lfo1_freq": 55, "patch1_source": "lfo1", "patch1_dest": "pitch",
                   "patch1_int": 30, "filter_type": "12bpf", "cutoff": 90, "resonance": 40, "distortion": "on"},
    },
    "explosion": {
        "kind": "sfx", "play": "One low note (C1-C2), held 0.3 s; the tail rings on. Longer: raise eg1_decay and "
                                "eg2_release together.",
        "params": {"osc1_wave": "noise", "osc1_ctrl1": 127, "noise_level": 127, "cutoff": 15, "resonance": 20,
                   "filter_eg_int": 63, "eg1_decay": 85, "eg1_sustain": 0, "eg1_release": 85, "eg2_decay": 95,
                   "eg2_sustain": 0, "eg2_release": 95, "distortion": "on", "eq_low_freq": 4, "eq_low_gain": 9,
                   "delay_depth": 20, "delay_time": 60},
    },
    "ui blip": {
        "kind": "sfx", "play": "One very short note, C6-C7. Confirm = two rising notes, cancel = two falling, "
                                "error = one low note (C4) with distortion on.",
        "params": {"assign_mode": "mono", "osc1_wave": "sine", "patch3_source": "eg1", "patch3_dest": "pitch",
                   "patch3_int": 12, "eg1_decay": 15, "eg1_sustain": 0, "eg2_decay": 22, "eg2_sustain": 0,
                   "eg2_release": 18},
    },
    "sci-fi drone": {
        "kind": "sfx", "play": "Hold a low fifth (C2 G2) for the whole loop; it moves slowly by itself. For a "
                                "seamless loop record at least 20 s.",
        "params": {"voice_mode": "layer", "osc2_mod": "ring", "osc2_level": 90, "osc2_semitone": 7, "osc2_tune": 9,
                   "noise_level": 15, "cutoff": 45, "resonance": 70, "lfo2_wave": "sine", "lfo2_freq": 8,
                   "patch2_source": "lfo2", "patch2_dest": "cutoff", "patch2_int": 28, "lfo1_wave": "s/h",
                   "lfo1_freq": 12, "patch1_source": "lfo1", "patch1_dest": "pan", "patch1_int": 40,
                   "eg2_attack": 90, "eg2_release": 100, "mod_type": "ensemble", "mod_depth": 70, "mod_speed": 10,
                   "delay_depth": 50, "delay_time": 90},
        "timbre2": {"osc1_wave": "dwgs", "dwgs_wave": 40, "transpose": -12, "cutoff": 35, "resonance": 50,
                    "lfo2_wave": "sine", "lfo2_freq": 5, "patch2_source": "lfo2", "patch2_dest": "cutoff",
                    "patch2_int": -30, "eg2_attack": 100, "eg2_release": 100},
    },
    "alien chatter": {
        "kind": "sfx", "play": "Hold one note (C4-C5): random pitches bubble out for as long as it's held. "
                                "lfo1_freq sets how fast it talks.",
        "params": {"assign_mode": "mono", "osc1_wave": "vox", "osc1_ctrl1": 60, "lfo1_wave": "s/h", "lfo1_freq": 75,
                   "lfo1_key_sync": "voice", "patch1_source": "lfo1", "patch1_dest": "pitch", "patch1_int": 45,
                   "patch2_source": "lfo1", "patch2_dest": "osc1 ctrl1", "patch2_int": 50, "filter_type": "12bpf",
                   "cutoff": 80, "resonance": 60, "delay_depth": 30, "delay_time": 25},
    },
    "ufo hover": {
        "kind": "sfx", "play": "Hold a note around C4; bend or automate the pitch for fly-bys.",
        "params": {"assign_mode": "mono", "osc1_wave": "sine", "osc1_ctrl1": 45, "osc2_wave": "triangle",
                   "osc2_level": 80, "osc2_mod": "ring", "osc2_semitone": 5, "lfo1_wave": "triangle",
                   "lfo1_freq": 85, "patch1_source": "lfo1", "patch1_dest": "pitch", "patch1_int": 14,
                   "lfo2_wave": "sine", "lfo2_freq": 20, "patch2_source": "lfo2", "patch2_dest": "pan",
                   "patch2_int": 50, "eg2_attack": 40, "eg2_release": 60, "mod_type": "phaser", "mod_depth": 60},
    },
    "radio static": {
        "kind": "sfx", "play": "Hold any note for the length of the transmission; short notes make comms clicks.",
        "params": {"osc1_level": 0, "noise_level": 127, "filter_type": "12bpf", "cutoff": 85, "resonance": 55,
                   "lfo1_wave": "s/h", "lfo1_freq": 100, "patch1_source": "lfo1", "patch1_dest": "cutoff",
                   "patch1_int": 35, "lfo2_wave": "s/h", "lfo2_freq": 90, "patch2_source": "lfo2",
                   "patch2_dest": "amp", "patch2_int": 40, "distortion": "on", "eq_low_gain": -8},
    },
    "robot voice": {
        "kind": "sfx", "play": "A vocoder: it only sounds while a voice comes into the microKORG's AUDIO IN 1 (its "
                                "mic, or a line from an interface output playing a spoken track) AND keys are held. "
                                "One held note = a monotone robot; a chord = a choir of them. formant_shift -1/-2 "
                                "makes it bigger and darker, +1/+2 smaller.",
        "params": {"voice_mode": "vocoder", "assign_mode": "poly", "osc1_wave": "saw", "noise_level": 15,
                   "hpf_level": 50, "resonance": 40, "formant_shift": "-1", "direct_level": 0, "eg2_release": 15},
    },
}

# Korg presets that reviewers and players point to by name. Only the program is named
# here; the tool selects it on the synth (if the slot still holds Korg's sound).
FACTORY_NOTES = {
    "b.14": "Phaser Lead: the program forum posts connect with \"Somebody Told Me\"",
    "A.28": "Hard House Lead: the program forum posts connect with \"Smile Like You Mean It\"",
    "A.16": "Slippy Pad: a reviewer hears Underworld's \"Born Slippy\" in it",
    "b.72": "Domin8or: a 'hoover' rave lead",
    "b.43": "Reverse Bass",
    "b.66": "Square Comp",
    "A.84": "Vocoder Ensemble: the manual's vocoder example (A.81-A.88 and b.81-b.88 are the vocoder programs)",
}


def find_recipe(name: str) -> tuple[str, dict]:
    wanted = name.strip().lower()
    if wanted in RECIPES:
        return wanted, RECIPES[wanted]
    near = [k for k in RECIPES if wanted in k or wanted in RECIPES[k].get("style_of", "").lower()]
    if len(near) == 1:
        return near[0], RECIPES[near[0]]
    raise ValueError(f"no microKORG recipe named '{name}'; there are: {', '.join(RECIPES)}")


def part_fit(recipe: dict, notes: list[dict]) -> list[str]:
    """What a part asks that this recipe's sound can't do: notes outside its range, more
    notes at once than it has voices. notes: [{pitch, start, length}] in any one time unit."""
    from .theory import midi_to_note, note_to_midi

    said = []
    if not notes:
        return said
    if recipe.get("range"):
        lo, hi = (note_to_midi(n) for n in recipe["range"])
        low = [n for n in notes if n["pitch"] < lo]
        high = [n for n in notes if n["pitch"] > hi]
        for group, word, edge in ((low, "below", lo), (high, "above", hi)):
            if len(group) > max(2, len(notes) // 25):          # a few stray notes aren't worth a line
                worst = min(n["pitch"] for n in group) if word == "below" else max(n["pitch"] for n in group)
                said.append(f"{len(group)} of {len(notes)} notes are {word} where this sound works "
                            f"({midi_to_note(edge)}; the part goes to {midi_to_note(worst)}): move them an octave, "
                            "or choose a sound for that register")
    voices = int(recipe.get("voices") or 0)
    if voices:
        events = sorted([(n["start"] + 0.03, 1) for n in notes] + [(n["start"] + n["length"] - 0.03, -1) for n in notes])
        most = now = 0
        for _, step in events:
            now += step
            most = max(most, now)
        if voices == 1 and most > 1:
            said.append(f"the part plays up to {most} notes at once and this sound plays one (the latest note wins): "
                        "fine for a line doubled in octaves, wrong for chords")
        elif most > voices:
            said.append(f"the part plays up to {most} notes at once and this sound has {voices} voices: notes will "
                        "be cut off; thin the chords to {voices} notes".replace("{voices}", str(voices)))
    return said


def describe_recipes(kind: str | None = None) -> list[dict]:
    out = []
    for name, r in RECIPES.items():
        if kind and r["kind"] != kind:
            continue
        entry = {"recipe": name, "kind": r["kind"], "play": r["play"]}
        for key in ("role", "range", "voices", "style_of", "evidence", "factory"):
            if r.get(key):
                entry[{"factory": "factory_program"}.get(key, key)] = r[key]
        out.append(entry)
    return out


# ------------------------------------- what hardware_sound_tools asks of a profile
# (the interface is written down in hardware_profiles.Profile)

READS_PATCH = True      # it answers a request for its current sound
ACKS_LOAD = True        # it confirms, or refuses, a sound sent to it
PARTS = 1               # one sound at a time, on one MIDI channel
TEMPO_RANGE = (20, 300)
TEMPO_PARAM = "arp_tempo"   # the parameter that holds a patch's tempo

# How the synth answers the MIDI identity request, for scan_hardware.
IDENTITY = {
    "maker": "42", "family": 0x0058, "member": 0x0011, "kind": "synth", "device_id_is_channel": True,
    "setup": ("Its audio comes from the L/MONO and R outputs on the back: plug them into two interface inputs "
              "(L/MONO alone gives mono). On the microKORG's MIDI settings: 'CtrlChg' filter ENA lets creaper "
              "turn its knobs over MIDI, and 'SystemEx' filter ENA lets it read and load patches. "
              "It's 4-voice, one patch at a time (two timbres in a layer or split patch)."),
}

PROTECT_HELP = "SHIFT + the program key labelled WRITE PROTECT, then OFF"


def read_request(channel: int) -> tuple[list[str], set[int]]:
    """(messages that ask for the current sound, the function codes that answer them)."""
    return [message(channel, F_CURRENT_REQUEST)], {F_CURRENT_DUMP, F_LOAD_ERROR}


def patch_reply(function: int, payload: bytes) -> bytes | None:
    """The patch in the answer to read_request; None when the synth answered with an error."""
    return unpack(payload) if function == F_CURRENT_DUMP else None


def load_request(channel: int, data: bytes) -> tuple[list[str], set[int]]:
    return [program_dump(channel, data)], {F_LOAD_OK, F_LOAD_ERROR, F_FORMAT_ERROR}


def load_error(function: int) -> str | None:
    """None when the synth took the sound, else what it reported."""
    return None if function == F_LOAD_OK else "data format error" if function == F_FORMAT_ERROR else "load error"


def setup_request(channel: int) -> tuple[list[str], set[int]]:
    return [message(channel, F_GLOBAL_REQUEST)], {F_GLOBAL_DUMP}


def setup_reply(function: int, payload: bytes) -> dict:
    return decode_global(unpack(payload))


def write_request(channel: int, number: int) -> tuple[list[str], set[int]]:
    """Stores the edit buffer in program `number` (0-127). Korg's payload: a zero, then the program."""
    return [message(channel, F_WRITE_REQUEST, [0, number])], {F_WRITE_OK, F_WRITE_ERROR}


def write_error(function: int) -> str | None:
    return None if function == F_WRITE_OK else "write error"


def select_program(channel: int, number: int) -> list[str]:
    """Selects a stored program: one program change (128 programs, so no bank select)."""
    return [f"{0xC0 | (channel - 1):02X} {number:02X}"]


def patch_in_message(hexstr: str) -> bytes | None:
    """The patch a sound message carries (what program_dump wrote), or None for anything else."""
    parsed = parse_message(hexstr)
    return unpack(parsed[1]) if parsed and parsed[0] == F_CURRENT_DUMP else None


def click_patch(current: bytes | None) -> bytes:
    """A short click with an instant attack, for measuring latency."""
    return apply(init_program(current, name="click"),
                 {"osc1_wave": "pulse", "osc1_ctrl1": 0, "cutoff": 127, "eg2_attack": 0, "eg2_decay": 40,
                  "eg2_sustain": 0, "eg2_release": 0, "assign_mode": "mono"})


def level_patch(current: bytes | None) -> bytes:
    """A loud plain sound (four detuned saws in unison, filter open) for setting the
    interface's input gain. Not the loudest there is: a distorted lead measured 7 dB over
    it, which is why the level check aims it well under full scale."""
    return apply(init_program(current, name="level"),
                 {"assign_mode": "unison", "unison_detune": 10, "osc2_level": 127, "osc2_tune": 5, "cutoff": 127,
                  "eg2_attack": 0, "eg2_sustain": 127, "eg2_release": 0})


def brief(data: bytes) -> dict:
    """The few facts about a patch that every result carries."""
    return {"voice_mode": voice_mode(data)}


def flat(prog: dict) -> dict:
    """A decoded program as one level of names (timbre 2's prefixed), to show what a change did."""
    out = {"voice_mode": prog["voice_mode"]}
    for block in ("common", "timbre1", "timbre2", "vocoder"):
        for key, value in (prog.get(block) or {}).items():
            out[key if block in ("common", "timbre1", "vocoder") else f"timbre2.{key}"] = value
    return out


def setup_problems(setup: dict) -> list[str]:
    """What in the synth's own MIDI settings stands in creaper's way."""
    problems = []
    if not setup["control_change_enabled"]:
        problems.append("it ignores control changes (knob moves over MIDI): " + SETUP_HELP)
    if not setup["program_change_enabled"]:
        problems.append("it ignores program changes, so creaper can't select its stored programs")
    if setup["memory_protect"]:
        problems.append("memory protect is on: write_hardware_program will be refused until the user turns it off "
                        "(SHIFT + the program key labelled WRITE PROTECT)")
    return problems


def live_blocked(setup: dict) -> str | None:
    """Why parameters can't be set live with these MIDI settings (follows the device's name), or None."""
    return None if setup.get("control_change_enabled") else f"ignores control changes. {SETUP_HELP}"


def live(params: dict[str, Any], timbre: int | str, channel: int, setup: dict) -> tuple[list[str], list[str]]:
    """(the messages that set these parameters while the synth plays, the names that can't be set live)."""
    messages, cant = [], []
    for key, value in params.items():
        made = live_messages(key, value, channel, setup.get("knob_ccs", {}))
        if made is None:
            cant.append(key)
        else:
            messages += made
    select = setup.get("timbre_select_cc")
    if select is not None and timbre in (1, 2):
        messages.insert(0, f"{0xB0 | (channel - 1):02X} {select:02X} {0 if timbre == 1 else 0x7F:02X}")
    return messages, cant


# ------------------------------------------------------------------ tempo
# The synth has one tempo per program ("arp_tempo"): the arpeggiator, a synced delay and
# tempo-synced LFOs all run at it while the synth is on its own clock. With its Clock
# setting on External (or Auto, while MIDI clock arrives) they follow the MIDI clock
# instead and the program's tempo is ignored.

def tempo_features(data: bytes) -> list[str]:
    """What in this patch runs at the tempo; empty when nothing does."""
    prog = decode_program(data)
    uses = []
    if prog["common"]["arp_on"] == "on":
        uses.append("arpeggiator")
    if prog["common"]["delay_sync"] == "on" and prog["common"]["delay_depth"] > 0:
        uses.append("synced delay")
    blocks = [prog[b] for b in ("timbre1", "timbre2", "vocoder") if prog.get(b)]
    if any(b.get(f"lfo{n}_tempo_sync") == "on" for b in blocks for n in (1, 2)):
        uses.append("tempo-synced LFO")
    return uses


def tempo(data: bytes) -> int:
    return int(COMMON_BY_NAME["arp_tempo"].read(data))


def with_tempo(data: bytes, bpm: float) -> tuple[bytes, int]:
    """(the patch at this tempo, the tempo it got): whole BPM, inside the synth's range."""
    lo, hi = TEMPO_RANGE
    whole = int(min(hi, max(lo, round(bpm))))
    return apply(data, {"arp_tempo": whole}), whole


def start_on_the_note(data: bytes) -> tuple[bytes, str | None]:
    """(the patch with its arpeggiator restarting at every new note, what changed or None).
    With arp_key_sync off the arpeggiator steps on a clock that never stops, so a part's
    first step waits for the next tick: measured on a microKORG at 97 BPM, a printed
    arpeggio sat about 100 ms behind the bar; with it on, 5 ms, and 2 ms of drift in 4 bars."""
    common = decode_program(data)["common"]
    if common["arp_on"] != "on" or common["arp_key_sync"] == "on":
        return data, None
    return apply(data, {"arp_key_sync": "on"}), (
        "arp_key_sync was turned on in the song's copy of this sound, so the arpeggio starts with the part's first "
        "note; with it off the first step waits for the synth's free-running clock and the part sits up to a step "
        "late.")


def clock_note(setup: dict | None) -> str:
    """What the synth's Clock setting means for a patch that runs at the tempo."""
    clock = (setup or {}).get("clock")
    change = "CLOCK on the microKORG's MIDI edit page"
    if clock == "external":
        return ("The microKORG's Clock is set to External: it ignores the patch's tempo and waits for MIDI clock, so "
                "the arpeggiator, a synced delay and synced LFOs only run right if REAPER sends clock to its MIDI "
                "output (Preferences > MIDI Devices > the output > 'Send clock/SPP to this device'). creaper doesn't "
                f"check or send clock: have the user set {change} to Internal, or turn that REAPER option on.")
    if clock == "auto":
        return ("The microKORG's Clock is set to Auto: it uses the patch's tempo unless MIDI clock arrives, and then "
                "follows the clock instead.")
    if clock == "internal":
        return ("The microKORG is on its own clock (Internal), so it runs at the patch's tempo. It keeps that speed "
                "but isn't locked to REAPER's bar lines: an arpeggio starts with its note when the patch's "
                "arp_key_sync is on (creaper's recipes have it on, and it's turned on in a sound written into the "
                "song), then runs on the synth's clock.")
    return ("The patch's tempo only counts while the microKORG is on its own clock: with its Clock setting on "
            f"External (or Auto with MIDI clock arriving) it follows MIDI clock instead ({change}; hardware_profile "
            "show='setup' reads the setting).")


# What the 0-127 values are in real units, measured on one microKORG through an SSL 2+ on
# 2026-11-13 (notes/hardware/calibrate_microkorg.py: each value loaded, played, recorded,
# measured). Other units will differ a little; the shapes won't. Times are: attack to 90%
# of full level; decay and release to fall 20 dB. None = not measurable that way.
CALIBRATION: dict[str, Any] = {
    "measured": "one microKORG, 2026-11-13",
    # value 0 is quicker than could be timed; decay and release 0 are a click's length
    "eg_attack_ms": {0: 1, 16: 64, 32: 158, 48: 338, 64: 621, 80: 898, 96: 1164, 112: 3806, 127: 14780},
    "eg_decay_ms": {0: 5, 16: 27, 32: 78, 48: 187, 64: 333, 80: 480, 96: 635, 112: 2097, 127: 12972},
    "eg_release_ms": {0: 5, 16: 32, 32: 89, 48: 195, 64: 341, 80: 490, 96: 641, 112: 2100, 127: 12986},
    # keyboard tracking off: a semitone a step up to about 6 kHz, then it flattens to a ceiling near 18 kHz
    "cutoff_hz": {0: 65, 20: 207, 40: 658, 60: 2089, 80: 6109, 100: 13690, 127: 18000},
    "cutoff_ref": (60, 2089.0),
    # how far a fully open EG1 moves the cutoff: about 0.13 octave a step (16 and 32 measured,
    # the rest on that line: the filter's ceiling hid them)
    "filter_eg_octaves": {0: 0.0, 16: 2.05, 32: 4.26, 48: 6.4, 63: 8.4},
    # filter_kbd_track: 16 = a third, 32 = two thirds, 48 = follows the keys exactly, 63 = twice as fast
    "kbd_track_full": 48,
    "kbd_track_ratio": {16: 0.33, 32: 0.67, 48: 1.0, 63: 2.0},
    # both LFOs alike. Under 0.3 Hz couldn't be timed in a 6 s recording: 0 and 20 are the
    # manual's 0.01 Hz and the measurement's upper bound
    "lfo1_hz": {0: 0.01, 20: 0.26, 40: 1.75, 60: 4.33, 80: 12.97, 100: 41.2, 127: 65.7},
    "lfo2_hz": {0: 0.01, 20: 0.26, 40: 1.75, 60: 4.33, 80: 12.97, 100: 41.2, 127: 65.7},
    # time for an octave to arrive (within 60 cents)
    "portamento_ms_per_octave": {0: 0, 10: 40, 20: 75, 30: 125, 40: 170, 55: 275, 70: 550, 90: 1120},
    # oscillator 2 against oscillator 1: nothing like even steps
    "osc2_tune_cents": {0: 0, 2: 2.2, 3: 2.5, 4: 3.6, 5: 5.0, 6: 9.4, 7: 15.1, 8: 19.4, 9: 25.0, 10: 37.8, 12: 59.5,
                        15: 90.5, 18: 150, 21: 225, 30: 450, 40: 800, 48: 1200, 63: 2400},
    # the unsynced delay: 0 is under 15 ms; past 100 the echo was too long or faint to time
    "delay_time_ms": {0: 10, 20: 78, 40: 142, 60: 206, 80: 332, 100: 475},
    # a modulation patch's intensity to pitch: the whole swing of an LFO, the rise of a full EG1
    "lfo_pitch_semitones": {0: 0.0, 4: 0.1, 8: 0.41, 16: 2.0, 32: 10.0, 48: 24.0, 63: 48.0},
    "eg_pitch_semitones": {0: 0.0, 4: 0.04, 8: 0.21, 16: 1.0, 32: 5.0, 48: 12.0, 63: 24.0},
}


def calibration_summary() -> dict:
    """The calibration for the model: each parameter's values in real units, to work out any
    value a blueprint doesn't give."""
    c = CALIBRATION
    def curve(name: str) -> dict:
        return {str(v): r for v, r in c[name].items()}
    return {
        "measured_on": c["measured"],
        "eg_attack (ms to 90%)": curve("eg_attack_ms"),
        "eg_decay (ms to fall 20 dB)": curve("eg_decay_ms"),
        "eg_release (ms to fall 20 dB)": curve("eg_release_ms"),
        "cutoff (Hz, keyboard tracking off)": curve("cutoff_hz"),
        "filter_eg_int (octaves a full envelope moves the cutoff; 16 and 32 measured, 48 and 63 on that line)":
            curve("filter_eg_octaves"),
        "filter_kbd_track (cutoff octaves per keyboard octave)": curve("kbd_track_ratio"),
        "lfo1_freq and lfo2_freq (Hz)": curve("lfo1_hz"),
        "portamento (ms for an octave)": curve("portamento_ms_per_octave"),
        "osc2_tune (cents)": curve("osc2_tune_cents"),
        "delay_time (ms, unsynced)": curve("delay_time_ms"),
        "patch_int to pitch from an LFO (semitones, whole swing)": curve("lfo_pitch_semitones"),
        "patch_int to pitch from EG1 (semitones)": curve("eg_pitch_semitones"),
        "not measured": "unison_detune, pulse width, velocity amounts, effect speeds: set, audition, adjust",
    }


# ------------------------------------------------- a design in real units, as parameters
# sound_design.py describes sounds in milliseconds, hertz, cents and octaves. CALIBRATION
# (measured on one microKORG, notes/hardware/calibrate_microkorg.py) says what this synth's
# 0-127 values are in those units; from_design turns a blueprint into parameters with it.

def _value_for(curve: dict[int, float], want: float) -> int:
    """The parameter value whose measured result is nearest `want`, between measured points
    by straight lines (in the logarithm for results that span decades)."""
    points = sorted((v, r) for v, r in curve.items() if r is not None)
    if want <= min(r for _, r in points):
        return min(points, key=lambda p: p[1])[0]
    if want >= max(r for _, r in points):
        return max(points, key=lambda p: p[1])[0]
    logs = all(r > 0 for _, r in points) and max(r for _, r in points) / min(r for _, r in points) > 20
    scale = math.log if logs else (lambda x: x)
    for (v0, r0), (v1, r1) in zip(points, points[1:]):
        if min(r0, r1) <= want <= max(r0, r1) and r0 != r1:
            return int(round(v0 + (v1 - v0) * (scale(want) - scale(r0)) / (scale(r1) - scale(r0))))
    return min(points, key=lambda p: abs(p[1] - want))[0]


def cutoff_for(hz: float) -> int:
    """The cutoff value for a frequency (keyboard tracking off): one step is one semitone."""
    return _value_for(CALIBRATION["cutoff_hz"], max(hz, 1.0))


_WAVE1 = {"saw": "saw", "pulse": "pulse", "square": "pulse", "triangle": "triangle", "sine": "sine", "noise": "noise"}
_WAVE2 = {"saw": "saw", "square": "square", "pulse": "square", "triangle": "triangle", "sine": "triangle"}
_FILTER = {"lp24": "24lpf", "lp12": "12lpf", "bp": "12bpf", "hp": "12hpf"}
_LFO_SHAPES = {1: {"triangle": "triangle", "sine": "triangle", "saw": "saw", "square": "square", "random": "s/h"},
               2: {"sine": "sine", "triangle": "sine", "saw": "saw", "square": "square+", "random": "s/h"}}


def from_design(blueprint: dict) -> dict:
    """A sound_design blueprint as this synth's parameters: {"params": for set_hardware_params
    start_from='init', "approximate": what was set by rule of thumb, not measurement,
    "left_out": what this synth can't do}. The result is a starting point to audition."""
    cal = CALIBRATION
    p: dict[str, Any] = {}
    approximate: list[str] = []
    left_out: list[str] = []
    slots = iter((1, 2, 3, 4))

    def patch(source: str, dest: str, amount: int, what: str) -> None:
        n = next(slots, None)
        if n is None:
            left_out.append(f"{what}: all four modulation patches are in use")
            return
        p[f"patch{n}_source"], p[f"patch{n}_dest"] = source, dest
        p[f"patch{n}_int"] = int(max(-63, min(63, amount)))

    voices = blueprint.get("voices")
    if voices:
        p["assign_mode"] = voices
    if blueprint.get("unison_cents") is not None:
        p["unison_detune"] = int(min(99, round(blueprint["unison_cents"])))
        approximate.append("unison_detune is taken as cents, as Korg labels it (not measured)")
    if blueprint.get("legato") is not None:
        p["trigger_mode"] = "single" if blueprint["legato"] else "multi"
    if blueprint.get("glide_ms"):
        p["portamento"] = _value_for(cal["portamento_ms_per_octave"], blueprint["glide_ms"])

    o1 = blueprint.get("osc1") or {}
    if o1.get("wave"):
        p["osc1_wave"] = _WAVE1[o1["wave"]]
        if o1["wave"] == "square":
            p["osc1_ctrl1"] = 0
    if "level" in o1:
        p["osc1_level"] = int(round(127 * o1["level"]))
    if o1.get("width") is not None and p.get("osc1_wave", "saw") == "pulse":
        p["osc1_ctrl1"] = int(max(0, min(127, round((o1["width"] - 0.5) / 0.5 * 127))))
    if o1.get("pwm"):
        p["osc1_ctrl2"] = int(round(127 * o1["pwm"]))       # how far LFO1 moves the wave shape

    o2 = blueprint.get("osc2") or {}
    if o2:
        if o2.get("wave"):
            p["osc2_wave"] = _WAVE2[o2["wave"]]
            if o2["wave"] == "sine":
                approximate.append("oscillator 2 has no sine: a triangle stands in")
        p["osc2_level"] = int(round(127 * o2.get("level", 1.0)))
        if o2.get("semitones"):
            p["osc2_semitone"] = int(max(-24, min(24, o2["semitones"])))
        if o2.get("cents"):
            cents = abs(o2["cents"])
            p["osc2_tune"] = int(math.copysign(_value_for(cal["osc2_tune_cents"], cents), o2["cents"]))
    if blueprint.get("osc_mod"):
        p["osc2_mod"] = blueprint["osc_mod"]
    if blueprint.get("noise") is not None:
        p["noise_level"] = int(round(127 * blueprint["noise"]))

    f = blueprint.get("filter") or {}
    if f.get("type"):
        p["filter_type"] = _FILTER[f["type"]]
    if f.get("cutoff_hz"):
        p["cutoff"] = cutoff_for(f["cutoff_hz"])
    if f.get("resonance") is not None:
        p["resonance"] = int(round(127 * f["resonance"]))
    if f.get("env_octaves"):
        p["filter_eg_int"] = int(math.copysign(_value_for(cal["filter_eg_octaves"], abs(f["env_octaves"])), f["env_octaves"]))
    if f.get("key_track") is not None:
        p["filter_kbd_track"] = int(round(cal["kbd_track_full"] * f["key_track"]))
    if f.get("velocity"):
        p["filter_velocity"] = int(round(63 * f["velocity"]))
        approximate.append("filter_velocity is scaled 0-63 by rule of thumb")

    for name, eg in (("filter_env", "eg1"), ("amp_env", "eg2")):
        env = blueprint.get(name) or {}
        if "attack_ms" in env:
            p[f"{eg}_attack"] = _value_for(cal["eg_attack_ms"], env["attack_ms"])
        if env.get("decay_ms"):
            p[f"{eg}_decay"] = _value_for(cal["eg_decay_ms"], env["decay_ms"])
        if "sustain" in env:
            p[f"{eg}_sustain"] = int(round(127 * env["sustain"]))
        if "release_ms" in env:
            p[f"{eg}_release"] = _value_for(cal["eg_release_ms"], env["release_ms"])

    for n in (1, 2):
        lfo = blueprint.get(f"lfo{n}") or {}
        if not lfo:
            continue
        if lfo.get("shape"):
            p[f"lfo{n}_wave"] = _LFO_SHAPES[n][lfo["shape"]]
        if lfo.get("sync"):
            p[f"lfo{n}_tempo_sync"], p[f"lfo{n}_division"] = "on", lfo["sync"]
        elif lfo.get("hz"):
            p[f"lfo{n}_freq"] = _value_for(cal[f"lfo{n}_hz"], lfo["hz"])
        if lfo.get("retrigger"):
            p[f"lfo{n}_key_sync"] = "voice"
        to, depth = lfo.get("to"), lfo.get("depth") or 0
        if to == "width":
            if n == 1:
                p["osc1_ctrl2"] = int(round(127 * depth))
            else:
                left_out.append("only LFO1 moves the pulse width on this synth: put the width movement on lfo1")
        elif to == "pitch" and depth:
            patch(f"lfo{n}", "pitch", _value_for(cal["lfo_pitch_semitones"], depth), "LFO to pitch")
        elif to == "cutoff" and depth:
            patch(f"lfo{n}", "cutoff", _value_for(cal["filter_eg_octaves"], depth), "LFO to cutoff")
            approximate.append("LFO-to-cutoff depth uses the filter envelope's measured scale")
        elif to in ("amp", "pan") and depth:
            patch(f"lfo{n}", to, int(round(63 * depth)), f"LFO to {to}")

    pe = blueprint.get("pitch_env") or {}
    if pe.get("semitones"):
        amount = int(math.copysign(_value_for(cal["eg_pitch_semitones"], abs(pe["semitones"])), pe["semitones"]))
        patch("eg1", "osc2 pitch" if pe.get("to") == "osc2" else "pitch", amount, "pitch envelope")
        if pe.get("decay_ms"):
            p["eg1_attack"], p["eg1_sustain"] = 0, 0
            p["eg1_decay"] = p["eg1_release"] = _value_for(cal["eg_decay_ms"], pe["decay_ms"])
            if blueprint.get("filter_env") or f.get("env_octaves"):
                approximate.append("the pitch envelope is EG1, which is also the filter envelope: they share one "
                                   "shape (the pitch envelope's times were used)")
    if blueprint.get("velocity_to_amp"):
        p["amp_velocity"] = int(round(63 * blueprint["velocity_to_amp"]))

    fx = blueprint.get("fx") or {}
    kinds = [k for k in ("chorus", "ensemble", "phaser") if fx.get(k)]
    if kinds:
        p["mod_type"] = {"chorus": "chorus/flanger", "ensemble": "ensemble", "phaser": "phaser"}[kinds[0]]
        p["mod_depth"] = int(round(127 * fx[kinds[0]]))
        if len(kinds) > 1:
            left_out.append(f"one modulation effect at a time: {kinds[0]} kept, {', '.join(kinds[1:])} dropped")
    delay = fx.get("delay") or {}
    if delay:
        p["delay_depth"] = int(round(127 * delay.get("mix", 0.25)))
        if delay.get("sync"):
            p["delay_sync"], p["delay_division"] = "on", delay["sync"]
        elif delay.get("ms"):
            p["delay_time"] = _value_for(cal["delay_time_ms"], delay["ms"])
    if fx.get("distortion"):
        p["distortion"] = "on"
    apply(init_program(), p)     # every name and value is one this synth takes, or this raises
    return {"params": p, "approximate": approximate, "left_out": left_out}
