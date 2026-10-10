import json

import pytest

from creaper.sounds import SoundLibrary, describe, short_plugin_name

MINI = {
    "plugin": "VST3i: Mini V3 (Arturia)", "file": "mini v3.vst3", "format": "VST3", "instrument": True,
    "preset": "Program 1", "chunk": "QUJD" * 2000, "params": [{"index": 0, "name": "Cutoff", "value": 0.3}],
}
REACOMP = {
    "plugin": "VST: ReaComp (Cockos)", "file": "reacomp.dll", "format": "VST", "instrument": False,
    "preset": "stock - steady rock kick", "chunk": None, "params": [{"index": 0, "name": "Threshold", "value": 0.1}],
}


@pytest.fixture
def lib(tmp_path):
    return SoundLibrary(tmp_path / "sounds")


def test_save_find_and_restore_state(lib):
    entry = lib.save("Dark Pad", MINI, tags=["Pad", "dark", "pad"], description="Slow, warm, low-pass pad")
    assert entry["tags"] == ["pad", "dark"]
    assert entry["kind"] == "instrument" and entry["restore"] == "full plugin state"
    assert entry["plugin_name"] == "Mini V3"
    assert entry["plugin_preset"] is None  # "Program 1" placeholders aren't kept
    _, found = lib.find("dark pad")
    assert lib.state(found)["chunk"] == MINI["chunk"]
    # The big state lives in its own file, not the index.
    assert len(lib.index_path.read_text()) < 2000


def test_parameter_fallback_and_effects(lib):
    entry = lib.save("Kick Squash", REACOMP, tags=["drums"])
    assert entry["restore"] == "parameters" and entry["kind"] == "effect"
    assert entry["plugin_preset"] == "stock - steady rock kick"


def test_names_are_unique_unless_overwriting(lib):
    lib.save("Dark Pad", MINI)
    with pytest.raises(ValueError, match="already"):
        lib.save("dark pad", MINI)
    assert lib.save("Dark Pad", REACOMP, overwrite=True)["plugin_name"] == "ReaComp"


def test_search(lib):
    lib.save("Dark Pad", MINI, tags=["pad", "dark"])
    lib.save("Bright Pluck", MINI, tags=["pluck", "bright"], description="Short and glassy")
    lib.save("Kick Squash", REACOMP, tags=["drums"])
    assert [e["name"] for e in lib.search("pad")] == ["Dark Pad"]
    assert [e["name"] for e in lib.search("glassy")] == ["Bright Pluck"]
    assert [e["name"] for e in lib.search(tag="drums")] == ["Kick Squash"]
    assert [e["name"] for e in lib.search(kind="instrument")] == ["Bright Pluck", "Dark Pad"]
    assert [e["name"] for e in lib.search(plugin="reacomp")] == ["Kick Squash"]


def test_partial_names_must_be_unambiguous(lib):
    lib.save("Dark Pad", MINI)
    lib.save("Dark Bass", MINI)
    with pytest.raises(ValueError, match="several"):
        lib.find("dark")
    assert lib.find("bass")[1]["name"] == "Dark Bass"


def test_update_and_rename(lib):
    lib.save("Dark Pad", MINI, tags=["pad"])
    entry = lib.update("Dark Pad", new_name="Midnight Pad", add_tags=["Dark"], description="Moody")
    assert entry["name"] == "Midnight Pad" and entry["tags"] == ["pad", "dark"]
    assert lib.state(lib.find("midnight pad")[1])["chunk"] == MINI["chunk"]
    with pytest.raises(ValueError):
        lib.find("Dark Pad")


def test_delete_needs_exact_name(lib):
    entry = lib.save("Dark Pad", MINI)
    state_file = lib.folder / f"{entry['id']}.state.json"
    assert state_file.exists()
    with pytest.raises(ValueError, match="exact"):
        lib.delete("dark")
    lib.delete("Dark Pad")
    assert not state_file.exists() and lib.search() == []


def test_index_cant_point_outside_the_library(lib):
    lib.save("Dark Pad", MINI)
    data = json.loads(lib.index_path.read_text())
    data["sounds"]["dark pad"]["id"] = "../../evil"
    lib.index_path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="outside"):
        lib.state(lib.find("dark pad")[1])


def test_describe_and_short_names():
    assert short_plugin_name("VST3i: SILA (SILA) (18 out)") == "SILA"
    assert short_plugin_name("VSTi: ReaSynDr (Cockos) (4 out)") == "ReaSynDr"
    assert "id" not in describe({"id": "x", "name": "A", "tags": []})
