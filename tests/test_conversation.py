"""What outlasts one message in the chat panel, and what the panel is told while it waits.

The panel starts a new creaper server for every message. A conversation id from the
panel (CREAPER_CONVERSATION) lets the server keep, in the bridge folder, the user's
answers to standing questions, notices already given, noisy-synth readings and the
tracks creaper made. Also here: questions nobody answers, the timing log and the
progress line of long tools."""

import json
import threading
import time

import numpy as np
import pytest
import soundfile as sf
from test_bridge import fake_bridge
from test_hardware_sound import korg  # noqa: F401 - the fixture
from test_render_cache import FakeReaper

from creaper import batch, chat, convstate, export_tools, music_tools, server, sound_tools, timing
from creaper import hardware_sound_tools as hst
from creaper.bridge import Bridge

CONVERSATION = "6734a1f0-0001-0002-0003"


@pytest.fixture
def folder(tmp_path, monkeypatch):
    """A bridge folder of the test's own."""
    monkeypatch.setattr(server.bridge, "directory", tmp_path)
    return tmp_path


@pytest.fixture
def conversation(folder, monkeypatch):
    """The server runs for a panel conversation."""
    monkeypatch.setenv(convstate.ENV, CONVERSATION)
    return folder


def _next_message(monkeypatch):
    """The user sends another message: a new server, with nothing in memory."""
    monkeypatch.setattr(hst, "_asked", set())
    monkeypatch.setattr(server, "_noticed", set())
    monkeypatch.setattr(server, "_notices", [])
    monkeypatch.setattr(server, "_made_tracks", set())
    monkeypatch.setattr(batch, "_noisy", {})


def _tool(name):
    """A tool as the MCP server calls it: through creaper's wrapper."""
    return server.mcp._tool_manager.get_tool(name).fn


# ------------------------------------------------------ the conversation's memory

def test_an_answer_is_kept_for_the_conversation_and_no_other(conversation, monkeypatch):
    assert not convstate.allowed("hardware:microKORG")
    convstate.allow("hardware:microKORG")
    assert convstate.allowed("hardware:microKORG")
    assert not convstate.allowed("hardware:record:microKORG")      # one key per question
    saved = json.loads((conversation / "conversations.json").read_text())
    assert list(saved) == [CONVERSATION]
    monkeypatch.setenv(convstate.ENV, "aaaaaaaa-0000")              # another conversation
    assert not convstate.allowed("hardware:microKORG")


def test_an_answer_lapses_an_hour_after_it_was_last_relied_on(conversation, monkeypatch):
    now = [1_000_000.0]
    monkeypatch.setattr(convstate.time, "time", lambda: now[0])
    convstate.allow("hardware:microKORG")
    now[0] += 50 * 60
    assert convstate.allowed("hardware:microKORG")                 # relied on: the hour starts again
    now[0] += 50 * 60
    assert convstate.allowed("hardware:microKORG")
    now[0] += 61 * 60
    assert not convstate.allowed("hardware:microKORG")
    convstate.put("tracks", "{G}")                                 # the next write tidies the lapsed answer away
    saved = json.loads((conversation / "conversations.json").read_text())
    assert saved[CONVERSATION].get("allowed") == {}


def test_outside_the_panel_nothing_is_kept_on_disk(folder):
    convstate.allow("hardware:microKORG")
    convstate.put("tracks", "{G}")
    assert not convstate.allowed("hardware:microKORG") and convstate.value("tracks", "{G}") is None
    assert not (folder / "conversations.json").exists()


def test_an_id_that_is_not_an_id_is_not_used(folder, monkeypatch):
    monkeypatch.setenv(convstate.ENV, "../../somewhere else")
    assert convstate.conversation_id() is None
    convstate.allow("x")
    assert not (folder / "conversations.json").exists()


def test_old_conversations_are_dropped_and_a_damaged_file_starts_again(conversation, monkeypatch):
    path = conversation / "conversations.json"
    week_old = time.time() - convstate.CONVERSATION_TTL_S - 60
    path.write_text(json.dumps({"0000aaaa-old": {"used": week_old, "allowed": {"q": [True, week_old]}},
                                "0000bbbb-new": {"used": time.time(), "tracks": {"{T}": [True, time.time()]}}}))
    convstate.allow("q")
    assert sorted(json.loads(path.read_text())) == sorted(["0000bbbb-new", CONVERSATION])
    path.write_text("{ not json")
    assert not convstate.allowed("q")                              # unreadable: asked again, no error
    convstate.allow("q")
    assert convstate.allowed("q")


def test_the_panel_passes_its_conversation_to_the_server():
    env = chat.conversation_env({"conversation": CONVERSATION, "session_id": "11111111-2222",
                                 "status": "C:/chat/turn_1.status.json", "question_sound": False})
    assert env == {"CREAPER_CONVERSATION": CONVERSATION, "CREAPER_STATUS_FILE": "C:/chat/turn_1.status.json",
                   "CREAPER_QUESTION_SOUND": "0"}
    # A panel script from before this sends no id of its own: Claude's serves from the second message.
    assert chat.conversation_env({"session_id": "11111111-2222"}) == {"CREAPER_CONVERSATION": "11111111-2222"}
    assert chat.conversation_env({}) == {}
    assert chat.conversation_env({"conversation": "x; rm -rf"}) == {}


# ------------------------------------------------- standing questions (hardware)

def test_a_hardware_permission_is_asked_once_a_conversation_not_once_a_message(korg, monkeypatch):  # noqa: F811
    monkeypatch.setenv(convstate.ENV, CONVERSATION)
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    hst.audition_hardware("microKORG")
    assert len([a for a in korg.asked if "load sounds" in a]) == 1
    assert len([a for a in korg.asked if "record short test clips" in a]) == 1
    _next_message(monkeypatch)
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    hst.audition_hardware("microKORG")
    assert len([a for a in korg.asked if "load sounds" in a]) == 1
    assert len([a for a in korg.asked if "record short test clips" in a]) == 1


def test_outside_the_panel_a_hardware_permission_lasts_for_the_process(korg, monkeypatch):  # noqa: F811
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    assert len([a for a in korg.asked if "load sounds" in a]) == 1
    _next_message(monkeypatch)                                     # another process
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    assert len([a for a in korg.asked if "load sounds" in a]) == 2


def test_the_click_test_is_not_a_yes_to_loading_sounds(korg):  # noqa: F811
    hst.calibrate_hardware_latency("microKORG")
    assert [a for a in korg.asked if "five test clicks" in a]
    assert not [a for a in korg.asked if "load sounds" in a]       # its own two loads are covered by its question
    assert "microKORG" not in hst._asked
    hst.load_hardware_sound("microKORG", recipe="glide distortion lead")
    assert len([a for a in korg.asked if "load sounds" in a]) == 1  # a different question: asked


# ------------------------------------------------------- notices, noise, tracks

def test_a_notice_is_said_once_a_conversation(conversation, monkeypatch):
    _next_message(monkeypatch)
    server.notice("REAPER had taken 2 audio items offline")
    assert "offline" in server._pending_notices()
    _next_message(monkeypatch)
    server.notice("REAPER had taken 2 audio items offline")
    assert server._pending_notices() == ""
    server.notice("something else")
    assert server._pending_notices() == "something else"


def test_a_noisy_synth_is_remembered_into_the_next_message(conversation, monkeypatch):
    key = batch._noise_key("C:/songs/a.rpp", 3, {"fx": [{"name": "Pigments"}], "instrument_fx": 1})
    batch._remember_noise(key, 13.2)
    _next_message(monkeypatch)
    assert batch._known_noise(key) == 13.2
    batch._remember_noise(key, 0.1)                                # it read cleanly: forgotten everywhere
    _next_message(monkeypatch)
    assert batch._known_noise(key) is None


class Tracks:
    """A bridge with tracks to create, describe and delete."""

    def __init__(self, directory):
        self.directory, self.sent = directory, []

    def call(self, cmd, params=None, timeout=30.0):
        self.sent.append(cmd)
        if cmd == "create_track":
            return {"track": {"number": 4, "name": params["name"], "guid": "{MADE-BY-CREAPER}"}}
        if cmd == "describe_track":
            guid = "{MADE-BY-CREAPER}" if params["track"] == "Pad" else "{THE-USERS-OWN}"
            return {"number": 4, "name": params["track"], "guid": guid, "item_count": 6, "fx": ["Pigments"]}
        return {"deleted": params.get("track")}


def test_deleting_a_track_creaper_made_in_this_conversation_is_not_asked(conversation, monkeypatch):
    monkeypatch.setattr(server, "bridge", Tracks(conversation))
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, str(conversation / "turn_1.confirm.json"))
    asked = []
    monkeypatch.setattr(server, "confirm_with_user", lambda action, irreversible=False: asked.append(action))
    server.create_track(name="Pad", instrument="Pigments")
    _next_message(monkeypatch)                                     # deleted two messages later: still creaper's own
    server.delete_track("Pad")
    assert asked == []
    server.delete_track("Vocals")                                  # the user's track, with items on it
    assert len(asked) == 1 and 'delete track 4 "Vocals"' in asked[0]


def test_a_folder_allowed_in_one_message_is_not_asked_again_in_the_next(folder, tmp_path, monkeypatch):
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, str(folder / "turn_1.confirm.json"))
    monkeypatch.setattr(export_tools, "bridge", server.bridge)
    monkeypatch.setattr(export_tools, "_FOLDERS_ALLOWED", set())
    asked = []
    monkeypatch.setattr(export_tools, "confirm_with_user", lambda action, irreversible=False: asked.append(action))
    game = tmp_path.parent / f"{tmp_path.name}_game_assets"
    game.mkdir()
    export_tools.check_folder(game, {})
    monkeypatch.setattr(export_tools, "_FOLDERS_ALLOWED", set())   # the next message: a new server
    export_tools.check_folder(game, {})
    assert len(asked) == 1


# ------------------------------------------------------ a question nobody answers

def test_an_unanswered_question_skips_the_step_instead_of_failing(folder, monkeypatch):
    monkeypatch.setattr(server, "bridge", Tracks(folder))
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, str(folder / "turn_1.confirm.json"))
    monkeypatch.setattr(server, "CONFIRM_TIMEOUT", 0.3)
    result = _tool("delete_track")(track="Vocals")
    assert result["skipped"] == "nobody answered" and 'delete track 4 "Vocals"' in result["not_done"]
    assert "Carry on" in result["message"] and "still to do" in result["message"]
    assert "delete_track" not in server.bridge.sent                # nothing was deleted
    assert not (folder / "turn_1.confirm.json").exists()           # the question is withdrawn
    line = json.loads((folder / "timing.jsonl").read_text().splitlines()[-1])
    assert line["tool"] == "delete_track" and line["skipped"] and not line["ok"]


def test_after_one_unanswered_question_the_next_waits_minutes_not_another_half_hour(folder, monkeypatch):
    confirm = folder / "turn_1.confirm.json"
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, str(confirm))
    monkeypatch.setattr(server, "CONFIRM_TIMEOUT", 0.2)
    monkeypatch.setattr(server, "AWAY_TIMEOUT", 0.05)
    with pytest.raises(server.Unanswered, match="within 1 minute"):
        server.confirm_with_user("delete track 3")
    started = time.monotonic()
    with pytest.raises(server.Unanswered):
        server.confirm_with_user("delete track 4")
    assert time.monotonic() - started < 0.19
    # The user is back and answers: full patience again.
    monkeypatch.setattr(server, "AWAY_TIMEOUT", 5.0)

    def click():
        for _ in range(500):
            if confirm.exists():
                request = json.loads(confirm.read_text())
                confirm.with_suffix(".answer").write_text(json.dumps({"id": request["id"], "allow": True}))
                return
            time.sleep(0.01)
    clicker = threading.Thread(target=click)
    clicker.start()
    server.confirm_with_user("delete track 5")
    clicker.join()
    assert server._nobody_there == [False]


def test_what_cannot_be_undone_is_still_always_asked(folder, monkeypatch):
    """The conversation's memory never answers for run_action or a program write, and
    outside the panel they're refused unless the user opted in."""
    monkeypatch.setenv(convstate.ENV, CONVERSATION)
    convstate.allow("hardware:microKORG")
    monkeypatch.delenv(server.CONFIRM_FILE_ENV, raising=False)
    monkeypatch.delenv(server.ALLOW_UNCONFIRMED_ENV, raising=False)
    with pytest.raises(ValueError, match="can only ask in its chat panel"):
        server.confirm_with_user("run the REAPER action \"Remove all tracks\"", irreversible=True)
    with pytest.raises(ValueError, match="can only ask in its chat panel"):
        server.require_asking("OVERWRITE program A.11 on the microKORG")
    import inspect

    assert "confirm_with_user(f\"run the REAPER action" in inspect.getsource(server.run_action)
    source = inspect.getsource(hst.write_hardware_program)
    assert "irreversible=True" in source and "_was_asked" not in source


# ------------------------------------------------------- audition: plain errors

def _overview_call(tmp_path, frames):
    """server.call for _listen, whose render comes back with this many frames."""
    def call(cmd, timeout=30.0, **params):
        if cmd == "get_project_overview":
            return {"tempo_bpm": 120, "time_signature": "4/4", "length": {"bar": 8}}
        if cmd == "create_midi_item":
            return {"id": "{ITEM}"}
        if cmd == "get_instrument_notes":
            return {"instrument": "VSTi: Synth"}
        if cmd == "render_audio":
            (tmp_path / "renders").mkdir(exist_ok=True)
            f = tmp_path / "renders" / "render_listen.wav"
            sf.write(str(f), np.zeros((frames, 2), dtype=np.float32), 48000)
            return {"files": [str(f)]}
        return {}
    return call


def test_an_empty_render_is_a_plain_message_not_a_numpy_error(folder, monkeypatch):
    monkeypatch.setattr(music_tools, "call", _overview_call(folder, 0))
    with pytest.raises(ValueError, match="rendered no audio for the test notes") as e:
        music_tools.audition_instrument(track="Pad")
    assert "zero-size" not in str(e.value)


@pytest.mark.parametrize("frames", [100, 48000, 5 * 48000])
def test_a_silent_or_short_render_reads_as_silent_notes(folder, monkeypatch, frames):
    monkeypatch.setattr(music_tools, "call", _overview_call(folder, frames))
    result = music_tools.audition_instrument(track="Pad")
    assert len(result["notes"]) == 7 and all(n["silent"] for n in result["notes"])


def test_audition_sounds_on_a_track_that_is_not_there_yet_says_to_create_it_first(monkeypatch):
    def call(cmd, **params):
        raise server.BridgeError("there is no track named 'Pad'")
    monkeypatch.setattr(sound_tools, "call", call)
    with pytest.raises(ValueError, match="there is no track named 'Pad'.*create the track in an earlier call"):
        sound_tools.audition_sounds(track="Pad", role="pad")


# ------------------------------------------------------------- the timing log

def _lines(folder):
    return [json.loads(line) for line in (folder / "timing.jsonl").read_text().splitlines()]


def test_every_tool_call_gets_a_line_with_its_renders_and_cache_hits(folder, monkeypatch):
    fake = FakeReaper(folder)
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_render_cache", server.RenderCache())
    monkeypatch.setattr(server, "_media_tried", [0.0])
    analyze = _tool("analyze_audio")
    analyze(track="master")
    analyze(track="master")                                        # unchanged: from the cache
    tools = [e for e in _lines(folder) if e["kind"] == "tool"]
    assert [(e["tool"], e["ok"], e["renders"], e["cache_hits"]) for e in tools] == [
        ("analyze_audio", True, 1, 0), ("analyze_audio", True, 0, 1)]
    assert all(e["seconds"] >= 0 and "at" in e for e in tools)


def test_a_failed_tool_call_is_logged_with_its_message(folder, monkeypatch):
    class Gone:
        directory = folder

        def call(self, cmd, params=None, timeout=30.0):
            raise server.BridgeError("there is no track named 'Pad'")
    monkeypatch.setattr(server, "bridge", Gone())
    with pytest.raises(server.ToolError):
        _tool("get_track_details")(track="Pad")
    last = _lines(folder)[-1]
    assert last["tool"] == "get_track_details" and last["ok"] is False and "no track named" in last["error"]


def test_every_bridge_command_gets_a_line(tmp_path, monkeypatch):
    stop = threading.Event()
    fake_bridge(tmp_path, 2, stop, answer=lambda req: ({"ok": True, "result": {}} if req["cmd"] == "ping"
                                                        else {"ok": False, "error": "no such thing"}))
    bridge = Bridge(tmp_path)
    bridge.observer = timing.bridge_call
    monkeypatch.setattr(server, "bridge", bridge)
    try:
        time.sleep(0.05)
        record = timing.begin("get_project_overview")
        bridge.call("ping")
        with pytest.raises(server.BridgeError):
            bridge.call("get_track_details", {"track": 9})
        timing.finish(record, True)
    finally:
        stop.set()
    lines = _lines(tmp_path)
    assert [(e["kind"], e.get("cmd"), e["ok"]) for e in lines] == [
        ("bridge", "ping", True), ("bridge", "get_track_details", False), ("tool", None, True)]
    assert lines[0]["tool"] == "get_project_overview" and lines[2]["bridge_calls"] == 2


def test_the_servers_own_bridge_reports_to_the_timing_log():
    assert isinstance(server.bridge, Bridge) and server.bridge.observer == timing.bridge_call


def test_the_timing_log_is_capped(folder, monkeypatch):
    monkeypatch.setattr(timing, "LOG_MAX_BYTES", 2000)
    for i in range(60):
        timing.finish(timing.begin(f"tool_{i}"), True)
    log, old = folder / "timing.jsonl", folder / "timing.1.jsonl"
    assert log.stat().st_size <= 2000 and old.exists() and old.stat().st_size <= 2000
    assert json.loads(log.read_text().splitlines()[-1])["tool"] == "tool_59"
    assert sorted(p.name for p in folder.glob("timing*")) == ["timing.1.jsonl", "timing.jsonl"]


def test_the_log_never_fails_a_tool(folder, monkeypatch):
    monkeypatch.setattr(server.bridge, "directory", folder / "not there")
    timing.finish(timing.begin("get_project_overview"), True)      # no folder: nothing written, nothing raised
    assert not (folder / "not there").exists()


# ------------------------------------------------------------------- progress

def test_a_long_tool_says_where_it_is_before_each_render(folder, monkeypatch):
    status = folder / "turn_1.status.json"
    monkeypatch.setenv(timing.STATUS_FILE_ENV, str(status))
    monkeypatch.setattr(timing, "STATUS_SETTLE_S", 0.0)
    for _ in range(3):                                             # what auto_mix took the last three times
        earlier = timing.begin("auto_mix")
        earlier["renders"] = 14
        timing.finish(earlier, True)
    said = []
    record = timing.begin("auto_mix")
    timing.stage("measuring every track")
    assert not status.exists()                                     # nothing slow has started yet
    timing.render_starting()
    said.append(json.loads(status.read_text())["text"])
    timing.stage("compressors")
    said.append(json.loads(status.read_text())["text"])
    for _ in range(8):
        timing.render_starting()
    said.append(json.loads(status.read_text())["text"])
    for _ in range(6):
        timing.render_starting()
    said.append(json.loads(status.read_text())["text"])            # past the usual count: no "of about"
    timing.finish(record, True)
    assert said == ["auto_mix: measuring every track, render 1 of about 14", "auto_mix: compressors, render 1 of about 14",
                    "auto_mix: compressors, render 9 of about 14", "auto_mix: compressors, render 15"]
    assert json.loads(status.read_text())["text"] == ""            # done: the line goes


def test_a_render_through_the_server_reports_progress_and_a_cache_hit_does_not(folder, monkeypatch):
    status = folder / "turn_1.status.json"
    monkeypatch.setenv(timing.STATUS_FILE_ENV, str(status))
    monkeypatch.setattr(timing, "STATUS_SETTLE_S", 0.0)
    monkeypatch.setattr(server, "bridge", FakeReaper(folder))
    monkeypatch.setattr(server, "_render_cache", server.RenderCache())
    monkeypatch.setattr(server, "_media_tried", [0.0])
    record = timing.begin("check_song")
    server.call("render_audio", track="master")
    assert json.loads(status.read_text())["text"] == "check_song: render 1"
    server.call("render_audio", track="master")
    assert record["renders"] == 1 and record["cache_hits"] == 1
    timing.finish(record, True)


def test_outside_the_panel_no_status_is_written_and_no_time_is_spent(folder, monkeypatch):
    monkeypatch.setattr(timing.time, "sleep", lambda s: pytest.fail("a render waited for a panel that isn't there"))
    record = timing.begin("auto_mix")
    timing.stage("compressors")
    timing.render_starting()
    timing.finish(record, True)
    assert [p.name for p in folder.iterdir()] == ["timing.jsonl"]


def test_the_panel_script_sends_the_conversation_and_reads_the_status():
    from pathlib import Path

    lua = (Path(server.__file__).parent / "reaper" / "creaper_chat.lua").read_text(encoding="utf-8")
    for needed in ("conversation = state.conversation", "status = t.status", "state.conversation = nil",
                   "question_sound = not state.quiet_questions", "turn_progress()", "QUESTION WAITING"):
        assert needed in lua
