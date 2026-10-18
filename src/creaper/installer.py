"""`creaper setup`: everything after `pip install`, in one go.

1. Install ReaImGui (for the chat panel) from its official GitHub release, if missing.
2. Install creaper's scripts into REAPER and start them with REAPER (install-bridge).
3. Find Claude Code, and say how to install it and sign in if it isn't there.
4. Offer to add creaper to Claude Desktop and to Claude Code as an MCP server.

Nothing here handles a Claude login: signing in happens in Claude's own apps.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REAIMGUI_REPO = "cfillion/reaimgui"
# The release creaper installs and its files' SHA-256 (from the GitHub release): REAPER loads
# the plugin as native code, so a changed file is refused. Update both together.
REAIMGUI_TAG = "v0.10.0.5"
REAIMGUI_SHA256 = {
    "reaper_imgui-x64.dll": "800b216e0937bf5bb6b08ba2767b7b974a746b3fc3b54943b4d3011da0a68f2a",
    "reaper_imgui-x86.dll": "6840f7c76673018d9a42590f70c4c06ce8074b7c0f126c8deb6440a24c483082",
    "reaper_imgui-arm64.dylib": "1f90cf004c0bbada45358609c943f601b2cb0e625ecf7739ae5df8708ab705ae",
    "reaper_imgui-x86_64.dylib": "2209fec3eae03f22fe94b9d2681b04e21f41c7d4587cb0d69e4eb72e39a64e65",
    "reaper_imgui-aarch64.so": "9b72753132a2ce96ae0405effaf9a8d8eeab9ab6d0f8c41ca7f62064333cdfc7",
    "reaper_imgui-x86_64.so": "b967a30b356f1c689ab457f2ce393b936267e4287939ece616e10d74399e2997",
}
USER_AGENT = "creaper-setup"


def reaimgui_asset(system: str | None = None, machine: str | None = None) -> str:
    """The ReaImGui plugin file for this platform, as named in its GitHub releases."""
    system = (system or platform.system()).lower()
    machine = (machine or platform.machine()).lower()
    if system == "windows":
        return "reaper_imgui-x86.dll" if machine in ("x86", "i386", "i686") else "reaper_imgui-x64.dll"
    if system == "darwin":
        return "reaper_imgui-arm64.dylib" if machine in ("arm64", "aarch64") else "reaper_imgui-x86_64.dylib"
    if machine in ("aarch64", "arm64"):
        return "reaper_imgui-aarch64.so"
    return "reaper_imgui-x86_64.so"


def has_reaimgui(resource_dir: Path) -> bool:
    plugins = resource_dir / "UserPlugins"
    return plugins.is_dir() and any(p.name.lower().startswith("reaper_imgui") for p in plugins.iterdir())


def _get(url: str, timeout: float = 60.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https URLs only
        return response.read()


def install_reaimgui(resource_dir: Path, log=print) -> str:
    """Downloads ReaImGui's plugin from its official release (the pinned one) and checks
    it against the SHA-256 recorded here before REAPER can load it."""
    release = json.loads(_get(f"https://api.github.com/repos/{REAIMGUI_REPO}/releases/tags/{REAIMGUI_TAG}"))
    tag = release["tag_name"]
    name = reaimgui_asset()
    asset = next((a for a in release.get("assets", []) if a["name"] == name), None)
    if asset is None:
        raise RuntimeError(f"ReaImGui {tag} has no {name} for this computer")
    plugins = resource_dir / "UserPlugins"
    plugins.mkdir(parents=True, exist_ok=True)
    data = _get(asset["browser_download_url"], timeout=180.0)
    if len(data) < 100_000:
        raise RuntimeError("the ReaImGui download looks incomplete")
    expected = REAIMGUI_SHA256.get(name)
    if expected is None or hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError(f"the ReaImGui download ({name}) doesn't match its recorded checksum, so it wasn't "
                           "installed; install ReaImGui with ReaPack instead")
    part = plugins / (name + ".part")
    part.write_bytes(data)
    part.replace(plugins / name)
    # The panel loads ReaImGui's Lua API from the plugin itself (ImGui_GetBuiltinPath),
    # so ReaPack's separate imgui.lua shim isn't needed.
    log(f"Installed ReaImGui {tag} ({name})")
    return tag


def claude_desktop_config() -> Path:
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def server_entry(python: str | None = None) -> dict:
    return {"command": python or sys.executable, "args": ["-I", "-m", "creaper"]}


def add_to_claude_desktop(config_path: Path, python: str | None = None) -> str:
    """Adds (or updates) creaper in Claude Desktop's MCP servers, keeping everything
    else in the file and a .bak copy of the original. Returns what happened."""
    data: dict = {}
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8").strip()
        if text:
            try:
                data = json.loads(text)
            except ValueError as e:
                raise RuntimeError(f"{config_path} isn't valid JSON ({e}); fix it and run setup again") from None
    servers = data.setdefault("mcpServers", {})
    entry = server_entry(python)
    if servers.get("creaper") == entry:
        return "already set up"
    if config_path.exists():
        shutil.copyfile(config_path, config_path.with_suffix(".json.bak"))
    servers["creaper"] = entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return "updated" if config_path.with_suffix(".json.bak").exists() else "added"


def add_to_claude_code(claude: str, python: str | None = None) -> str:
    probe = subprocess.run([claude, "mcp", "get", "creaper"], capture_output=True, text=True, timeout=60)
    if probe.returncode == 0:
        if " -I " in f" {probe.stdout} " or "-I -m" in probe.stdout:
            return "already set up"
        # From before v0.29.1: started without isolated mode. Replace it.
        subprocess.run([claude, "mcp", "remove", "--scope", "user", "creaper"], capture_output=True, text=True,
                       timeout=60)
    done = subprocess.run([claude, "mcp", "add", "--scope", "user", "creaper", "--", python or sys.executable,
                           "-I", "-m", "creaper"], capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout).strip() or "claude mcp add failed")
    return "added"


CLAUDE_CODE_INSTALL = {
    "Windows": "irm https://claude.ai/install.ps1 | iex      (in PowerShell)",
    "Darwin": "curl -fsSL https://claude.ai/install.sh | bash",
    "Linux": "curl -fsSL https://claude.ai/install.sh | bash",
}


def _ask(question: str, yes: bool) -> bool:
    if yes:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        return False
    answer = input(f"{question} [Y/n] ").strip().lower()
    return answer in ("", "y", "yes")


def run_setup(resource_dir: Path, yes: bool = False, dry_run: bool = False, reaimgui: bool = True,
              desktop: bool = True, code: bool = True, autostart: bool = True, chat: bool = True) -> int:
    from .chat import find_claude
    from .cli import install_bridge

    def step(text: str) -> None:
        print(f"\n== {text}")

    if not resource_dir.is_dir():
        print(f"REAPER's resource folder wasn't found at {resource_dir}.\n"
              "Install REAPER and open it once, or pass --reaper-resource-path "
              "(in REAPER: Options > Show REAPER resource path in explorer/finder).")
        return 1

    step("ReaImGui (for the chat panel inside REAPER)")
    if not chat:
        print("Skipped: the chat panel isn't wanted (--no-chat).")
    elif has_reaimgui(resource_dir):
        print("Already installed.")
    elif not reaimgui:
        print("Not installed. Get it in REAPER: Extensions > ReaPack > Browse packages > ReaImGui.")
    elif dry_run:
        print(f"Would download {reaimgui_asset()} from github.com/{REAIMGUI_REPO} (latest release).")
    elif _ask("Download and install ReaImGui from its official GitHub release?", yes):
        try:
            install_reaimgui(resource_dir)
        except Exception as e:  # noqa: BLE001 - setup should carry on and say what to do
            print(f"Couldn't install ReaImGui ({e}). Install it through ReaPack instead "
                  "(reapack.com, then Extensions > ReaPack > Browse packages > ReaImGui).")

    step("creaper's scripts in REAPER")
    if dry_run:
        print(f"Would copy the scripts into {resource_dir / 'Scripts' / 'creaper'} and start them with REAPER.")
    else:
        install_bridge(resource_dir, autostart=autostart, chat=chat)

    step("Claude Code (runs the chat panel on your Claude account)")
    claude = find_claude()
    if claude:
        print(f"Found at {claude}. If you haven't yet, sign in once: run `claude` in a terminal.")
    else:
        print("Not found. Install it with:\n  " + CLAUDE_CODE_INSTALL.get(platform.system(), CLAUDE_CODE_INSTALL["Linux"]))
        print("then run `claude` once to sign in, and run `creaper setup` again.")

    step("Claude Desktop")
    config = claude_desktop_config()
    if not desktop:
        print("Skipped (--skip-claude-desktop).")
    elif not config.parent.exists():
        print("Claude Desktop isn't installed (that's fine: the chat panel and Claude Code work without it).")
    elif dry_run:
        print(f"Would add creaper to {config}.")
    elif _ask("Add creaper to Claude Desktop, so you can also use it from there?", yes):
        try:
            print(f"creaper {add_to_claude_desktop(config)} in {config}. Restart Claude Desktop to load it.")
        except RuntimeError as e:
            print(str(e))

    step("Claude Code in a terminal")
    if not code or not claude:
        print("Skipped." if not code else "Skipped until Claude Code is installed.")
    elif dry_run:
        print("Would run: claude mcp add --scope user creaper -- <python> -m creaper")
    elif _ask("Add creaper to Claude Code too (for `claude` in a terminal)?", yes):
        try:
            print(f"creaper {add_to_claude_code(claude)} in Claude Code.")
        except Exception as e:  # noqa: BLE001
            print(f"Couldn't add it ({e}). You can run: claude mcp add creaper -- \"{sys.executable}\" -m creaper")

    step("Done")
    print("Restart REAPER: the creaper panel opens by itself (dock it with the Dock button).")
    if not claude:
        print("The panel needs Claude Code: install it and sign in, then run `creaper setup` again.")
    return 0
