"""Text to speech with the voices built into the operating system, for robot vocals.

Windows uses its speech voices (System.Speech through PowerShell), macOS `say`, and
Linux espeak-ng or espeak. Each word becomes its own WAV file with the silence
around it trimmed, so it starts exactly where it's placed.
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

TIMEOUT = 180.0
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class SpeechError(RuntimeError):
    """No speech engine, or it failed."""


def _powershell(script: str, timeout: float = TIMEOUT) -> str:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                          capture_output=True, text=True, timeout=timeout, creationflags=_NO_WINDOW)
    if done.returncode != 0:
        raise SpeechError(f"Windows speech failed: {done.stderr.strip()[:300]}")
    return done.stdout


def _ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _espeak() -> str | None:
    return shutil.which("espeak-ng") or shutil.which("espeak")


def voices() -> list[dict]:
    """The installed voices: name, and gender or language where the system says."""
    if sys.platform == "win32":
        out = _powershell(
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$s.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object "
            "{ $_.VoiceInfo.Name + '|' + $_.VoiceInfo.Gender + '|' + $_.VoiceInfo.Culture }", timeout=60)
        found = []
        for line in out.splitlines():
            parts = line.strip().split("|")
            if len(parts) == 3:
                found.append({"name": parts[0], "gender": parts[1].lower(), "language": parts[2]})
        return found
    if sys.platform == "darwin":
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=60).stdout
        found = []
        for line in out.splitlines():
            m = re.match(r"^(.+?)\s{2,}(\S+)\s+#", line)
            if m:
                found.append({"name": m.group(1).strip(), "language": m.group(2)})
        return found
    engine = _espeak()
    if not engine:
        return []
    out = subprocess.run([engine, "--voices"], capture_output=True, text=True, timeout=60).stdout
    found = []
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 4:
            found.append({"name": cols[3], "language": cols[1]})
    return found


def choose_voice(wanted: str | None) -> str | None:
    """The installed voice matching `wanted` (part of a name, or 'female'/'male'), or
    None for the system default."""
    if not wanted:
        return None
    available = voices()
    w = wanted.strip().lower()
    by_gender = [v for v in available if v.get("gender") == w]
    if by_gender:
        return by_gender[0]["name"]
    for v in available:
        if w in v["name"].lower():
            return v["name"]
    names = ", ".join(v["name"] for v in available) or "none found"
    raise SpeechError(f"there's no voice like '{wanted}'. Installed voices: {names}")


def speak(texts: list[str], folder: Path, voice: str | None = None) -> list[Path]:
    """Speaks each text into its own trimmed WAV file in `folder`, in order."""
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"{i + 1:03d} {_safe(t)}.wav" for i, t in enumerate(texts)]
    if sys.platform == "win32":
        job = folder / "speech-job.json"
        job.write_text(json.dumps({"voice": voice or "", "items": [
            {"text": t, "path": str(p)} for t, p in zip(texts, paths)]}), encoding="utf-8")
        _powershell(
            "Add-Type -AssemblyName System.Speech;"
            f"$job = Get-Content -Raw -Encoding UTF8 -LiteralPath {_ps_quote(str(job))} | ConvertFrom-Json;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "if ($job.voice) { $s.SelectVoice($job.voice) };"
            "$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(44100, "
            "[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono);"
            "foreach ($w in $job.items) { $s.SetOutputToWaveFile($w.path, $fmt); $s.Speak($w.text) };"
            "$s.SetOutputToNull(); $s.Dispose()")
        job.unlink(missing_ok=True)
    elif sys.platform == "darwin":
        for text, path in zip(texts, paths):
            cmd = ["say", "-o", str(path), "--file-format=WAVE", "--data-format=LEI16@44100"]
            if voice:
                cmd += ["-v", voice]
            _run(cmd + ["--", text])
    else:
        engine = _espeak()
        if not engine:
            raise SpeechError("no speech engine found: install espeak-ng (e.g. sudo apt install espeak-ng)")
        for text, path in zip(texts, paths):
            _run([engine, "-w", str(path)] + (["-v", voice] if voice else []) + ["--", text])
    for path in paths:
        if not path.exists():
            raise SpeechError(f"the speech engine didn't write {path.name}")
        trim_silence(path)
    return paths


def trim_silence(path: Path, floor_db: float = -40.0, pad: float = 0.01) -> float:
    """Cuts the silence before and after the speech and evens out its level (peak at
    -3 dBFS). Returns the remaining length in seconds."""
    with wave.open(str(path), "rb") as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        return len(raw) / (rate * channels * width)
    audio = np.frombuffer(raw, dtype="<i2").reshape(-1, channels).astype(np.float64) / 32768.0
    level = np.abs(audio).max(axis=1)
    peak = float(level.max()) if len(level) else 0.0
    if peak <= 0:
        return 0.0
    loud = np.nonzero(level > peak * 10 ** (floor_db / 20))[0]
    start = max(0, int(loud[0] - pad * rate))
    end = min(len(audio), int(loud[-1] + pad * rate) + 1)
    audio = audio[start:end] * (10 ** (-3 / 20) / peak)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    return len(audio) / rate


def _run(cmd: list[str]) -> None:
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    if done.returncode != 0:
        raise SpeechError(f"speech failed: {done.stderr.strip()[:300]}")


def _safe(text: str) -> str:
    return re.sub(r"[^\w'-]+", "_", text).strip("_")[:40] or "word"
