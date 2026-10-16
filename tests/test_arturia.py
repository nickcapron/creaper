"""find_arturia_presets, against a tiny database shaped like Arturia's db.db3."""

import sqlite3

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import arturia

SCHEMA = """
CREATE TABLE Instruments (key_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE Types_V2 (key_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE Subtypes_V2 (key_id INTEGER PRIMARY KEY, name TEXT NOT NULL, type_key INTEGER NOT NULL);
CREATE TABLE Packs (key_id INTEGER PRIMARY KEY, name TEXT NOT NULL, factory INTEGER DEFAULT 0);
CREATE TABLE Characteristics_Types (key_id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE Characteristics (key_id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, type_key INTEGER);
CREATE TABLE Preset_Id (key_id INTEGER PRIMARY KEY, name TEXT NOT NULL, type_v2 INTEGER NOT NULL DEFAULT 0,
    subtype_v2 INTEGER NOT NULL DEFAULT 0, instrument_key INTEGER NOT NULL, rating REAL NOT NULL DEFAULT 0,
    pack INTEGER NOT NULL, comment TEXT NOT NULL DEFAULT '', file_path TEXT UNIQUE NOT NULL,
    featured_idx INTEGER DEFAULT 10000, hide_in_browser INTEGER DEFAULT 0);
CREATE TABLE Preset_Characteristics (key_id INTEGER PRIMARY KEY, preset_key INTEGER, characteristic_key INTEGER);
"""


@pytest.fixture
def db(tmp_path, monkeypatch):
    path = tmp_path / "db.db3"
    c = sqlite3.connect(path)
    c.executescript(SCHEMA)
    c.executemany("INSERT INTO Instruments VALUES (?, ?)", [(1, "Jup-8"), (2, "Pigments"), (3, "Bus FORCE")])
    c.executemany("INSERT INTO Types_V2 VALUES (?, ?)", [(1, "Bass"), (8, "Pad"), (17, "Dynamics")])
    c.executemany("INSERT INTO Subtypes_V2 VALUES (?, ?, ?)", [(1, "Sub Bass", 1), (2, "Evolving Pad", 8)])
    c.execute("INSERT INTO Packs VALUES (1, 'Factory', 1)")
    c.executemany("INSERT INTO Characteristics VALUES (?, ?, ?)",
                  [(1, "Analog", 1), (2, "Synthwave", 2), (3, "Dark", 3), (4, "Warm", 3), (5, "Hip Hop/Trap", 2)])
    root = "C:/ProgramData/Arturia/Presets"
    presets = [  # key, name, type, subtype, instrument, file, featured, hidden, chars
        (1, "Doomsday Sub", 1, 1, 1, f"{root}/Jup-8 V4/Factory/Factory/Doomsday Sub", 10000, 0, [1, 3, 5]),
        (2, "Night Drive", 8, 2, 1, f"{root}/Jup-8 V4/Factory/Factory/Night Drive", 3, 0, [1, 2, 4]),
        (3, "Glass Pad", 8, 2, 2, f"{root}/Pigments/Factory/Factory/Glass Pad", 10000, 0, [2, 4]),
        (4, "Hidden Bass", 1, 1, 1, f"{root}/Jup-8 V4/Factory/Factory/Hidden Bass", 10000, 1, [3]),
        (5, "Glue Master", 17, 0, 3, f"{root}/Bus FORCE/Factory/Factory/Glue Master", 10000, 0, []),
        (6, "Warm Pad", 8, 2, 1, f"{root}/Jup-8 V4/Factory/Factory/Warm Pad", 1, 0, [4]),
    ]
    k = 0
    for key, name, t, s, inst, fp, featured, hidden, chars in presets:
        c.execute("INSERT INTO Preset_Id (key_id, name, type_v2, subtype_v2, instrument_key, pack, file_path, "
                  "featured_idx, hide_in_browser, comment) VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, '')",
                  (key, name, t, s, inst, fp, featured, hidden))
        for ch in chars:
            k += 1
            c.execute("INSERT INTO Preset_Characteristics VALUES (?, ?, ?)", (k, key, ch))
    c.commit()
    c.close()
    monkeypatch.setenv("CREAPER_ARTURIA_DB", str(path))
    return path


def names(found):
    return [p["name"] for p in found]


def test_filters_by_type_subtype_and_every_characteristic(db):
    conn = arturia.connect()
    assert names(arturia.find(conn, type="bass")) == ["Doomsday Sub"]            # hidden presets left out
    assert names(arturia.find(conn, subtype="evolving")) == ["Warm Pad", "Night Drive", "Glass Pad"]  # featured first
    assert names(arturia.find(conn, type="pad", characteristics=["warm", "analog"])) == ["Night Drive"]
    assert names(arturia.find(conn, genre="synthwave")) == ["Night Drive", "Glass Pad"]
    assert names(arturia.find(conn, genre="hip hop")) == ["Doomsday Sub"]
    assert names(arturia.find(conn, characteristics=["synthwave"])) == []         # a genre isn't a characteristic
    assert "Glue Master" not in names(arturia.find(conn))                        # effect presets left out
    assert names(arturia.find(conn, type="dynamics")) == ["Glue Master"]


def test_results_name_the_plugin_and_browser_path(db):
    found = arturia.find(arturia.connect(), search="doomsday")
    assert found[0]["plugin"] == "Jup-8 V4"
    assert found[0]["browser_path"] == "Jup-8 V4 > Factory > Doomsday Sub"
    assert found[0]["characteristics"] == ["Analog", "Hip Hop/Trap", "Dark"]


def test_installed_filter_and_plugin_names(db):
    conn = arturia.connect()
    installed = {arturia.normalize_plugin("VST3i: Jup-8 V4 (Arturia)")}
    assert installed == {"jup-8 v4"}
    assert names(arturia.find(conn, type="pad", installed=installed)) == ["Warm Pad", "Night Drive"]
    assert arturia.plugin_folder(r"C:\ProgramData\Arturia\Presets\CMI V\Factory\DRUMS2\MILBDRUM") == "CMI V"


def test_vocabulary(db):
    words = arturia.vocabulary(arturia.connect())
    assert words["types"] == ["Bass", "Pad"]
    assert words["genres"] == ["Hip Hop/Trap", "Synthwave"] and words["styles"] == ["Dark", "Warm"]


def test_missing_database(tmp_path, monkeypatch):
    monkeypatch.setenv("CREAPER_ARTURIA_DB", str(tmp_path / "nope.db3"))
    with pytest.raises(ValueError, match="CREAPER_ARTURIA_DB"):
        arturia.connect()


def test_the_copy_follows_the_original(db):
    assert names(arturia.find(arturia.connect(), search="new one")) == []
    c = sqlite3.connect(db)
    c.execute("INSERT INTO Preset_Id (key_id, name, type_v2, subtype_v2, instrument_key, pack, file_path) "
              "VALUES (9, 'New One', 1, 1, 1, 1, 'C:/ProgramData/Arturia/Presets/Jup-8 V4/Factory/Factory/New One')")
    c.commit()
    c.close()
    assert names(arturia.find(arturia.connect(), search="new one")) == ["New One"]


def test_tool(db, monkeypatch):
    from creaper import sound_tools
    monkeypatch.setattr(sound_tools, "call", lambda cmd, **kw: {"plugins": [{"name": "Jup-8 V4 (Arturia)"}]})
    out = sound_tools.find_arturia_presets(type="pad", genre="synthwave")
    assert names(out["presets"]) == ["Night Drive"] and "browser_path" in out["how_to_use"]
    none = sound_tools.find_arturia_presets(type="pad", characteristics=["metallic"])
    assert none["count"] == 0 and "Synthwave" in none["known_words"]["genres"]


def test_presets_that_play_their_own_pattern_are_left_out_unless_asked(db):
    c = sqlite3.connect(db)
    c.execute("INSERT INTO Types_V2 VALUES (10, 'Sequence')")
    c.execute("INSERT INTO Characteristics VALUES (9, 'Arpeggiated', 1)")
    root = "C:/ProgramData/Arturia/Presets/Jup-8 V4/Factory/Factory"
    c.execute("INSERT INTO Preset_Id (key_id, name, type_v2, subtype_v2, instrument_key, pack, file_path) "
              f"VALUES (20, 'Arp Pad', 8, 2, 1, 1, '{root}/Arp Pad')")
    c.execute("INSERT INTO Preset_Characteristics VALUES (100, 20, 9)")
    c.execute("INSERT INTO Preset_Id (key_id, name, type_v2, subtype_v2, instrument_key, pack, file_path) "
              f"VALUES (21, 'Running Seq', 10, 0, 1, 1, '{root}/Running Seq')")
    c.commit()
    c.close()
    conn = arturia.connect()
    assert "Arp Pad" not in names(arturia.find(conn, type="pad"))
    assert "Running Seq" not in names(arturia.find(conn))
    assert "Arp Pad" in names(arturia.find(conn, type="pad", patterns=True))
    assert names(arturia.find(conn, type="sequence")) == ["Running Seq"]


# ------------------------------------------------------------------- loading

def test_preset_chunk_frames_the_file_twice_and_names_it(tmp_path):
    import base64
    import struct
    f = tmp_path / "Doomsday Sub"
    body = b"22 serialization::archive 10 0 7 0 7 12 Doomsday Sub 7 Factory 3 rest of the state"
    f.write_bytes(body)
    raw = base64.b64decode(arturia.preset_chunk(f))
    n = len(body)
    assert raw == struct.pack("<II", n, 1) + body + struct.pack("<II", n, 0) + body
    assert arturia.chunk_preset_name(arturia.preset_chunk(f)) == "Doomsday Sub"
    assert arturia.chunk_preset_name(None) is None and arturia.chunk_preset_name("bm90IGEgY2h1bms=") is None
    (tmp_path / "junk").write_bytes(b"not a preset")
    with pytest.raises(ValueError, match="isn't an Arturia preset"):
        arturia.preset_chunk(tmp_path / "junk")


def test_resolve_by_name_or_browser_path(db, tmp_path, monkeypatch):
    c = sqlite3.connect(db)
    for key, name, folder in ((30, "Shared Name", "Jup-8 V4"), (31, "Shared Name", "Mini V3")):
        path = tmp_path / folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"22 serialization::archive")
        c.execute("INSERT INTO Preset_Id (key_id, name, type_v2, subtype_v2, instrument_key, pack, file_path) "
                  "VALUES (?, ?, 1, 1, 1, 1, ?)", (key, name, str(path).replace("\\", "/").replace(
                      str(tmp_path).replace("\\", "/"), "C:/ProgramData/Arturia/Presets")))
    c.commit()
    c.close()
    conn = arturia.connect()
    monkeypatch.setattr(arturia.Path, "exists", lambda self: True)
    assert arturia.resolve(conn, "Doomsday Sub")["plugin"] == "Jup-8 V4"
    assert arturia.resolve(conn, "Jup-8 V4 > Factory > doomsday sub")["name"] == "Doomsday Sub"
    with pytest.raises(ValueError, match="several instruments"):
        arturia.resolve(conn, "Shared Name")
    assert arturia.resolve(conn, "Shared Name", plugin="Mini V3")["plugin"] == "Mini V3"
    assert arturia.resolve(conn, "Shared Name", installed={"mini v3"})["plugin"] == "Mini V3"
    with pytest.raises(ValueError, match="no Arturia preset called"):
        arturia.resolve(conn, "Nope")


def test_audition_spreads_candidates_across_instruments():
    from creaper import sound_tools
    found = [{"name": f"A{i}", "plugin": "Jup-8 V4"} for i in range(20)] + [{"name": "B0", "plugin": "Mini V3"},
                                                                            {"name": "B1", "plugin": "Mini V3"}]
    picked = sound_tools._by_plugin(found, 6)
    assert len(picked) == 6 and {p["plugin"] for p in picked} == {"Jup-8 V4", "Mini V3"}
    assert [p["name"] for p in picked if p["plugin"] == "Mini V3"] == ["B0", "B1"]


def test_load_arturia_preset_tool(db, tmp_path, monkeypatch):
    from creaper import music_tools, sound_tools
    preset_file = tmp_path / "Night Drive"
    preset_file.write_bytes(b"22 serialization::archive 10 0 7 0 7 11 Night Drive 7 Factory")
    monkeypatch.setattr(arturia, "resolve", lambda conn, preset, plugin=None, installed=None: {
        "name": "Night Drive", "plugin": "Jup-8 V4", "path": str(preset_file)})
    applied = {}

    def fake_call(cmd, **kw):
        if cmd == "list_installed_fx":
            return {"plugins": [{"name": "Jup-8 V4 (Arturia)", "load_as": "VST3i: Jup-8 V4 (Arturia)"}]}
        if cmd == "apply_fx_state":
            applied.update(kw)
            return {"restored": "full plugin state"}
        if cmd == "capture_fx_state":
            return {"plugin": "VST3i: Jup-8 V4 (Arturia)", "chunk": applied["state"]["chunk"]}
        raise AssertionError(cmd)

    monkeypatch.setattr(sound_tools, "call", fake_call)
    monkeypatch.setattr(music_tools, "audition_instrument", lambda **kw: {
        "summary": {"character": "warm"}, "warning": "held notes play a pattern of their own"})
    out = sound_tools.load_arturia_preset(track="Lead", preset="Night Drive")
    assert applied["state"]["plugin"] == "VST3i: Jup-8 V4 (Arturia)" and applied["replace_instrument"] is True
    assert out["confirmed"] is True and out["browser_path"] == "Jup-8 V4 > Factory > Night Drive"
    assert out["problems"] == ["held notes play a pattern of their own"]


def test_another_seed_draws_other_candidates():
    from creaper import sound_tools
    found = [{"name": f"A{i:02d}", "plugin": "Jup-8 V4"} for i in range(40)]
    first = [p["name"] for p in sound_tools._by_plugin([dict(p) for p in found], 5)]
    again = [p["name"] for p in sound_tools._by_plugin([dict(p) for p in found], 5)]
    other = [p["name"] for p in sound_tools._by_plugin([dict(p) for p in found], 5, seed=3)]
    assert first == again and set(first) != set(other)
