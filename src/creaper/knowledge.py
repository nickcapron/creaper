"""Notes Claude keeps between sessions: plugin quirks, the user's taste, mix lessons.

Stored as plain JSON in <REAPER resource path>/creaper/knowledge.json, so the user
can read, edit or delete it.
"""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path

from . import jsonstore

TOPICS = ("plugin", "preference", "mix", "sound", "project", "other")


class Knowledge:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _read(self) -> list[dict]:
        return jsonstore.read(self.path, dict).get("notes", [])

    def _updating(self):
        """The notes list to change, saved (under the store's lock) when the block ends."""
        return jsonstore.updating(self.path, lambda: {"version": 1, "notes": []}, indent=2)

    def add(self, text: str, topic: str = "other", subject: str | None = None) -> dict:
        text = text.strip()
        if not text:
            raise ValueError("the note is empty")
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
                    "text": text, "saved": dt.date.today().isoformat()}
            notes.append(note)
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
