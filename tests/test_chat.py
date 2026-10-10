from creaper import chat


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


def test_command_only_allows_creaper_tools(tmp_path):
    cmd = chat.build_command("claude", tmp_path / "mcp.json", "sess", None)
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--allowedTools") + 1] == "mcp__creaper"
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    assert "--strict-mcp-config" in cmd
    assert cmd[cmd.index("--resume") + 1] == "sess"
    assert "--model" not in cmd
    # Passed to a Windows .cmd shim, so it must not contain characters cmd.exe interprets.
    assert not set(chat.PANEL_PROMPT) & set('&|<>^%!"')
