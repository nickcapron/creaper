from creaper.cli import LEGACY_STARTUP, STARTUP_BEGIN, STARTUP_END, update_startup

USER_CODE = '-- my own startup stuff\nreaper.ShowConsoleMsg("hi")\n'


def blocks(text):
    return text.count(STARTUP_BEGIN), text.count(STARTUP_END)


def test_adds_one_block_and_keeps_the_users_code():
    out = update_startup(USER_CODE, autostart=True, chat=True)
    assert out.startswith(USER_CODE)
    assert blocks(out) == (1, 1)
    assert "creaper_bridge.lua" in out and "creaper_chat.lua" in out
    assert "ImGui_GetBuiltinPath" in out  # the panel opens only when ReaImGui is there


def test_rerunning_doesnt_duplicate_and_can_change_options():
    once = update_startup(USER_CODE, True, True)
    assert update_startup(once, True, True) == once
    bridge_only = update_startup(once, True, False)
    assert blocks(bridge_only) == (1, 1) and "creaper_chat.lua" not in bridge_only


def test_removing_leaves_the_rest_untouched():
    out = update_startup(update_startup(USER_CODE, True, True), autostart=False, chat=True)
    assert out == USER_CODE
    assert update_startup("", False, False) == ""


def test_replaces_the_old_one_line_snippet():
    old = USER_CODE + LEGACY_STARTUP
    out = update_startup(old, True, True)
    assert LEGACY_STARTUP not in out and blocks(out) == (1, 1)
    assert out.startswith(USER_CODE)


def test_file_without_trailing_newline():
    out = update_startup("x = 1", True, False)
    assert out.startswith("x = 1\n" + STARTUP_BEGIN)
