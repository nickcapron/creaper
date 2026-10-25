"""Fewer renders for the same measurements. A song with heavy instruments renders at
about twice real time, and calibrating a mix used to render it dozens of times: each
compressor rendered its whole track to find its loudest bars, then up to eight more
times, one track after another. Here:

- span hints: the loudest stretch of each track, found once from a render already made
  (auto_mix's first pass over every track), so calibrations don't render to find it;
- calibrate_many: every compressor that needs setting is searched at once, each step one
  render pass of all of them together (REAPER renders several stems in one pass);
- a predicted first guess: a model of the compressor run on the dry audio picks the
  threshold to start from, so the search usually lands in one or two renders;
- the limiter model master_to_target uses to pick its setting before rendering.

The measurement that decides is still the rendered one; the models only choose where
to look first."""

from __future__ import annotations

import math
import os
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from . import analysis, plugin_profiles

# --------------------------------------------------------------- span hints

_SPANS: dict[str, tuple[float, float]] = {}
ENV_HOP_S = 0.5     # the envelope's resolution: as loudest_span reads it


def track_envelope(audio: np.ndarray, fs: int) -> np.ndarray:
    """A track's power in ENV_HOP_S windows (mono): enough to find its loud stretch."""
    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    hop = int(ENV_HOP_S * fs)
    count = mono.size // hop
    if count == 0:
        return np.zeros(0)
    return np.mean(np.square(mono[: count * hop].astype(np.float64)).reshape(count, hop), axis=1)


def loudest_start_s(power: np.ndarray, span_s: float) -> float | None:
    """Start (s) of the loudest span_s in a power envelope; None if it's shorter or silent."""
    width = max(1, int(round(span_s / ENV_HOP_S)))
    if power.size <= width or not power.any():
        return None
    return float(np.argmax(np.convolve(power, np.ones(width), mode="valid")) * ENV_HOP_S)


@contextmanager
def span_hints(spans: dict[str, tuple[float, float]]):
    """While it lasts, calibrations of these tracks (by ref or name) measure on the given
    (start_bar, end_bar) instead of rendering the whole track to find its loud part."""
    before = {str(k): _SPANS.get(str(k)) for k in spans}
    _SPANS.update({str(k): v for k, v in spans.items() if v})
    try:
        yield
    finally:
        for k, v in before.items():
            if v is None:
                _SPANS.pop(k, None)
            else:
                _SPANS[k] = v


def hinted_span(track) -> tuple[float, float] | None:
    return _SPANS.get(str(track))


# ------------------------------------------------------------ group renders

def render_group(tracks: list, start_bar: float | None, end_bar: float | None) -> dict[str, np.ndarray]:
    """Several tracks' outputs over one range in a single render pass, by the ref they
    were asked for; the master (or a single track) through the ordinary render. Returns
    {ref: frames x channels}, plus the sample rate under '_fs'."""
    from . import server

    tracks = list(dict.fromkeys(tracks))
    if len(tracks) == 1 or "master" in tracks:
        out: dict = {}
        for t in tracks:
            audio, fs, _ = server._render_array(t, start_bar, end_bar)
            out[t], out["_fs"] = audio, fs
        return out
    import soundfile as sf

    from .export_tools import _check_renders

    details = {t: server.call("get_track_details", track=t) for t in tracks}
    names = {str(details[t].get("name")): t for t in tracks}
    numbers = {details[t].get("number"): t for t in tracks}
    stems = server.call("render_stems", timeout=900.0, tracks=tracks, start_bar=start_bar, end_bar=end_bar)
    files = stems.get("files", [])
    out = {}
    try:
        _check_renders(files)
        for s in stems.get("stems", []):
            ref = names.get(str(s["track"].get("name"))) or numbers.get(s["track"].get("number"))
            if ref is None:
                continue
            audio, fs = sf.read(s["file"], always_2d=True)
            out[ref], out["_fs"] = audio, int(fs)
    finally:
        if not os.environ.get("CREAPER_KEEP_RENDERS"):
            for f in files:
                Path(f).unlink(missing_ok=True)
    missing = [t for t in tracks if t not in out]
    for t in missing:     # anything the pass didn't give back, the slow way
        audio, fs, _ = server._render_array(t, start_bar, end_bar)
        out[t], out["_fs"] = audio, fs
    return out


# --------------------------------------------------------- compressor model

def _blocks_db(mono: np.ndarray, n: int, rms: bool) -> np.ndarray:
    count = mono.size // n
    if count == 0:
        return np.zeros(0)
    seg = mono[: count * n].reshape(count, n)
    level = np.sqrt(np.mean(seg ** 2, axis=1)) if rms else np.max(np.abs(seg), axis=1)
    return 20 * np.log10(level + 1e-12)


def simulate_compressor(audio: np.ndarray, fs: int, threshold_db: float, ratio: float, attack_ms: float,
                        release_ms: float, knee_db: float = 0.0, block_ms: float = 1.0) -> np.ndarray:
    """A feed-forward compressor at 1 ms resolution: an RMS detector, attack and release
    smoothing of the gain, a soft knee. Close enough to ReaComp to choose a threshold."""
    mono = audio.mean(axis=1) if audio.ndim > 1 else audio
    n = max(1, int(fs * block_ms / 1000))
    level = _blocks_db(mono.astype(np.float64), n, rms=True)
    over = level - threshold_db
    slope = 1 - 1 / max(1.0, ratio)
    if knee_db > 0:
        gr = np.where(over <= -knee_db / 2, 0.0,
                      np.where(over >= knee_db / 2, over * slope, slope * (over + knee_db / 2) ** 2 / (2 * knee_db)))
    else:
        gr = np.maximum(0.0, over) * slope
    a = math.exp(-block_ms / max(0.1, attack_ms))
    r = math.exp(-block_ms / max(1.0, release_ms))
    smooth = np.empty_like(gr)
    g = 0.0
    for i, target in enumerate(gr):
        g = a * g + (1 - a) * target if target > g else r * g + (1 - r) * target
        smooth[i] = g
    gain = np.repeat(10 ** (-smooth / 20), n)
    out = audio[: gain.size].astype(np.float64)
    return out * (gain[:, None] if out.ndim > 1 else gain)


def predict_threshold(dry: np.ndarray, fs: int, target_db: float, ratio: float, attack_ms: float,
                      release_ms: float, lo: float = -60.0, hi: float = 0.0) -> float | None:
    """The threshold at which the model takes target_db off the loud moments (read as
    analysis.gain_reduction reads a real render); None when it can't get there."""
    def reduction(t: float) -> float:
        wet = simulate_compressor(dry, fs, t, ratio, attack_ms, release_ms)
        return float(analysis.gain_reduction(dry[: wet.shape[0]], wet, fs, lag=0).get("gr_db_p95") or 0.0)

    if reduction(lo) < target_db * 0.5:
        return None
    for _ in range(14):           # bisection: reduction grows as the threshold falls
        mid = (lo + hi) / 2
        if reduction(mid) < target_db:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 2)


def _comp_settings(track, fx_index: int) -> dict[str, float]:
    """ReaComp's ratio, attack and release as set (defaults when they can't be read)."""
    from . import server

    out = {"ratio": 4.0, "attack": 10.0, "release": 100.0}
    try:
        params = server.call("get_fx_parameters", track=track, fx=fx_index, limit=60).get("parameters", [])
    except Exception:  # noqa: BLE001
        return out
    for p in params:
        key = {"Ratio": "ratio", "Attack": "attack", "Release": "release"}.get(p.get("name"))
        if key:
            try:
                out[key] = server._number(p.get("display", ""))
            except ValueError:
                pass
    return out


# ------------------------------------------------------- the drive search

class DriveSearch:
    """One compressor's search for the drive that takes target_db off its loud moments:
    the steps of the original calibration (grow while nothing changes, a secant step once
    two points are known, at most MAX_DRIVE_STEP_DB a step, an RMS floor for thresholds)."""

    def __init__(self, job: dict, drive: float, floor: float | None, max_step: float, tolerance: float = 0.3):
        self.job, self.drive, self.floor, self.max_step, self.tol = job, drive, floor, max_step, tolerance
        self.profile: plugin_profiles.Profile = job["profile"]
        self.target = job["target"]
        self.steps: list[dict] = []
        self.boost, self.previous = 1.0, None
        self.done = False

    def observe(self, reduction: float) -> float | None:
        """Record what the current drive does; the next drive to try, or None when done."""
        reduction = round(reduction, 2)
        self.steps.append({"drive": round(self.drive, 2), "loud_part_reduction_db": reduction})
        if abs(reduction - self.target) <= self.tol:
            self.done = True
            return None
        if self.previous is not None and abs(reduction - self.previous) < 0.15 and reduction < self.target:
            self.boost = min(self.boost * 2, 8.0)
        else:
            self.boost = 1.0
        self.previous = reduction
        new = plugin_profiles.next_drive(self.drive, reduction, self.target, self.profile, scale=self.boost)
        if len(self.steps) >= 2:
            d_drive = self.steps[-1]["drive"] - self.steps[-2]["drive"]
            d_red = self.steps[-1]["loud_part_reduction_db"] - self.steps[-2]["loud_part_reduction_db"]
            if d_drive and abs(d_red) > 0.05:
                new = self.drive + (self.target - reduction) * d_drive / d_red
        new = max(self.drive - self.max_step * self.boost, min(self.drive + self.max_step * self.boost, new))
        lo, hi = self.profile.drive_range or (-60, 60)
        new = max(lo, min(hi, new))
        if self.floor is not None and new < self.floor:
            if self.drive <= self.floor:
                self.done = True
                return None
            new = self.floor
        if new == self.drive:
            self.done = True
            return None
        self.drive = new
        return new


# Two renders of the same unchanged bars differing by more than this (p95 over 50 ms
# windows) can't have a compressor's gain reduction read off them: it's the search's own
# tolerance. Synths with free-running oscillators (Arturia's Prophet-VS, Jun-6) render
# differently every time: measured in the rig on a 90s pop song, the master differed
# from itself by 6 dB and the synth tracks by 3-8 dB, while sampler drums repeated
# exactly. Every master glue calibration had been reading that noise (4 dB with the
# threshold at 0, where it compresses nothing) and walking the threshold at random.
NOISE_FLOOR_DB = 0.3


def _read_noise_floor(jobs: list[dict], idx: list[int], searches: dict, lo_bar, hi_bar, fs: int) -> None:
    """For compressors whose first reading was off: renders their tracks once more with the
    compressors bypassed and reads the dry render against that. What it reads is noise, not
    compression; over NOISE_FLOOR_DB the search can't work, and the model's prediction (or
    the gentle starting setting) stands."""
    from . import server

    for i in idx:
        server.call("update_fx", track=jobs[i]["track"], fx=jobs[i]["fx"], enabled=False)
    try:
        again = render_group([jobs[i]["track"] for i in idx], lo_bar, hi_bar)
    finally:
        for i in idx:
            server.call("update_fx", track=jobs[i]["track"], fx=jobs[i]["fx"], enabled=True)
    for i in idx:
        s = searches[i]
        floor = analysis.gain_reduction(s.dry, again[jobs[i]["track"]], fs, lag=0).get("gr_db_p95") or 0.0
        s.noise = round(float(floor), 2)
        if s.noise > NOISE_FLOOR_DB:
            s.by_model, s.done = True, True
            s.steps.append({"drive": round(s.drive, 2), "loud_part_reduction_db": s.reading, "unreadable": True})


def _model_result(s: "DriveSearch") -> dict:
    modelled = s.predicted is not None
    out = {"control": s.profile.drive, "value": round(s.drive, 2),
           "loud_part_reduction_db": s.target if modelled else None, "target_db": s.target,
           "calibration": s.steps, **s.where, "repeat_noise_db": s.noise,
           "method": ("the compressor model on the dry render" if modelled
                      else "left at its starting setting: the renders can't be read"),
           "note": (f"two renders of these bars differ from each other by {s.noise:g} dB (instruments that play "
                    f"differently every time), more than a {s.target:g} dB target can be read through, so the "
                    + ("threshold is the model's: it takes about the target off the dry render in simulation"
                       if modelled else "compressor stays at its gentle starting setting"))}
    if modelled:
        out["predicted_start"] = s.predicted
    return out


def calibrate_many(jobs: list[dict], passes: int = 7) -> list[dict]:
    """Calibrates several compressors at once. Each job: {'track', 'fx', 'profile',
    'target' (dB), 'span': (start_bar, end_bar) or None for the given range,
    'sidechain': bool}. Jobs on the same span share every render: one pass for the dry
    (all their compressors bypassed), then one per step for all still searching. Returns
    one result per job, as _calibrate_compressor reports it."""
    from . import server

    results: list[dict | None] = [None] * len(jobs)
    groups: dict[tuple, list[int]] = {}
    for i, j in enumerate(jobs):
        groups.setdefault(tuple(j.get("span") or (None, None)), []).append(i)
    for span, idx in groups.items():
        try:
            _calibrate_group(jobs, idx, span, passes, results)
        except Exception as e:  # noqa: BLE001 - this group's parts; the others keep theirs
            for i in idx:
                if results[i] is None:
                    results[i] = {"error": str(e)}
    return results  # type: ignore[return-value]


def _calibrate_group(jobs: list[dict], idx: list[int], span: tuple, passes: int, results: list) -> None:
    from . import server

    lo_bar, hi_bar = span
    for i in idx:
        server.call("update_fx", track=jobs[i]["track"], fx=jobs[i]["fx"], enabled=False)
    try:
        dry = render_group([jobs[i]["track"] for i in idx], lo_bar, hi_bar)
    finally:
        for i in idx:
            server.call("update_fx", track=jobs[i]["track"], fx=jobs[i]["fx"], enabled=True)
    fs = dry["_fs"]
    searches: dict[int, DriveSearch] = {}
    for i in idx:
        j = jobs[i]
        where = {"measured_on_bars": [lo_bar, hi_bar]} if j.get("span") and j.get("report_span", True) else {}
        audio = dry[j["track"]]
        if float(abs(audio).max()) <= 1e-6:
            raise ValueError("that range is silent, so there's nothing to calibrate a compressor on")
        base = analysis.envelope_range(audio, fs)
        if base is None:
            raise ValueError("too little sound in that range to calibrate a compressor")
        profile, target = j["profile"], j["target"]
        params = server.call("get_fx_parameters", track=j["track"], fx=j["fx"], search=profile.drive)["parameters"]
        exact = next((p for p in params if p["name"] == profile.drive), None)
        if exact is None:
            raise ValueError(f"{profile.name} has no '{profile.drive}' control; its profile may be out of date")
        drive = server._number(exact["display"])
        if base < 2 * target and not j.get("sidechain"):
            results[i] = {"control": profile.drive, "value": round(drive, 2), "loud_part_reduction_db": 0.0,
                          "target_db": target, "calibration": [], **where,
                          "note": f"the material has little dynamic movement ({base:.1f} dB between loud and "
                                  "quiet moments), so the compressor was left at its gentle starting settings "
                                  "instead of being pushed"}
            continue
        rms = analysis._db(float((audio.astype("float64") ** 2).mean()) ** 0.5)
        floor = (rms - server.THRESHOLD_BELOW_RMS_DB
                 if (profile.drive_more == "down" and rms is not None and not j.get("sidechain")) else None)
        predicted = None
        if profile.name == "ReaComp" and profile.drive == "Threshold" and not j.get("sidechain"):
            k = _comp_settings(j["track"], j["fx"])
            predicted = predict_threshold(audio, fs, target, k["ratio"], k["attack"], k["release"],
                                          *(profile.drive_range or (-60, 0)))
            if predicted is not None and floor is not None:
                predicted = max(predicted, floor)
        s = DriveSearch(j, drive, floor, server.MAX_DRIVE_STEP_DB)
        s.where, s.dry, s.predicted = where, audio, predicted
        if predicted is not None and abs(predicted - drive) > 0.05:
            s.drive = predicted
            server.call("set_fx_parameters", track=j["track"], fx=j["fx"],
                        changes=[{"parameter": profile.drive, "display_value": predicted}])
        searches[i] = s
    for n_pass in range(passes):
        active = [i for i, s in searches.items() if not s.done]
        if not active:
            break
        wet = render_group([jobs[i]["track"] for i in active], lo_bar, hi_bar)
        off = []
        for i in active:
            s = searches[i]
            gr = analysis.gain_reduction(s.dry, wet[jobs[i]["track"]], fs, lag=getattr(s, "lag", None))
            s.lag = gr.get("lag_samples", getattr(s, "lag", None))   # a plugin's latency doesn't change
            s.reading = float(gr.get("gr_db_p95") or 0.0)
            if n_pass == 0 and abs(s.reading - s.target) > s.tol:
                off.append(i)
        if off:
            _read_noise_floor(jobs, off, searches, lo_bar, hi_bar, fs)
        for i in active:
            s = searches[i]
            if s.done:
                continue
            new = s.observe(s.reading)
            if new is not None:
                server.call("set_fx_parameters", track=jobs[i]["track"], fx=jobs[i]["fx"],
                            changes=[{"parameter": s.profile.drive, "display_value": new}])
    for i, s in searches.items():
        j = jobs[i]
        if getattr(s, "by_model", False):
            results[i] = _model_result(s)
            continue
        if not s.done and s.steps and s.steps[-1]["drive"] != round(s.drive, 2):
            # Out of passes right after a move: the last measured setting is what we know.
            s.drive = s.steps[-1]["drive"]
            server.call("set_fx_parameters", track=j["track"], fx=j["fx"],
                        changes=[{"parameter": s.profile.drive, "display_value": s.drive}])
        last = s.steps[-1] if s.steps else {"loud_part_reduction_db": 0.0}
        result = {"control": s.profile.drive, "value": round(s.drive, 2),
                  "loud_part_reduction_db": last["loud_part_reduction_db"], "target_db": s.target,
                  "calibration": s.steps, **s.where,
                  "method": "gain reduction read from dry and processed renders, on the loud part"}
        if s.predicted is not None:
            result["predicted_start"] = s.predicted
        if s.steps:
            best = min(s.steps, key=lambda st: abs(st["loud_part_reduction_db"] - s.target))
            if abs(best["loud_part_reduction_db"] - s.target) > 0.3 or best["drive"] != round(s.drive, 2):
                if best["drive"] != round(s.drive, 2):
                    server.call("set_fx_parameters", track=j["track"], fx=j["fx"],
                                changes=[{"parameter": s.profile.drive, "display_value": best["drive"]}])
                result.update(value=best["drive"], loud_part_reduction_db=best["loud_part_reduction_db"])
                if abs(best["loud_part_reduction_db"] - s.target) > 0.3:
                    result["note"] = (f"{s.profile.name} couldn't reach {s.target} dB here; kept the closest "
                                      f"setting ({best['loud_part_reduction_db']} dB). Its other controls "
                                      "(ratio/amount) can go further.")
        results[i] = result


# ------------------------------------------------------------ limiter model

LIMIT_BLOCK_S = 0.002     # the limiter model's resolution
LIMIT_RELEASE_MS = 30.0


def _limiter_gain(peaks: np.ndarray, threshold_db: float, release_ms: float = LIMIT_RELEASE_MS) -> np.ndarray:
    """Per block: the gain that holds the peaks (with a block of lookahead) to the
    threshold, falling at once and recovering with the release."""
    count = peaks.size
    ahead = np.maximum(peaks, np.concatenate([peaks[1:], [0.0]]))
    need = np.minimum(1.0, 10 ** (threshold_db / 20) / np.maximum(ahead, 1e-12))
    if need.min() >= 1.0:
        return need
    r = math.exp(-LIMIT_BLOCK_S * 1000 / release_ms)
    gain = np.empty(count)
    g = 1.0
    for i in range(count):
        want = need[i]
        g = want if want < g else r * g + (1 - r) * want
        gain[i] = g
    return gain


class LimiterModel:
    """ReaLimit as master_to_target drives it, on the audio reaching it: peaks over the
    threshold held to it, the result raised so the threshold sits at the ceiling, then
    the master fader. The audio is K-weighted and cut into 2 ms blocks once, so trying a
    setting costs a pass over the blocks, not over the audio: the integrated loudness
    (BS.1770 gating, as analysis.loudness measures it) comes from the blocks' energy."""

    def __init__(self, audio: np.ndarray, fs: int):
        from scipy import signal

        x = audio if audio.ndim > 1 else audio[:, None]
        self.x, self.fs = x, fs
        self.n = max(1, int(round(LIMIT_BLOCK_S * fs)))
        self.count = x.shape[0] // self.n
        cut = x[: self.count * self.n]
        self.peaks = np.abs(cut).max(axis=1).reshape(self.count, self.n).max(axis=1)
        sos = analysis.k_weighting_sos(fs)
        energy = np.zeros(self.count)
        for ch in range(x.shape[1]):
            z = signal.sosfilt(sos, x[:, ch].astype(np.float64))[: self.count * self.n]
            energy += np.square(z).reshape(self.count, self.n).sum(axis=1)
        self.energy = energy
        self.per_hop = max(1, int(round(0.1 / LIMIT_BLOCK_S)))

    def lufs(self, threshold_db: float, ceiling_db: float, fader_db: float = 0.0) -> float:
        gain = _limiter_gain(self.peaks, threshold_db)
        makeup = 10 ** ((ceiling_db - threshold_db + fader_db) / 10)       # as power
        blocks = self.energy * gain ** 2 * makeup
        hops = blocks.size // self.per_hop
        if hops < 4:
            return -70.0
        hop_energy = blocks[: hops * self.per_hop].reshape(hops, self.per_hop).sum(axis=1)
        cumulative = np.concatenate([[0.0], np.cumsum(hop_energy)])
        momentary = (cumulative[4:] - cumulative[:-4]) / (4 * self.per_hop * self.n)
        with np.errstate(divide="ignore"):
            level = -0.691 + 10 * np.log10(momentary)
        above = level > -70
        if not above.any():
            return -70.0
        gate = -0.691 + 10 * np.log10(momentary[above].mean()) - 10
        kept = above & (level > gate)
        return float(-0.691 + 10 * np.log10(momentary[kept].mean()))

    def render(self, threshold_db: float, ceiling_db: float, fader_db: float = 0.0) -> np.ndarray:
        gain = _limiter_gain(self.peaks, threshold_db)
        full = np.concatenate([np.repeat(gain, self.n), np.full(self.x.shape[0] - self.count * self.n, gain[-1])])
        return self.x * full[:, None] * 10 ** ((ceiling_db - threshold_db + fader_db) / 20)


def simulate_limiter(audio: np.ndarray, fs: int, threshold_db: float, ceiling_db: float, fader_db: float = 0.0,
                     release_ms: float = LIMIT_RELEASE_MS) -> np.ndarray:
    """The limiter model applied to audio (frames x channels)."""
    y = LimiterModel(audio, fs).render(threshold_db, ceiling_db, fader_db)
    return y if audio.ndim > 1 else y[:, 0]


def plan_limiter(audio: np.ndarray, fs: int, target_lufs: float, ceiling_db: float, min_threshold: float,
                 fader_db: float = 0.0, model: LimiterModel | None = None) -> dict:
    """The limiter threshold (and fader, for a mix already too loud) that the model says
    reaches target_lufs, held at min_threshold (the gain-reduction cap): {'threshold',
    'fader', 'lufs', 'true_peak', 'capped'}. audio is what reaches the limiter."""
    m = model or LimiterModel(audio, fs)
    floor = min(0.0, max(-30.0, min_threshold))   # a cap above 0 (a mix peaking over +5 dBFS) means no limiting
    at_zero = m.lufs(0.0, ceiling_db, fader_db)
    if at_zero <= -69.9:
        raise ValueError("the mix is silent in that range, so there's nothing to master")
    if at_zero >= target_lufs:          # too loud already: no limiting, the fader down
        threshold, fader = 0.0, fader_db + (target_lufs - at_zero)
    elif m.lufs(floor, ceiling_db, fader_db) < target_lufs:
        threshold, fader = floor, fader_db
    else:
        lo, hi = floor, 0.0
        for _ in range(14):
            mid = (lo + hi) / 2
            if m.lufs(mid, ceiling_db, fader_db) < target_lufs:
                hi = mid
            else:
                lo = mid
        threshold, fader = (lo + hi) / 2, fader_db
    y = m.render(threshold, ceiling_db, fader)
    tp = max(analysis.true_peak(y[:, ch], fs) for ch in range(y.shape[1]))
    return {"threshold": round(threshold, 2), "fader": round(fader, 2),
            "lufs": round(m.lufs(threshold, ceiling_db, fader), 2),
            "true_peak": analysis._db(tp), "capped": threshold <= floor + 0.05 and floor < 0}


# REAPER's JS Soft Clipper/Limiter (schwa), as it computes: level in its own dB
# (SOFT_CLIP_AMP per neper, a hair under 20/ln 10) plus Boost; over a knee that starts
# SOFT_CLIP_KNEE_DB under the Output Brickwall, the excess is bent (a*x + b*x^2) and
# capped at the brickwall.
SOFT_CLIP_AMP = 8.6562
SOFT_CLIP_KNEE_DB = -9.0
SOFT_CLIP_A, SOFT_CLIP_B = 1.017, -0.025
SOFT_CLIP_MAX_BOOST_DB = 9.0
MASTER_CLIP_OVER_DB = 3.0   # the master's clipper pushes the mix's peaks at most this far over its brickwall


def soft_clip(audio: np.ndarray, boost_db: float, brickwall_db: float = 0.0) -> np.ndarray:
    """REAPER's JS Soft Clipper/Limiter applied to audio, sample by sample: Boost (dB) and
    Output Brickwall (dB) as on its sliders."""
    x = np.asarray(audio, dtype=np.float64)
    with np.errstate(divide="ignore"):
        level = SOFT_CLIP_AMP * np.log(np.maximum(np.abs(x), 1e-30)) + boost_db
    knee = SOFT_CLIP_KNEE_DB + brickwall_db
    over = level - knee
    bent = SOFT_CLIP_A * over + SOFT_CLIP_B * over * over
    out = np.where(over > 0, np.minimum(knee + bent, brickwall_db), level)
    return np.exp(out / SOFT_CLIP_AMP) * np.sign(x)


def plan_master_clip(audio: np.ndarray, fs: int, target_lufs: float, ceiling_db: float, cap_db: float,
                     fader_db: float = 0.0, max_over_db: float = MASTER_CLIP_OVER_DB) -> dict | None:
    """When the limiter alone (its gain reduction capped at cap_db) can't reach
    target_lufs, the least soft clipping before it that lets it: the clipper's Boost set
    so the mix's peaks land over_db over its brickwall at 0 dBFS, tried at 1, 2 ...
    max_over_db. None when the limiter alone gets there; else {'boost_db', 'over_db',
    'peak_shaved_db' (how far the peaks came down), 'peak_db' (the clipped peak),
    'audio' (the clipped mix, for the limiter model), 'capped' (still short at
    max_over_db)}. audio is what reaches the clipper."""
    peak = analysis._db(float(np.abs(audio).max()))
    if not plan_limiter(audio, fs, target_lufs, ceiling_db, peak - cap_db, fader_db)["capped"]:
        return None
    plan = None
    over = 1.0
    while over <= max_over_db + 1e-9:
        boost = round(max(0.0, min(SOFT_CLIP_MAX_BOOST_DB, over - peak)), 1)
        clipped = soft_clip(audio, boost)
        cpeak = analysis._db(float(np.abs(clipped).max()))
        limited = plan_limiter(clipped, fs, target_lufs, ceiling_db, cpeak - cap_db, fader_db)
        plan = {"boost_db": boost, "over_db": over, "peak_shaved_db": round(peak + boost - cpeak, 1),
                "peak_db": cpeak, "audio": clipped, "capped": limited["capped"]}
        if not limited["capped"]:
            break
        over += 1.0
    return plan
