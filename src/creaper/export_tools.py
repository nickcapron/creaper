"""MCP tools for saving the project and exporting finished audio.

Exports reuse creaper's render path (32-bit float, render settings restored
afterwards), then measure the result and write the format asked for, so every
export comes back with its loudness and true peak checked.
"""

from __future__ import annotations

import math
import os
import re
import time
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import soundfile as sf
from pydantic import Field
from scipy import signal

from . import analysis
from .server import BridgeError, bridge, call, confirm_with_user, tool

Format = Literal["wav", "flac", "mp3", "ogg"]
EXTENSIONS = {"wav": ".wav", "flac": ".flac", "mp3": ".mp3", "ogg": ".ogg"}


def safe_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", name).strip(" .")
    return re.sub(r"\s+", " ", cleaned)[:120] or "creaper export"


def _project_info() -> dict:
    return call("project_paths")


def _default_folder(info: dict) -> Path:
    if info.get("project"):
        return Path(info["project"]).parent / "Exports"
    return Path.home() / "Music" / "creaper exports"


def _stem_name(info: dict) -> str:
    name = info.get("name") or ""
    name = re.sub(r"\.rpp$", "", name, flags=re.IGNORECASE)
    return safe_name(name) if name else time.strftime("creaper export %Y-%m-%d %H%M")


def _check_renders(files: list[str]) -> None:
    renders = (bridge.directory / "renders").resolve()
    for f in files:
        if renders not in Path(f).resolve().parents:
            raise BridgeError(f"refusing to use a render outside {renders}: {f}")


def _cleanup(files: list[str]) -> None:
    if not os.environ.get("CREAPER_KEEP_RENDERS"):
        for f in files:
            Path(f).unlink(missing_ok=True)


OGG_QUALITY = 0.6   # Vorbis quality 0-1; 0.6 is about 150-190 kbps for stereo music
OGG_BLOCK = 8192    # frames per write when encoding Vorbis


def convert(src: str | Path, dest: Path, fmt: Format, bit_depth: int = 24, sample_rate: int | None = None,
            gain_db: float = 0.0, ogg_quality: float = OGG_QUALITY) -> dict:
    """Writes a float render as the delivery format: resampled if asked, gain applied,
    TPDF-dithered when going to 16-bit, clipped samples counted."""
    audio, fs = sf.read(str(src), dtype="float64", always_2d=True)
    if sample_rate and sample_rate != fs:
        g = math.gcd(int(sample_rate), int(fs))
        audio = signal.resample_poly(audio, int(sample_rate) // g, int(fs) // g, axis=0)
        fs = int(sample_rate)
    if gain_db:
        audio *= 10 ** (gain_db / 20)
    clipped = 0
    if fmt in ("wav", "flac") and bit_depth in (16, 24) or fmt in ("mp3", "ogg"):
        if fmt in ("wav", "flac") and bit_depth == 16:
            lsb = 1 / 32768
            rng = np.random.default_rng(0)
            audio = audio + (rng.random(audio.shape) - rng.random(audio.shape)) * lsb
        clipped = int(np.count_nonzero(np.abs(audio) > 1.0))
        audio = np.clip(audio, -1.0, 1.0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "wav":
        subtype = {16: "PCM_16", 24: "PCM_24", 32: "FLOAT"}[bit_depth]
        sf.write(str(dest), audio, fs, subtype=subtype, format="WAV")
    elif fmt == "flac":
        sf.write(str(dest), audio, fs, subtype="PCM_16" if bit_depth == 16 else "PCM_24", format="FLAC")
    elif fmt == "mp3":
        sf.write(str(dest), audio, fs, format="MP3", subtype="MPEG_LAYER_III",
                 bitrate_mode="CONSTANT", compression_level=0.0)
    else:
        # libsndfile's compression level is the inverse of Vorbis quality. Write in blocks:
        # libsndfile crashes the whole process encoding Vorbis from one long write (a
        # 27-second file was enough).
        with sf.SoundFile(str(dest), "w", fs, audio.shape[1], format="OGG", subtype="VORBIS",
                          compression_level=round(1.0 - min(1.0, max(0.0, ogg_quality)), 3)) as out:
            for i in range(0, len(audio), OGG_BLOCK):
                out.write(audio[i:i + OGG_BLOCK])
    return {"sample_rate": fs, "clipped_samples": clipped}


def _destination(folder: str | None, name: str, fmt: Format, info: dict, overwrite: bool) -> Path:
    base = Path(folder) if folder else _default_folder(info)
    dest = base / (safe_name(name) + EXTENSIONS[fmt])
    if dest.exists() and not overwrite:
        confirm_with_user(f"overwrite the existing file {dest}")
    return dest


def _deliver(src: str, dest: Path, fmt: Format, bit_depth: int, sample_rate: int | None,
             target_lufs: float | None, ceiling_db: float, avoid_clipping: bool = True,
             extra_gain: float = 0.0, ogg_quality: float = OGG_QUALITY) -> dict:
    measured = analysis.analyze_file(src)
    loud = measured.get("loudness", {}).get("integrated_lufs")
    peak = measured.get("levels", {}).get("true_peak_dbtp")
    gain, notes = 0.0, []
    if target_lufs is not None and loud is not None:
        gain = target_lufs - loud
        if peak is not None and peak + gain > ceiling_db:
            gain = ceiling_db - peak
            notes.append(f"stopped at {loud + gain:.1f} LUFS to keep true peaks under {ceiling_db} dBTP; "
                         "use master_to_target for a louder master")
    elif avoid_clipping and peak is not None and peak > ceiling_db and not (fmt in ("wav",) and bit_depth == 32):
        # A fixed-point or encoded file can't hold peaks over 0 dBFS: turn it down rather than clip it.
        gain = ceiling_db - peak
        notes.append(f"turned down {-gain:.1f} dB so the file doesn't clip (the mix peaks at {peak:+.1f} dBTP); "
                     "master_to_target makes it loud without clipping")
    gain += extra_gain
    written = convert(src, dest, fmt, bit_depth, sample_rate, gain, ogg_quality)
    out = {"file": str(dest), "format": fmt + (f" {bit_depth}-bit" if fmt in ("wav", "flac") else
                                               f" (Vorbis quality {ogg_quality:g})" if fmt == "ogg" else ""),
           "sample_rate": written["sample_rate"], "duration_s": measured.get("duration_seconds"),
           "integrated_lufs": round(loud + gain, 1) if loud is not None else None,
           "true_peak_dbtp": round(peak + gain, 1) if peak is not None else None,
           "size_mb": round(dest.stat().st_size / 1e6, 2)}
    if gain:
        out["gain_applied_db"] = round(gain, 2)
    if written["clipped_samples"]:
        notes.append(f"{written['clipped_samples']} samples went over 0 dBFS and were clipped: lower the master or "
                     "run master_to_target")
    elif peak is not None and peak + gain > -1.0 and fmt in ("mp3", "ogg"):
        notes.append("true peaks are above -1 dBTP, which can distort once encoded; master_to_target fixes that")
    if measured.get("silent"):
        notes.append("the export is silent: are the tracks muted, or the instruments missing?")
    if notes:
        out["notes"] = notes
    return out


@tool()
def save_project(
    name: Annotated[str | None, Field(description="Save as this name (first save or save-as); default: save in place")] = None,
    folder: Annotated[str | None, Field(description="Folder for a new file; default: REAPER's project folder")] = None,
    copy: Annotated[bool, Field(description="Save a copy (a snapshot) and keep working in the current project")] = False,
    overwrite: Annotated[bool, Field(description="Replace an existing file of that name without asking")] = False,
) -> dict:
    """Saves the project: in place when it already has a file, as a new file the first
    time (or with a new name), or as a snapshot copy before big changes. A first save
    or save-as reopens the saved file in the same tab, so the undo history starts fresh."""
    info = _project_info()
    if not name and not copy:
        if info.get("project"):
            return call("save_project", mode="save")
        raise ValueError("the project hasn't been saved yet: give it a name")
    base = Path(folder) if folder else (Path(info["project"]).parent if info.get("project")
                                         else Path(info.get("default_folder") or Path.home() / "Documents" / "REAPER Projects"))
    stem = safe_name(name) if name else _stem_name(info) + time.strftime(" %Y-%m-%d %H%M")
    if not folder and not info.get("project") and not copy:
        base = base / stem  # a folder per project, as REAPER does
    path = base / (stem + ".rpp")
    if path.exists() and not overwrite and not (info.get("project") and Path(info["project"]) == path):
        confirm_with_user(f"overwrite the existing project file {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    result = call("save_project", timeout=120.0, mode="copy" if copy else "save_as", path=str(path))
    if not copy:
        result["note"] = "Saved and reopened from the new file; the undo history starts fresh from here."
    return result


@tool()
def export_mix(
    name: Annotated[str | None, Field(description="File name without extension; default: the project's name")] = None,
    format: Annotated[Format, Field(description="wav or flac (lossless), mp3 (320 kbps), ogg")] = "wav",
    bit_depth: Annotated[Literal[16, 24, 32], Field(description="WAV/FLAC: 24 for masters, 16 (dithered) for CD")] = 24,
    sample_rate: Annotated[int | None, Field(description="e.g. 44100 or 48000; default: the project's")] = None,
    folder: Annotated[str | None, Field(description="Default: an 'Exports' folder next to the project")] = None,
    start_bar: Annotated[float | None, Field(ge=1)] = None,
    end_bar: Annotated[float | None, Field(description="Default: end of project")] = None,
    region: Annotated[str | None, Field(description="Export just this region (by name), e.g. 'Chorus'")] = None,
    tail_seconds: Annotated[float, Field(ge=0, le=30, description="Extra time after the end for reverb and delay tails")] = 2.0,
    target_lufs: Annotated[float | None, Field(ge=-40, le=-5, description="Turn the file up/down to this loudness (gain only; true peak kept under the ceiling)")] = None,
    ceiling_db: Annotated[float, Field(le=0)] = -1.0,
    avoid_clipping: Annotated[bool, Field(description="Turn the file down instead of clipping when the mix peaks too high")] = True,
    ogg_quality: Annotated[float, Field(ge=0, le=1, description="OGG Vorbis quality, 0 to 1 (0.6 is about 150-190 kbps)")] = OGG_QUALITY,
    overwrite: bool = False,
) -> dict:
    """Exports the finished mix (the master, with its effects) to an audio file and
    reports its loudness and true peak. Use master_to_target first for a release master."""
    info = _project_info()
    if region:
        regions = [m for m in call("get_project_overview").get("regions", []) if m.get("name", "").lower() == region.lower()]
        if not regions:
            raise ValueError(f"there's no region called '{region}'")
        span = {"start_seconds": regions[0]["start"]["seconds"], "end_seconds": regions[0]["end"]["seconds"]}
    else:
        span = {"start_bar": start_bar, "end_bar": end_bar}
    stem = name or (_stem_name(info) + (f" - {region}" if region else ""))
    dest = _destination(folder, stem, format, info, overwrite)
    render = call("render_audio", timeout=900.0, track="master", tail_seconds=tail_seconds, **span)
    _check_renders(render["files"])
    try:
        out = _deliver(render["files"][0], dest, format, bit_depth, sample_rate, target_lufs, ceiling_db, avoid_clipping,
                       ogg_quality=ogg_quality)
    finally:
        _cleanup(render["files"])
    if render.get("warning"):
        out.setdefault("notes", []).append(render["warning"])
    return out


@tool()
def export_stems(
    tracks: Annotated[list[str | int] | None, Field(description="Tracks to export; default: every track with items")] = None,
    format: Format = "wav",
    bit_depth: Literal[16, 24, 32] = 24,
    sample_rate: int | None = None,
    folder: Annotated[str | None, Field(description="Default: 'Exports/<project> stems' next to the project")] = None,
    start_bar: Annotated[float | None, Field(ge=1)] = None,
    end_bar: float | None = None,
    tail_seconds: Annotated[float, Field(ge=0, le=30)] = 2.0,
    ogg_quality: Annotated[float, Field(ge=0, le=1, description="OGG Vorbis quality, 0 to 1 (0.6 is about 150-190 kbps)")] = OGG_QUALITY,
    overwrite: bool = False,
) -> dict:
    """Exports each track as its own audio file (post-fader, with its effects but not the
    master's), all the same length so they line up from the same start: for mixing
    elsewhere, remixes, or sharing parts."""
    info = _project_info()
    overview = call("get_project_overview")
    chosen = tracks or [t["number"] for t in overview["tracks"] if t.get("item_count", 0) > 0]
    if not chosen:
        raise ValueError("no tracks with items to export")
    base = Path(folder) if folder else _default_folder(info) / f"{_stem_name(info)} stems"
    existing = [p for p in base.glob("*") if p.suffix.lower() == EXTENSIONS[format]] if base.exists() else []
    if existing and not overwrite:
        confirm_with_user(f"overwrite stems in {base}")
    render = call("render_stems", timeout=900.0, tracks=chosen, start_bar=start_bar, end_bar=end_bar,
                  tail_seconds=tail_seconds)
    _check_renders(render["files"])
    results = []
    try:
        # One shared gain for all stems if any would clip, so their balance stays exact.
        shared = 0.0
        if not (format == "wav" and bit_depth == 32):
            peaks = [analysis.analyze_file(st["file"]).get("levels", {}).get("true_peak_dbtp") for st in render["stems"]]
            worst = max((p for p in peaks if p is not None), default=None)
            if worst is not None and worst > -0.3:
                shared = -0.3 - worst
        for i, stem in enumerate(render["stems"], start=1):
            label = f"{stem['track']['number']:02d} {safe_name(stem['track']['name'])}"
            dest = base / (label + EXTENSIONS[format])
            r = _deliver(stem["file"], dest, format, bit_depth, sample_rate, None, 0.0, avoid_clipping=False,
                         extra_gain=shared, ogg_quality=ogg_quality)
            results.append({"track": stem["track"]["name"], "file": r["file"], "true_peak_dbtp": r["true_peak_dbtp"],
                            **({"notes": r["notes"]} if r.get("notes") else {})})
    finally:
        _cleanup(render["files"])
    out = {"folder": str(base), "stems": results}
    if shared:
        out["gain_applied_db"] = round(shared, 2)
        out["note_on_level"] = (f"all stems turned down {-shared:.1f} dB together so none clips; "
                                "their balance is unchanged")
    if len(results) < len(chosen):
        out["note"] = f"{len(chosen) - len(results)} track(s) produced no file (silent or muted?)"
    return out


@tool()
def reveal_exports(folder: Annotated[str | None, Field(description="Default: the project's Exports folder")] = None) -> dict:
    """Lists the exported files in the export folder (newest first)."""
    info = _project_info()
    base = Path(folder) if folder else _default_folder(info)
    if not base.exists():
        return {"folder": str(base), "files": []}
    files = sorted((p for p in base.rglob("*") if p.suffix.lower() in EXTENSIONS.values()),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    return {"folder": str(base), "files": [{"file": str(p), "size_mb": round(p.stat().st_size / 1e6, 2),
                                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))}
                                           for p in files[:50]]}

