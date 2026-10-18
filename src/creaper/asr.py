"""Optional (pip install "creaper[asr]"): what a listener would hear in a robot vocal,
from a speech recogniser, faster-whisper (MIT) running OpenAI's Whisper English model
converted for CTranslate2 (Systran/faster-whisper-base.en, MIT). Each lyric line of a
take is transcribed from the processed vocal and compared word by word with the
lyrics: lines the recogniser gets mostly wrong are the ones listeners mishear, so they
can be rewritten before anyone listens. Nothing loads or downloads (about 150 MB,
once) until it's used, and only when the extra is installed."""

from __future__ import annotations

import importlib.util
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

MODEL = "Systran/faster-whisper-base.en"
# A fixed commit: a later change to the model repo isn't downloaded. model.bin is
# CTranslate2's own weight format (no pickle, no code runs from it).
REVISION = "3d3d5dee26484f91867d81cb899cfcf72b96be6c"
FILES = ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]
LICENSE = "MIT"
RATE = 16000              # what Whisper hears
LINE_REST_QN = 1.0        # a rest this long between words ends a line
MAX_LINE_S = 25.0         # Whisper hears 30 s at a time; longer lines are split
PAD_S = 0.3               # silence either side of a line
# Lines with fewer of their key words heard than this are unclear: one key word in four
# heard wrong ('cold pain on the glass', 'more than waking up') is a misheard line.
UNCLEAR = 0.8
# Small words don't count: a recogniser (or a listener) fills in 'on the' from context,
# so 'coating on the glass' for 'cold rain on the glass' is one word in three heard.
SMALL_WORDS = {"a", "an", "the", "and", "or", "but", "of", "on", "in", "into", "to", "at", "by", "for", "from",
               "with", "up", "as", "is", "it", "its", "my", "your", "i", "you", "me", "we"}
# Words heard with less confidence than this are named as unsure even when right: on
# test renders that caught 2 more of 18 misheard takes, and named 1 clear take of 18.
UNSURE = 0.3


def available() -> bool:
    return importlib.util.find_spec("faster_whisper") is not None


@lru_cache(maxsize=1)
def _model():
    import logging
    import os

    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # Windows without Developer Mode
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")     # no 'Fetching 4 files' in the log
    from faster_whisper import WhisperModel  # the heavy import, only on first use
    from huggingface_hub import snapshot_download

    logging.getLogger("faster_whisper").setLevel(logging.WARNING)  # not a line per clip

    path = snapshot_download(MODEL, revision=REVISION, allow_patterns=FILES)
    return WhisperModel(path, device="cpu", compute_type="float32")  # int8 was slower here, and looped more


def transcribe(audio: np.ndarray) -> tuple[str, list[str]]:
    """What the recogniser hears in mono 16 kHz audio, and the words it was unsure of.
    No prompt and no previous text, so it can't lean on the lyrics: it has only the
    sound to go on."""
    segments, _ = _model().transcribe(audio.astype(np.float32), language="en", beam_size=5,
                                      condition_on_previous_text=False, vad_filter=False, word_timestamps=True)
    segments = list(segments)
    unsure = [w.word.strip(" .,!?") for s in segments for w in (s.words or []) if w.probability < UNSURE]
    return " ".join(s.text.strip() for s in segments).strip(), unsure


def normalize(text: str) -> list[str]:
    """Lowercase words without punctuation; hyphenated syllables joined ('to-night'
    is 'tonight'), lone holds ('_', '-') dropped, apostrophes dropped ("don't" is 'dont')."""
    words = []
    for token in text.lower().split():
        w = re.sub(r"[^a-z0-9]", "", token.replace("-", ""))
        if w:
            words.append(w)
    return words


def _join_compounds(words: list[str], other: set[str]) -> list[tuple[str, int]]:
    # 'street lights' heard as 'streetlights' (or the other way round) is the same
    # words: each token with how many words it was made of.
    out, i = [], 0
    while i < len(words):
        if i + 1 < len(words) and words[i] + words[i + 1] in other:
            out.append((words[i] + words[i + 1], 2))
            i += 2
        else:
            out.append((words[i], 1))
            i += 1
    return out


def words_matched(lyric: str, heard: str) -> float:
    """The share (0-1) of the lyric's key words the recogniser heard, in order (the
    longest common subsequence of the two word lists); a line of only small words
    counts them all."""
    a, b = normalize(lyric), normalize(heard)
    a = [w for w in a if w not in SMALL_WORDS] or a
    if not a:
        return 1.0
    lyric_tokens = _join_compounds(a, set(b))
    heard_tokens = [t for t, _ in _join_compounds(b, set(a))]
    # best[j]: the most lyric words matched using the first j heard tokens.
    best = [0] * (len(heard_tokens) + 1)
    for word, count in lyric_tokens:
        diagonal = 0
        for j, h in enumerate(heard_tokens, 1):
            above = best[j]
            best[j] = max(above, best[j - 1], diagonal + count if word == h else 0)
            diagonal = above
    return round(best[-1] / len(a), 2)


def group_lines(clips: list[dict], seconds: list[tuple[float, float]], rest_qn: float = LINE_REST_QN,
                max_s: float = MAX_LINE_S) -> list[list[int]]:
    """The lyric lines of a take: the word clips (in order, each with 'start_qn',
    'end_qn') split at rests of rest_qn or more, and before any line would pass max_s.
    `seconds` is each clip's (start, end) in seconds. Returns lists of clip indexes."""
    lines: list[list[int]] = []
    for i, clip in enumerate(clips):
        if lines:
            prev = clips[lines[-1][-1]]
            if clip["start_qn"] - prev["end_qn"] < rest_qn - 1e-6 and seconds[i][1] - seconds[lines[-1][0]][0] <= max_s:
                lines[-1].append(i)
                continue
        lines.append([i])
    return lines


def line_audio(paths: list[Path], offsets: list[float], pad: float = PAD_S) -> np.ndarray:
    """A line's processed words mixed to mono 16 kHz, each at its offset in seconds from
    the line's start, with `pad` seconds of silence either side."""
    import soundfile as sf

    from .perception import _resample

    parts = []
    for path, at in zip(paths, offsets):
        x, fs = sf.read(str(path), dtype="float32", always_2d=True)
        parts.append((int(round((at + pad) * RATE)), _resample(x.mean(axis=1), fs, RATE)))
    out = np.zeros(max(s + len(x) for s, x in parts) + int(pad * RATE), dtype=np.float32)
    for s, x in parts:
        out[s: s + len(x)] += x
    peak = float(np.abs(out).max())
    return out / peak * 0.9 if peak > 0 else out


def check_lines(clips: list[dict], seconds: list[tuple[float, float]]) -> dict:
    """What the recogniser heard in each lyric line of a take (clips as placed: 'path',
    'start_qn', 'end_qn', 'word'), and the lines to rewrite."""
    heard, seen = [], set()
    for idx in group_lines(clips, seconds):
        lyric = " ".join(clips[i]["word"] for i in idx if clips[i]["word"] not in ("_", "-"))
        t0 = seconds[idx[0]][0]
        text, unsure = transcribe(line_audio([Path(clips[i]["path"]) for i in idx],
                                             [seconds[i][0] - t0 for i in idx]))
        if (lyric, tuple(normalize(text))) in seen:
            continue  # a repeated line heard the same way
        seen.add((lyric, tuple(normalize(text))))
        limit = 2 * len(lyric.split()) + 4
        if len(text.split()) > limit:  # a recogniser stuck repeating itself ('ah, ah, ah, ...')
            text = " ".join(text.split()[:limit]) + " ..."
        heard.append({"line": lyric, "heard_as": text, "words_matched": words_matched(lyric, text),
                      "at_qn": round(clips[idx[0]]["start_qn"], 3)})
        if unsure:
            heard[-1]["unsure_of"] = unsure[:8]
    unclear = sorted({h["line"] for h in heard if h["words_matched"] < UNCLEAR}, key=[h["line"] for h in heard].index)
    out = {"heard": heard, "heard_by": f"{MODEL} (speech recogniser, {LICENSE}); words_matched: the share of "
                                      "each line's key words (not 'the', 'on', 'into') it heard"}
    if unclear:
        out["unclear_lines"] = unclear
        out["unclear_next"] = ("A speech recogniser misheard these lines, so listeners will too: rewrite them "
                               "(common words, open vowels, fewer consonant clusters) and sing again with "
                               "replace=True.")
    if any("unsure_of" in h for h in heard):
        out["unsure_note"] = ("unsure_of: words heard right but barely; listeners often miss those too, so "
                              "consider rewriting those lines as well.")
    return out
