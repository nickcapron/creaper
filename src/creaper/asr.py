"""Optional (pip install "creaper[asr]"): what a listener would hear in a vocal, from a
speech recogniser, faster-whisper (MIT) running OpenAI's Whisper English model
converted for CTranslate2 (Systran/faster-whisper-base.en, MIT). Each lyric line of a
take (a robot vocal's word clips, or a sung VocalVST take's rendered audio) is
transcribed and compared word by word with the lyrics: lines the recogniser gets mostly
wrong are the ones listeners mishear ("Saturday night and the city is warm" came back
as "Sat turd day night and the synth tire is born" from a listener and a sung take
alike), so they can be rewritten before anyone listens. Nothing loads or downloads
(about 150 MB, once) until it's used, and only when the extra is installed."""

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
    return match_words(lyric, heard)[0]


def match_words(lyric: str, heard: str) -> tuple[float, list[str]]:
    """words_matched, and the lyric's key words that weren't heard ('rain' when 'cold
    rain on the glass' came back as 'coating on the glass'), in the lyric's order."""
    a, b = normalize(lyric), normalize(heard)
    a = [w for w in a if w not in SMALL_WORDS] or a
    if not a:
        return 1.0, []
    lyric_tokens = _join_compounds(a, set(b))
    heard_tokens = [t for t, _ in _join_compounds(b, set(a))]
    # best[i][j]: the most lyric words matched using the first i lyric tokens and j heard tokens.
    rows = [[0] * (len(heard_tokens) + 1)]
    for word, count in lyric_tokens:
        prev, row = rows[-1], [0] * (len(heard_tokens) + 1)
        for j, h in enumerate(heard_tokens, 1):
            row[j] = max(prev[j], row[j - 1], prev[j - 1] + count if word == h else 0)
        rows.append(row)
    # Walk back for the words that took part in the match; the rest were missed.
    matched: set[int] = set()
    i, j = len(lyric_tokens), len(heard_tokens)
    while i > 0 and j > 0:
        word, count = lyric_tokens[i - 1]
        if word == heard_tokens[j - 1] and rows[i][j] == rows[i - 1][j - 1] + count:
            matched.add(i - 1)
            i, j = i - 1, j - 1
        elif rows[i - 1][j] >= rows[i][j - 1]:
            i -= 1
        else:
            j -= 1
    missed = [word for k, (word, _) in enumerate(lyric_tokens) if k not in matched]
    return round(rows[-1][-1] / len(a), 2), missed


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
    """What the recogniser heard in each lyric line of a robot vocal (clips as placed:
    'path', 'start_qn', 'end_qn', 'word'), and the lines to rewrite."""
    entries = []
    for idx in group_lines(clips, seconds):
        lyric = " ".join(clips[i]["word"] for i in idx if clips[i]["word"] not in ("_", "-"))
        t0 = seconds[idx[0]][0]
        audio = line_audio([Path(clips[i]["path"]) for i in idx], [seconds[i][0] - t0 for i in idx])
        entries.append((lyric, {"at_qn": round(clips[idx[0]]["start_qn"], 3)}, audio))
    return report(entries, "sing again with replace=True")


LINE_TAIL_S = 0.25        # a sung line's last word rings on past its note


def hear_lines(audio: np.ndarray, fs: int, lines: list[dict], next_step: str = "render again") -> dict:
    """What the recogniser hears in each lyric line of a sung take: `audio` (mono, or
    frames x channels) at `fs`, and the lines as {'line': the words, 'start', 'end'} in
    seconds from the audio's start (plus anything else to carry into the report, such
    as 'at_bar'). Same report as check_lines."""
    from .perception import _resample

    mono = np.asarray(audio, dtype=np.float32)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    pad = np.zeros(int(PAD_S * RATE), dtype=np.float32)
    entries = []
    for ln in lines:
        a = max(0, int(round(ln["start"] * fs)))
        b = min(len(mono), int(round((ln["end"] + LINE_TAIL_S) * fs)))
        clip = _resample(mono[a:b], fs, RATE).astype(np.float32) if b > a else np.zeros(0, dtype=np.float32)
        peak = float(np.abs(clip).max()) if len(clip) else 0.0
        if peak > 0:
            clip = clip / peak * 0.9
        extra = {k: v for k, v in ln.items() if k not in ("line", "start", "end")}
        entries.append((ln["line"], extra, np.concatenate([pad, clip, pad])))
    return report(entries, next_step)


def report(entries: list[tuple[str, dict, np.ndarray]], next_step: str) -> dict:
    """The lines (lyric, extra fields, 16 kHz mono audio) transcribed and compared with
    their words; repeated lines heard the same way are reported once."""
    heard, seen = [], set()
    total = matched_total = 0.0
    for lyric, extra, audio in entries:
        text, unsure = transcribe(audio)
        share, missed = match_words(lyric, text)
        key_words = [w for w in normalize(lyric) if w not in SMALL_WORDS] or normalize(lyric)
        total += len(key_words)
        matched_total += share * len(key_words)
        if (lyric, tuple(normalize(text))) in seen:
            continue  # a repeated line heard the same way
        seen.add((lyric, tuple(normalize(text))))
        limit = 2 * len(lyric.split()) + 4
        if len(text.split()) > limit:  # a recogniser stuck repeating itself ('ah, ah, ah, ...')
            text = " ".join(text.split()[:limit]) + " ..."
        heard.append({"line": lyric, "heard_as": text, "words_matched": share, **extra})
        if missed and share < 1.0:
            heard[-1]["missed"] = missed[:8]
        if unsure:
            heard[-1]["unsure_of"] = unsure[:8]
    unclear = sorted({h["line"] for h in heard if h["words_matched"] < UNCLEAR}, key=[h["line"] for h in heard].index)
    out = {"heard": heard, "words_heard": round(matched_total / total, 2) if total else None,
           "heard_by": f"{MODEL} (speech recogniser, {LICENSE}); words_matched: the share of each line's key "
                       "words (not 'the', 'on', 'into') it heard; missed: the ones it didn't"}
    if unclear:
        out["unclear_lines"] = unclear
        out["unclear_next"] = ("A speech recogniser misheard these lines, so listeners will too: rewrite them "
                               "(common words, open vowels, fewer consonant clusters, the missed words first) "
                               f"and {next_step}.")
    if any("unsure_of" in h for h in heard):
        out["unsure_note"] = ("unsure_of: words heard right but barely; listeners often miss those too, so "
                              "consider rewriting those lines as well.")
    return out
