"""MCP tools that test plugins to learn what they actually do, and the catalog of results.

Each test loads the plugin on a hidden temporary track after the end of the project,
renders it offline and deletes the track again (one undo step that changes nothing).
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
import soundfile as sf
from pydantic import Field

from . import listen, pluginscan, theory
from .server import READ_ONLY, BridgeError, bridge, call, plugin_catalog, tool

# Instrument test: one note per octave (pitch tracking, range, envelope, tone), then
# a row of drum keys 36-51 (C2-D#3, the General MIDI kit) on channel 10. Everything
# starts after a lead-in, so plugins that finish loading late still get measured.
LEAD_IN = 1.0
OCTAVES = [24 + 12 * i for i in range(7)]
DRUM_KEYS = list(range(36, 52))
NOTE_S, NOTE_SLOT = 1.0, 2.0
HIT_S, HIT_SLOT = 0.25, 0.8


def _instrument_notes() -> tuple[list[dict], float]:
    notes = [{"pitch": p, "start": LEAD_IN + i * NOTE_SLOT, "length": NOTE_S, "velocity": 100, "channel": 1}
             for i, p in enumerate(OCTAVES)]
    offset = LEAD_IN + len(OCTAVES) * NOTE_SLOT
    notes += [{"pitch": p, "start": offset + i * HIT_SLOT, "length": HIT_S, "velocity": 110, "channel": 10}
              for i, p in enumerate(DRUM_KEYS)]
    return notes, offset + len(DRUM_KEYS) * HIT_SLOT + 1.0


def _test_file(fs: int) -> Path:
    path = bridge.directory / "probe" / f"test_signal_v{pluginscan.SIGNAL_VERSION}_{fs}.wav"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(path), pluginscan.test_signal(fs).astype(np.float32), fs, subtype="FLOAT")
    return path


def _read(files: list[str]) -> tuple[np.ndarray, int]:
    renders = (bridge.directory / "renders").resolve()
    for f in files:
        if renders not in Path(f).resolve().parents:
            raise BridgeError(f"refusing to use a render outside {renders}: {f}")
    try:
        audio, fs = sf.read(files[0], dtype="float32", always_2d=True)
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in files:
                Path(f).unlink(missing_ok=True)
    return audio, int(fs)


def test_plugin(plugin: dict, sample_rate: int) -> dict:
    """Tests one plugin (an entry from list_installed_fx) and returns its catalog entry."""
    kind = plugin["kind"]
    name = plugin["load_as"]
    if kind == "instrument":
        notes, length = _instrument_notes()
        info = call("probe_plugin", timeout=240.0, name=name, kind="instrument", notes=notes, length=length)
    else:
        info = call("probe_plugin", timeout=240.0, name=name, kind="effect", offset=LEAD_IN,
                    audio_file=str(_test_file(sample_rate)), length=LEAD_IN + pluginscan.LENGTH)
    audio, fs = _read(info["files"])
    audio = audio[int(LEAD_IN * fs):]
    if kind == "instrument":
        mono = audio.mean(axis=1)
        pitched, kit = [], []
        for i, p in enumerate(OCTAVES):
            seg = mono[int(i * NOTE_SLOT * fs): int((i + 1) * NOTE_SLOT * fs)]
            f = listen.features(seg, fs, note_off=NOTE_S, expected_hz=listen.note_freq(p))
            f.update({"pitch": p, "note": theory.midi_to_note(p)})
            pitched.append(f)
        offset = len(OCTAVES) * NOTE_SLOT  # after the lead-in, which was cut off above
        for i, p in enumerate(DRUM_KEYS):
            a = int((offset + i * HIT_SLOT) * fs)
            f = listen.features(mono[a: a + int(HIT_SLOT * fs)], fs, expected_hz=listen.note_freq(p))
            f.update({"pitch": p, "note": theory.midi_to_note(p)})
            kit.append(f)
        result = pluginscan.analyze_instrument(pitched, kit)
    else:
        dry = pluginscan.test_signal(fs)
        wet = audio[: len(dry)]
        if len(wet) < len(dry):
            wet = np.concatenate([wet, np.zeros((len(dry) - len(wet), wet.shape[1]), dtype=wet.dtype)])
        result = pluginscan.analyze_effect(dry, wet, fs)
    entry = {"kind": kind, "name": plugin.get("name"), "developer": plugin.get("developer"),
             "category": plugin.get("category"), **result}
    reported = info.get("reported_latency_samples")
    if reported:
        entry["reported_latency_ms"] = round(1000 * reported / fs, 1)
    entry["parameters"] = info.get("parameters")
    return entry


@tool()
def scan_plugins(
    kind: Annotated[Literal["all", "instrument", "effect"], Field(description="Which plugins to test")] = "all",
    search: Annotated[str | None, Field(description="Only plugins matching these words, e.g. 'reverb', 'arturia', 'drum'")] = None,
    names: Annotated[list[str] | None, Field(description="Exact plugins to test (names from list_installed_fx)")] = None,
    refresh: Annotated[bool, Field(description="Test again even if already in the catalog")] = False,
    include_js: Annotated[bool, Field(description="Also test REAPER's JS effects (there are hundreds)")] = False,
    max_seconds: Annotated[float, Field(ge=10, le=600, description="Stop after about this long; call again to continue")] = 100,
) -> dict:
    """Tests installed plugins to learn what they actually do, at their default settings:
    instruments (makes sound? pitched or drum kit, range, character, late starts) and
    effects (reverb, delay, compressor/limiter, gate, EQ curve, saturation, modulation,
    pitch, stereo width, latency). Each test runs on a hidden temporary track after the
    end of the project and is removed again. Results go into the plugin catalog
    (get_plugin_catalog, list_installed_fx). Long scans stop after max_seconds and
    report what's left; call again to continue."""
    listing = call("list_installed_fx", kind=None if kind == "all" else kind, search=search, limit=5000)
    plugins = listing.get("plugins", [])
    if names:
        wanted = [n.lower() for n in names]
        plugins = [p for p in plugins if any(w in (p.get("name") or "").lower() or w == (p.get("load_as") or "").lower()
                                             for w in wanted)]
    if not include_js:
        plugins = [p for p in plugins if (p.get("format") or "").upper() != "JS"]
    known = plugin_catalog.all()
    # Failed tests are retried: the cause (a dialog, a busy REAPER) is often temporary.
    todo = [p for p in plugins if refresh or p["load_as"] not in known or known[p["load_as"]].get("error")]
    sample_rate = int(call("get_project_overview").get("sample_rate") or 48000)
    tested, skipped, failed = [], [], []
    started = time.monotonic()
    for plugin in todo:
        if time.monotonic() - started > max_seconds:
            break
        if plugin.get("hardware") or plugin.get("realtime_only"):
            plugin_catalog.put(plugin["load_as"], {"kind": plugin["kind"], "name": plugin.get("name"),
                                                   "developer": plugin.get("developer"), "roles": ["hardware"],
                                                   "summary": "needs its hardware or real-time playback, so it can't be tested offline"})
            skipped.append(plugin["name"])
            continue
        try:
            entry = test_plugin(plugin, sample_rate)
        except (BridgeError, ValueError) as e:
            plugin_catalog.put(plugin["load_as"], {"kind": plugin["kind"], "name": plugin.get("name"), "error": str(e)})
            failed.append({"plugin": plugin["name"], "error": str(e)})
            continue
        plugin_catalog.put(plugin["load_as"], entry)
        tested.append({"plugin": plugin["name"], "kind": plugin["kind"], "roles": entry.get("roles"),
                       "summary": entry.get("summary")})
    done = len(tested) + len(skipped) + len(failed)
    out = {"tested": tested, "already_in_catalog": len(plugins) - len(todo), "remaining": len(todo) - done}
    if failed and all("doesn't know 'probe_plugin'" in f["error"] for f in failed):
        out["fix"] = "The running bridge is older than creaper: run `creaper install-bridge` and restart REAPER."
    if skipped:
        out["hardware_skipped"] = skipped
    if failed:
        out["failed"] = failed
    if out["remaining"]:
        out["next"] = "Call scan_plugins again with the same filters to continue."
    return out


# REAPER category words that mean a role, for plugins that do nothing at their defaults.
ROLE_CATEGORIES = {
    "compressor": ("dynamics", "compressor"), "limiter": ("dynamics", "limiter"), "gate": ("dynamics", "gate"),
    "eq": ("eq", "filter"), "filter": ("filter", "eq"), "reverb": ("reverb",), "delay": ("delay",),
    "modulation": ("modulation", "chorus", "flanger", "phaser"), "saturation": ("distortion", "saturation"),
    "distortion": ("distortion",), "pitch": ("pitch",), "stereo": ("stereo", "imager"),
}


def _categories(role: str) -> tuple[str, ...]:
    word = role.lower().split("/")[0].strip()
    return ROLE_CATEGORIES.get(word, (word,))


@tool(annotations=READ_ONLY)
def get_plugin_catalog(
    role: Annotated[str | None, Field(description=(
        "e.g. reverb, delay, compressor, limiter, eq/filter, saturation, distortion, modulation, stereo, pitch, "
        "gate/expander, pitched instrument, drum kit"))] = None,
    kind: Literal["instrument", "effect"] | None = None,
    search: Annotated[str | None, Field(description="Words in the plugin name, developer or summary")] = None,
) -> dict:
    """What creaper has learned about the user's plugins by testing them (scan_plugins):
    each plugin's roles and a summary of what it does at default settings."""
    entries = []
    for load_as, e in plugin_catalog.all().items():
        if kind and e.get("kind") != kind:
            continue
        # A plugin that does nothing at its defaults (a compressor at 0 dB threshold, a
        # flat EQ) still matches by REAPER's category.
        if role and not any(role.lower() in r for r in e.get("roles", []))                 and not any(c in (e.get("category") or "").lower() for c in _categories(role)):
            continue
        hay = f"{load_as} {e.get('developer') or ''} {e.get('summary') or ''}".lower()
        if search and not all(w in hay for w in search.lower().split()):
            continue
        entries.append({"plugin": e.get("name") or load_as, "load_as": load_as, "kind": e.get("kind"),
                        "roles": e.get("roles"), "summary": e.get("summary") or e.get("error"),
                        **({"category": e["category"]} if e.get("category") else {}),
                        "tested": e.get("tested")})
    entries.sort(key=lambda x: (x["kind"] or "", x["plugin"]))
    out: dict = {"count": len(entries), "plugins": entries}
    if not entries:
        out["note"] = "Nothing matches in the catalog yet; scan_plugins tests plugins to fill it."
    return out
