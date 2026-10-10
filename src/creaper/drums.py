"""Saved drum maps: which note (and channel) each drum sound is on, per instrument.

General MIDI covers many drum plugins, and plugins that name their notes are
matched automatically. Drum maps cover the rest, e.g. a sampler with its own
layout, or Elektron Overbridge machines where each drum is on its own channel.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .theory import drum_map_entry

# Instruments creaper knows how to play. A map the user saves under the same
# name takes precedence.
BUILTIN_DRUM_MAPS: dict[str, dict[str, Any]] = {
    # SILA (github: nickcapron, vdigitakt): live MIDI on channel N triggers lane N;
    # note 60 plays the lane's sample at its programmed pitch. Lanes as in a new
    # SILA instance's factory kit.
    "SILA": {
        "lanes": {
            "kick": 1, "snare": 2,
            "perc": 3, "percussion": 3, "tom": 3, "clap": 3, "rim": 3, "shaker": 3,
            "closed hat": 4, "hat": 4, "pedal hat": 4,
            "open hat": 5, "cymbal": 5, "crash": 5, "ride": 5,
        },
        "notes": (
            "SILA plays lane N on MIDI channel N, and note C4 (60) plays the lane at its "
            "own pitch (other notes transpose it, up to 2 octaves). A new SILA has lanes "
            "1 Kick, 2 Snare, 3 Perc (toms, claps), 4 Closed hat, 5 Open hat, 6 Bass, "
            "7 Keys, 8 Pad (no cymbal lane: cymbals go to the open-hat lane); write bass, keys or pad lines as notes on channels 6, 7 or 8. "
            "If the user has changed SILA's kit, ask what's on each lane and save_drum_map. "
            "Its outputs split per lane with split_instrument_outputs."
        ),
    },
}


def builtin_entries(spec: dict[str, Any]) -> dict[str, dict]:
    return {lane: {"pitch": 60, "channel": channel} for lane, channel in spec["lanes"].items()}


class DrumMaps:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def all(self) -> dict[str, dict[str, dict]]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except ValueError as e:
            raise ValueError(f"{self.path} isn't valid JSON ({e}); fix or delete it") from None
        return data.get("maps", {})

    def _write(self, maps: dict[str, dict[str, dict]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "maps": maps}, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def save(self, instrument: str, mapping: dict[str, Any]) -> dict[str, dict]:
        instrument = instrument.strip()
        if not instrument:
            raise ValueError("give the instrument's name, e.g. 'Analog Rytm'")
        if not mapping:
            raise ValueError("the drum map is empty")
        entries = {lane.strip(): drum_map_entry(value) for lane, value in mapping.items()}
        maps = self.all()
        maps[instrument] = entries
        self._write(maps)
        return entries

    def delete(self, instrument: str) -> bool:
        maps = self.all()
        for key in list(maps):
            if key.lower() == instrument.strip().lower():
                del maps[key]
                self._write(maps)
                return True
        return False

    def find(self, fx_name: str | None) -> tuple[str, dict[str, dict]] | None:
        """The map whose instrument name appears in the FX name: the user's own maps
        first, then built-in ones. The longest name wins, so 'Analog Rytm MKII' beats
        'Analog Rytm'."""
        if not fx_name:
            return None
        name = fx_name.lower()
        saved = self.all()
        for maps in (saved, {k: builtin_entries(v) for k, v in BUILTIN_DRUM_MAPS.items()}):
            matches = [k for k in maps if k.lower() in name]
            if matches:
                key = max(matches, key=len)
                return key, maps[key]
        return None

    @staticmethod
    def notes_for(fx_name: str | None) -> str | None:
        """How to play a built-in instrument, for Claude."""
        name = (fx_name or "").lower()
        for key, spec in BUILTIN_DRUM_MAPS.items():
            if key.lower() in name:
                return spec["notes"]
        return None
