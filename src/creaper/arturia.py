"""Arturia's preset library, read from the database its plugins and Analog Lab share
(db.db3, SQLite). Each preset there has a type (Bass, Pad, Lead...), a subtype (Sub
Bass, Evolving Pad...), and characteristics that cover its sound (Warm, Dark, Wide),
genres (Synthwave, House, Cinematic) and styles. That lets Claude pick sounds the way a
producer browses: by role and character, across every Arturia instrument installed.

Read-only. The database is live (the plugins write to it), so it's copied to a temp
file and the copy is opened read-only. Nothing from it is ever saved in creaper.

Loading a preset: each preset file is the plugin's own state, a Boost text archive
("22 serialization::archive ..."). Arturia's VST3 plugins take their state as that
archive twice, each with a little-endian (length, flag) header: flag 1 then flag 0.
So a preset loads by handing the plugin its file in that frame (apply_fx_state with
the chunk), which every installed Arturia instrument accepted in a live test: it reads
back under the preset's name with its parameters set. The file goes from Arturia's
folder into Arturia's plugin; creaper keeps no copy.
"""

from __future__ import annotations

import base64
import hashlib
import os
import shutil
import sqlite3
import struct
import sys
import tempfile
from pathlib import Path

# Types_V2 ids at or above this are effect presets and templates, not instrument sounds.
FIRST_EFFECT_TYPE = 14
# Presets that play a pattern of their own (an arpeggiator, sequencer or gate inside the
# patch): any part written on them is re-played as their pattern. Left out unless asked.
PATTERN_TYPES = ("sequence",)
PATTERN_CHARACTERISTICS = ("arpeggiated", "sequenced", "sequence/loop", "tempo-synced", "synced", "gated",
                           "phrases", "rhythmic")


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


ARCHIVE_MAGIC = b"22 serialization::archive"
MAX_PRESET_BYTES = 16 * 1024 * 1024


def preset_chunk(path: str | Path) -> str:
    """The base64 VST3 state that loads a preset file into its Arturia plugin."""
    data = Path(path).read_bytes()
    if not data.startswith(ARCHIVE_MAGIC):
        raise ValueError(f"{Path(path).name} isn't an Arturia preset file this version of creaper can load")
    if len(data) > MAX_PRESET_BYTES:
        raise ValueError(f"{Path(path).name} is too big to be a preset")
    frame = struct.pack("<II", len(data), 1) + data + struct.pack("<II", len(data), 0) + data
    return base64.b64encode(frame).decode("ascii")


def chunk_preset_name(chunk: str | None) -> str | None:
    """The preset name an Arturia plugin's state (capture_fx_state's chunk) says it holds."""
    if not chunk:
        return None
    try:
        raw = base64.b64decode(chunk)
        n = struct.unpack_from("<I", raw, 0)[0]
        body = raw[8: 8 + min(n, 400)]
        if not body.startswith(ARCHIVE_MAGIC):
            return None
        # "22 serialization::archive 10 0 7 0 7 <length> <name>": the name is length-prefixed.
        tokens = body.split(b" ", 8)
        length = int(tokens[7])
        return tokens[8][:length].decode("utf-8", "replace")
    except (ValueError, IndexError, struct.error):
        return None


def resolve(conn: sqlite3.Connection, preset: str, plugin: str | None = None,
            installed: set[str] | None = None) -> dict:
    """One preset from a name ('Doomsday Sub') or a browser path ('Jup-8 V4 > Factory >
    Doomsday Sub'), on the given plugin when several have one by that name, else on an
    installed one. Returns name, plugin (folder), path."""
    parts = [p.strip() for p in preset.split(">")]
    name = parts[-1]
    if len(parts) >= 2 and not plugin:
        plugin = parts[0]
    rows = conn.execute("SELECT name, file_path FROM Preset_Id WHERE LOWER(name) = LOWER(?) AND hide_in_browser = 0",
                        (name,)).fetchall()
    found = [{"name": r[0], "plugin": plugin_folder(r[1]), "path": r[1]} for r in rows]
    if plugin:
        want = normalize_plugin(plugin)
        found = [f for f in found if normalize_plugin(f["plugin"]) == want] or \
                [f for f in found if want in normalize_plugin(f["plugin"])]
    if installed is not None and len(found) > 1:
        found = [f for f in found if normalize_plugin(f["plugin"]) in installed] or found
    if not found:
        raise ValueError(f"there's no Arturia preset called '{name}'" + (f" for {plugin}" if plugin else "")
                         + "; find_arturia_presets lists them")
    if len({f["plugin"] for f in found}) > 1:
        raise ValueError(f"'{name}' exists for several instruments ({', '.join(sorted({f['plugin'] for f in found}))}): "
                         "say which with plugin=")
    if not Path(found[0]["path"]).exists():
        raise ValueError(f"the preset file for '{name}' isn't on this computer ({found[0]['plugin']} may need "
                         "reinstalling in Arturia Software Center)")
    return found[0]


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
         search: str | None = None, installed: set[str] | None = None, limit: int = 20,
         patterns: bool = False) -> list[dict]:
    """Presets matching every filter given, curated ones (Arturia's featured picks)
    first. Words match loosely (case-insensitive, part of the name): 'sub' finds 'Sub
    Bass'; each characteristic must be present; genre matches a genre characteristic
    ('synthwave', 'hip hop'). installed: normalized plugin names to keep (None: all).
    Presets that play a pattern of their own (Sequence type, Arpeggiated, Sequenced,
    Gated...) are left out unless patterns is True or the type asked for is Sequence."""
    where, args = [], []
    if type:
        where.append("LOWER(t.name) LIKE ?")
        args.append(_like(type))
    else:
        where.append("p.type_v2 > 0 AND p.type_v2 < ?")
        args.append(FIRST_EFFECT_TYPE)
    if not patterns and not any(word in (type or "").lower() for word in PATTERN_TYPES):
        where.append("LOWER(COALESCE(t.name, '')) NOT IN (" + ", ".join("?" * len(PATTERN_TYPES)) + ")")
        args += list(PATTERN_TYPES)
        where.append("NOT EXISTS (SELECT 1 FROM Preset_Characteristics pc JOIN Characteristics c "
                     "ON c.key_id = pc.characteristic_key WHERE pc.preset_key = p.key_id AND LOWER(TRIM(c.name)) IN ("
                     + ", ".join("?" * len(PATTERN_CHARACTERISTICS)) + "))")
        args += list(PATTERN_CHARACTERISTICS)
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
        out.append({"name": row["name"], "plugin": folder, "path": row["file_path"], "type": row["type"],
                    "subtype": row["subtype"] or None,
                    "characteristics": chars, "pack": row["pack"],
                    "browser_path": f"{folder} > {row['pack'] or 'Factory'} > {row['name']}",
                    **({"comment": row["comment"][:160]} if row["comment"] else {})})
        if len(out) >= limit:
            break
    return out
