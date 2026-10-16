import json

from creaper import installer


def test_asset_names():
    assert installer.reaimgui_asset("Windows", "AMD64") == "reaper_imgui-x64.dll"
    assert installer.reaimgui_asset("Darwin", "arm64") == "reaper_imgui-arm64.dylib"
    assert installer.reaimgui_asset("Darwin", "x86_64") == "reaper_imgui-x86_64.dylib"
    assert installer.reaimgui_asset("Linux", "x86_64") == "reaper_imgui-x86_64.so"


def test_has_reaimgui(tmp_path):
    assert not installer.has_reaimgui(tmp_path)
    (tmp_path / "UserPlugins").mkdir()
    (tmp_path / "UserPlugins" / "reaper_imgui-x64.dll").write_bytes(b"x")
    assert installer.has_reaimgui(tmp_path)


def test_claude_desktop_config_is_merged_not_replaced(tmp_path):
    cfg = tmp_path / "claude_desktop_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}, "theme": "dark"}), encoding="utf-8")
    assert installer.add_to_claude_desktop(cfg, python="py.exe") == "updated"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["theme"] == "dark" and data["mcpServers"]["other"] == {"command": "x"}
    assert data["mcpServers"]["creaper"] == {"command": "py.exe", "args": ["-m", "creaper"]}
    assert cfg.with_suffix(".json.bak").exists()
    assert installer.add_to_claude_desktop(cfg, python="py.exe") == "already set up"


def test_claude_desktop_config_created(tmp_path):
    cfg = tmp_path / "Claude" / "claude_desktop_config.json"
    assert installer.add_to_claude_desktop(cfg, python="py.exe") == "added"
    assert json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"]["creaper"]["args"] == ["-m", "creaper"]


def test_install_reaimgui_writes_only_the_plugin(tmp_path, monkeypatch):
    # The panel loads ReaImGui's Lua API from the plugin itself, so ReaPack's imgui.lua
    # shim is no longer downloaded into ReaPack's folder.
    release = {"tag_name": "v9.9", "assets": [{"name": installer.reaimgui_asset(), "browser_download_url": "https://x/plugin"}]}
    fetched = []

    def fake_get(url, timeout=60.0):
        fetched.append(url)
        if "api.github.com" in url:
            return json.dumps(release).encode()
        assert url.endswith("/plugin"), url
        return b"\0" * 200_000

    monkeypatch.setattr(installer, "_get", fake_get)
    assert installer.install_reaimgui(tmp_path, log=lambda *_: None) == "v9.9"
    assert (tmp_path / "UserPlugins" / installer.reaimgui_asset()).stat().st_size == 200_000
    assert not (tmp_path / "Scripts").exists() and len(fetched) == 2


def test_install_bridge_keeps_a_startup_script_in_another_encoding(tmp_path):
    # A __startup.lua with cp1252 comments stopped the install with a decode error.
    from creaper import cli
    scripts = tmp_path / "Scripts"
    scripts.mkdir()
    original = "-- caf\xe9 r\xe9glages\nreaper.ShowConsoleMsg('hi')\n".encode("cp1252")
    (scripts / "__startup.lua").write_bytes(original)
    cli.install_bridge(tmp_path)
    data = (scripts / "__startup.lua").read_bytes().replace(b"\r\n", b"\n")  # Windows line endings
    assert data.startswith(original) and b"creaper autostart" in data


def test_dry_run_changes_nothing(tmp_path, capsys):
    (tmp_path / "Scripts").mkdir()
    assert installer.run_setup(tmp_path, dry_run=True, desktop=False, code=False) == 0
    assert not (tmp_path / "Scripts" / "creaper").exists()
    assert "Would" in capsys.readouterr().out
