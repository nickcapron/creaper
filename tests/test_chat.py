import json
import threading
import time

import pytest

from creaper import chat, server


def collect():
    events = []
    return events, chat.Translator(lambda **e: events.append(e))


def test_translates_a_claude_code_turn():
    events, t = collect()
    # Shapes taken from a real `claude -p --output-format stream-json` run.
    t.feed({"type": "system", "subtype": "init", "session_id": "abc", "tools": []})
    t.feed({"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "tool_use"}}})
    t.feed({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t1", "name": "mcp__creaper__add_fx", "input": {"track": "Lead", "fx_name": "FET-76"}}]}})
    t.feed({"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "t1", "is_error": True,
         "content": [{"type": "text", "text": "Error executing tool add_fx: there is no track named 'Lead'"}]}]}})
    t.feed({"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
        "five_hour": {"utilization": 0.75}, "seven_day": {"utilization": 0.54}}}})
    t.feed({"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "text", "text": ""}}})
    t.feed({"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Done"}}})
    t.feed({"type": "result", "subtype": "success", "is_error": False, "result": "Done"})

    assert events == [
        {"t": "session", "id": "abc"},
        {"t": "tool", "id": "t1", "summary": "add_fx(track=Lead, fx_name=FET-76)"},
        {"t": "tool_error", "id": "t1", "message": "add_fx: there is no track named 'Lead'"},
        {"t": "usage", "five_hour": 0.75, "seven_day": 0.54},
        {"t": "text_start"},
        {"t": "text", "text": "Done"},
    ]
    assert t.got_result and t.error_text is None


def test_result_errors_are_reported():
    _, t = collect()
    t.feed({"type": "result", "subtype": "error_max_turns", "is_error": True})
    assert t.error_text == "error_max_turns"


def test_notices_when_creapers_tools_did_not_start():
    # The shape Claude Code reports when an MCP server fails to start.
    _, t = collect()
    t.feed({"type": "system", "subtype": "init", "session_id": "abc",
            "mcp_servers": [{"name": "creaper", "status": "failed", "source": "dynamic"}]})
    assert t.tools_missing
    _, ok = collect()
    ok.feed({"type": "system", "subtype": "init", "session_id": "abc",
             "mcp_servers": [{"name": "creaper", "status": "connected"}]})
    assert not ok.tools_missing


def test_turn_retries_once_when_the_tools_did_not_start(tmp_path, monkeypatch):
    runs = []

    def fake_run(cmd, prompt, cwd, translator, cancel):
        runs.append(cmd)
        if len(runs) == 1:
            translator.feed({"type": "system", "subtype": "init", "session_id": "abc",
                             "mcp_servers": [{"name": "creaper", "status": "failed"}]})
            return 1, "", False
        translator.feed({"type": "system", "subtype": "init", "session_id": "abc",
                         "mcp_servers": [{"name": "creaper", "status": "connected"}]})
        translator.feed({"type": "result", "subtype": "success", "is_error": False, "result": "ok"})
        return 0, "", False

    monkeypatch.setattr(chat, "find_claude", lambda configured=None: "claude")
    monkeypatch.setattr(chat, "run_claude", fake_run)
    events = []
    ok, cancelled = chat._turn({"prompt": "hi"}, tmp_path, None, lambda **e: events.append(e))
    assert ok and not cancelled and len(runs) == 2
    assert any(e["t"] == "info" and "didn't start in time" in e["message"] for e in events)


def _request(tmp_path, **extra):
    req = {"prompt": "hi", "events": str(tmp_path / "t.jsonl"), "cancel": str(tmp_path / "t.cancel"), **extra}
    path = tmp_path / "t.json"
    path.write_text(json.dumps(req), encoding="utf-8")
    return path


def test_turn_says_started_before_claude_runs(tmp_path, monkeypatch):
    # The panel gave up after 45 s without an event, but creaper's server may take up
    # to 2 minutes to start: the helper now says "started" first thing.
    seen = []

    def fake_turn(request, workdir, cancel, emit):
        seen.append(json.loads((tmp_path / "t.jsonl").read_text(encoding="utf-8").splitlines()[0]))
        return True, False

    monkeypatch.setattr(chat, "_turn", fake_turn)
    assert chat.run_turn(_request(tmp_path)) == 0
    assert seen == [{"t": "started"}]


def test_a_stopped_turn_never_starts_claude(tmp_path, monkeypatch):
    runs = []
    monkeypatch.setattr(chat, "find_claude", lambda configured=None: "claude")
    monkeypatch.setattr(chat, "run_claude", lambda *a: runs.append(a) or (0, "", False))
    cancel = tmp_path / "t.cancel"
    cancel.write_text("stop", encoding="utf-8")
    ok, cancelled = chat._turn({"prompt": "hi"}, tmp_path, cancel, lambda **e: None)
    assert cancelled and not ok and not runs


def test_a_turn_the_panel_gave_up_on_tidies_up_its_files(tmp_path, monkeypatch):
    # When the panel gives up it removes the request: the helper, finishing later,
    # removes the events and cancel files nobody will read.
    request = _request(tmp_path)
    (tmp_path / "t.cancel").write_text("stop", encoding="utf-8")

    def panel_gives_up(*a):
        request.unlink()
        return False, True

    monkeypatch.setattr(chat, "_turn", panel_gives_up)
    chat.run_turn(request)
    assert not (tmp_path / "t.jsonl").exists() and not (tmp_path / "t.cancel").exists()


def test_claude_gets_a_longer_mcp_start_timeout(monkeypatch):
    monkeypatch.delenv("MCP_TIMEOUT", raising=False)
    assert chat.claude_env()["MCP_TIMEOUT"] == chat.MCP_START_TIMEOUT_MS
    monkeypatch.setenv("MCP_TIMEOUT", "5000")  # the user's own setting wins
    assert chat.claude_env()["MCP_TIMEOUT"] == "5000"


def test_describe_tool_keeps_it_short():
    assert chat.describe_tool("mcp__creaper__add_chord_progression",
                              {"item_id": "x", "chords": [{"chord": "Am7"}, {"chord": "D9"}]}) == "add_chord_progression(Am7 D9)"
    assert chat.describe_tool("mcp__creaper__set_fx_parameters",
                              {"track": 2, "fx": "FET", "changes": [{}, {}]}) == "set_fx_parameters(track=2, fx=FET, 2 changes)"
    assert len(chat.describe_tool("mcp__creaper__create_track", {"name": "x" * 200})) <= 90


SESSION = "73e7216f-1dbf-4381-847c-df359cb6a7ef"


def test_command_only_allows_creaper_tools():
    cmd = chat.build_command("claude", "mcp.json", SESSION, None)
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--allowedTools") + 1] == "mcp__creaper"
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert "--strict-mcp-config" in cmd
    assert cmd[cmd.index("--resume") + 1] == SESSION
    assert "--model" not in cmd
    # If claude can only be reached through a .cmd shim, cmd.exe sees these arguments.
    assert not set(chat.PANEL_PROMPT) & set('&|<>^%!"')


@pytest.mark.parametrize("session, model", [
    ('x" & calc & "', None), ("../../etc", None), (SESSION, "opus & calc"), (SESSION, "a" * 200),
])
def test_command_rejects_odd_ids(session, model):
    with pytest.raises(ValueError):
        chat.build_command("claude", "mcp.json", session, model)


def test_windows_shim_resolves_to_the_exe(tmp_path):
    shim = tmp_path / "claude.CMD"
    shim.write_text("@echo off")
    assert chat.resolve_windows_shim(str(shim)) == str(shim)  # no exe next to it: keep the shim
    exe = tmp_path / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    assert chat.resolve_windows_shim(str(shim)) == str(exe)
    assert chat.resolve_windows_shim("/usr/local/bin/claude") == "/usr/local/bin/claude"


def _answer_when_asked(confirm, allow):
    """Plays the panel: waits for the question, then clicks Allow or Deny."""
    for _ in range(200):
        if confirm.exists():
            request = json.loads(confirm.read_text())
            confirm.with_suffix(".answer").write_text(json.dumps({"id": request["id"], "allow": allow}))
            return request["action"]
        time.sleep(0.01)


@pytest.mark.parametrize("allow", [True, False])
def test_risky_tools_wait_for_the_panel(tmp_path, monkeypatch, allow):
    confirm = tmp_path / "turn_1.confirm.json"
    monkeypatch.setenv(server.CONFIRM_FILE_ENV, str(confirm))
    asked = []
    clicker = threading.Thread(target=lambda: asked.append(_answer_when_asked(confirm, allow)))
    clicker.start()
    if allow:
        server.confirm_with_user("delete track 3 \"Bass\"")
    else:
        with pytest.raises(ValueError, match="declined"):
            server.confirm_with_user("delete track 3 \"Bass\"")
    clicker.join()
    assert asked == ['delete track 3 "Bass"']
    assert not confirm.exists() and not confirm.with_suffix(".answer").exists()


def test_no_confirmation_outside_the_panel(monkeypatch):
    monkeypatch.delenv(server.CONFIRM_FILE_ENV, raising=False)
    server.confirm_with_user("anything")  # Claude Desktop / Code ask on their own
