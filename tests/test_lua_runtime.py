"""The bridge's Lua, run for real (Lua 5.4 through lupa, a fake `reaper` table): the
hardware state a mistake would cost the user something in. Settings changed for a
hardware session go back; a recording pass leaves the tracks as it found them, also when
nobody comes back to finish it; SysEx never reaches a synth from an imported MIDI file;
and a closed audio device (Audio_IsRunning() == 0, which is true in Lua) counts as closed."""

import os

import pytest

if os.environ.get("CI"):
    import lupa.lua54  # noqa: F401  in CI a missing lupa is a failure, not a quiet skip
else:
    pytest.importorskip("lupa.lua54", reason="the Lua runtime tests need lupa (pip install -e '.[dev]')")

from lua_harness import BridgeError, Rig  # noqa: E402


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


@pytest.fixture
def bridge(rig):
    return rig.start_bridge()


def names(rig):
    return [t.name for t in rig.f.tracks.values()]


def value(rig, track, key):
    return rig.f.track(track).v[key]


def items(rig, track):
    return list(rig.f.track(track)["items"].values())    # ["items"]: .items is the Lua table's own method


def settings(rig):
    return {key: rig.f.config[key] for key in ("promptendrec", "audiocloseinactive")}


# ------------------------------------------------------------------- the harness itself

def test_the_bridge_loads_and_answers_without_starting_its_loop(rig, bridge):
    assert bridge.call("ping")["reaper_version"] == "7.85/fake"
    with pytest.raises(BridgeError, match="doesn't know 'no_such_command'"):
        bridge.call("no_such_command")


def test_a_function_the_fake_lacks_fails_loudly(rig, bridge):
    with pytest.raises(BridgeError, match=r"fake reaper has no '\w+'") as failure:
        bridge.call("project_state")
    assert failure.value.traceback                       # a bug, not a fail(): it has a traceback


# ------------------------------------------------------------ the audio device's state

@pytest.mark.parametrize("answer, running", [(0, False), (0.0, False), (1, True), (1.0, True),
                                             (False, False), (True, True)])
def test_audio_is_running_compares_the_answer(rig, bridge, answer, running):
    rig.f.audio.answer = answer                          # 0 is true in Lua: it has to be compared
    assert bridge.parts.audio_is_running() is running


def test_a_closed_device_is_reported_closed_and_opened_when_asked(rig, bridge):
    rig.f.audio.running = False
    status = bridge.call("hardware_status")
    assert status["audio"]["running"] is False and rig.f.audio.opened == 0
    sent = bridge.call("send_midi", device=0, messages=["90 3C 64"], open_audio=True)
    assert rig.f.audio.opened == 1 and sent == {"device": 0, "sent": 1, "audio_running": True}
    bridge.call("send_midi", device=0, messages=["80 3C 00"], open_audio=True)
    assert rig.f.audio.opened == 1                       # already open: not opened again


def test_no_take_starts_on_a_device_that_will_not_open(rig, bridge):
    rig.f.audio.running, rig.f.audio.can_open = False, False
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    with pytest.raises(BridgeError, match="audio device is closed and wouldn't open"):
        bridge.call("hardware_take_start", scratch=True, midi_device=0, audio_input=1)
    assert names(rig) == ["Vocals"] and value(rig, "Vocals", "I_RECARM") == 1
    assert list(rig.f.actions.values()) == []            # record was never pressed


# ------------------------------------------------------- 1. the hardware session's settings

def test_a_session_turns_the_two_settings_off_and_end_puts_them_back(rig, bridge):
    rig.f.config["promptendrec"] = "3"                   # other bits of the setting are the user's
    begun = bridge.call("hardware_status", session="begin")["settings"]
    assert settings(rig) == {"promptendrec": "2", "audiocloseinactive": "0"}
    assert begun["promptendrec"] is False and begun["audiocloseinactive"] is False and begun["can_change"] is True
    assert begun["changed_for_session"] == {"promptendrec": 3, "audiocloseinactive": 1}
    saved = rig.f.ext["creaper/hw_session"]
    assert saved[1] == "promptendrec=3;audiocloseinactive=1" and saved[2] is True   # kept across a crash

    ended = bridge.call("hardware_status", session="end")
    assert settings(rig) == {"promptendrec": "3", "audiocloseinactive": "1"}
    assert ended["restored"] == {"promptendrec": True, "audiocloseinactive": True}
    assert ended["settings"].get("changed_for_session") is None and rig.f.ext_value("creaper", "hw_session") == ""
    assert bridge.call("hardware_status", session="end").get("restored") is None    # nothing left to put back


def test_beginning_twice_keeps_the_users_originals(rig, bridge):
    bridge.call("hardware_status", session="begin")
    bridge.call("hardware_status", session="begin")      # the settings read 0 now: not the originals
    assert rig.f.ext_value("creaper", "hw_session") == "promptendrec=1;audiocloseinactive=1"
    bridge.call("hardware_status", session="end")
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}


def test_a_setting_the_user_had_off_stays_off(rig, bridge):
    rig.f.config["audiocloseinactive"] = "0"
    bridge.call("hardware_status", session="begin")
    assert rig.f.ext_value("creaper", "hw_session") == "promptendrec=1"
    assert bridge.call("hardware_status", session="end")["restored"] == {"promptendrec": True}
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "0"}


def test_nothing_is_on_record_when_reaper_refuses_the_change(rig, bridge):
    rig.f.config_refused = True
    bridge.call("hardware_status", session="begin")
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}
    assert rig.f.ext_value("creaper", "hw_session") == ""


def test_an_older_reaper_is_left_alone(rig):
    rig.f.without("set_config_var_string")               # before REAPER 7.74
    bridge = rig.start_bridge()
    status = bridge.call("hardware_status", session="begin")["settings"]
    assert status["can_change"] is False and status["promptendrec"] is True
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}
    assert rig.f.ext_value("creaper", "hw_session") == ""


def test_the_settings_go_back_when_the_bridge_stops(rig, bridge):
    bridge.call("hardware_status", session="begin")
    rig.f.run_atexit()
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}
    assert rig.f.ext_value("creaper", "hw_session") == ""


def test_a_bridge_that_starts_after_a_crash_puts_them_back(rig, bridge):
    bridge.call("hardware_status", session="begin")
    assert settings(rig) == {"promptendrec": "0", "audiocloseinactive": "0"}
    rig.start_bridge()                                   # the first one never ran its atexit
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}
    assert rig.f.ext_value("creaper", "hw_session") == ""


def test_the_settings_go_back_after_half_an_hour_without_hardware_work(rig, bridge):
    bridge.call("hardware_status", session="begin")
    rig.f.now += bridge.hws.SESSION_IDLE_S - 1
    bridge.step()
    assert settings(rig) == {"promptendrec": "0", "audiocloseinactive": "0"}
    rig.f.now += 2
    rig.f.play_state = 5                                 # a recording is running: not in the middle of it
    bridge.step()
    assert settings(rig) == {"promptendrec": "0", "audiocloseinactive": "0"}
    rig.f.play_state = 0
    bridge.step()
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}


def test_only_the_two_session_settings_are_ever_put_back(rig, bridge):
    # The record is a line in an .ini file anyone could have edited.
    rig.f.config["autosaveint"] = "15"
    rig.f.config["audiocloseinactive"] = "0"
    rig.f.ext["creaper/hw_session"] = rig.table(["audiocloseinactive=1;autosaveint=99;defsavepath=7", True])
    assert bridge.call("hardware_status", session="end")["restored"] == {"audiocloseinactive": True}
    assert rig.f.config["audiocloseinactive"] == "1"
    assert rig.f.config["autosaveint"] == "15" and rig.f.config["defsavepath"] == ""


# --------------------------------------------------------- 2. a recording pass (a take)

def scratch_take(bridge, **more):
    return bridge.call("hardware_take_start", scratch=True, midi_device=0, audio_input=1, seconds=3,
                       notes=[{"at": 0, "length": 1, "pitch": 60}], **more)


def test_a_scratch_take_arms_only_its_own_track_and_cleans_up(rig, bridge):
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    rig.f.new_track("Bass")
    rig.f.cursor = 1.5
    started = scratch_take(bridge)
    assert started["recording"] is True and (started["start_seconds"], started["end_seconds"]) == (2, 5)
    assert names(rig) == ["Vocals", "Bass", "creaper hardware scratch (MIDI)", "creaper hardware scratch"]
    assert value(rig, "Vocals", "I_RECARM") == 0 and value(rig, "Bass", "I_RECARM") == 0
    assert value(rig, "creaper hardware scratch", "I_RECARM") == 1
    assert value(rig, "creaper hardware scratch (MIDI)", "I_RECARM") == 0
    assert value(rig, "creaper hardware scratch (MIDI)", "I_MIDIHWOUT") == 0      # device 0, all channels
    assert len(items(rig, "creaper hardware scratch (MIDI)")[0].takes[1].notes) == 1
    assert list(rig.f.actions.values()) == [1013] and rig.f.cursor == 2

    rig.f.play_position = 5.0
    finished = bridge.call("hardware_take_finish")
    assert finished["scratch"] is True and len(finished["items"]) == 1
    assert finished["items"][0]["file"] == "take.wav" and finished["items"][0]["file_starts_at_seconds"] == 0
    assert names(rig) == ["Vocals", "Bass"]              # the scratch tracks are gone
    assert value(rig, "Vocals", "I_RECARM") == 1 and value(rig, "Bass", "I_RECARM") == 0
    assert rig.f.play_state == 0 and rig.f.cursor == 1.5
    assert items(rig, "Vocals") == []         # disarmed for the pass: nothing recorded on it
    with pytest.raises(BridgeError, match="no hardware recording is under way"):
        bridge.call("hardware_take_finish")


def hardware_part(rig, bridge):
    """A hardware part (two tracks) among other tracks: one armed, one playing the same synth
    (device 0), one playing another (device 1)."""
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    rig.f.new_track("Same synth", rig.table({"I_MIDIHWOUT": 3}))
    rig.f.new_track("Other synth", rig.table({"I_MIDIHWOUT": (1 << 5) | 1}))
    rig.f.midi_outputs[1] = "Other synth"
    made = bridge.call("create_hardware_tracks", name="MK Lead", device="microKORG", midi_device=0, channel=1,
                       audio_input=1, stereo=True)
    assert made["midi_track"]["name"] == "MK Lead (MIDI)" and made["audio_track"]["name"] == "MK Lead"
    assert value(rig, "MK Lead (MIDI)", "I_MIDIHWOUT") == 1 and value(rig, "MK Lead", "I_RECINPUT") == 1024


def test_a_print_take_mutes_the_synths_other_tracks_and_puts_everything_back(rig, bridge):
    hardware_part(rig, bridge)
    midi, audio = rig.f.track("MK Lead (MIDI)"), rig.f.track("MK Lead")
    midi.v["B_MUTE"] = 1                                 # muted after an earlier print
    sound = rig.f.new_midi_item(midi, 3.5, 0.5, rig.table({"sysex": 1}))
    under = rig.f.new_audio_item(audio, 4.0, 4.0)        # an older print of the same stretch
    before = rig.f.new_audio_item(audio, 0.0, 2.0)       # and one from earlier in the song

    started = bridge.call("hardware_take_start", track="MK Lead", start_seconds=4, end_seconds=8,
                          mute_items=[sound.guid])
    assert started["recording"] is True
    assert midi.v["B_MUTE"] == 0 and audio.v["I_RECARM"] == 1
    assert value(rig, "Same synth", "B_MUTE") == 1 and value(rig, "Other synth", "B_MUTE") == 0
    assert value(rig, "Vocals", "I_RECARM") == 0 and sound.v["B_MUTE"] == 1

    rig.f.play_position = 8.0
    finished = bridge.call("hardware_take_finish", mute_midi=True, replace=True, take_name="MK Lead print",
                           latency_seconds=0.25)
    assert finished["scratch"] is False and len(finished["items"]) == 1
    assert finished["items"][0]["length_seconds"] == 3.75          # the device's latency is skipped
    left = {item.guid: item for item in items(rig, "MK Lead")}   # Lua tables: compared by GUID
    assert under.guid not in left and before.guid in left and len(left) == 2  # the new print replaced the old one
    new = [item for guid, item in left.items() if guid != before.guid][0]
    assert new.takes[1].name == "MK Lead print" and new.takes[1].v["D_STARTOFFS"] == 0.25
    assert midi.v["B_MUTE"] == 1                         # printed: the synth doesn't play over its recording
    assert audio.v["I_RECARM"] == 0 and value(rig, "Vocals", "I_RECARM") == 1
    assert value(rig, "Same synth", "B_MUTE") == 0 and sound.v["B_MUTE"] == 0
    assert names(rig) == ["Vocals", "Same synth", "Other synth", "MK Lead (MIDI)", "MK Lead"]


def test_a_print_take_leaves_the_midi_track_as_it_was_unless_asked(rig, bridge):
    hardware_part(rig, bridge)
    rig.f.track("Same synth").v["B_MUTE"] = 1            # the user's own mute
    bridge.call("hardware_take_start", track="MK Lead", start_seconds=4, end_seconds=8)
    bridge.call("hardware_take_finish")
    assert value(rig, "MK Lead (MIDI)", "B_MUTE") == 0 and value(rig, "Same synth", "B_MUTE") == 1


def test_a_second_take_waits_for_the_first(rig, bridge):
    scratch_take(bridge)
    with pytest.raises(BridgeError, match="already under way") as refused:
        scratch_take(bridge)
    assert "hardware_take_finish" not in refused.value.message      # a command Claude can't call
    assert len(names(rig)) == 2


def test_a_take_nobody_finished_is_finished_by_the_bridge(rig, bridge):
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    bridge.call("hardware_status", session="begin")
    scratch_take(bridge)                                 # ...and the server is killed: no finish comes
    rig.f.play_position = 5.1
    bridge.step()                                        # the pass reaches its end: the bridge stops REAPER
    assert rig.f.play_state == 0 and len(names(rig)) == 3

    rig.f.now += bridge.hws.TAKE_GRACE_S - 1
    bridge.step()
    assert len(names(rig)) == 3 and value(rig, "Vocals", "I_RECARM") == 0    # still the caller's to collect
    rig.f.now += 2
    bridge.step()
    assert names(rig) == ["Vocals"] and value(rig, "Vocals", "I_RECARM") == 1
    assert settings(rig) == {"promptendrec": "0", "audiocloseinactive": "0"}  # the session goes on

    rig.f.now += bridge.hws.SESSION_IDLE_S + 1
    bridge.step()
    assert settings(rig) == {"promptendrec": "1", "audiocloseinactive": "1"}
    assert rig.f.ext_value("creaper", "hw_session") == ""


def test_an_abandoned_print_take_unmutes_and_rearms(rig, bridge):
    hardware_part(rig, bridge)
    bridge.call("hardware_take_start", track="MK Lead", start_seconds=4, end_seconds=8)
    rig.lua.globals().reaper.OnStopButton()              # the user stopped REAPER themselves
    bridge.step()                                        # the grace period counts from the tick that sees it
    rig.f.now += bridge.hws.TAKE_GRACE_S + 1
    bridge.step()
    assert value(rig, "Vocals", "I_RECARM") == 1 and value(rig, "MK Lead", "I_RECARM") == 0
    assert value(rig, "Same synth", "B_MUTE") == 0 and value(rig, "MK Lead (MIDI)", "B_MUTE") == 0
    assert len(items(rig, "MK Lead")) == 1        # what was recorded is kept


def test_a_recording_that_runs_past_its_end_is_stopped(rig, bridge):
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    scratch_take(bridge)
    rig.f.now += 3 + bridge.hws.TAKE_OVERRUN_S - 1
    bridge.step()
    assert rig.f.play_state == 5 and len(names(rig)) == 3
    rig.f.now += 2
    bridge.step()
    assert rig.f.play_state == 0 and names(rig) == ["Vocals"] and value(rig, "Vocals", "I_RECARM") == 1


def test_the_next_take_finishes_an_abandoned_one_first(rig, bridge):
    rig.f.new_track("Vocals", rig.table({"I_RECARM": 1}))
    scratch_take(bridge)
    rig.lua.globals().reaper.OnStopButton()
    bridge.step()
    rig.f.now += bridge.hws.TAKE_GRACE_S + 1             # no tick since: the next start does it
    scratch_take(bridge)
    assert names(rig) == ["Vocals", "creaper hardware scratch (MIDI)", "creaper hardware scratch"]
    bridge.call("hardware_take_finish")
    assert names(rig) == ["Vocals"] and value(rig, "Vocals", "I_RECARM") == 1


def test_a_take_that_cannot_be_finished_does_not_block_the_next(rig, bridge):
    scratch_take(bridge)
    rig.lua.globals().reaper.OnStopButton()
    bridge.step()
    rig.f.raise_in["DeleteTrack"] = True                 # REAPER fails in the middle of the clean-up
    rig.f.now += bridge.hws.TAKE_GRACE_S + 1
    bridge.step()
    rig.f.raise_in["DeleteTrack"] = None
    assert scratch_take(bridge)["recording"] is True


# ------------------------------------------------- 3. SysEx in an imported MIDI file

SONG = "C:/x/song.mid"


def import_song(rig, bridge, track):
    rig.f.media[SONG] = rig.table({"notes": 3, "sysex": 2, "text": 1})
    rig.f.cursor = 6.0
    return bridge.call("insert_audio_file", path=SONG, track=track, start_bar=2)


def test_sysex_is_stripped_from_midi_imported_onto_a_hardware_track(rig, bridge):
    track = rig.f.new_track("Synth", rig.table({"I_MIDIHWOUT": 0}))
    info = import_song(rig, bridge, "Synth")
    item = items(rig, "Synth")[0]
    assert info["sysex_removed"] == 2 and info["note_count"] == 3 and info["start"]["bar"] == 2
    assert rig.f.sysex_count(item) == 0
    assert [e.kind for e in item.takes[1].events.values()] == [1]   # the text event stays
    assert len(item.takes[1].notes) == 3 and rig.f.cursor == 6.0


def test_sysex_is_stripped_on_a_hardware_parts_track_too(rig, bridge):
    rig.f.new_track("Vocals")
    made = bridge.call("create_hardware_tracks", name="MK", device="microKORG", midi_device=0, audio_input=1)
    midi = rig.f.track(made["midi_track"]["name"])
    midi.v["I_MIDIHWOUT"] = -1                           # the user took the output off: still a hardware part
    assert import_song(rig, bridge, "MK (MIDI)")["sysex_removed"] == 2
    assert rig.f.sysex_count(items(rig, "MK (MIDI)")[0]) == 0


def test_sysex_stays_on_a_track_that_plays_no_hardware(rig, bridge):
    track = rig.f.new_track("Piano")
    info = import_song(rig, bridge, "Piano")
    assert "sysex_removed" not in info and rig.f.sysex_count(items(rig, "Piano")[0]) == 2


def test_a_file_whose_sysex_cannot_be_removed_is_not_imported(rig, bridge):
    track = rig.f.new_track("Synth", rig.table({"I_MIDIHWOUT": 0}))
    kept = rig.f.new_midi_item(track, 0.0, 2.0, rig.table({"notes": 1}))
    rig.f.sysex_stuck = True
    with pytest.raises(BridgeError, match="not imported: .* holds SysEx messages"):
        import_song(rig, bridge, "Synth")
    assert [item.guid for item in items(rig, "Synth")] == [kept.guid] and rig.f.cursor == 6.0


def test_strip_sysex_counts_every_take_of_an_item(rig, bridge):
    track = rig.f.new_track("Synth", rig.table({"I_MIDIHWOUT": 0}))
    item = rig.f.new_midi_item(track, 0.0, 2.0, rig.table({"sysex": 2, "text": 1, "notes": 4}))
    assert tuple(bridge.hws.strip_sysex(item)) == (2, 0)
    assert tuple(bridge.hws.strip_sysex(item)) == (0, 0) and len(item.takes[1].notes) == 4


def test_a_sound_written_into_the_song_keeps_its_sysex_and_is_reported(rig, bridge):
    rig.f.new_track("Vocals")
    bridge.call("create_hardware_tracks", name="MK", device="microKORG", midi_device=0, audio_input=1)
    bridge.call("hardware_patch_item", track="MK", name="Pad", sysex="F0 42 30 58 F7", start_bar=3)
    part = bridge.call("hardware_tracks")["hardware_tracks"][0]
    assert part["sounds"][0]["sysex_count"] == 1 and part["sounds"][0]["sysex_events"] == ["F0423058F7"]
    assert part["sounds"][0]["sound"] == "Pad" and part["sounds"][0]["sysex"] == "F0423058F7"


# ------------------------------------------------ actions: scripts are refused in the bridge too

def test_the_bridge_names_actions_and_refuses_scripts_itself(rig, bridge):
    rig.f.action_names[40001] = rig.table({"name": "Track: Insert new track"})
    rig.f.action_names[53001] = rig.table({"name": "Skript: foo.lua", "named": "_RS7d3c0f4e5a6b"})
    rig.f.action_names[53002] = rig.table({"name": "Custom: my macro", "named": "_" + "0123456789abcdef" * 2})
    rig.f.action_names[53003] = rig.table({"name": "SWS: About", "named": "_SWS_ABOUT"})
    assert bridge.call("describe_action", command=53001) == {
        "command_id": 53001, "name": "Skript: foo.lua", "named_id": "RS7d3c0f4e5a6b"}
    assert bridge.call("describe_action", command=40001)["named_id"] == ""

    for script in (53001, "_RS7d3c0f4e5a6b", 53002):
        with pytest.raises(BridgeError, match="is a script or a custom action"):
            bridge.call("run_action", command=script)
    assert list(rig.f.actions.values()) == []            # refused before anything ran
    assert bridge.call("run_action", command=40001) == {"ran": "Track: Insert new track", "command_id": 40001}
    bridge.call("run_action", command="_SWS_ABOUT")      # an extension's action isn't a script
    assert list(rig.f.actions.values()) == [40001, 53003]
    with pytest.raises(BridgeError, match="no action with id '99999'"):
        bridge.call("run_action", command=99999)
