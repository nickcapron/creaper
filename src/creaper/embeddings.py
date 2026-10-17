"""Optional (pip install "creaper[ml]"): what a mix sounds like to a model trained on
music and its descriptions, LAION's CLAP (laion/larger_clap_music, Apache-2.0). It
places the mix between pairs of descriptions listeners use ("realistic instruments" or
"cheap synthetic", "modern production" or "90s game music") and measures how alike two
tracks sound. One line on the scorecard, never a gate: the model can be wrong, the
measurements decide. Nothing loads or downloads (about 800 MB, once) until it's used,
and only when the extra is installed."""

from __future__ import annotations

import importlib.util
from functools import lru_cache

import numpy as np

MODEL = "laion/larger_clap_music"
LICENSE = "Apache-2.0"
RATE = 48000              # what CLAP's feature extractor expects
WINDOW_S = 10.0           # CLAP hears 10 s at a time
WINDOWS = 3               # from the middle of the track, averaged
# (name, the description a listener would praise, the one they'd complain with)
PAIRS = [
    ("realism", "realistic acoustic instruments played by musicians", "cheap synthetic MIDI instruments"),
    ("era", "modern professionally produced music", "1990s video game music"),
    ("mix", "a clear, punchy, well mixed song", "a muddy, harsh amateur mix"),
    ("energy", "an energetic, driving track", "a flat, static loop"),
]


def available() -> bool:
    return all(importlib.util.find_spec(m) is not None for m in ("transformers", "torch"))


@lru_cache(maxsize=1)
def _model():
    from transformers import ClapModel, ClapProcessor  # the heavy import, only on first use

    return ClapModel.from_pretrained(MODEL).eval(), ClapProcessor.from_pretrained(MODEL)


def _windows(mono: np.ndarray, fs: int) -> list[np.ndarray]:
    from .perception import _resample

    x = _resample(mono, fs, RATE)
    n = int(WINDOW_S * RATE)
    if len(x) <= n:
        return [x]
    middle = len(x) // 2
    span = min(len(x) - n, n * WINDOWS)
    starts = np.linspace(middle - span // 2, middle + span // 2 - n, WINDOWS).astype(int).clip(0, len(x) - n)
    return [x[s: s + n] for s in sorted(set(starts.tolist()))]


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def audio_embedding(mono: np.ndarray, fs: int) -> np.ndarray:
    """One unit vector for a track: the mean of its middle windows' CLAP embeddings."""
    import torch

    model, processor = _model()
    with torch.no_grad():
        inputs = processor(audios=_windows(mono, fs), sampling_rate=RATE, return_tensors="pt")
        emb = model.get_audio_features(**inputs).cpu().numpy()
    return _unit(_unit(emb).mean(axis=0))


def text_embeddings(texts: list[str]) -> np.ndarray:
    import torch

    model, processor = _model()
    with torch.no_grad():
        inputs = processor(text=texts, return_tensors="pt", padding=True)
        return _unit(model.get_text_features(**inputs).cpu().numpy())


def character(audio_emb: np.ndarray, text_emb: np.ndarray, pairs=PAIRS, scale: float = 100.0) -> dict:
    """Where the track sits on each pair: the share (0-1) for the praising description,
    a softmax over the two cosine similarities at CLAP's logit scale."""
    out = {}
    for i, (name, good, bad) in enumerate(pairs):
        sims = text_emb[2 * i: 2 * i + 2] @ audio_emb * scale
        p = float(np.exp(sims[0] - sims.max()) / np.exp(sims - sims.max()).sum())
        out[name] = {"leans": good if p >= 0.5 else bad, "share": round(p, 2)}
    return out


def describe(mono: np.ndarray, fs: int) -> dict:
    """The scorecard's character line for a mix."""
    texts = [t for _, good, bad in PAIRS for t in (good, bad)]
    return {"model": MODEL, "license": LICENSE,
            "character": character(audio_embedding(mono, fs), text_embeddings(texts)),
            "how_to_read": "share: how far toward the first description (0.5 = undecided); a hint, not a verdict"}


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two tracks' embeddings: about 0.9 or more sounds alike."""
    return round(float(_unit(a) @ _unit(b)), 3)
