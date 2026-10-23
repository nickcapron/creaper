"""Notes Claude keeps between sessions: plugin quirks, the user's taste, mix lessons.

Stored as plain JSON in <REAPER resource path>/creaper/knowledge.json, so the user
can read, edit or delete it.
"""

from __future__ import annotations

import datetime as dt
import re
import time
import uuid
from pathlib import Path

from . import __version__, jsonstore

TOPICS = ("plugin", "preference", "mix", "sound", "project", "other")
MAX_NOTE_CHARS = 600     # a lesson, not a document: a long note is more likely pasted-in text
MAX_NOTES = 300          # the oldest go when there are more
# A note naming one of creaper's tools (snake_case, like auto_mix) describes how that tool
# behaved then: "auto_mix chokes on VocalVST tracks" kept steering Claude to mix by hand
# for days after the fix.
TOOL_WORDS = re.compile(r"\b[a-z]+_[a-z_]+\b|\bcreaper\b|\bvocalvst\b", re.I)


def _version(v: str | None) -> tuple:
    try:
        return tuple(int(x) for x in (v or "").split("."))
    except ValueError:
        return ()


def staleness(note: dict) -> str | None:
    """Why a note about creaper's own tools may be out of date, or None. Taste notes
    (topic preference) don't age with the tools."""
    if note.get("topic") == "preference" or not TOOL_WORDS.search(note.get("text", "")):
        return None
    saved = note.get("creaper")
    if saved and _version(saved) >= _version(__version__):
        return None
    when = f"under creaper {saved}" if saved else "before creaper recorded versions (older than 0.36)"
    return (f"saved {when}; creaper is {__version__} now: a limit, crash or workaround it describes may be "
            "fixed. Use the tool as documented before working around it")


def recent(note: dict, hours: float) -> bool:
    return time.time() - float(note.get("saved_at") or 0) < hours * 3600


class Knowledge:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _read(self) -> list[dict]:
        return jsonstore.read(self.path, dict).get("notes", [])

    def _updating(self):
        """The notes list to change, saved (under the store's lock) when the block ends."""
        return jsonstore.updating(self.path, lambda: {"version": 1, "notes": []}, indent=2)

    def add(self, text: str, topic: str = "other", subject: str | None = None) -> dict:
        text = " ".join(text.split())   # one line: a note can't pose as several
        if not text:
            raise ValueError("the note is empty")
        if len(text) > MAX_NOTE_CHARS:
            raise ValueError(f"notes are lessons of up to {MAX_NOTE_CHARS} characters; this one is {len(text)}")
        topic = topic.strip().lower()
        if topic not in TOPICS:
            raise ValueError(f"topic must be one of {', '.join(TOPICS)}")
        subject_key = (subject or "").strip().lower()
        with self._updating() as data:
            notes = data.setdefault("notes", [])
            for note in notes:  # the same lesson twice adds nothing
                if note["text"].lower() == text.lower() and (note.get("subject") or "").lower() == subject_key:
                    return note
            note = {"id": uuid.uuid4().hex[:8], "topic": topic, "subject": (subject or "").strip() or None,
                    "text": text, "saved": dt.date.today().isoformat(), "saved_at": int(time.time()),
                    "creaper": __version__}
            notes.append(note)
            del notes[:-MAX_NOTES]
        return note

    def find(self, search: str | None = None, topic: str | None = None, subject: str | None = None) -> list[dict]:
        words = (search or "").lower().split()
        out = []
        for note in self._read():
            haystack = " ".join([note["text"], note.get("subject") or "", note["topic"]]).lower()
            if words and not any(w in haystack for w in words):
                continue
            if topic and note["topic"] != topic.lower():
                continue
            if subject and subject.lower() not in (note.get("subject") or "").lower():
                continue
            out.append(note)
        if words:  # most relevant first: notes matching more of the words
            out.sort(key=lambda n: -sum(w in (n["text"] + " " + (n.get("subject") or "")).lower() for w in words))
        return out

    def delete(self, note_id: str) -> dict:
        with self._updating() as data:
            notes = data.setdefault("notes", [])
            for i, note in enumerate(notes):
                if note["id"] == note_id.strip():
                    del notes[i]
                    return note
        raise ValueError(f"there's no note with id '{note_id}' (find_notes lists them)")
