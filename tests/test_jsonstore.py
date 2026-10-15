import json
import os
import subprocess
import sys
import time

import pytest

from creaper import jsonstore
from creaper.knowledge import Knowledge


def test_missing_file_reads_as_default(tmp_path):
    assert jsonstore.read(tmp_path / "x.json", dict) == {}


def test_unreadable_file_is_an_error_and_is_never_overwritten(tmp_path):
    # Reading a broken store as empty let the next save write an empty store over it.
    path = tmp_path / "motifs.json"
    path.write_text('{"theme": {"name": "Theme"', encoding="utf-8")
    with pytest.raises(ValueError, match="isn't valid JSON"):
        with jsonstore.updating(path, dict) as data:
            data["new"] = 1
    assert path.read_text(encoding="utf-8") == '{"theme": {"name": "Theme"'


def test_nothing_is_written_when_the_change_fails(tmp_path):
    path = tmp_path / "x.json"
    jsonstore.write(path, {"a": 1})
    with pytest.raises(RuntimeError):
        with jsonstore.updating(path, dict) as data:
            data["a"] = 2
            raise RuntimeError("stop")
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1}


def test_a_stale_lock_from_a_dead_process_is_cleared(tmp_path):
    path = tmp_path / "x.json"
    lock = tmp_path / "x.json.lock"
    lock.write_text("")
    old = time.time() - jsonstore.STALE_LOCK - 5
    os.utime(lock, (old, old))
    with jsonstore.updating(path, dict) as data:
        data["ok"] = True
    assert jsonstore.read(path, dict) == {"ok": True} and not lock.exists()


WRITER = """
import sys
from creaper.knowledge import Knowledge
k = Knowledge(sys.argv[1])
for i in range(int(sys.argv[3])):
    k.add(f"note {sys.argv[2]}-{i}", "other")
"""


def test_several_processes_saving_at_once_lose_nothing(tmp_path):
    # Claude Desktop, Claude Code and the chat panel each run a server; each used to
    # read, change and write the same file with no lock, so saves overwrote each other.
    path = tmp_path / "knowledge.json"
    procs = [subprocess.Popen([sys.executable, "-c", WRITER, str(path), str(w), "15"]) for w in range(4)]
    assert all(p.wait(timeout=120) == 0 for p in procs)
    texts = {n["text"] for n in Knowledge(path).find()}
    assert texts == {f"note {w}-{i}" for w in range(4) for i in range(15)}
    assert not list(tmp_path.glob("*.tmp")) and not (tmp_path / "knowledge.json.lock").exists()
