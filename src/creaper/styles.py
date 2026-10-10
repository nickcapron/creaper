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


STYLES: tuple[Style, ...] = (
    Style("pop", ("mainstream", "top 40"), (-10, -7), (4, 7), "moderate", "bright", "wide", (90, 130),
          "Vocal on top and upfront; punchy but controlled drums; polished, bright top end.",
          elements=("lead vocal", "drums", "bass", "keys/synths")),
    Style("hip-hop", ("hip hop", "rap", "boom bap"), (-10, -7), (4, 7), "heavy", "warm", "moderate", (80, 100),
          "Kick and bass carry the track; vocal clear and dry-ish; sampled textures fine to be a bit lo-fi.",
          elements=("drums", "808/bass", "samples", "vocal")),
    Style("trap", ("drill",), (-9, -6), (3, 6), "very heavy", "bright", "moderate", (130, 160),
          "Long 808s with mono sub; crisp rolling hats; sparse, loud, heavily compressed.",
          elements=("808", "hi-hats", "snare/clap", "vocal")),
    Style("house", ("deep house", "dance"), (-9, -7), (3, 6), "heavy", "neutral", "wide", (118, 128),
          "Four-on-the-floor kick and bass locked together; side-chain pumping common; mono low end.",
          elements=("kick", "bass", "hats/percussion", "chords")),
    Style("techno", (), (-9, -7), (3, 6), "heavy", "dark", "wide", (125, 140),
          "Kick dominates; hypnotic, repetitive; dark, driving low mids; wide atmospherics.",
          elements=("kick", "rumble/bass", "percussion", "textures")),
    Style("edm", ("electro", "big room", "future bass"), (-8, -5), (3, 6), "heavy", "bright", "wide", (124, 150),
          "Very loud and dense; huge drops; aggressive limiting and side-chain.",
          elements=("kick", "bass", "lead", "fx")),
    Style("drum and bass", ("dnb", "jungle", "liquid"), (-8, -6), (3, 7), "very heavy", "bright", "wide", (165, 178),
          "Fast breakbeats; deep sub-bass under midrange bass; snare cuts through.",
          elements=("breaks", "sub", "reese/mid bass", "pads")),
    Style("dubstep", ("bass music", "riddim"), (-7, -5), (3, 6), "very heavy", "bright", "wide", (138, 150),
          "Half-time drums; heavy, aggressive mid bass over a mono sub; very loud.",
          elements=("kick/snare", "sub", "mid bass", "fx")),
    Style("lo-fi", ("lofi", "lofi hip hop", "chillhop"), (-14, -10), (4, 8), "moderate", "dark", "moderate", (70, 90),
          "Soft, dusty, rolled-off highs; relaxed drums; vinyl or tape character; quiet compared with pop.",
          elements=("dusty drums", "keys", "bass", "texture")),
    Style("rock", ("alt rock", "classic rock"), (-10, -8), (4, 8), "moderate", "neutral", "wide", (100, 140),
          "Guitars wide, drums punchy, bass supports the kick; vocal sits in the band.",
          elements=("drums", "bass", "guitars", "vocal")),
    Style("metal", ("heavy metal", "metalcore"), (-9, -6), (3, 6), "heavy", "bright", "wide", (100, 200),
          "Dense, saturated guitars; tight low end; clicky kick; aggressive limiting.",
          elements=("drums", "rhythm guitars", "bass", "vocal")),
    Style("indie", ("indie rock", "indie pop", "alternative"), (-12, -9), (5, 9), "moderate", "warm", "wide", (90, 140),
          "More dynamic and less polished than pop; character over perfection.",
          elements=("drums", "guitars/synths", "bass", "vocal")),
    Style("r&b", ("rnb", "soul", "neo soul", "90s r&b"), (-11, -8), (4, 8), "heavy", "warm", "moderate", (65, 100),
          "Smooth, warm low end; lush vocals and harmonies; soft, swung drums.",
          elements=("vocal", "keys", "bass", "drums")),
    Style("synthwave", ("retrowave", "80s", "outrun"), (-11, -8), (4, 7), "moderate", "bright", "wide", (80, 118),
          "Gated-reverb snares, analog-style pads and arps, wide chorus; nostalgic and glossy.",
          elements=("drums", "bass arp", "pads", "lead")),
    Style("trip-hop", ("downtempo",), (-12, -9), (5, 9), "heavy", "dark", "wide", (70, 100),
          "Slow, moody breakbeats; deep bass; cinematic, smoky textures.",
          elements=("breaks", "bass", "atmospheres", "vocal")),
    Style("jazz", ("jazz trio", "big band"), (-18, -12), (8, 15), "light", "warm", "wide", (60, 220),
          "Natural dynamics, little limiting; real room sound; instruments balanced as if live.",
          elements=("piano", "bass", "drums", "horns")),
    Style("acoustic", ("folk", "singer-songwriter", "country"), (-16, -11), (6, 12), "light", "warm", "moderate", (70, 130),
          "Natural, intimate; vocal and acoustic instruments close and clear; gentle compression.",
          elements=("vocal", "acoustic guitar", "light percussion")),
    Style("cinematic", ("film score", "trailer", "orchestral"), (-18, -12), (8, 18), "moderate", "neutral", "wide", (60, 140),
          "Big dynamic arcs from quiet to huge; wide, deep reverbs; space for impacts.",
          elements=("strings", "brass", "percussion", "synths")),
    Style("classical", ("orchestra", "chamber"), (-24, -16), (10, 20), "light", "neutral", "wide", (40, 180),
          "Preserve dynamics; no obvious compression or limiting; realistic hall sound.",
          elements=("ensemble",)),
    Style("ambient", ("drone", "new age"), (-20, -14), (6, 14), "moderate", "dark", "wide", (50, 100),
          "Slow-evolving textures; soft transients; space and depth over punch.",
          elements=("pads", "textures", "drones")),
)

STREAMING_TARGETS = {"spotify": -14, "youtube": -14, "apple music": -16, "tidal": -14, "amazon music": -14,
                     "soundcloud": -14, "club": -7}


def find_style(name: str) -> Style:
    wanted = name.strip().lower()
    for style in STYLES:
        if wanted == style.name or wanted in style.aliases:
            return style
    for style in STYLES:
        if wanted in style.name or any(wanted in a for a in style.aliases):
            return style
    raise ValueError(f"no style profile for '{name}'. Known: {', '.join(s.name for s in STYLES)}")


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
