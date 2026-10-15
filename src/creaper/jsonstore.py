"""JSON files that several creaper servers share: Claude Desktop, Claude Code and the
chat panel can each run one at the same time, all reading and writing the same notes,
sound library, drum maps, plugin catalog and motifs.

Every change is made under a lock file (read, change, write as one step), written to a
temporary file of its own and swapped in, with retries for the moment Windows holds a
file another process is replacing. A file that can't be read is an error, never "empty":
treating it as empty let the next save write an empty store over everything in it."""

from __future__ import annotations

import contextlib
import json
import os
import time
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

LOCK_TIMEOUT = 15.0   # seconds to wait for another process to finish writing
STALE_LOCK = 60.0     # a lock older than this was left by a process that died
RETRY_FOR = 2.0       # seconds to retry a read or replace Windows refuses for a moment


def _retry(fn: Callable[[], Any]) -> Any:
    deadline = time.monotonic() + RETRY_FOR
    while True:
        try:
            return fn()
        except PermissionError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.02)


@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    """Holds <file>.lock while the block runs, so only one process changes the file."""
    path = Path(path)
    lock = path.with_name(path.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT
    while True:
        try:
            os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except (FileExistsError, PermissionError):
            with contextlib.suppress(OSError):
                if time.time() - lock.stat().st_mtime > STALE_LOCK:
                    lock.unlink()
                    continue
            if time.monotonic() > deadline:
                raise TimeoutError(f"{path.name} is busy (another creaper is saving it); try again") from None
            time.sleep(0.02)
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def read(path: Path, default: Callable[[], Any]) -> Any:
    """The file's data; default() when it doesn't exist yet. Raises ValueError when it
    exists but isn't valid JSON."""
    path = Path(path)

    def text() -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    raw = _retry(text)
    if raw is None:
        return default()
    try:
        return json.loads(raw)
    except ValueError as e:
        raise ValueError(f"{path} isn't valid JSON ({e}); fix or delete it") from None


def write(path: Path, data: Any, indent: int | None = 1) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=indent), encoding="utf-8")
        _retry(lambda: os.replace(tmp, path))
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()


@contextlib.contextmanager
def updating(path: Path, default: Callable[[], Any], indent: int | None = 1) -> Iterator[Any]:
    """Read, change and write the file as one step under its lock:

        with updating(path, dict) as data:
            data["x"] = 1

    Nothing is written if the block raises."""
    with locked(path):
        data = read(path, default)
        yield data
        write(path, data, indent)
