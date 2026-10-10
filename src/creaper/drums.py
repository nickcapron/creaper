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
        """The map whose instrument name appears in the FX name; the longest wins,
        so 'Analog Rytm MKII' beats 'Analog Rytm'."""
        if not fx_name:
            return None
        name = fx_name.lower()
        matches = [k for k in self.all() if k.lower() in name]
        if not matches:
            return None
        key = max(matches, key=len)
        return key, self.all()[key]
