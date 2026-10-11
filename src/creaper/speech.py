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


def _read(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate, channels = w.getframerate(), w.getnchannels()
        raw = w.readframes(w.getnframes())
    return np.frombuffer(raw, dtype="<i2").reshape(-1, channels).mean(axis=1) / 32768.0, rate


def _write(path: Path, audio: np.ndarray, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())


def time_stretch(x: np.ndarray, length: int, rate: int) -> np.ndarray:
    """Stretches or squeezes `x` to `length` samples without changing its pitch or
    formants (WSOLA: overlapping windows, each placed where it best continues the last)."""
    if length <= 0:
        return np.zeros(0)
    win = max(16, int(0.03 * rate))
    if len(x) < win * 2:
        idx = np.linspace(0, max(len(x) - 1, 0), length)
        return np.interp(idx, np.arange(len(x)), x) if len(x) else np.zeros(length)
    hop = win // 4
    tolerance = hop // 2
    window = np.hanning(win)
    frames = max(2, int(np.ceil((length - win) / hop)) + 1)
    sources = np.linspace(0, len(x) - win, frames)
    out = np.zeros(frames * hop + win)
    norm = np.zeros_like(out)
    previous = None
    for i, src in enumerate(sources):
        pos = int(src)
        if previous is not None:
            # The natural continuation of the last frame; pick the nearby frame most like it.
            target = x[previous + hop: previous + hop + win]
            best, best_score = pos, -np.inf
            for cand in range(max(0, pos - tolerance), min(len(x) - win, pos + tolerance) + 1, 2):
                seg = x[cand: cand + win]
                if len(target) == win:
                    score = float(np.dot(seg, target))
                    if score > best_score:
                        best, best_score = cand, score
            pos = best
        out[i * hop: i * hop + win] += x[pos: pos + win] * window
        norm[i * hop: i * hop + win] += window
        previous = pos
    norm[norm < 1e-6] = 1.0
    return (out / norm)[:length]


def vowel_span(x: np.ndarray, rate: int, below_peak_db: float = 10.0) -> tuple[int, int]:
    """The word's sustained loud part (its main vowel): the longest run of 10 ms frames
    within `below_peak_db` of the loudest. Consonants sit before and after it."""
    frame = max(1, int(0.01 * rate))
    n = len(x) // frame
    if n < 3:
        return 0, len(x)
    rms = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1)) + 1e-12
    loud = 20 * np.log10(rms / rms.max()) > -below_peak_db
    best, run_start = (0, 0), None
    for i, on in enumerate(list(loud) + [False]):
        if on and run_start is None:
            run_start = i
        elif not on and run_start is not None:
            if i - run_start > best[1] - best[0]:
                best = (run_start, i)
            run_start = None
    return best[0] * frame, best[1] * frame


def fit_word(path: Path, seconds: float) -> float:
    """Rewrites a spoken word to last exactly `seconds` the way a singer would: the
    consonants keep their natural speed and the vowel is held (or shortened) to fill
    the notes. Returns how much faster than natural the word had to go (1 = natural)."""
    x, rate = _read(path)
    target = max(1, int(round(seconds * rate)))
    start, end = vowel_span(x, rate)
    head, vowel, tail = x[:start], x[start:end], x[end:]
    room = target - len(head) - len(tail)
    if len(vowel) >= int(0.03 * rate) and room >= max(int(0.04 * rate), len(vowel) * 0.4):
        fitted = np.concatenate([head, time_stretch(vowel, room, rate), tail])
    else:
        fitted = time_stretch(x, target, rate)  # too short to hold back the consonants
    fade = min(len(fitted) // 4, int(0.005 * rate))
    if fade:
        ramp = np.linspace(0, 1, fade)
        fitted[:fade] *= ramp
        fitted[-fade:] *= ramp[::-1]
    _write(path, fitted, rate)
    return len(x) / target


def _run(cmd: list[str]) -> None:
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    if done.returncode != 0:
        raise SpeechError(f"speech failed: {done.stderr.strip()[:300]}")


def _safe(text: str) -> str:
    return re.sub(r"[^\w'-]+", "_", text).strip("_")[:40] or "word"
