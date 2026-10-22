"""How specific plugins work, so creaper can set them up instead of guessing from
parameter names.

A compressor's profile names its "drive": the control that sets how hard it works,
and which way. Threshold-style compressors compress more as the threshold goes
down; input-style ones (FET and opto designs) compress more as the input goes up.
Calibration measures the peak-to-loudness ratio, which compression lowers whatever
the output level is, so plugins that link output to input (keeping the level
constant) can stay that way.

Profiles were read from the plugins themselves (parameter names and ranges as
REAPER reports them). Values are in each plugin's displayed units.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Profile:
    name: str                         # matched against the FX name
    role: str                         # "compressor", "bus processor", "eq", "preamp", "instrument"
    summary: str
    setup: tuple[dict, ...] = ()      # changes that make it behave as a plain processor
    drive: str | None = None          # control that sets how hard a compressor works
    drive_more: str = "down"          # "down": lower = more (threshold); "up": higher = more (input)
    drive_range: tuple[float, float] | None = None
    glue: tuple[dict, ...] = ()       # gentle mix-bus settings, before calibrating the drive
    controls: dict[str, str] = field(default_factory=dict)  # role -> parameter name


def _set(parameter: str, **value: Any) -> dict:
    return {"parameter": parameter, **value}


PROFILES: tuple[Profile, ...] = (
    Profile(
        "Bus FORCE", "bus processor",
        "Mix-bus strip with three parallel paths (dry, compressor, saturation) after a filter and EQ, "
        "then an output clipper. By default only the saturation path is open (clean at zero drive), so "
        "its compressor does nothing until the compressor path is opened.",
        setup=(_set("Comp On/Off", display_text="On"), _set("Comp Path Mute", display_text="Off"),
               _set("Comp Path Level", display_value=0), _set("Sat Path Mute", display_text="On"),
               _set("Dry Path Mute", display_text="On"), _set("Comp Make Up gain", display_value=0)),
        drive="Comp Threshold", drive_more="down", drive_range=(-50, 0),
        glue=(_set("Comp Attack", display_value=30), _set("Comp Release", display_value=150),
              _set("Comp Force", display_value=4), _set("Comp Threshold", display_value=-10)),
        controls={"threshold": "Comp Threshold", "attack": "Comp Attack", "release": "Comp Release",
                  "amount": "Comp Force", "makeup": "Comp Make Up gain", "low shelf": "Low Shelf Gain",
                  "presence": "Presence Gain", "high shelf": "High Shelf Gain", "high-pass": "High Pass Freq",
                  "low-pass": "Low Pass Freq", "saturation": "Overdrive Gain", "harmonics": "Harmonics",
                  "clipper": "Output Clipping On/Off", "clip threshold": "Output Clipping Threshold",
                  "input": "Input Trim", "output": "Output Trim", "dry level": "Dry Path Level",
                  "comp level": "Comp Path Level", "sat level": "Sat Path Level"},
    ),
    Profile(
        "Comp VCA-65", "compressor",
        "VCA compressor in the style of the dbx 165: threshold and compression amount, normalized "
        "attack/release, a limit level, output gain and mix.",
        drive="Threshold", drive_more="down", drive_range=(-40, 20),
        glue=(_set("Compression", value=0.5), _set("Attack Time", value=0.5), _set("Release Time", value=0.5),
              _set("Output Gain", display_value=0), _set("Threshold", display_value=0)),
        controls={"threshold": "Threshold", "amount": "Compression", "attack": "Attack Time",
                  "release": "Release Time", "limit": "Limit Level", "output": "Output Gain", "mix": "Mix"},
    ),
    Profile(
        "Comp FET-76", "compressor",
        "FET compressor in the style of the 1176: more input gain means more compression; ratio 4 to "
        "'All' (all buttons); attack and release 1-7 (7 = fastest); input/output link keeps the level.",
        setup=(_set("Input/Output Link", display_text="On"),),
        drive="Input Gain", drive_more="up", drive_range=(-48, 0),
        glue=(_set("Ratio", display_text="4"), _set("Attack", display_value=3), _set("Release", display_value=5),
              _set("Input Gain", display_value=-24)),
        controls={"input": "Input Gain", "ratio": "Ratio", "attack": "Attack", "release": "Release",
                  "output": "Output Gain", "mix": "Mix", "link": "Input/Output Link"},
    ),
    Profile(
        "Comp TUBE-STA", "compressor",
        "Tube/opto compressor: more input gain means more compression, with recovery (release) modes; "
        "input/output link keeps the level.",
        setup=(_set("Input/Output Link", display_text="On"),),
        drive="Input Gain", drive_more="up", drive_range=(0, 48),
        glue=(_set("Input Gain", display_value=12),),
        controls={"input": "Input Gain", "recovery": "Recovery Time", "recovery mode": "Recovery Mode",
                  "output": "Output Gain", "mix": "Mix", "link": "Input/Output Link"},
    ),
    Profile(
        "Stereo Width", "width",
        "REAPER's JS stereo width (Stillwell): Width Boost raises or lowers the side signal against the "
        "middle in dB; -20 is close to mono (for basses and kicks whose low end has spread), +3 to +6 "
        "widens a pad or keys. Center Boost does the same for the middle.",
        controls={"width": "Width Boost (dB)", "center": "Center Boost (dB)", "gain": "Gain (dB)",
                  "balance": "Width Balance (%)"},
    ),
    Profile(
        "Soft Clipper/Limiter", "clipper",
        "REAPER's JS soft clipper: Boost drives the signal into a soft knee at 0 dBFS that rounds the "
        "peaks over it; Output Brickwall caps the result. Turn the track down by the boost to keep its "
        "loudness: only the peaks change.",
        controls={"drive": "Boost (dB)", "ceiling": "Output Brickwall (dB)"},
    ),
    Profile(
        "EQ SITRAL-295", "eq",
        "Broadcast-style EQ with two channels (L/R, or Mid/Side via M/S Mode): high-pass, low shelf "
        "(50-300 Hz), bell (normalized frequency), high shelf (5-30 kHz) and low-pass per channel. "
        "Set Ch.1 and Ch.2 alike for stereo; with M/S Mode, Ch.1 is the mid and Ch.2 the side.",
        controls={"mode": "M/S Mode", "low shelf freq": "Ch.1: LowShelf Freq", "low shelf": "Ch.1: LowShelf Gain",
                  "bell freq (0-1)": "Ch.1: Bell Freq", "bell": "Ch.1: Bell Gain",
                  "high shelf freq": "Ch.1: HighShelf Freq", "high shelf": "Ch.1: HighShelf Gain",
                  "output": "Ch.1: Output Trim", "auto gain": "Auto Gain"},
    ),
    Profile(
        "Pre 1973", "preamp",
        "Neve-style preamp and EQ for color: input gain drives the transformer; high shelf, presence "
        "and low shelf per channel.",
        controls={"input": "Ch.1: Input Gain", "high shelf": "Ch.1: HighShelf Gain",
                  "presence": "Ch.1: Presence Gain", "low shelf": "Ch.1: LowShelf Gain", "output": "Ch.1: Output Trim"},
    ),
    Profile(
        "Pre TridA", "preamp",
        "Trident-style preamp and EQ: high shelf, two bells, low shelf, and switchable low/high-pass "
        "filters per channel.",
        controls={"input": "Ch.1: Input Gain", "high shelf": "Ch.1: HighShelf Gain", "bell 1": "Ch.1: Bell 1 Gain",
                  "bell 2": "Ch.1: Bell 2 Gain", "low shelf": "Ch.1: LowShelf Gain", "output": "Ch.1: Output Trim"},
    ),
    Profile(
        "Pre V76", "preamp",
        "Telefunken V76-style tube preamp: input gain for warmth, a high-pass and low/high tone controls.",
        controls={"input": "Ch.1: Input Gain", "low": "Ch.1: Eq Low Tone Gain", "high": "Ch.1: Eq High Tone Gain",
                  "output": "Ch.1: Output Trim"},
    ),
    Profile(
        "ReaComp", "compressor",
        "REAPER's compressor: threshold, ratio, attack, release, knee, RMS size, wet/dry.",
        drive="Threshold", drive_more="down", drive_range=(-60, 0),
        glue=(_set("Ratio", display_value=2), _set("Attack", display_value=30), _set("Release", display_value=150)),
        controls={"threshold": "Threshold", "ratio": "Ratio", "attack": "Attack", "release": "Release",
                  "knee": "Knee", "wet": "Wet", "dry": "Dry"},
    ),
    Profile(
        "Piano V", "instrument",
        "Arturia's physically modelled acoustic piano (grands and uprights). It makes a real piano, not "
        "the sampled, compressed house piano of a Korg M1 or an electric piano: for those, use a sampled "
        "or preset-based instrument. Hammer Hardness and Brightness near their maximum, plus its EQ's "
        "presence and high-shelf boosts, make it harsh and cheap; small moves from the default are "
        "usually enough. Other piano models are picked in its own preset browser. Its default patch is "
        "nearly out of phase on low chords (stereo correlation around -0.16: hollow, vanishes in mono), and "
        "its Stereo Width control doesn't fix it; a stereo-width effect after it (JS: Stereo Width, width "
        "-12 dB, center +4 dB) brought it to +0.5.",
        controls={"hardness": "Hammer Hardness", "brightness": "Brightness", "low shelf": "Low Shelf Gain",
                  "presence": "Presence Gain", "high shelf": "High Shelf Gain", "width": "Stereo Width",
                  "reverb": "Reverb Dry/Wet"},
    ),
    Profile(
        "ReaSynth", "instrument",
        "REAPER's simple synth (square, saw, triangle and sine mix, ADSR). It plays notes shorter than about "
        "25 ms as nothing, so for clicks and ticks use 25 ms or longer notes and shape them with Decay and "
        "Sustain -inf. Its default is a pure sine: add Saw or Square mix for anything that needs harmonics.",
        controls={"attack": "Attack", "decay": "Decay", "sustain": "Sustain", "release": "Release",
                  "saw": "Saw mix", "square": "Square mix", "triangle": "Triangle mix", "volume": "Volume"},
    ),
    Profile(
        "Rev INTENSITY", "reverb",
        "Arturia's algorithmic reverb. Its tail length follows Size, not Decay: Decay is a small bipolar "
        "offset (display = value - 0.5) that barely shortens it, while Size 0.85 rang for 6+ seconds with "
        "tonal lines. For about a 2 s arena tail: Size 0.5, Decay 0.3, Damping 0.55, Post Filter 6 kHz, "
        "Modulation on (it smears ringing). On a return track set Dry/Wet Balance to 1; Function Destination "
        "1/2 amounts start slightly off centre, so set them to 0.5 for no effect.",
        controls={"size": "Size", "decay": "Decay", "damping": "Damping", "mix": "Dry/Wet Balance"},
    ),
    Profile(
        "Augmented VOICES", "instrument",
        "Arturia's sampled-voice and choir instrument (sampler layers plus synth layers). Its default patch "
        "sounds like a low rumble: the sampler layers have Sustain 0 and the synth layers 5-second attacks. "
        "For a sustained wordless choir: bypass Synth 1 and 2, set Sampler 1/2 Sustain to 1, attack about "
        "0.1 s, release about 3 s; then it plays in tune. The sample itself is chosen in its own browser, not "
        "by a parameter, and velocity does nothing by default (use volume automation for dynamics).",
        controls={},
    ),
    Profile(
        "Synclavier V", "instrument",
        "Arturia's Synclavier (additive/FM with sampled partials). Its default timbre is about 18-20 cents "
        "sharp (FM Ratio Fine 1 = +0.019, Partial File Tuning 2 = -17 cents, some Timbre Modulation) with "
        "2.4 s release tails. For an in-tune clean sound: FM Ratio (Fine) 1-3 to 0, Partial File Tuning 2 to "
        "0, Timbre Modulation 0, then check_tuning. Its factory sample folder (ProgramData/Arturia/Samples/"
        "Synclavier V/Factory) has real brass (tuba, trombones, French horn, trumpets) for "
        "build_sampled_instrument.",
        controls={},
    ),
    Profile(
        "VocalVST", "instrument",
        "The user's own singing plugin (a DiffSinger voice, Canary: clean English singing). It isn't a live "
        "instrument: it records the notes that pass through it while the transport plays, with their timeline "
        "positions, and sings them only after an offline render, so audition_instrument and scan_plugins hear "
        "silence. render_vocalvst(track, lyrics, mode) does the whole order: lyrics into its state (one syllable "
        "per note; its window takes them too), Mode, a transport pass over every note on the track (an item is "
        "lengthened first when its notes run past its end), Render, and waits for the result (its log is "
        "%APPDATA%\\VocalVST\\host.log). Then the vocal plays in sync with the transport and in "
        "offline renders (analyze_audio, export_mix). Modes: Sing holds notes with vibrato; Rap cuts every "
        "syllable to about 220 ms; Scat sings nonsense syllables when there are no lyrics. Monophonic: overlapping "
        "notes are cut, chords keep the top note. The capture is by position, so moved or rewritten notes need "
        "another render_vocalvst; so does a reopened project (the capture is saved, the rendered audio isn't). "
        "A clean voice: growls, shrieks or robot tones come from distortion and effects after it.",
        controls={"mode": "Mode", "gain": "Gain", "render": "Render"},
    ),
    Profile(
        "Filter MINI", "filter",
        "Arturia's Minimoog ladder filter as an effect. Its Cutoff is 0-1 and very steep at the bottom: on "
        "a part around C5-A5, about 0.5 barely changes anything, about 0.33 dulls it 2-6 dB, and 0.25 "
        "silences it. Its default Output Volume (0.37) takes about 4 dB off; make it up with the fader. "
        "Automate Cutoff for sweeps rather than leaving it low.",
        controls={"cutoff": "Cutoff", "resonance": "Resonance", "output": "Output Volume"},
    ),
)


def find_profile(fx_name: str | None) -> Profile | None:
    """The profile whose name appears in an FX name ('VST3: Bus FORCE (Arturia)')."""
    if not fx_name:
        return None
    name = fx_name.lower()
    matches = [p for p in PROFILES if p.name.lower() in name]
    return max(matches, key=lambda p: len(p.name)) if matches else None


def describe(profile: Profile) -> dict:
    out: dict[str, Any] = {"plugin": profile.name, "role": profile.role, "how_it_works": profile.summary,
                           "key_controls": profile.controls}
    if profile.drive:
        out["drive"] = {"control": profile.drive,
                        "more_compression": "lower values" if profile.drive_more == "down" else "higher values"}
    if profile.setup:
        out["setup_for_plain_use"] = list(profile.setup)
    return out


def next_drive(current: float, gain_reduction: float, target: float, profile: Profile, scale: float = 1.0) -> float:
    """One calibration step: move the drive by about the missing reduction, times
    `scale` (grown by the caller while the compressor hasn't started working yet)."""
    missing = target - gain_reduction
    span = (profile.drive_range[1] - profile.drive_range[0]) if profile.drive_range else 60
    # The drive has to move further than the reduction it buys (ratio > 1); at
    # least 2% of its range, so tiny misses still make progress.
    step = math.copysign(max(abs(3.0 * missing), 0.02 * span), missing) * scale
    value = current - step if profile.drive_more == "down" else current + step
    lo, hi = profile.drive_range or (-60, 60)
    return max(lo, min(hi, value))
