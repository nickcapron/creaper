"""Sound effects for games and apps: every region of a project becomes its own file,
named after the region (shot_01, shot_02 ...), in one render pass. One-shots come out
mono by default, trimmed so the sound starts within a millisecond of the file start,
DC-free and peak-normalised; loops (crowd beds, room tones, engine hums) are made
seamless by crossfading the sound that follows the region into its start."""

from __future__ import annotations

import fnmatch
import math
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import soundfile as sf
from pydantic import Field
from scipy import signal

from . import export_tools  # the module, not its names: it may still be loading (circular import)
from .server import call, confirm_with_user, tool

HEAD_FLOOR_DB = -50.0      # below the peak: where a sound "starts"
PREROLL_MS = 1.0           # kept before the start, faded in so it can't click
TAIL_FLOOR_DB = -80.0      # below the peak: a tail this quiet has died away
CUT_TAIL_DB = -50.0        # a region ending louder than this (re peak) cuts the sound off


def to_channels(audio: np.ndarray, channels: Literal["mono", "stereo"]) -> np.ndarray:
    a = np.asarray(audio, dtype=float)
    if a.ndim == 1:
        a = a[:, None]
    if channels == "mono":
        return a.mean(axis=1, keepdims=True)
    return a if a.shape[1] >= 2 else np.repeat(a, 2, axis=1)


DC_HIGHPASS_HZ = 15.0
SILENCE_DBFS = -96.0       # the floor of 24-bit audio: anything quieter counts as silence


def remove_dc(audio: np.ndarray, fs: int = 44100) -> np.ndarray:
    """Removes DC, including an offset that only lingers at the end (a low sine's
    residue): subtracting the average missed that and kept a near-silent tail. A
    gentle high-pass under the audible range does it; a causal one, since a zero-phase
    filter smears energy before the transient and spoils the head trim."""
    a = audio - audio.mean(axis=0, keepdims=True)
    if len(a) < int(0.1 * fs):
        return a
    sos = signal.butter(2, DC_HIGHPASS_HZ, btype="highpass", fs=fs, output="sos")
    return signal.sosfilt(sos, a, axis=0)


def _level_db(audio: np.ndarray) -> np.ndarray:
    return 20 * np.log10(np.abs(audio).max(axis=1) + 1e-12)


def trim_head(audio: np.ndarray, fs: int, floor_db: float = HEAD_FLOOR_DB, preroll_ms: float = PREROLL_MS) -> tuple[np.ndarray, float]:
    """Cuts the silence before the sound so it starts within `preroll_ms` of the file
    start (fading that sliver in). Returns the audio and how much was cut (ms)."""
    level = _level_db(audio)
    loud = np.nonzero(level > level.max() + floor_db)[0]
    if not len(loud):
        return audio, 0.0
    start = max(0, int(loud[0] - preroll_ms / 1000 * fs))
    out = audio[start:].copy()
    ramp = int(loud[0] - start)
    if ramp > 1:
        out[:ramp] *= np.linspace(0, 1, ramp)[:, None]
    return out, start / fs * 1000


def tail_state(audio: np.ndarray) -> dict:
    """Whether the sound has died away by the end (its last 10 ms well under the peak)."""
    level = _level_db(audio)
    end = level[-max(1, len(level) // 100):].max()
    below = round(float(level.max() - end), 1)
    return {"end_db_below_peak": below, "cut_off": below < -CUT_TAIL_DB}


def trim_tail(audio: np.ndarray, floor_db: float = TAIL_FLOOR_DB) -> np.ndarray:
    """Drops the silence after the sound has died away: everything after the last
    moment above floor_db (re its peak) or above -96 dBFS, whichever is higher. A
    generator fading to "-100 dB" instead of true silence used to keep its tail."""
    level = _level_db(audio)
    floor = max(level.max() + floor_db, SILENCE_DBFS)
    loud = np.nonzero(level > floor)[0]
    return audio[: loud[-1] + 1] if len(loud) else audio


def normalize_peak(audio: np.ndarray, peak_db: float) -> tuple[np.ndarray, float]:
    peak = float(np.abs(audio).max())
    if peak <= 0:
        return audio, 0.0
    gain = 10 ** (peak_db / 20) / peak
    return audio * gain, 20 * math.log10(gain)


def make_loop(audio: np.ndarray, length: int, crossfade: int) -> np.ndarray:
    """A seamless loop `length` samples long from audio that runs `crossfade` samples
    past it: the sound after the loop point is faded into the loop's start (equal
    power), so the end flows straight back into the beginning with no fade or gap."""
    if len(audio) < length + crossfade:
        raise ValueError("the render is too short to crossfade the loop")
    loop = audio[:length].copy()
    t = np.linspace(0, np.pi / 2, crossfade)[:, None]
    loop[:crossfade] = audio[:crossfade] * np.sin(t) + audio[length:length + crossfade] * np.cos(t)
    return loop


def loop_seam_db(loop: np.ndarray) -> float:
    """The jump from the loop's last sample to its first, against the sound's typical
    sample-to-sample step (dB): about 0 or below is a natural continuation; a cut
    stands well above it (+10 dB and up is a click)."""
    jump = float(np.abs(loop[0] - loop[-1]).max())
    step = float(np.sqrt(np.mean(np.diff(loop, axis=0) ** 2))) + 1e-12
    return round(20 * math.log10(jump / step + 1e-12), 1)


def _matches(name: str, patterns: list[str] | None) -> bool:
    return any(fnmatch.fnmatch(name.lower(), p.lower()) for p in patterns or [])


@tool()
def export_regions(
    folder: Annotated[str, Field(description="Where the files go, e.g. a game's assets/audio/sfx folder")],
    regions: Annotated[list[str] | None, Field(description="Region names to export; default: every region")] = None,
    stereo: Annotated[list[str] | None, Field(description=(
        "Regions to keep stereo, by name or pattern ('crowd_*', 'organ_*', '*_room'); everything else is mono"))] = None,
    loops: Annotated[list[str] | None, Field(description=(
        "Regions that loop (by name or pattern, e.g. 'crowd_bed*', 'skate_stride'): made seamless by crossfading "
        "what follows the region into its start, so leave the sound running a little past the region's end"))] = None,
    peak_db: Annotated[float | None, Field(le=0, description="Peak level for one-shots (loops keep their level)")] = -1.0,
    sample_rate: Annotated[int, Field(description="e.g. 44100 or 48000")] = 44100,
    bit_depth: Annotated[Literal[16, 24, 32], Field(description="24 for game audio")] = 24,
    loop_crossfade_s: Annotated[float, Field(gt=0, le=5, description="Length of the loop seam's crossfade")] = 1.0,
    overwrite: bool = False,
) -> dict:
    """Exports each region of the project as its own file named after the region (for
    sound effects and their variations: shot_01, shot_02 ...), in one render pass.
    One-shots: mono unless listed in `stereo`, DC removed, the silence before the sound
    cut so it starts within a millisecond of the file start, trailing silence dropped,
    peak set to peak_db, and a warning when the region cuts the sound off before it
    dies away. Loops: seamless (crossfaded seam, no fade at either end), their length
    reported. 16-bit files are dithered; 24-bit aren't. Put each sound in its own region
    with a little room after it (for its tail), then call this once."""
    overview = call("get_project_overview")
    all_regions = overview.get("regions", [])
    chosen = [r for r in all_regions if not regions or any(r["name"].lower() == n.lower() for n in regions)]
    if not chosen:
        names = ", ".join(r["name"] for r in all_regions) or "none"
        raise ValueError(f"no regions to export (regions in the project: {names})")
    missing = [n for n in regions or [] if not any(r["name"].lower() == n.lower() for r in all_regions)]
    out_dir = export_tools.check_folder(folder, call("project_paths"))
    targets = [(r, out_dir / f"{export_tools.safe_name(r['name'])}.wav") for r in chosen]
    by_file: dict[str, list[str]] = {}
    for r, dest in targets:
        by_file.setdefault(dest.name.lower(), []).append(r["name"])
    clashes = [names for names in by_file.values() if len(names) > 1]
    if clashes:  # one file would silently overwrite the other
        raise ValueError("these regions would be saved to the same file; rename one of each: "
                         + "; ".join(" / ".join(f"'{n}'" for n in names) for names in clashes))
    existing = [p.name for _, p in targets if p.exists()]
    if existing:   # always asked in the chat panel; overwrite only says replacing is wanted
        confirm_with_user(f"replace {len(existing)} existing file(s) in {out_dir} (e.g. {existing[0]})")
    start = min(r["start"]["seconds"] for r in chosen)
    end = max(r["end"]["seconds"] for r in chosen)
    extra = loop_crossfade_s + 0.5 if any(_matches(r["name"], loops) for r in chosen) else 0.5
    render = call("render_audio", timeout=900.0, track="master", start_seconds=start, end_seconds=end,
                  tail_seconds=extra)
    export_tools._check_renders(render["files"])
    try:
        audio, fs = sf.read(render["files"][0], dtype="float64", always_2d=True)
    finally:
        export_tools._cleanup(render["files"])
    if fs != sample_rate:
        g = math.gcd(int(fs), int(sample_rate))
        audio = signal.resample_poly(audio, sample_rate // g, fs // g, axis=0)
        fs = sample_rate
    out_dir.mkdir(parents=True, exist_ok=True)
    subtype = {16: "PCM_16", 24: "PCM_24", 32: "FLOAT"}[bit_depth]
    files, problems = [], []
    for region, dest in targets:
        a = int(round((region["start"]["seconds"] - start) * fs))
        b = int(round((region["end"]["seconds"] - start) * fs))
        is_loop = _matches(region["name"], loops)
        channels = "stereo" if _matches(region["name"], stereo) else "mono"
        entry: dict = {"file": dest.name, "channels": channels}
        if is_loop:
            xf = int(loop_crossfade_s * fs)
            part = remove_dc(to_channels(audio[a:b + xf], channels), fs)
            if b - a <= xf * 2:
                problems.append(f"{region['name']}: too short to loop with a {loop_crossfade_s:g} s crossfade")
                continue
            sound = make_loop(part, b - a, xf)
            peak = float(np.abs(sound).max())
            if peak > 10 ** (-1 / 20):
                sound = sound * (10 ** (-1 / 20) / peak)
                entry["turned_down"] = True
            entry.update(loop=True, loop_length_s=round(len(sound) / fs, 3), loop_samples=len(sound),
                         seam_db=loop_seam_db(sound))
        else:
            part = remove_dc(to_channels(audio[a:b], channels), fs)
            if not np.any(np.abs(part) > 1e-6):
                problems.append(f"{region['name']}: silent")
                continue
            tail = tail_state(part)
            sound, cut_ms = trim_head(part, fs)
            sound = trim_tail(sound)
            if peak_db is not None:
                sound, gain = normalize_peak(sound, peak_db)
                entry["gain_db"] = round(gain, 1)
            entry.update(length_s=round(len(sound) / fs, 3), head_trimmed_ms=round(cut_ms, 1))
            if tail["cut_off"]:
                entry["tail_cut_off"] = True
                problems.append(f"{region['name']}: the region ends while the sound is still {tail['end_db_below_peak']:g} "
                                "dB under its peak: lengthen the region so the tail can die away")
        if bit_depth == 16:
            lsb = 1 / 32768
            rng = np.random.default_rng(0)
            sound = sound + (rng.random(sound.shape) - rng.random(sound.shape)) * lsb
        clipped = int(np.count_nonzero(np.abs(sound) > 1.0))
        sf.write(str(dest), np.clip(sound, -1.0, 1.0), fs, subtype=subtype, format="WAV")
        entry["peak_dbfs"] = round(20 * math.log10(float(np.abs(sound).max()) + 1e-12), 2)
        if clipped:
            problems.append(f"{region['name']}: {clipped} samples clipped")
        files.append(entry)
    result: dict = {"folder": str(out_dir), "exported": len(files), "files": files,
                    "format": f"WAV {bit_depth}-bit {fs} Hz"}
    if problems:
        result["problems"] = problems
    if missing:
        result["not_found"] = missing
    return result
