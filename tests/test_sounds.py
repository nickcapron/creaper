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


# ------------------------------------------------------------- whole FX chains

from creaper import server  # noqa: E402
from creaper.sounds import chain_has_instrument, chain_plugins, chain_summary, clean_chain  # noqa: E402

# A sampled guitar as a project file holds it: indented, with plugin ids, an open
# window and a parameter envelope from the song.
GUITAR_CHAIN = """    <FXCHAIN
      WNDRECT 0 0 0 0
      SHOW 2
      LASTSEL 0
      DOCKED 0
      BYPASS 0 0 0
      <VST "VSTi: ReaSamplOmatic5000 (Cockos)" reasamplomatic.dll 0 "C2 B1-D2" 1920167789<56535472736F6D72656173616D706C6F> ""
        bW9zcu5e7f4AAAAAAgAAAA==
      >
      FLOATPOS 0 0 0 0
      FXID {C6932472-11E8-4E78-A314-D2A9DF9FFA72}
      WAK 0 0
      BYPASS 0 0 0
      <VST "VSTi: ReaSamplOmatic5000 (Cockos)" reasamplomatic.dll 0 "E2 D#2-E2" 1920167789<56535472736F6D72656173616D706C6F> ""
        bW9zcu5e7f4AAAAAAgAAAB==
      >
      FLOAT 120 80 400 300
      FXID {0B9D53A8-ED94-4438-88B7-0D64861DD39D}
      <PARMENV 3:0 0 1 0.5
        ACT 1 -1
        PT 0 0.5 0
      >
      WAK 0 0
      BYPASS 0 0 0
      <JS loser/Saturation ""
        30 - - -
      >
      FXID {A1117ACF-D939-40FF-92AA-CC3875C79016}
      WAK 0 0
    >"""


def test_a_chain_is_cleaned_to_load_anywhere():
    chain = clean_chain(GUITAR_CHAIN)
    lines = chain.splitlines()
    assert lines[0] == "<FXCHAIN" and lines[-1] == ">"
    assert not any(line.startswith(("FXID", "FLOAT ", "<PARMENV", "PT ", "ACT ")) for line in lines)
    assert "SHOW 0" in lines and "FLOATPOS 0 0 0 0" in lines      # no window opens; positions stay
    assert "bW9zcu5e7f4AAAAAAgAAAB==" in lines                     # the plugins' state is untouched
    with pytest.raises(ValueError, match="FX chain"):
        clean_chain("<TRACK\nNAME x\n>")


def test_a_chain_names_its_plugins_in_order():
    plugins = chain_plugins(clean_chain(GUITAR_CHAIN))
    assert plugins == ["VSTi: ReaSamplOmatic5000 (Cockos)"] * 2 + ["JS: loser/Saturation"]
    assert chain_summary(plugins) == "ReaSamplOmatic5000 x2 + loser/Saturation"
    assert chain_has_instrument(plugins) and not chain_has_instrument(["JS: loser/Saturation"])


def test_a_chain_is_one_instrument_sound_found_by_its_plugins(lib):
    entry = lib.save_chain("Distorted Guitar", clean_chain(GUITAR_CHAIN), True, tags=["guitar"])
    assert entry["kind"] == "instrument" and entry["restore"] == "whole FX chain" and entry["plugins"] == 3
    assert [e["name"] for e in lib.search(plugin="reasamplomatic")] == ["Distorted Guitar"]
    assert [e["name"] for e in lib.search(kind="instrument")] == ["Distorted Guitar"]
    state = lib.state(entry)
    assert state["source"] == "chain" and state["chain"].startswith("<FXCHAIN")
    assert describe(entry)["plugin_name"] == "ReaSamplOmatic5000 x2 + loser/Saturation"
    with pytest.raises(ValueError, match="already"):
        lib.save_chain("distorted guitar", clean_chain(GUITAR_CHAIN), True)


@pytest.fixture
def library_bridge(lib, monkeypatch):
    calls = []

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "capture_fx_state":
            # a zone renamed after its sample, as an older bridge named it
            return {"plugin": "C2_s1_soft_01 B1-D2 v1-92", "file": "reasamplomatic.dll", "instrument": True,
                    "chunk": "x", "track": {"name": "Guitar"}}
        if command == "capture_fx_chain":
            return {"chain": GUITAR_CHAIN, "instrument": True, "track": {"name": "Guitar"}}
        if command == "apply_fx_chain":
            return {"track": {"name": args.get("new_track_name") or args["track"]}, "fx": ["a", "b"]}
        raise AssertionError(command)

    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(server, "sound_library", lib)
    return calls


def test_saving_a_sampled_instrument_keeps_the_whole_chain(library_bridge):
    result = server.save_sound(track="Guitar", name="Distorted Guitar", tags=["guitar"])
    assert result["restore"] == "whole FX chain" and "3 plugins" in result["note"]
    assert [c for c, _ in library_bridge] == ["capture_fx_state", "capture_fx_chain"]
    with pytest.raises(ValueError, match="leave fx out"):
        server.save_sound(track="Guitar", name="Other", fx=2, whole_chain=True)


def test_a_chain_loads_in_place_of_the_tracks_plugins(library_bridge):
    server.save_sound(track="Guitar", name="Distorted Guitar", whole_chain=True)
    result = server.load_sound("distorted guitar", new_track="Guitar 2")
    command, args = library_bridge[-1]
    assert command == "apply_fx_chain" and args["new_track_name"] == "Guitar 2"
    assert args["chain"].startswith("<FXCHAIN") and result["sound"] == "Distorted Guitar"
    assert "only 2 of the 3" in result["warning"]                       # one plugin isn't installed
    with pytest.raises(ValueError, match="new_track"):
        server.load_sound("distorted guitar", track="Guitar", replace_instrument=False)
