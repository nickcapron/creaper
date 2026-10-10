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
