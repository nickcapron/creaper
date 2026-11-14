"""Hardware beyond the one synth creaper knows in depth: what a profile has to offer,
devices without a profile (played, heard, printed and measured all the same), a patch's
tempo following the project, and hardware parts in the song pipeline (printed, stale or
never). The fake REAPER and microKORG are test_hardware_sound's."""

import types
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
from test_hardware_sound import global_data, korg  # noqa: F401  (korg is the fixture)

from creaper import export_tools, hardware_profiles, mix_tools, song_tools
from creaper import hardware_sound_tools as hst
from creaper import hardware_tools as hw
from creaper import microkorg as mk

# ------------------------------------------------------------ the interface


def test_every_profile_has_the_whole_interface():
    assert {"read_request", "load_request", "write_request", "select_program", "click_patch", "READS_PATCH",
            "ACKS_LOAD", "PROGRAM_BYTES", "tempo_features", "with_tempo"} <= set(hardware_profiles.INTERFACE)
    for model, profile in hardware_profiles.PROFILES.items():
        missing = [name for name in hardware_profiles.INTERFACE if not hasattr(profile, name)]
        assert missing == [], f"{model} lacks {missing}"
        assert profile.MODEL == model


def test_scan_knows_a_model_from_its_profile():
    known = hw.KNOWN_MODELS[("42", 0x0058, 0x0011)]
    assert known["model"] == "Korg microKORG" and known["device_id_is_channel"] and "L/MONO" in known["setup"]


def test_the_generic_layer_names_no_function_codes():
    source = (hst.__file__, hw.__file__)
    for path in source:
        text = open(path, encoding="utf-8").read()
        assert "F_CURRENT" not in text and "F_WRITE" not in text and "F_LOAD" not in text and "import microkorg" not in text


def test_the_microkorg_selects_a_program_without_bank_select_and_writes_korgs_way():
    assert mk.select_program(1, 67) == ["C0 43"] and mk.select_program(16, 0) == ["CF 00"]
    messages, replies = mk.write_request(1, 9)
    assert messages == ["F0 42 30 58 11 00 09 F7"] and replies == {mk.F_WRITE_OK, mk.F_WRITE_ERROR}
    click = mk.decode_program(mk.click_patch(None))
    assert click["timbre1"]["eg2_attack"] == 0 and click["timbre1"]["eg2_sustain"] == 0 and click["name"] == "click"


# ------------------------------------------------- a device without a profile

@pytest.fixture
def wasp(korg):  # noqa: F811
    """A synth creaper has no profile for, on the same MIDI interface; the hardware part
    in the project plays it."""
    hw.save_hardware("Wasp", midi_output="UM-ONE", midi_input="UM-ONE", channel=2, audio_input=1, stereo=False,
                     model="EDP Wasp")
    korg.part_device = "Wasp"
    return korg


def test_a_device_without_a_profile_gets_its_track_pair(wasp):
    made = hst.create_hardware_track("Wasp", "Wasp Bass")
    params = next(p for c, p in wasp.commands if c == "create_hardware_tracks")
    assert params["device"] == "Wasp" and params["channel"] == 2 and params["midi_device"] == 1 and not params["stereo"]
    assert made["audio_track"]["name"] == "Wasp Bass" and "sets the sound on the synth" in made["next"]
    assert "load_hardware_sound" not in made["next"] and wasp.sent == []


def test_a_device_without_a_profile_is_heard_and_measured(wasp):
    result = hst.audition_hardware("Wasp", notes=[hst.PhraseNote(pitch=69, at=0, length=0.8)])
    start = next(p for c, p in wasp.commands if c == "hardware_take_start")
    assert start["scratch"] and start["channel"] == 2
    assert abs(result["notes"][0]["pitch_hz"] - 440) < 3 and "problem" not in result
    assert wasp.sent == []                                      # nothing is asked of a synth creaper doesn't know
    wasp.silent, wasp.noise_dbfs = True, -95.0
    problem = hst.audition_hardware("Wasp")["problem"]
    assert "the input is live but silent" in problem and "answers over MIDI" not in problem and wasp.sent == []


def test_a_device_without_a_profile_is_printed_with_the_sound_it_has(wasp):
    result = hst.print_hardware("MK Lead")
    assert result["device"] == "Wasp" and result["printed"]["name"] == "MK Lead"
    assert "no profile for Wasp" in result["warning"] and "load_hardware_sound" not in result["warning"]
    finish = next(p for c, p in wasp.commands if c == "hardware_take_finish")
    assert finish["mute_midi"] and finish["replace"] and wasp.sent == []


def test_a_sound_item_on_a_device_without_a_profile_is_not_played(wasp):
    wasp.patch_items.append({"name": "something", "sysex": "F0 7E 7F 06 01 F7"})
    with pytest.raises(ValueError, match="no profile for that synth to check it"):
        hst.print_hardware("MK Lead")
    assert not any(c == "hardware_take_start" for c, _ in wasp.commands) and wasp.sent == []


def test_latency_is_measured_on_a_device_without_a_profile_with_the_users_own_sound(wasp):
    wasp.tone_delay = 0.012
    result = hst.calibrate_hardware_latency("Wasp")
    assert abs(result["latency_ms"] - 12) < 1.5 and result["clicks_measured"] == 5 and result["saved"]
    assert hw._devices()["Wasp"]["latency_ms"] == result["latency_ms"]
    assert "slow attack" in result["measured_with"]
    assert wasp.sent == []                                      # no click loaded, nothing to put back
    asked = [a for a in wasp.asked if "latency" in a]
    assert len(asked) == 1 and "percussive" in asked[0] and "put back" not in asked[0]
    notes = next(p for c, p in wasp.commands if c == "hardware_take_start")["notes"]
    assert len(notes) == 5 and {n["length"] for n in notes} == {0.1}


@pytest.mark.parametrize("tool", [
    lambda: hst.set_hardware_params("Wasp", {"cutoff": 50}),
    lambda: hst.set_hardware_params("Wasp", {"cutoff": 50}, live=True),
    lambda: hst.load_hardware_sound("Wasp", recipe="laser zap"),
    lambda: hst.load_hardware_sound("Wasp", program="A.11"),
    lambda: hst.write_hardware_program("Wasp", "A.11"),
    lambda: hst.read_hardware_patch("Wasp"),
    lambda: hst.read_hardware_patch("Wasp", backups=True),
    lambda: hst.save_hardware_sound("Wasp", "Buzz"),
    lambda: hst.hardware_profile("Wasp"),
    lambda: hst.hardware_profile("Wasp", show="setup"),
], ids=["set", "set live", "load recipe", "load program", "write", "read", "backups", "save", "profile", "setup"])
def test_tools_that_need_a_profile_refuse_in_plain_words(wasp, tool):
    with pytest.raises(ValueError, match=r"no sound-design profile for Wasp \(EDP Wasp\), so it can't .*"
                                         "user sets the sound on the synth.*audition_hardware"):
        tool()
    assert wasp.sent == [] and wasp.asked == []                 # not a byte, not a question


def test_a_profile_that_cannot_read_or_confirm_is_loaded_on_trust(korg, monkeypatch):  # noqa: F811
    mute = types.SimpleNamespace(**{k: getattr(mk, k) for k in dir(mk) if not k.startswith("__")})
    mute.MODEL, mute.READS_PATCH, mute.ACKS_LOAD = "Mute Box", False, False
    monkeypatch.setitem(hst.PROFILES, "Mute Box", mute)
    hw.save_hardware("Box", midi_output="UM-ONE", midi_input="UM-ONE", audio_input=1, model="Mute Box")
    korg.answers = False                                        # it never says a word
    result = hst.load_hardware_sound("Box", recipe="laser zap", track="MK Lead", bar=3)
    assert result["loaded"] == "laser zap" and "undo" not in result
    assert [mk.parse_message(m)[0] for m in korg.sent] == [mk.F_CURRENT_DUMP]      # sent, never asked for
    assert korg.patch_items[0]["name"] == "laser zap" and hst._backups(hst._link("Box")) == []
    with pytest.raises(ValueError, match="can't send its current sound"):
        hst.read_hardware_patch("Box")
    korg.sent.clear()
    assert "program change" in hst.load_hardware_sound("Box", program="A.12")["note"] and korg.sent == ["C0 01"]
    with pytest.raises(ValueError, match="can't write one of its stored programs into the song"):
        hst.load_hardware_sound("Box", program="A.12", track="MK Lead", bar=3)
    korg.sent.clear()
    korg.tone_delay = 0.01
    assert "measured_with" in hst.calibrate_hardware_latency("Box") and korg.sent == []   # the user's sound, untouched


# --------------------------------------------------- a patch's tempo and the project's

def _tempo_in(korg_bridge):
    return mk.decode_program(korg_bridge.buffer)["common"]["arp_tempo"]


def test_what_runs_at_the_tempo_is_read_from_the_patch():
    init = mk.init_program()
    assert mk.tempo_features(init) == []
    assert mk.tempo_features(mk.apply(init, {"arp_on": "on"})) == ["arpeggiator"]
    assert mk.tempo_features(mk.apply(init, {"delay_sync": "on"})) == []           # a synced delay nobody hears
    assert mk.tempo_features(mk.apply(init, {"delay_sync": "on", "delay_depth": 40, "lfo2_tempo_sync": "on"})) == [
        "synced delay", "tempo-synced LFO"]
    layer = mk.apply(mk.apply(init, {"voice_mode": "layer"}), {"lfo1_tempo_sync": "on"}, timbre=2)
    assert mk.tempo_features(layer) == ["tempo-synced LFO"]
    assert mk.with_tempo(init, 97.4)[1] == 97 and mk.with_tempo(init, 12)[1] == 20 and mk.with_tempo(init, 999)[1] == 300
    assert mk.tempo(mk.with_tempo(init, 300)[0]) == 300


def test_a_sound_written_into_the_song_takes_the_tempo_at_its_bar(korg):  # noqa: F811
    korg.tempo = 97.0
    korg.tempo_changes = [{"position": {"bar": 1, "beat": 1}, "bpm": 97.0}, {"position": {"bar": 9, "beat": 1}, "bpm": 140.0}]
    result = hst.load_hardware_sound("microKORG", recipe="glide distortion lead", track="MK Lead", bar=3)
    assert result["tempo"]["patch_tempo_bpm"] == 97 and result["tempo"]["runs_at_the_tempo"] == ["synced delay"]
    assert "set to 97 BPM (it was 120)" in result["tempo"]["note"] and "at bar 3" in result["tempo"]["note"]
    assert "project's tempo changes" in result["tempo"]["note"]
    assert "own clock" in result["tempo"]["clock"]
    written = mk.patch_in_message(korg.patch_items[0]["sysex"])
    assert mk.tempo(written) == 97 and _tempo_in(korg) == 97           # the song's copy and the synth agree
    later = hst.load_hardware_sound("microKORG", recipe="glide distortion lead", track="MK Lead", bar=9)
    assert later["tempo"]["patch_tempo_bpm"] == 140 and mk.tempo(mk.patch_in_message(korg.patch_items[1]["sysex"])) == 140


def test_a_tempo_the_synth_cannot_hold_is_said_not_hidden(korg):  # noqa: F811
    korg.tempo = 97.5
    told = hst.load_hardware_sound("microKORG", recipe="pulse band-pass keys", track="MK Lead", bar=3)["tempo"]
    assert told["patch_tempo_bpm"] == 98 and "97.5 BPM" in told["note"] and "drift" in told["note"]
    korg.tempo = 400.0
    told = hst.load_hardware_sound("microKORG", recipe="pulse band-pass keys", track="MK Lead", bar=3)["tempo"]
    assert told["patch_tempo_bpm"] == 300 and "20 to 300" in told["note"]


def test_a_sound_loaded_live_takes_the_projects_opening_tempo(korg):  # noqa: F811
    korg.tempo = 88.0
    result = hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    assert result["tempo"]["patch_tempo_bpm"] == 88 and _tempo_in(korg) == 88 and "at bar" not in result["tempo"]["note"]


def test_a_sound_without_tempo_features_is_left_alone_and_nothing_is_asked(korg):  # noqa: F811
    korg.tempo = 97.0
    result = hst.load_hardware_sound("microKORG", recipe="laser zap", track="MK Lead", bar=3)
    assert "tempo" not in result and _tempo_in(korg) == 120
    assert not any(c == "get_tempo_map" for c, _ in korg.commands)


def test_a_recipe_with_a_speed_of_its_own_keeps_it(korg):  # noqa: F811
    korg.tempo = 97.0
    result = hst.load_hardware_sound("microKORG", recipe="power-up", track="MK Lead", bar=3)
    assert _tempo_in(korg) == 200 and result["tempo"]["patch_tempo_bpm"] == 200
    assert "Kept at its own tempo" in result["tempo"]["note"] and "arp_tempo" in result["tempo"]["note"]


def test_a_stored_program_is_played_at_the_projects_tempo_and_stays_as_stored(korg):  # noqa: F811
    korg.programs[5] = mk.apply(mk.init_program(name="arp"), {"arp_on": "on", "arp_tempo": 150})
    stored = korg.programs[5]
    korg.tempo = 97.0
    result = hst.load_hardware_sound("microKORG", program="A.16")
    assert result["tempo"]["patch_tempo_bpm"] == 97 and _tempo_in(korg) == 97
    assert korg.programs[5] == stored                           # only the edit buffer
    assert not any(mk.parse_message(m) and mk.parse_message(m)[0] == mk.F_WRITE_REQUEST for m in korg.sent)


def _key_sync(data):
    return mk.decode_program(data)["common"]["arp_key_sync"]


def test_an_arpeggio_written_into_the_song_starts_with_its_note(korg):  # noqa: F811
    # Live, 2026-11-13: with key sync off a printed arpeggio sat about 100 ms behind the bar.
    korg.programs[5] = mk.apply(mk.init_program(name="arp"), {"arp_on": "on", "arp_key_sync": "off"})
    korg.tempo = 97.0
    by_hand = hst.load_hardware_sound("microKORG", program="A.16")
    assert "arpeggiator" not in by_hand["tempo"] and _key_sync(korg.buffer) == "off"   # the user's patch, as it is
    told = hst.load_hardware_sound("microKORG", program="A.16", track="MK Lead", bar=3)["tempo"]
    assert "arp_key_sync was turned on" in told["arpeggiator"]
    assert _key_sync(mk.patch_in_message(korg.patch_items[0]["sysex"])) == "on" and _key_sync(korg.buffer) == "on"
    assert _key_sync(korg.programs[5]) == "off"                                        # the stored program too
    again = hst.load_hardware_sound("microKORG", backup=1, track="MK Lead", bar=5)["tempo"]
    assert "arpeggiator" in again                                                      # a backup going into the song
    plain = mk.init_program()
    assert mk.start_on_the_note(plain) == (plain, None)                                # no arpeggio: nothing to do
    assert _key_sync(mk.build(mk.find_recipe("power-up")[1])) == "on"                  # creaper's own arpeggios


def test_a_backup_comes_back_exactly_as_it_was(korg):  # noqa: F811
    hst.set_hardware_params("microKORG", {"arp_on": "on", "arp_tempo": 133})
    mine = korg.buffer
    korg.tempo = 97.0
    hst.load_hardware_sound("microKORG", recipe="laser zap")
    result = hst.load_hardware_sound("microKORG", backup=1)
    assert korg.buffer == mine and "comes back exactly" in result["tempo"]["note"]


@pytest.mark.parametrize("clock, said", [("external", "Send clock/SPP"), ("auto", "unless MIDI clock arrives"),
                                         ("internal", "own clock")])
def test_the_synths_clock_setting_is_read_and_explained(korg, clock, said):  # noqa: F811
    korg.globals = global_data(clock=clock)
    told = hst.load_hardware_sound("microKORG", recipe="glide distortion lead", track="MK Lead", bar=3)["tempo"]
    assert said in told["clock"]
    if clock == "external":
        assert "ignores the patch's tempo" in told["clock"] and "Internal" in told["clock"]


def test_a_tempo_that_cannot_be_read_leaves_the_patch_alone(korg, monkeypatch):  # noqa: F811
    from creaper.bridge import BridgeError
    real = korg.call

    def no_tempo(cmd, params=None, **kw):
        if cmd == "get_tempo_map":
            raise BridgeError("this bridge doesn't know 'get_tempo_map'")
        return real(cmd, params, **kw)
    monkeypatch.setattr(korg, "call", no_tempo)
    told = hst.load_hardware_sound("microKORG", recipe="glide distortion lead")["tempo"]
    assert told["patch_tempo_bpm"] == 120 and "couldn't be read" in told["note"]


# ------------------------------------------- the bridge's guards (Lua, read as text)

BRIDGE_LUA = (Path(hst.__file__).parent / "reaper" / "creaper_bridge.lua").read_text(encoding="utf-8")


def _lua(start, end="\nend\n"):
    return BRIDGE_LUA.split(start)[1].split(end)[0]


def test_a_midi_output_a_track_cannot_hold_is_refused():
    check = _lua("function hws.check_output(device)")
    assert "if device > hws.MAX_MIDI_OUTPUT then" in check and "hws.MAX_MIDI_OUTPUT = 31" in BRIDGE_LUA
    assert check.index("hws.MAX_MIDI_OUTPUT") < check.index("return device")
    assert "device > hws.MAX_MIDI_OUTPUT then fail(" in _lua("local function hw_set_output(t, device, channel)")


def test_send_modes_are_declared_once():
    assert BRIDGE_LUA.count("local SEND_MODES =") == 1
    assert BRIDGE_LUA.index("local SEND_MODES =") < BRIDGE_LUA.index("local function send_info(")
    assert BRIDGE_LUA.index("local SEND_MODES =") < BRIDGE_LUA.index("local function channel_text(")


def test_the_audio_page_number_is_only_used_where_it_was_seen():
    prefs = _lua("function commands.hardware_open_prefs(p)")
    assert "reaper.ViewPrefs and hws.version_at_least(hws.AUDIO_PAGE_SINCE)" in prefs
    assert "reaper.ViewPrefs(hws.AUDIO_PAGE, \"\")" in prefs and "ViewPrefs(118" not in BRIDGE_LUA
    assert "reaper.Main_OnCommand(40099, 0)" in prefs            # older REAPER: the audio device window
    assert "hws.AUDIO_PAGE = 118" in BRIDGE_LUA and "hws.AUDIO_PAGE_SINCE = 7.85" in BRIDGE_LUA
    # The MIDI pages too: by number, on the REAPER they were seen on; a page name does nothing there.
    assert "hws.MIDI_PAGES = { midi_outputs = 620, midi_inputs = 153 }" in BRIDGE_LUA
    assert 'ViewPrefs(0, "MIDI Devices")' not in BRIDGE_LUA and "reaper.ViewPrefs(midi_page, \"\")" in prefs


def test_a_print_is_remembered_by_what_it_was_made_from():
    finish = _lua("function commands.hardware_take_finish(p)", "\nend\n\n")
    assert 'if midi and #items > 0 and p.mute_midi then hw_ext(midi, "printed", hws.part_hash(midi)) end' in finish
    assert finish.index("take.item_mutes or {}") < finish.index("hws.part_hash(midi)")   # after the items are unmuted
    printed = _lua("function hws.printed(midi, audio)")
    assert '"never"' in printed and '"yes" or "stale"' in printed
    assert "flags & ~1" in _lua("function hws.part_hash(midi)")  # selecting a note isn't an edit
    assert "printed = hws.printed(midi, audio)" in _lua("function commands.hardware_tracks(p)")
    overview = _lua("function commands.get_project_overview()\n  local out = hws.plain_overview()")
    assert "summary.hardware = {" in overview and "printed = midi and hws.printed(midi, audio)" in overview


# ------------------------------------------- hardware parts in the song pipeline

def test_unprinted_and_stale_parts_are_named_in_one_sentence(korg):  # noqa: F811
    assert "MK Lead has never been printed" in hw.unprinted_warning()
    korg.printed = "stale"
    warning = hw.unprinted_warning()
    assert "MK Lead changed after it was printed" in warning and "print_hardware it before mixing" in warning
    assert "won't hear it" in warning
    korg.printed = "yes"
    assert hw.unprinted_warning() is None
    korg.printed, korg.parts = "never", []
    assert hw.unprinted_warning() is None                       # an empty pair has nothing to print
    korg.parts, korg.printed = [{"id": "{P1}"}], None
    assert hw.unprinted_warning() is None                       # a bridge from before prints were tracked


def test_several_parts_are_grouped_by_what_is_wrong():
    pairs = [{"audio_track": {"name": "MK Lead"}, "printed": "stale", "parts": [1]},
             {"audio_track": {"name": "MK Bass"}, "printed": "never", "parts": [1]},
             {"audio_track": {"name": "Zap"}, "printed": "never", "parts": [1]},
             {"audio_track": {"name": "MK Pad"}, "printed": "yes", "parts": [1]}]
    warning = hw.unprinted_warning(lambda cmd: {"hardware_tracks": pairs})
    assert "MK Lead changed after it was printed; MK Bass, Zap have never been printed" in warning
    assert "print_hardware each" in warning and "MK Pad" not in warning


def test_a_project_without_hardware_or_a_bridge_that_cannot_say_costs_nothing():
    def broken(cmd):
        raise AssertionError(cmd)
    assert hw.unprinted_warning(lambda cmd: {"hardware_tracks": []}) is None
    assert hw.unprinted_warning(lambda cmd: {}) is None
    assert hw.unprinted_warning(broken) is None


STALE = {"hardware_tracks": [{"audio_track": {"name": "MK Lead"}, "printed": "stale", "parts": [1]}]}


def test_auto_mix_warns_about_a_stale_hardware_part_and_carries_on(monkeypatch):
    channels = [{"name": "MK Lead", "track": 1, "ref": "{V}"}, {"name": "Pad", "track": 2, "ref": "{H}"}]
    monkeypatch.setattr(mix_tools, "_channels", lambda: [dict(c) for c in channels])
    monkeypatch.setattr(mix_tools, "call", lambda cmd, **kw: STALE if cmd == "hardware_tracks" else {"stems": [], "files": []})
    report = mix_tools.auto_mix(dry_run=True)
    assert len(report["warnings"]) == 1 and "MK Lead changed after it was printed" in report["warnings"][0]
    assert report["plan"]                                       # it warned; it didn't refuse


def test_export_mix_warns_about_a_stale_hardware_part_and_still_exports(monkeypatch, tmp_path):
    fs = 44100
    t = np.arange(4 * fs) / fs
    x = 0.3 * np.sin(2 * np.pi * 220 * t)
    renders = tmp_path / "renders"
    renders.mkdir()
    monkeypatch.setattr(export_tools.bridge, "directory", tmp_path)

    def fake_call(cmd, **kw):
        if cmd == "render_audio":
            f = renders / "r.wav"
            sf.write(str(f), np.stack([x, x], axis=1), fs, subtype="FLOAT")
            return {"files": [str(f)]}
        if cmd == "hardware_tracks":
            return STALE
        raise AssertionError(cmd)
    monkeypatch.setattr(export_tools, "call", fake_call)
    monkeypatch.setattr(export_tools, "_project_info", lambda: {"path": None, "name": "song"})
    done = export_tools.export_mix(folder=str(tmp_path / "out"))
    assert (tmp_path / "out" / "song.wav").exists()
    assert [n for n in done["notes"] if "MK Lead changed after it was printed" in n]


def test_finish_stage_warns_about_a_stale_hardware_part_from_the_parts_stage_on(monkeypatch, tmp_path):
    monkeypatch.setattr(song_tools, "_plan", lambda: ({"genre": None}, tmp_path / "plan.json"))
    monkeypatch.setattr(song_tools, "_Context", lambda *a: types.SimpleNamespace(overview={"tracks": []}))
    monkeypatch.setattr(song_tools, "_rows_for", lambda stage, ctx: [])
    asked = []
    monkeypatch.setattr(song_tools, "call", lambda cmd, **kw: asked.append(cmd) or STALE)
    done = song_tools.finish_stage(stage="parts")
    assert done["done"] and "MK Lead changed after it was printed" in done["hardware_warning"]
    assert "hardware_warning" not in song_tools.finish_stage(stage="form") and asked == ["hardware_tracks"]


def test_a_discarded_recording_takes_its_peaks_with_it(tmp_path):
    # Live, 2026-11-13: every audition left a .reapeaks in REAPER's "peaks" folder.
    wav = tmp_path / "02-creaper hardware scratch.wav"
    beside, in_folder = tmp_path / (wav.name + ".reapeaks"), tmp_path / "peaks" / (wav.name + ".reapeaks")
    in_folder.parent.mkdir()
    for f in (wav, beside, in_folder):
        f.write_bytes(b"x")
    other = in_folder.with_name("song.wav.reapeaks")
    other.write_bytes(b"x")
    hst._discard(str(wav))
    assert not wav.exists() and not beside.exists() and not in_folder.exists() and other.exists()


def test_the_level_check_says_which_knob_and_how_far():
    # Live, 2026-11-13: a whole song printed with input 1 thirty dB under input 2 (one ear only).
    advice = hst.level_advice([-45.6, -24.9], 1, "microKORG")
    assert "Input 1 gets next to nothing" in advice[0] and "L/MONO" in advice[0] and "LINE" in advice[0]
    assert "Input 2 is low (peak -25 dBFS): turn its gain up about 9 dB" in advice[1]
    assert hst.level_advice([-15.5, -16.5], 1, "microKORG") == []                   # the user's fourth round: good
    assert hst.level_advice([-13.0, -12.2], 1, "microKORG") == []                      # in the window, matched
    assert hst.level_advice([-11.6, -12.8], 1, "microKORG") == []       # half a dB over: nobody is sent to the knob
    assert "Input 3 is 3 dB under the other" in hst.level_advice([-17.0, -14.0], 3, "x")[0]
    # Live: with the test sound at -12.6 a distorted lead printed at -5.5. -9 leaves it no room.
    assert "Input 1 is hot" in hst.level_advice([-9.0, -9.5], 1, "x")[0]
    assert "clips" in hst.level_advice([0.0, -9.0], 1, "x")[0]
    assert "turn its gain down about 13 dB" in hst.level_advice([-3.0], 1, "x")[0]   # one input: a mono synth
    quiet = hst.level_advice([-40.0, -41.0], 1, "microKORG")
    assert "volume knob" in quiet[0] and "Input 1 is low" in quiet[1]


def test_a_one_sided_recording_is_called_that(korg):  # noqa: F811
    import numpy as np
    link = hst._link("microKORG")
    link.device["stereo"] = True
    audio = np.zeros((4800, 2), dtype="float32")
    audio[:, 0], audio[:, 1] = 0.005, 0.2
    assert "one-sided" in hst._level_problem(audio, link) and "action='level'" in hst._level_problem(audio, link)
    audio[:, 0] = 0.15
    assert hst._level_problem(audio, link) is None
