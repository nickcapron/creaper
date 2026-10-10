"""`creaper` command: runs the MCP server, installs the REAPER bridge, checks the setup."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import resources
from pathlib import Path

from . import __version__
from .bridge import Bridge, BridgeError, default_bridge_dir
from .chat import find_claude

STARTUP_MARKER = "-- creaper bridge (added by `creaper install-bridge`)"
STARTUP_SNIPPET = (
    f"{STARTUP_MARKER}\n"
    'dofile(reaper.GetResourcePath() .. "/Scripts/creaper/creaper_bridge.lua")\n'
)


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


def install_bridge(resource_dir: Path, autostart: bool) -> None:
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

    if autostart:
        startup = resource_dir / "Scripts" / "__startup.lua"
        existing = startup.read_text(encoding="utf-8") if startup.exists() else ""
        if STARTUP_MARKER in existing:
            print(f"Autostart was already set up in {startup}")
        else:
            prefix = "" if not existing or existing.endswith("\n") else "\n"
            startup.write_text(existing + prefix + STARTUP_SNIPPET, encoding="utf-8")
            print(f"REAPER will start the bridge when it launches (added to {startup})")

    print("\nNext:")
    if autostart:
        print("  - Restart REAPER, or run the script once now (below) so you don't have to.")
    print("  - In REAPER: Actions > Show action list > New action > Load ReaScript, pick")
    print(f"    {target}")
    print("    and run it. It keeps running in the background; running it again stops it.")
    print("  - Then check the connection with: creaper doctor")
    print("  - For the chat panel, install ReaImGui (Extensions > ReaPack > Browse packages) and run")
    print("    'creaper_chat.lua' from the action list (the bridge adds it there when it starts).")


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
    install.add_argument("--autostart", action="store_true",
                         help="start the bridge automatically whenever REAPER launches")
    sub.add_parser("doctor", help="check that the server can reach REAPER")
    turn = sub.add_parser("chat-turn", help="run one chat-panel turn (started by creaper_chat.lua)")
    turn.add_argument("request", type=Path)
    args = parser.parse_args(argv)

    if args.command == "install-bridge":
        install_bridge(args.reaper_resource_path or default_bridge_dir().parent, args.autostart)
    elif args.command == "doctor":
        sys.exit(doctor())
    elif args.command == "chat-turn":
        from .chat import run_turn

        sys.exit(run_turn(args.request))
    else:
        from .server import run

        run()
