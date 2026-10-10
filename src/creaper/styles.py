"""Genre style profiles: typical loudness, dynamics, tone and stereo for released music.

These are rough ranges for commercial releases, collected as rules of thumb, not
standards: plenty of great records sit outside them. They give Claude a starting
point and something to measure a mix against.

Integrated loudness is for a finished master. Streaming services turn loud
masters down (Spotify and YouTube to about -14 LUFS, Apple Music to about -16),
so louder isn't louder for listeners there.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import genres


@dataclass(frozen=True)
class Style:
    name: str
    aliases: tuple[str, ...]
    lufs: tuple[float, float]         # integrated loudness of a typical master
    lra: tuple[float, float]          # loudness range (LU): dynamics over the song
    low_end: str                      # "light", "moderate", "heavy", "very heavy"
    tone: str                         # "dark", "warm", "neutral", "bright"
    width: str                        # "narrow", "moderate", "wide"
    tempo: tuple[int, int]
    notes: str
    true_peak: float = -1.0           # ceiling (dBTP) that survives lossy encoding
    elements: tuple[str, ...] = field(default=())


def _from_genre(g) -> Style:
    m = g.mix
    return Style(g.name, tuple(g.aliases), m.lufs, m.lra, m.low_end, m.tone, m.width, g.tempo,
                 g.production, m.true_peak, tuple(g.instruments))


STYLES: tuple[Style, ...] = tuple(_from_genre(g) for g in genres.GENRES)

STREAMING_TARGETS = {"spotify": -14, "youtube": -14, "apple music": -16, "tidal": -14, "amazon music": -14,
                     "soundcloud": -14, "club": -7}


def find_style(name: str) -> Style:
    return _from_genre(genres.find(name))


def describe(style: Style) -> dict:
    return {
        "style": style.name,
        "also": list(style.aliases),
        "integrated_lufs": list(style.lufs),
        "true_peak_ceiling_dbtp": style.true_peak,
        "loudness_range_lu": list(style.lra),
        "low_end": style.low_end,
        "tone": style.tone,
        "stereo_width": style.width,
        "tempo_bpm": list(style.tempo),
        "core_elements": list(style.elements),
        "notes": style.notes,
        "caveat": "typical of commercial releases, not rules; streaming turns loud masters down to about -14 LUFS",
    }


def compare(analysis: dict, style: Style) -> list[dict]:
    """Findings from analyze_audio output against a style; each has an area, what
    was measured, what's typical, and a verdict ('ok', 'high', 'low', 'check').

    Loudness, peaks, dynamics and low-end mono have verdicts. Low-end weight and
    tone come back as 'info' next to the style's description: how much energy sits
    where depends on the arrangement, so a fixed threshold would mislead; judge
    them by ear or against a reference track.
    """
    findings: list[dict] = []

    def add(area: str, measured, typical, verdict: str, advice: str | None = None) -> None:
        f = {"area": area, "measured": measured, "typical": typical, "verdict": verdict}
        if advice and verdict != "ok":
            f["advice"] = advice
        findings.append(f)

    loud = analysis.get("loudness", {})
    lufs = loud.get("integrated_lufs")
    if lufs is not None:
        lo, hi = style.lufs
        verdict = "ok" if lo <= lufs <= hi else ("high" if lufs > hi else "low")
        add("integrated loudness (LUFS)", lufs, [lo, hi], verdict,
            "louder than typical: more limiting than needed, and streaming will turn it down" if verdict == "high"
            else "quieter than a typical master (fine before mastering; master_to_target can bring it up)")
    tp = analysis.get("levels", {}).get("true_peak_dbtp")
    if tp is not None:
        add("true peak (dBTP)", tp, f"<= {style.true_peak}", "ok" if tp <= style.true_peak else "high",
            "peaks above the ceiling can distort after MP3/AAC encoding; lower the limiter ceiling")
    lra = loud.get("loudness_range_lu")
    if lra is not None:
        lo, hi = style.lra
        verdict = "ok" if lo <= lra <= hi else ("high" if lra > hi else "low")
        add("loudness range (LU)", lra, [lo, hi], verdict,
            "more dynamic than typical: quiet parts may get lost; consider bus compression or automation"
            if verdict == "high" else "less dynamic than typical: sections may feel flat; ease compression/limiting")
    bands = analysis.get("spectrum", {}).get("bands", {})
    if bands:
        low = sum(bands.get(k, {}).get("share_pct", 0) for k in ("sub (20-60 Hz)", "bass (60-250 Hz)"))
        add("low end (% of energy below 250 Hz)", round(low, 1), f"{style.low_end} low end", "info")
    centroid = analysis.get("spectrum", {}).get("spectral_centroid_hz")
    if centroid:
        add("brightness (spectral centroid, Hz)", centroid, f"{style.tone} tone", "info")
    stereo = analysis.get("stereo", {})
    low_corr = stereo.get("low_end_correlation_below_150hz")
    if low_corr is not None:
        add("low-end mono compatibility", low_corr, ">= 0.8", "ok" if low_corr >= 0.8 else "check",
            "the low end is wide or out of phase; keep bass and kick mono below ~150 Hz")
    return findings
