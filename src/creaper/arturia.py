"""Arturia's preset library, read from the database its plugins and Analog Lab share
(db.db3, SQLite). Each preset there has a type (Bass, Pad, Lead...), a subtype (Sub
Bass, Evolving Pad...), and characteristics that cover its sound (Warm, Dark, Wide),
genres (Synthwave, House, Cinematic) and styles. That lets Claude pick sounds the way a
producer browses: by role and character, across every Arturia instrument installed.

Read-only. The database is live (the plugins write to it), so it's copied to a temp
file and the copy is opened read-only. Nothing from it is ever saved in creaper.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# Types_V2 ids at or above this are effect presets and templates, not instrument sounds.
FIRST_EFFECT_TYPE = 14


def default_path() -> Path:
    if os.environ.get("CREAPER_ARTURIA_DB"):
        return Path(os.environ["CREAPER_ARTURIA_DB"])
    if sys.platform == "darwin":
        return Path("/Library/Arturia/Presets/db.db3")
    return Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Arturia" / "Presets" / "db.db3"


def _copy(src: Path) -> Path:
    """A private copy of the live database, refreshed when the original changes."""
    key = hashlib.sha1(str(src.resolve()).encode("utf-8")).hexdigest()[:10]
    dest = Path(tempfile.gettempdir()) / f"creaper-arturia-presets-{key}.db3"
    st = src.stat()
    if not dest.exists() or dest.stat().st_size != st.st_size or dest.stat().st_mtime < st.st_mtime:
        shutil.copyfile(src, dest)
    return dest


def connect(path: Path | None = None) -> sqlite3.Connection:
    src = Path(path) if path else default_path()
    if not src.exists():
        raise ValueError(f"Arturia's preset database isn't at {src}: is Arturia Software Center or Analog Lab "
                         "installed? (Set CREAPER_ARTURIA_DB to its db.db3 if it's elsewhere.)")
    conn = sqlite3.connect(f"file:{_copy(src).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def plugin_folder(file_path: str) -> str:
    """The instrument's folder under Presets ('Jup-8 V4'), which is also its plugin name
    in REAPER ('Jup-8 V4 (Arturia)'). The db's own instrument names ('Jup-8') are shared
    by several versions, so the folder is the reliable key."""
    parts = file_path.replace("\\", "/").split("/")
    lowered = [p.lower() for p in parts]
    if "presets" in lowered:
        i = lowered.index("presets")
        if i + 1 < len(parts):
            return parts[i + 1]
    return parts[-3] if len(parts) >= 3 else ""


def normalize_plugin(name: str) -> str:
    """'VST3i: Jup-8 V4 (Arturia)' -> 'jup-8 v4'."""
    n = name.split(":", 1)[-1] if ":" in name[:8] else name
    n = n.replace("(Arturia)", "").replace("(arturia)", "")
    return " ".join(n.lower().split())


def vocabulary(conn: sqlite3.Connection) -> dict[str, list[str]]:
    """The words the database knows: types, subtypes, and characteristics by kind
    (sound characteristics, genres, styles)."""
    out = {"types": [r[0] for r in conn.execute("SELECT name FROM Types_V2 WHERE key_id < ? ORDER BY key_id",
                                                (FIRST_EFFECT_TYPE,))],
           "subtypes": sorted({r[0] for r in conn.execute("SELECT name FROM Subtypes_V2") if r[0]})}
    for kind_id, label in ((1, "characteristics"), (2, "genres"), (3, "styles")):
        out[label] = sorted({r[0].strip() for r in conn.execute("SELECT name FROM Characteristics WHERE type_key = ?",
                                                                (kind_id,)) if r[0].strip()})
    return out


def _like(word: str) -> str:
    return "%" + word.replace("%", "").replace("_", "").strip().lower() + "%"


def find(conn: sqlite3.Connection, instrument: str | None = None, type: str | None = None,
         subtype: str | None = None, characteristics: list[str] | None = None, genre: str | None = None,
         search: str | None = None, installed: set[str] | None = None, limit: int = 20) -> list[dict]:
    """Presets matching every filter given, curated ones (Arturia's featured picks)
    first. Words match loosely (case-insensitive, part of the name): 'sub' finds 'Sub
    Bass'; each characteristic must be present; genre matches a genre characteristic
    ('synthwave', 'hip hop'). installed: normalized plugin names to keep (None: all)."""
    where, args = [], []
    if type:
        where.append("LOWER(t.name) LIKE ?")
        args.append(_like(type))
    else:
        where.append("p.type_v2 > 0 AND p.type_v2 < ?")
        args.append(FIRST_EFFECT_TYPE)
    if subtype:
        where.append("LOWER(s.name) LIKE ?")
        args.append(_like(subtype))
    if search:
        where.append("(LOWER(p.name) LIKE ? OR LOWER(p.comment) LIKE ?)")
        args += [_like(search)] * 2
    if instrument:
        where.append("(LOWER(p.file_path) LIKE ? OR LOWER(i.name) LIKE ?)")
        args += [_like(instrument)] * 2
    # Each wanted word is its own EXISTS: a preset must carry all of them.
    for word, kinds in [(c, (1, 3)) for c in characteristics or []] + ([(genre, (2,))] if genre else []):
        where.append("EXISTS (SELECT 1 FROM Preset_Characteristics pc JOIN Characteristics c "
                     "ON c.key_id = pc.characteristic_key WHERE pc.preset_key = p.key_id "
                     f"AND c.type_key IN ({', '.join('?' * len(kinds))}) AND LOWER(c.name) LIKE ?)")
        args += [*kinds, _like(word)]
    sql = ("SELECT p.key_id, p.name, p.file_path, p.comment, i.name AS instrument, t.name AS type, s.name AS subtype, "
           "pk.name AS pack, p.featured_idx FROM Preset_Id p "
           "JOIN Instruments i ON i.key_id = p.instrument_key "
           "LEFT JOIN Types_V2 t ON t.key_id = p.type_v2 "
           "LEFT JOIN Subtypes_V2 s ON s.key_id = p.subtype_v2 "
           "LEFT JOIN Packs pk ON pk.key_id = p.pack "
           "WHERE p.hide_in_browser = 0 AND " + " AND ".join(where) +
           " ORDER BY p.featured_idx, p.rating DESC, p.name")
    out = []
    for row in conn.execute(sql, args):
        folder = plugin_folder(row["file_path"])
        if installed is not None and normalize_plugin(folder) not in installed:
            continue
        chars = [r[0].strip() for r in conn.execute(
            "SELECT c.name FROM Preset_Characteristics pc JOIN Characteristics c ON c.key_id = pc.characteristic_key "
            "WHERE pc.preset_key = ? ORDER BY c.type_key, c.name", (row["key_id"],))]
        out.append({"name": row["name"], "plugin": folder, "type": row["type"], "subtype": row["subtype"] or None,
                    "characteristics": chars, "pack": row["pack"],
                    "browser_path": f"{folder} > {row['pack'] or 'Factory'} > {row['name']}",
                    **({"comment": row["comment"][:160]} if row["comment"] else {})})
        if len(out) >= limit:
            break
    return out
