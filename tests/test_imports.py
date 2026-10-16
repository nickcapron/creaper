import subprocess
import sys

MODULES = ["server", "export_tools", "sfx_tools", "vocal_tools", "sample_tools", "mix_tools", "ear_tools",
           "motif_tools", "music_tools", "project_tools", "record_tools", "scan_tools", "arrange_tools", "sound_tools", "chat", "cli",
           "installer"]

CHECK = r"""
import importlib, sys
failed = []
for name in sys.argv[1:]:
    for loaded in [m for m in sys.modules if m == "creaper" or m.startswith("creaper.")]:
        del sys.modules[loaded]  # a fresh creaper each time; numpy/scipy stay loaded
    try:
        importlib.import_module("creaper." + name)
    except Exception as e:
        failed.append(f"{name}: {e!r}")
print("\n".join(failed))
sys.exit(1 if failed else 0)
"""


def test_each_module_imports_on_its_own():
    # server.py loads every tool module at its end, so a tool module imported first
    # used to break when it took names from a sibling still loading (circular import).
    done = subprocess.run([sys.executable, "-c", CHECK, *MODULES], capture_output=True, text=True)
    assert done.returncode == 0, (done.stdout + done.stderr)[-1500:]
