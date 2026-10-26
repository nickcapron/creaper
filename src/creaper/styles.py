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
    family: str = ""


def _from_genre(g) -> Style:
    m = g.mix
    return Style(g.name, tuple(g.aliases), m.lufs, m.lra, m.low_end, m.tone, m.width, g.tempo,
                 g.production, m.true_peak, tuple(g.instruments), g.family)


STYLES: tuple[Style, ...] = tuple(_from_genre(g) for g in genres.GENRES)

STREAMING_TARGETS = {"spotify": -14, "youtube": -14, "apple music": -16, "tidal": -14, "amazon music": -14,
                     "soundcloud": -14, "club": -7}


# Tone verdicts, as a share of the energy (%) in the loud part of the song (see
# analysis.tone_over_time). Calibrated on a set of finished masters: one judged
# piercing by ear had 13.6% of its energy at 2-5 kHz in its harshest seconds (p95);
# the others 2-11.5%. A darker genre tolerates less edge.
HARSH_P95_PCT = {"dark": 9.0, "warm": 10.0, "neutral": 12.0, "bright": 14.0}
HARSH_GATE_MARGIN = 2.0          # exports refuse this far over the warning (see harsh_limit)
SIBILANCE_P95_PCT = {"dark": 9.0, "warm": 10.0, "neutral": 12.0, "bright": 15.0}
MUD_MEDIAN_PCT = {"dark": 35.0, "warm": 35.0, "neutral": 30.0, "bright": 25.0}
SQUASHED_CREST_DB = 6.0          # even the liveliest seconds peak less than this over their RMS
LRA_FAIL_LU = 2.0                # under this the song has no sections, only one level


def harsh_limit(tone: str = "neutral", gate: bool = False) -> float:
    """The 2-5 kHz p95 share (%) a style's tone tolerates; with gate, the point where
    exports refuse rather than warn."""
    return HARSH_P95_PCT.get(tone, HARSH_P95_PCT["neutral"]) + (HARSH_GATE_MARGIN if gate else 0.0)


def is_ambient(style: Style | None) -> bool:
    """Styles where an almost flat level is the point (drones, ambient beds)."""
    return style is not None and ("ambient" in style.family or "ambient" in style.name.lower()
                                  or "drone" in style.name.lower())


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
    was measured, what's typical, and a verdict ('ok', 'high', 'low', 'check', or
    'fail' for a loudness range under 2 LU outside ambient styles).

    Loudness, peaks, dynamics, low-end mono and tone over time (harshness, sibilance,
    mud, squashing; judged against the style's tone) have verdicts. Low-end weight and
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
            else "quieter than a typical master: master_to_target brings it up; where it stopped short, compress "
                 "the peakiest parts it names (keeping their loudness) and master again")
    tp = analysis.get("levels", {}).get("true_peak_dbtp")
    if tp is not None:
        add("true peak (dBTP)", tp, f"<= {style.true_peak}", "ok" if tp <= style.true_peak else "high",
            "peaks above the ceiling can distort after MP3/AAC encoding; lower the limiter ceiling")
    lra = loud.get("loudness_range_lu")
    if lra is not None:
        lo, hi = style.lra
        verdict = "ok" if lo <= lra <= hi else ("high" if lra > hi else "low")
        duration = analysis.get("duration_seconds")
        if lra < LRA_FAIL_LU and not is_ambient(style) and (duration is None or duration >= GATE_MIN_SONG_S):
            verdict = "fail"
        add("loudness range (LU)", lra, [lo, hi], verdict,
            "more dynamic than typical: quiet parts may get lost; consider bus compression or automation"
            if verdict == "high" else
            f"under {LRA_FAIL_LU:g} LU: every section plays at the same level, so the song never lifts or "
            "breathes; give the sections different levels and density (thinner verses and breakdowns, a "
            "chorus or drop 1-2 LU up) and ease the master compression" if verdict == "fail" else
            "less dynamic than typical: sections may feel flat; ease compression/limiting")
    bands = analysis.get("spectrum", {}).get("bands", {})
    if bands:
        low = sum(bands.get(k, {}).get("share_pct", 0) for k in ("sub (20-60 Hz)", "bass (60-250 Hz)"))
        add("low end (% of energy below 250 Hz)", round(low, 1), f"{style.low_end} low end", "info")
    centroid = analysis.get("spectrum", {}).get("spectral_centroid_hz")
    if centroid:
        add("brightness (spectral centroid, Hz)", centroid, f"{style.tone} tone", "info")
    findings.extend(tone_findings(analysis.get("tone_over_time") or {}, style.tone))
    stereo = analysis.get("stereo", {})
    low_corr = stereo.get("low_end_correlation_below_150hz")
    if low_corr is not None:
        add("low-end mono compatibility", low_corr, ">= 0.8", "ok" if low_corr >= 0.8 else "check",
            "the low end is wide or out of phase; keep bass and kick mono below ~150 Hz")
    return findings


def tone_findings(tone: dict, style_tone: str = "neutral") -> list[dict]:
    """Verdicts on harshness, sibilance, mud and squashing from analysis.tone_over_time,
    judged against a style's tone ('dark' tolerates less edge than 'bright')."""
    out: list[dict] = []

    def add(area: str, measured, limit: float, over: bool, advice: str) -> None:
        if measured is None:
            return
        bad = measured > limit if over else measured < limit
        f = {"area": area, "measured": measured, "typical": f"{'<=' if over else '>='} {limit:g}",
             "verdict": ("high" if over else "low") if bad else "ok"}
        if bad:
            f["advice"] = advice
        out.append(f)

    add("harshness: 2-5 kHz share in the harshest seconds (%, p95)", tone.get("harsh_2_5k_pct_p95"),
        harsh_limit(style_tone), True,
        "piercing on headphones: find the track with the most 2-5 kHz (measure_tracks) and cut 2-3 dB around "
        "3 kHz, or pull back its brightness, resonance or drive; don't boost presence elsewhere to compensate")
    add("sibilance and fizz: 5-10 kHz share (%, p95)", tone.get("sibilance_5_10k_pct_p95"),
        SIBILANCE_P95_PCT.get(style_tone, SIBILANCE_P95_PCT["neutral"]), True,
        "hissy or fizzy: tame hats, cymbals or a bright synth with a high shelf or a de-esser")
    add("mud: 200-500 Hz share (%, median)", tone.get("mud_200_500_pct_median"),
        MUD_MEDIAN_PCT.get(style_tone, MUD_MEDIAN_PCT["neutral"]), True,
        "muddy or boxy: high-pass the parts that don't need lows (pads, keys, guitars) higher and dip "
        "250-400 Hz on the thickest one")
    add("liveliest seconds' crest factor (dB, p10)", tone.get("crest_db_p10"), SQUASHED_CREST_DB, False,
        "squashed: even its liveliest moments barely peak over their average; less limiting or bus compression")
    peaks = tone.get("resonances") or []
    if peaks:
        out.append({"area": "resonances (narrow peaks that stay put)", "verdict": "info",
                    "measured": [f"{p['hz']} Hz{' (' + p['note'] + ')' if p.get('note') else ''} "
                                 f"+{p['db_above_surroundings']:g} dB" for p in peaks],
                    "typical": "none",
                    "advice": "a peak on the key's root or fifth is likely a pedal or drone, not a problem; "
                              "otherwise a narrow 2-4 dB cut on the track that rings"})
    return out


GATE_MIN_SONG_S = 60.0   # loudness range is only judged on a whole song this long or longer


def gate_problems(measured: dict, style: Style | None = None, whole_song: bool = True) -> list[str]:
    """Why a mix shouldn't go out yet (export_mix and master_to_target refuse unless
    forced): it clips, it never changes level (a whole song with under 2 LU of loudness
    range, outside ambient styles), or it's piercing (2-5 kHz share in its harshest
    seconds over the style's limit). Loudness range and harshness are judged on whole
    songs of GATE_MIN_SONG_S or more only: a stinger, a hit or a region is meant to be
    what it is. measured: analyze_audio's result."""
    problems = []
    levels = measured.get("levels") or {}
    if levels.get("clipped_runs"):
        problems.append(f"it clips: {levels['clipped_runs']} flat-topped peaks at full scale. Lower the master or the "
                        "loudest track's output, or ease the plugin that's driving into 0 dB")
    song = whole_song and (measured.get("duration_seconds") or 0) >= GATE_MIN_SONG_S
    lra = (measured.get("loudness") or {}).get("loudness_range_lu")
    if song and lra is not None and lra < LRA_FAIL_LU and not is_ambient(style):
        problems.append(f"its loudness range is {lra:g} LU: every section plays at one level. Thin the verses and "
                        "breakdowns, lift the chorus or drop 1-2 LU, and ease the master compression")
    harsh = (measured.get("tone_over_time") or {}).get("harsh_2_5k_pct_p95")
    limit = harsh_limit(style.tone if style else "neutral", gate=True)
    if song and harsh is not None and harsh > limit:
        problems.append(f"it's piercing: {harsh:g}% of its energy sits at 2-5 kHz in its harshest seconds (limit "
                        f"{limit:g}% for a {style.tone if style else 'neutral'} style). measure_tracks shows which "
                        "track (harsh_pct_p95); cut 2-3 dB around 3 kHz there")
    return problems
