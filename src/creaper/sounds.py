"""The sound library: named, tagged snapshots of plugin sounds.

Many plugins keep their presets in their own browser, where REAPER (and so
Claude) can't reach them. A snapshot captures the plugin's complete state
after the user picks a sound there, so Claude can recall it on any track, in
any project.

Layout, in <REAPER resource path>/creaper/sounds/:
    library.json        names, tags, descriptions, which plugin
    <id>.state.json     the captured state (can be large for some plugins)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from . import jsonstore

# Where a sound comes from. Only plugins for now; hardware synths (MIDI out +
# audio in) can be added as another source later without changing the format.
SOURCE_PLUGIN = "plugin"


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "sound"
    return f"{slug}-{hashlib.sha1(name.lower().encode()).hexdigest()[:6]}"


def _norm_tags(tags: list[str] | None) -> list[str]:
    out: list[str] = []
    for tag in tags or []:
        t = tag.strip().lower()
        if t and t not in out:
            out.append(t)
    return out


def short_plugin_name(full_name: str) -> str:
    """'VST3i: Mini V3 (Arturia)' -> 'Mini V3'."""
    name = re.sub(r"^\w+:\s*", "", full_name)
    name = re.sub(r"\s*\((\d+\s*out|\d+->\d+\s*ch|\d+\s*ch)\)$", "", name)
    return re.sub(r"\s*\([^()]*\)$", "", name)


class SoundLibrary:
    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)
        self.index_path = self.folder / "library.json"

    # ------------------------------------------------------------- storage

    def _read(self) -> dict[str, dict]:
        return jsonstore.read(self.index_path, dict).get("sounds", {})

    def _updating(self):
        """The index to change, saved (under the library's lock) when the block ends."""
        return jsonstore.updating(self.index_path, lambda: {"version": 1, "sounds": {}}, indent=2)

    def _state_path(self, entry: dict) -> Path:
        path = (self.folder / f"{entry['id']}.state.json").resolve()
        if self.folder.resolve() not in path.parents:
            raise ValueError("the library index points outside the sound library")
        return path

    # ---------------------------------------------------------------- API

    def find(self, name: str) -> tuple[str, dict]:
        """Exact name (any case), else a single partial match."""
        return self._match(self._read(), name)

    @staticmethod
    def _match(sounds: dict[str, dict], name: str) -> tuple[str, dict]:
        wanted = name.strip().lower()
        if wanted in sounds:
            return wanted, sounds[wanted]
        partial = [k for k in sounds if wanted in k]
        if len(partial) == 1:
            return partial[0], sounds[partial[0]]
        if partial:
            names = ", ".join(sounds[k]["name"] for k in partial[:12])
            raise ValueError(f"'{name}' matches several sounds: {names}")
        raise ValueError(f"there's no sound named '{name}' in the library (list_sounds shows them)")

    def save(self, name: str, captured: dict, tags: list[str] | None = None,
             description: str | None = None, overwrite: bool = False) -> dict:
        name = name.strip()
        if not name:
            raise ValueError("give the sound a name, e.g. 'Dark Pad'")
        key = name.lower()
        existing = self._read()
        if key in existing and not overwrite:
            raise ValueError(f"there's already a sound named '{existing[key]['name']}'; "
                             "pick another name or set overwrite=true")
        entry = {
            "id": _slug(name),
            "name": name,
            "source": SOURCE_PLUGIN,
            "plugin": captured["plugin"],
            "plugin_name": short_plugin_name(captured["plugin"]),
            "kind": "instrument" if captured.get("instrument") else "effect",
            "format": captured.get("format"),
            "tags": _norm_tags(tags),
            "description": (description or "").strip() or None,
            # Placeholder program names ("Program 1") say nothing about the sound.
            "plugin_preset": None if re.fullmatch(r"Program \d+", captured.get("preset") or "")
            else captured.get("preset"),
            "restore": "full plugin state" if captured.get("chunk") else "parameters",
            "saved": dt.datetime.now().isoformat(timespec="seconds"),
        }
        state = {key_: captured.get(key_) for key_ in ("plugin", "file", "format", "instrument", "chunk", "params")}
        self.folder.mkdir(parents=True, exist_ok=True)
        jsonstore.write(self._state_path(entry), state, indent=None)
        with self._updating() as data:
            data.setdefault("sounds", {})[key] = entry
        return entry

    def state(self, entry: dict) -> dict:
        try:
            return json.loads(self._state_path(entry).read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ValueError(f"the saved state for '{entry['name']}' is missing from {self.folder}") from None

    def search(self, text: str | None = None, tag: str | None = None, plugin: str | None = None,
               kind: str | None = None) -> list[dict]:
        words = (text or "").lower().split()
        results = []
        for entry in self._read().values():
            haystack = " ".join([entry["name"], entry.get("plugin_name") or "", entry.get("description") or "",
                                 " ".join(entry.get("tags", []))]).lower()
            if words and not all(w in haystack for w in words):
                continue
            if tag and tag.strip().lower() not in entry.get("tags", []):
                continue
            if plugin and plugin.lower() not in entry["plugin"].lower():
                continue
            if kind and entry.get("kind") != kind:
                continue
            results.append(entry)
        return sorted(results, key=lambda e: e["name"].lower())

    def update(self, name: str, new_name: str | None = None, tags: list[str] | None = None,
               add_tags: list[str] | None = None, description: str | None = None) -> dict:
        with self._updating() as data:
            sounds = data.setdefault("sounds", {})
            key, entry = self._match(sounds, name)
            return self._edit(sounds, key, entry, new_name, tags, add_tags, description)

    @staticmethod
    def _edit(sounds: dict[str, dict], key: str, entry: dict, new_name: str | None, tags: list[str] | None,
              add_tags: list[str] | None, description: str | None) -> dict:
        if tags is not None:
            entry["tags"] = _norm_tags(tags)
        if add_tags:
            entry["tags"] = _norm_tags(entry.get("tags", []) + add_tags)
        if description is not None:
            entry["description"] = description.strip() or None
        if new_name and new_name.strip().lower() != key:
            new_key = new_name.strip().lower()
            if new_key in sounds:
                raise ValueError(f"there's already a sound named '{sounds[new_key]['name']}'")
            del sounds[key]
            key = new_key
            entry["name"] = new_name.strip()
        elif new_name:
            entry["name"] = new_name.strip()
        sounds[key] = entry
        return entry

    def delete(self, name: str) -> dict:
        with self._updating() as data:
            sounds = data.setdefault("sounds", {})
            key, entry = self._match(sounds, name)
            if key != name.strip().lower():
                raise ValueError(f"to delete a sound, use its exact name ('{entry['name']}')")
            del sounds[key]
        self._state_path(entry).unlink(missing_ok=True)
        return entry


def describe(entry: dict[str, Any]) -> dict[str, Any]:
    """The library entry as Claude sees it."""
    out = {k: entry.get(k) for k in ("name", "plugin_name", "kind", "tags", "description", "restore", "saved")}
    if entry.get("plugin_preset"):
        out["plugin_preset"] = entry["plugin_preset"]
    return {k: v for k, v in out.items() if v not in (None, [])}
