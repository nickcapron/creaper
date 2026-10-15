"""Finding out what plugins do by testing them.

Effects get a known test signal (an impulse, a noise burst, quiet and loud sines,
a low sine) and creaper compares what comes out with what went in: latency, gain,
EQ curve, reverb or delay tails, compression or gating, distortion, modulation,
pitch shift and stereo width. Instruments play notes across the keyboard and a
row of drum keys (see listen.py). Results are kept in a catalog so Claude can pick
the right plugin for a job. Everything describes the plugin at its default settings.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
from scipy import signal

from . import jsonstore

SIGNAL_VERSION = 2  # bump when the test signal changes, so cached files are rebuilt

# Test signal layout, in seconds.
IMPULSE_AT = 0.1
NOISE = (1.0, 1.5)
SINE_QUIET = (3.5, 4.5)      # 1 kHz at -30 dBFS
SINE_LOUD = (4.5, 5.5)       # 1 kHz at -6 dBFS
SINE_LOW = (6.0, 8.0)        # 220 Hz at -12 dBFS
SINE_FAINT = (8.0, 8.8)      # 1 kHz at -50 dBFS (gates close on it)
LENGTH = 9.5
QUIET_DB, LOUD_DB, LOW_DB, NOISE_DB, FAINT_DB = -30.0, -6.0, -12.0, -12.0, -50.0


def _amp(db: float) -> float:
    return 10 ** (db / 20)


def test_signal(fs: int) -> np.ndarray:
    """The mono test signal effects are measured with."""
    n = int(LENGTH * fs)
    x = np.zeros(n)
    x[int(IMPULSE_AT * fs)] = 0.9
    rng = np.random.default_rng(1234)
    a, b = (int(t * fs) for t in NOISE)
    white = rng.standard_normal(b - a)
    # Pink-ish noise (equal energy per octave) so every band is measured fairly.
    spec = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(len(white), 1 / fs)
    spec[1:] /= np.sqrt(freqs[1:])
    spec[0] = 0
    pink = np.fft.irfft(spec, len(white))
    pink *= _amp(NOISE_DB) / np.sqrt(np.mean(pink ** 2))
    fade = np.minimum(1, np.minimum(np.arange(len(pink)), np.arange(len(pink))[::-1]) / (0.005 * fs))
    x[a:b] = pink * fade
    for (s0, s1), db, freq in ((SINE_QUIET, QUIET_DB, 1000.0), (SINE_LOUD, LOUD_DB, 1000.0), (SINE_LOW, LOW_DB, 220.0),
                               (SINE_FAINT, FAINT_DB, 1000.0)):
        i0, i1 = int(s0 * fs), int(s1 * fs)
        t = np.arange(i1 - i0) / fs
        ramp = np.minimum(1, np.minimum(np.arange(i1 - i0), np.arange(i1 - i0)[::-1]) / (0.01 * fs))
        x[i0:i1] = _amp(db) * math.sqrt(2) * np.sin(2 * np.pi * freq * t) * ramp
    return x


def _rms_db(x: np.ndarray) -> float:
    r = math.sqrt(float(np.mean(np.square(x)))) if x.size else 0.0
    return 20 * math.log10(max(r, 1e-9))


def _seg(x: np.ndarray, fs: int, span: tuple[float, float], trim: float = 0.0) -> np.ndarray:
    a, b = int((span[0] + trim) * fs), int((span[1] - trim) * fs)
    return x[max(0, a): max(0, b)]


def _latency(dry: np.ndarray, wet: np.ndarray, fs: int) -> tuple[int, float]:
    """Delay (samples) at which the output best matches the noise burst, and how well."""
    a, b = (int(t * fs) for t in NOISE)
    ref = dry[a:b]
    win = wet[a: b + int(0.3 * fs)]
    if win.size < ref.size or not np.any(win):
        return 0, 0.0
    corr = signal.correlate(win, ref, mode="valid", method="fft")
    lag = int(np.argmax(np.abs(corr)))
    norm = float(np.abs(corr[lag]) / (np.linalg.norm(ref) * np.linalg.norm(win[lag: lag + ref.size]) + 1e-12))
    return lag, norm


OCTAVES = (63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)


def _bands(x: np.ndarray, fs: int) -> np.ndarray:
    f, p = signal.welch(x, fs=fs, nperseg=min(4096, len(x)))
    out = []
    for fc in OCTAVES:
        m = (f >= fc / math.sqrt(2)) & (f < fc * math.sqrt(2))
        out.append(float(p[m].sum()) if m.any() else 0.0)
    return np.array(out)


def _thd(x: np.ndarray, fs: int, f0: float) -> float:
    """Total harmonic distortion (%) of a sine segment."""
    n = len(x)
    if n < 2048:
        return 0.0
    spec = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, 1 / fs)

    def power(fc: float) -> float:
        m = np.abs(freqs - fc) <= 15
        return float(spec[m].sum())

    fund = power(f0)
    harm = sum(power(f0 * k) for k in range(2, 9) if f0 * k < fs / 2 - 100)
    return 100 * math.sqrt(harm / fund) if fund > 0 else 0.0


def _dominant(x: np.ndarray, fs: int) -> float:
    n = len(x)
    spec = np.abs(np.fft.rfft(x * np.hanning(n), 8 * n))
    freqs = np.fft.rfftfreq(8 * n, 1 / fs)
    m = (freqs > 40) & (freqs < 5000)
    return float(freqs[m][np.argmax(spec[m])])


def _impurity(x: np.ndarray, fs: int, f0: float) -> float:
    """Share of energy that isn't the sine or its harmonics (chorus, phaser, noise)."""
    n = len(x)
    spec = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2
    freqs = np.fft.rfftfreq(n, 1 / fs)
    keep = np.zeros_like(freqs, dtype=bool)
    for k in range(1, 12):
        keep |= np.abs(freqs - f0 * k) <= 1.6
    total = float(spec[freqs > 20].sum()) or 1e-12
    return float(spec[(freqs > 20) & ~keep].sum()) / total


def _pitch_wobble(x: np.ndarray, fs: int) -> float:
    """How much a steady sine's pitch moves (Hz, robust spread of the instantaneous
    frequency): chorus and vibrato move it, tremolo and filters don't."""
    if len(x) < fs // 4:
        return 0.0
    band = signal.sosfiltfilt(signal.butter(2, [150, 300], btype="bandpass", fs=fs, output="sos"), x)
    analytic = signal.hilbert(band)
    amp = np.abs(analytic)
    inst = np.diff(np.unwrap(np.angle(analytic))) * fs / (2 * np.pi)
    strong = amp[1:] > 0.3 * np.median(amp)
    inst = inst[strong]
    if inst.size < 100:
        return 0.0
    lo, hi = np.percentile(inst, [10, 90])
    return float((hi - lo) / 2)


def _envelope_db(x: np.ndarray, fs: int, frame: float = 0.01) -> np.ndarray:
    hop = max(1, int(frame * fs))
    n = len(x) // hop
    if n == 0:
        return np.array([-180.0])
    e = np.sqrt(np.mean(np.square(x[: n * hop]).reshape(n, hop), axis=1))
    return 20 * np.log10(e + 1e-9)


def _echoes(ir: np.ndarray, fs: int) -> list[float]:
    """Times (s) of distinct repeats in an impulse response: peaks well above what's
    around them, at least 40 ms apart."""
    env = _envelope_db(ir, fs, 0.004)
    if env.max() < -80:
        return []
    top = env.max()
    peaks = []
    for i in range(3, len(env) - 3):
        if env[i] >= top - 24 and env[i] == env[i - 3: i + 4].max():
            lo = min(env[max(0, i - 8): i].min(initial=env[i]), env[i + 1: i + 9].min(initial=env[i]))
            if env[i] - lo >= 9 and (not peaks or i - peaks[-1] >= 10):
                peaks.append(i)
    times = [p * 0.004 for p in peaks]
    return [t for t in times if t >= 0.04]


def _align(x: np.ndarray, lag: int, n: int) -> np.ndarray:
    y = x[lag:]
    return np.concatenate([y, np.zeros(max(0, n - len(y)))])[:n]


def _tail_bumps(after_db: np.ndarray) -> int:
    """Times the tail after the noise burst swells up again (repeats arriving), as
    opposed to dying away smoothly like a reverb."""
    bumps, low = 0, after_db[0] if after_db.size else 0.0
    for i in range(1, len(after_db)):
        low = min(low, after_db[i])
        if after_db[i] - low >= 4 and after_db[i] > after_db.max() - 45:
            bumps += 1
            low = after_db[i]
    return bumps


def _regular(times: list[float]) -> bool:
    """Echo times that are (near) multiples of the first: a delay line's repeats."""
    if len(times) < 2:
        return True
    first = times[0]
    return all(abs(t / first - round(t / first)) < 0.08 for t in times[1:])


def analyze_effect(dry: np.ndarray, wet: np.ndarray, fs: int) -> dict:
    """What an effect did to the test signal. wet is (samples, channels). Each output
    channel is measured on its own (a mono sum would hide chorus and invent comb
    filtering from stereo delays), then combined."""
    if wet.ndim == 1:
        wet = wet[:, None]
    chans = [wet[:, c] for c in range(min(2, wet.shape[1]))]
    if max(_rms_db(c) for c in chans) < -80:
        return {"passes_audio": False, "roles": ["no output"],
                "summary": "makes no sound from the test signal: it may need a sidechain or MIDI input, be an analyzer, or be an instrument"}
    n = len(dry)
    lags = [_latency(dry, c, fs) for c in chans]
    good = [(lag, m) for lag, m in lags if m > 0.2]
    lag = min(lag for lag, _ in good) if good else 0
    out: dict = {"latency_ms": round(1000 * lag / fs, 1) if good else None}
    al = [_align(c, lag, n) for c in chans]
    mid = sum(al) / len(al)
    side = (al[0] - al[-1]) / 2

    def level(span, trim):
        return 10 * math.log10(np.mean([10 ** (_rms_db(_seg(c, fs, span, trim)) / 10) for c in al]) + 1e-18)

    noise_in = _rms_db(_seg(dry, fs, NOISE, 0.05))
    noise_out = level(NOISE, 0.05)
    out["passes_audio"] = noise_out > -70
    out["gain_db"] = round(noise_out - noise_in, 1)
    bands_out = np.mean([_bands(_seg(c, fs, NOISE, 0.05), fs) for c in al], axis=0)
    ratio = 10 * np.log10((bands_out + 1e-20) / (_bands(_seg(dry, fs, NOISE, 0.05), fs) + 1e-20))
    curve = ratio - np.median(ratio)
    out["eq_curve_db"] = {f"{fc if fc < 1000 else str(fc // 1000) + 'k'}": round(float(v), 1) for fc, v in zip(OCTAVES, curve)}
    after = np.max([_envelope_db(c[int(NOISE[1] * fs): int(SINE_QUIET[0] * fs)], fs) for c in al], axis=0)
    out["tail_bumps"] = _tail_bumps(after - noise_out)
    below = np.where(after - noise_out < -40)[0]
    out["tail_s"] = round(float(below[0]) * 0.01, 2) if below.size else round(SINE_QUIET[0] - NOISE[1], 2)
    i0, i1 = int(IMPULSE_AT * fs), int((NOISE[0] - 0.05) * fs)
    ir_chan = max(al, key=lambda c: float(np.abs(c[i0:i1]).sum()))
    out["echoes_s"] = [round(t, 3) for t in _echoes(ir_chan[i0:i1], fs)][:6]
    q_in = _rms_db(_seg(dry, fs, SINE_QUIET, 0.25))
    l_in = _rms_db(_seg(dry, fs, SINE_LOUD, 0.25))
    f_in = _rms_db(_seg(dry, fs, SINE_FAINT, 0.15))
    q_out, l_out, f_out = level(SINE_QUIET, 0.25), level(SINE_LOUD, 0.25), level(SINE_FAINT, 0.15)
    out["compression_db"] = round((q_out - q_in) - (l_out - l_in), 1)
    out["loud_vs_quiet_out_db"] = round(l_out - q_out, 1)
    out["quiet_level_change_db"] = round(q_out - q_in, 1)
    out["faint_level_change_db"] = round(f_out - f_in, 1)
    out["thd_pct"] = round(max(_thd(_seg(c, fs, SINE_LOUD, 0.25), fs, 1000.0) for c in al), 2)
    wobble, smear, fwobble = 0.0, 0.0, 0.0
    for c in al:
        low = _seg(c, fs, SINE_LOW, 0.2)
        env = 10 ** (_envelope_db(low, fs, 0.02) / 20)
        wobble = max(wobble, 100 * float(np.std(env) / (np.mean(env) + 1e-12)))
        smear = max(smear, 100 * _impurity(low, fs, 220.0))
        fwobble = max(fwobble, _pitch_wobble(low, fs))
    out["amplitude_wobble_pct"] = round(wobble, 1)
    out["spectral_smear_pct"] = round(smear, 1)
    out["pitch_wobble_hz"] = round(fwobble, 2)
    dom = _dominant(_seg(mid, fs, SINE_LOW, 0.2), fs)
    out["pitch_shift_semitones"] = round(12 * math.log2(dom / 220.0), 2) if dom > 0 else 0.0
    out["stereo_width_db"] = round(_rms_db(_seg(side, fs, NOISE, 0.05)) - noise_out, 1)
    out["roles"], out["summary"] = _roles(out)
    return out


def _roles(m: dict) -> tuple[list[str], str]:
    roles, notes = [], []
    if not m.get("passes_audio", True):
        return ["no output"], "passes no audio at its default settings"
    curve = list(m["eq_curve_db"].values())
    spread = max(curve) - min(curve)
    echoes = m["echoes_s"]
    thd = m["thd_pct"]
    time_based = False
    wide = m["stereo_width_db"] > -30
    if echoes and _regular(echoes):
        roles.append("delay")
        notes.append(f"delay: repeats at {', '.join(f'{int(t * 1000)} ms' for t in echoes[:3])}")
        time_based = True
    elif echoes and len(echoes) >= 3 and m["tail_s"] >= 0.5:
        roles.append("reverb")
        notes.append(f"reverb: a {m['tail_s']:.1f} s tail with distinct early reflections (spring- or room-like)")
        time_based = True
    elif m["tail_s"] >= 0.3 and not wide and m.get("tail_bumps", 0) >= 2:
        roles.append("delay")
        notes.append(f"delay: smeared repeats (a dark, filtered echo) lasting {m['tail_s']:.1f} s")
        time_based = True
    elif m["tail_s"] >= 0.3 or (m["tail_s"] >= 0.15 and wide):
        roles.append("reverb")
        notes.append(f"reverb: a {m['tail_s']:.1f} s tail" + (" (short/subtle at default settings)" if m["tail_s"] < 0.5 else "")
                     + ("" if wide else ", mono"))
        time_based = True
    modulating = m["amplitude_wobble_pct"] >= 8 or m["spectral_smear_pct"] >= 4 or m.get("pitch_wobble_hz", 0) >= 0.35
    # Moving level (chorus, tremolo, delay repeats) fools the dynamics test, so only
    # trust a compression reading when nothing is modulating.
    if thd < 3 and m["compression_db"] >= 1.5 and not modulating and not time_based:
        flat = m["loud_vs_quiet_out_db"] <= 4
        roles.append("limiter" if flat else "compressor")
        notes.append(f"{roles[-1]}: loud parts come through {m['compression_db']:.1f} dB quieter than quiet ones")
    if not modulating and (m["faint_level_change_db"] - m["quiet_level_change_db"] <= -20 or m["compression_db"] <= -3):
        roles.append("gate/expander")
        notes.append("gate/expander: very quiet sounds are turned down or cut")
    if thd >= 1.0:
        roles.append("distortion" if thd >= 10 else "saturation")
        notes.append(f"{roles[-1]}: {thd:.1f}% harmonic distortion on a loud sine")
    if spread >= (6.0 if thd >= 10 else 2.0) and not (time_based and spread < 4):
        shape = []
        lo, hi = curve[0], curve[-1]
        if lo <= -6:
            shape.append("cuts lows")
        elif lo >= 4:
            shape.append("boosts lows")
        if hi <= -6:
            shape.append("cuts highs")
        elif hi >= 4:
            shape.append("boosts highs")
        mid = max(range(1, len(curve) - 1), key=lambda i: abs(curve[i]))
        if abs(curve[mid]) >= 3 and not shape:
            shape.append(f"{'boosts' if curve[mid] > 0 else 'cuts'} around {list(m['eq_curve_db'])[mid]} Hz")
        roles.append("eq/filter")
        notes.append("tone: " + (", ".join(shape) if shape else f"reshapes the spectrum (+/-{spread / 2:.1f} dB)"))
    if abs(m["pitch_shift_semitones"]) >= 0.4:
        roles.append("pitch")
        notes.append(f"pitch: shifts by {m['pitch_shift_semitones']:+.1f} semitones")
    moves_pitch = m.get("pitch_wobble_hz", 0) >= 0.35
    if not time_based and thd < 10 and (m["amplitude_wobble_pct"] >= 8 or m["spectral_smear_pct"] >= 4 or moves_pitch):
        roles.append("modulation")
        kind = "chorus/flanger/vibrato" if moves_pitch else ("tremolo" if m["amplitude_wobble_pct"] >= 8 else "phaser/filter movement")
        notes.append(f"modulation: {kind}")
    if m["stereo_width_db"] > -12:
        if not time_based and "modulation" not in roles:
            roles.append("stereo")
        notes.append("makes a mono source stereo")
    if abs(m["gain_db"]) >= 3:
        notes.append(f"level: {m['gain_db']:+.1f} dB")
        if not roles:
            roles.append("gain")
    if m.get("latency_ms") and m["latency_ms"] >= 1:
        notes.append(f"latency: {m['latency_ms']:.0f} ms")
    if not roles:
        roles.append("no audible change")
        notes.append("no audible change at its default settings (a utility or meter, or it needs settings first)")
    return roles, "; ".join(notes)


def analyze_instrument(pitched: list[dict], kit: list[dict]) -> dict:
    """Combines listen.py measurements of octaves and of drum keys into a description."""
    from . import listen

    sounding = [r for r in pitched if not r.get("silent")]
    kit_sounding = [r for r in kit if not r.get("silent")]
    if not sounding and not kit_sounding:
        return {"roles": ["silent"], "summary": "makes no sound at its default settings (it may need a preset or samples "
                "loaded, or its hardware connected)"}
    patch = listen.describe_patch(pitched) if sounding else {"sounding": False}
    out: dict = {"patch": patch}
    # A late start is a sound that jumps in after silence; a slow fade-in isn't one.
    late = [r["starts_late_ms"] for r in sounding + kit_sounding
            if r.get("starts_late_ms", 0) >= 8 and r.get("attack_ms", 0) < 25]
    if late:
        out["starts_late_ms"] = round(float(np.median(late)), 1)
    roles: list[str] = []
    notes: list[str] = []
    if patch.get("follows_pitch"):
        roles.append("pitched instrument")
        character = patch.get("character", "")
        guess = []
        if "slow attack" in character:
            guess.append("pad")
        if "plucky" in character:
            guess.append("pluck/keys")
        if "sustained" in character and "slow attack" not in character:
            guess.append("lead/keys")
        if patch.get("median_brightness_hz", 1000) < 700:
            guess.append("bass")
        out["default_patch_suits"] = guess or ["keys"]
        notes.append(f"plays in tune from {patch['lowest_sounding']} to {patch['highest_sounding']}; default patch: {character}")
        if patch.get("transposition_semitones"):
            notes.append(f"sounds {patch['transposition_semitones']:+d} semitones from the played note")
    kinds = {listen.classify_drum(r)[0] for r in kit_sounding} - {"silent", "tonal", "percussion"}
    kit_follows, _ = listen.tracks_pitch(kit_sounding)
    if not patch.get("follows_pitch") and not kit_follows and len(kit_sounding) >= 4 and len(kinds) >= 3:
        lanes, labels = listen.map_kit(kit_sounding)
        roles.append("drum kit")
        out["drum_lanes"] = {lane: p for lane, p in lanes.items()}
        out["general_midi_layout"] = listen.follows_gm(lanes)
        notes.append(f"drum kit with {len(kit_sounding)} sounding keys in C2-D#3 (36-51)"
                     + (", General MIDI layout" if out["general_midi_layout"] else ", custom layout (run map_drum_kit)"))
    if not roles:
        roles.append("unpitched sound")
        notes.append("makes sound but doesn't follow pitch (a one-shot, noise or effect patch)")
    if late:
        notes.append(f"sounds start about {out['starts_late_ms']:.0f} ms late")
    out["roles"] = roles
    out["summary"] = "; ".join(notes)
    return out


class PluginCatalog:
    """What creaper has learned about each plugin by testing it, kept between sessions."""

    VERSION = 1

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def all(self) -> dict[str, dict]:
        data = jsonstore.read(self.path, dict)
        return data.get("plugins", {}) if data.get("version") == self.VERSION else {}

    def get(self, name: str) -> dict | None:
        return self.all().get(name)

    def put(self, name: str, entry: dict) -> None:
        with jsonstore.updating(self.path, dict, indent=1) as data:
            if data.get("version") != self.VERSION:  # an old format starts over, as before
                data.clear()
                data.update(version=self.VERSION, plugins={})
            data.setdefault("plugins", {})[name] = {**entry, "tested": time.strftime("%Y-%m-%d")}
