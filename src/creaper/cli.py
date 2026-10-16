"""`creaper` command: runs the MCP server, installs the REAPER bridge, checks the setup."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .bridge import Bridge, BridgeError, default_bridge_dir
from .chat import find_claude

# What install-bridge keeps in REAPER's Scripts/__startup.lua, which REAPER runs at launch.
STARTUP_BEGIN = "-- >>> creaper autostart (managed by `creaper install-bridge`; `--no-autostart` removes it)"
STARTUP_END = "-- <<< creaper autostart"
STARTUP_BRIDGE = """\
do
  local dir = reaper.GetResourcePath() .. "/Scripts/creaper/"
  local ok, err = pcall(dofile, dir .. "creaper_bridge.lua")
  if not ok then reaper.ShowConsoleMsg("creaper bridge didn't start: " .. tostring(err) .. "\\n") end
"""
STARTUP_CHAT = """\
  -- Open the chat panel too, when ReaImGui is installed.
  if reaper.ImGui_GetBuiltinPath and reaper.file_exists(dir .. "creaper_chat.lua") then
    local command = reaper.AddRemoveReaScript(true, 0, dir .. "creaper_chat.lua", true)
    if command ~= 0 then reaper.Main_OnCommand(command, 0) end
  end
"""
# Written by creaper 0.1-0.4.
LEGACY_STARTUP = (
    "-- creaper bridge (added by `creaper install-bridge`)\n"
    'dofile(reaper.GetResourcePath() .. "/Scripts/creaper/creaper_bridge.lua")\n'
)
_STARTUP_BLOCK = re.compile(rf"(?ms)^{re.escape(STARTUP_BEGIN[:24])}.*?^{re.escape(STARTUP_END)}[^\n]*\n?")


def update_startup(text: str, autostart: bool, chat: bool) -> str:
    """The __startup.lua contents with creaper's block added, updated or removed.
    Everything else in the file is left as it was."""
    text = _STARTUP_BLOCK.sub("", text.replace(LEGACY_STARTUP, ""))
    if not autostart:
        return text
    block = STARTUP_BEGIN + "\n" + STARTUP_BRIDGE + (STARTUP_CHAT if chat else "") + "end\n" + STARTUP_END + "\n"
    if text and not text.endswith("\n"):
        text += "\n"
    return text + block


def write_chat_config(bridge_dir: Path) -> Path:
    """Tells the chat panel how to start a chat turn: which Python has creaper
    installed (the windowless one on Windows) and where Claude Code is."""
    python = Path(sys.executable)
    windowless = python.with_name("pythonw.exe")
    config = {
        "python": str(windowless if windowless.exists() else python),
        "claude": find_claude(),
        "creaper_version": __version__,
    }
    bridge_dir.mkdir(parents=True, exist_ok=True)
    path = bridge_dir / "chat_config.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def install_bridge(resource_dir: Path, autostart: bool = True, chat: bool = True) -> None:
    if not resource_dir.is_dir():
        sys.exit(f"REAPER's resource folder wasn't found at {resource_dir}. "
                 "Pass --reaper-resource-path (in REAPER: Options > Show REAPER resource path).")
    target_dir = resource_dir / "Scripts" / "creaper"
    target_dir.mkdir(parents=True, exist_ok=True)
    for script in sorted(resources.files("creaper").joinpath("reaper").iterdir(), key=lambda p: p.name):
        if script.name.endswith(".lua"):
            with resources.as_file(script) as source:
                shutil.copyfile(source, target_dir / script.name)
            print(f"Installed {target_dir / script.name}")
    target = target_dir / "creaper_bridge.lua"
    config = write_chat_config(resource_dir / "creaper")
    claude = json.loads(config.read_text(encoding="utf-8"))["claude"]
    if claude:
        print(f"Chat panel will use Claude Code at {claude}")
    else:
        print("Claude Code wasn't found on PATH, so the chat panel won't work until it's installed "
              "(then run install-bridge again). The MCP server works without it.")

    startup = resource_dir / "Scripts" / "__startup.lua"
    # surrogateescape: a startup script saved in another encoding (cp1252 comments)
    # comes back byte for byte instead of stopping the install with a decode error.
    existing = startup.read_text(encoding="utf-8", errors="surrogateescape") if startup.exists() else ""
    updated = update_startup(existing, autostart, chat)
    if updated != existing:
        startup.write_text(updated, encoding="utf-8", errors="surrogateescape")
    if autostart:
        opens = "the bridge and the chat panel" if chat else "the bridge"
        print(f"REAPER will start {opens} when it launches (a marked block in {startup}).")
        if chat:
            print("  The panel opens only once ReaImGui is installed (Extensions > ReaPack > Browse packages).")
    elif existing != updated:
        print(f"Autostart removed from {startup}.")

    print("\nNext:")
    if autostart:
        print("  - Restart REAPER. Until then you can run 'Script: creaper_chat.lua' from the action list,")
        print("    which starts the bridge too.")
    else:
        print("  - In REAPER: Actions > Show action list > New action > Load ReaScript, pick")
        print(f"    {target}")
        print("    and run it. It keeps running in the background; running it again stops it.")
    print("  - Check the connection with: creaper doctor")


def doctor() -> int:
    bridge = Bridge()
    print(f"creaper {__version__}")
    print(f"Bridge folder: {bridge.directory}")
    beat = bridge.heartbeat()
    if beat is None:
        print("No heartbeat from the bridge. Is REAPER open with creaper_bridge.lua running?")
        return 1
    if not bridge.is_running():
        print(f"The bridge's last heartbeat was {beat['age']:.0f} s ago; it seems to have stopped.")
        return 1
    try:
        info = bridge.call("ping")
    except BridgeError as e:
        print(f"The bridge is running but didn't answer: {e}")
        return 1
    print(f"Connected: REAPER {info['reaper_version']}, bridge {info['bridge_version']}")
    if info["bridge_version"] != __version__:
        print("The bridge and the server are different versions; run `creaper install-bridge` to update it.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="creaper", description="Let Claude work in REAPER.")
    parser.add_argument("--version", action="version", version=f"creaper {__version__}")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="run the MCP server over stdio (the default)")
    install = sub.add_parser("install-bridge", help="copy the bridge script into REAPER's Scripts folder")
    install.add_argument("--reaper-resource-path", type=Path, default=None,
                         help="REAPER's resource folder, if it isn't the standard one")
    install.add_argument("--no-autostart", action="store_true",
                         help="don't start creaper when REAPER launches (removes it if it was set up)")
    install.add_argument("--no-chat", action="store_true",
                         help="start only the bridge at launch, not the chat panel")
    install.add_argument("--autostart", action="store_true", help=argparse.SUPPRESS)  # the default now
    setup = sub.add_parser("setup", help="set everything up: ReaImGui, REAPER scripts, Claude Code and Claude Desktop")
    setup.add_argument("--reaper-resource-path", type=Path, default=None)
    setup.add_argument("--yes", action="store_true", help="answer yes to every question")
    setup.add_argument("--dry-run", action="store_true", help="say what would happen, change nothing")
    setup.add_argument("--skip-reaimgui", action="store_true")
    setup.add_argument("--skip-claude-desktop", action="store_true")
    setup.add_argument("--skip-claude-code", action="store_true")
    setup.add_argument("--no-autostart", action="store_true")
    setup.add_argument("--no-chat", action="store_true")
    sub.add_parser("doctor", help="check that the server can reach REAPER")
    turn = sub.add_parser("chat-turn", help="run one chat-panel turn (started by creaper_chat.lua)")
    turn.add_argument("request", type=Path)
    args = parser.parse_args(argv)

    if args.command == "install-bridge":
        install_bridge(args.reaper_resource_path or default_bridge_dir().parent,
                       autostart=not args.no_autostart, chat=not args.no_chat)
    elif args.command == "setup":
        from .installer import run_setup

        sys.exit(run_setup(args.reaper_resource_path or default_bridge_dir().parent, yes=args.yes,
                           dry_run=args.dry_run, reaimgui=not args.skip_reaimgui,
                           desktop=not args.skip_claude_desktop, code=not args.skip_claude_code,
                           autostart=not args.no_autostart, chat=not args.no_chat))
    elif args.command == "doctor":
        sys.exit(doctor())
    elif args.command == "chat-turn":
        from .chat import run_turn

        sys.exit(run_turn(args.request))
    else:
        from .server import run

        run()
