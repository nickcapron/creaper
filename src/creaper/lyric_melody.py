"""Words first: a sung line whose rhythm comes from the lyrics. The verse of a synth-funk
song came out as one syllable per beat on identical notes with one breath in 24 notes,
because write_melody writes an instrument line and the words were glued on afterwards.
Here each line is split into syllables, the stressed ones land on beats and the
unstressed ones between them, the last word of a line is held and a breath follows,
pickups start before the bar, lines that repeat their words repeat their tune, and the
pitches follow the chords (chord tones on the stressed syllables, steps between).

English syllables and stresses come from the CMU Pronouncing Dictionary when VocalVST's
copy is installed (the singer splits a word's sounds over the syllables it is given, so
the count has to be the dictionary's: 'neon' on one note came out "neonnoonn"), by
rule otherwise, and a hyphen in the input ('to-night') is always kept as written."""

from __future__ import annotations

import math
import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import composer
from .harmony import Key

VOWELS = set("aeiou")
# Monosyllables that take no stress in a sung line.
FUNCTION_WORDS = {
    "a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "at", "by", "for", "from", "with", "as", "if",
    "so", "than", "that", "this", "it", "its", "it's", "is", "are", "was", "were", "be", "been", "am", "i", "i'm",
    "i'll", "i've", "i'd", "you", "you're", "you'll", "you've", "your", "he", "she", "we", "we're", "we'll",
    "they", "them", "me", "him", "her", "us", "my", "his", "our", "their", "him", "do", "did", "does", "has",
    "have", "had", "can", "could", "will", "would", "should", "shall", "may", "might", "must", "up", "out",
    "oh", "yeah", "when", "then", "there", "here", "not", "no", "yes", "just", "like", "some", "all", "oh",
    "let", "get", "got", "been", "into", "'cause", "cause", "till", "until", "while", "though",
}
# Words that keep the stress on their first syllable despite the suffix rule.
# Two-syllable words starting with these take the stress on the second syllable (be-GIN,
# a-WAY, re-TURN, to-NIGHT); longer ones start their stress there too (be-GIN-ning).
UNSTRESSED_PREFIXES = {"a", "be", "re", "de", "pre", "pro", "per", "un", "en", "em", "ex", "e", "in", "im", "dis",
                       "mis", "to", "for", "sur", "sub", "con", "com", "ad", "ob", "o", "sup", "trans", "a-"}
PREFIX_EXCEPTIONS = {"baby", "open", "over", "under", "into", "also", "any", "every", "only", "ever", "even",
                     "after", "enter", "exit", "promise", "problem", "person", "perfect", "music", "river",
                     "recent", "record", "reason", "distant", "concert", "common", "comfort", "forest",
                     "forty", "former", "insight", "image", "income", "inner", "instant", "subway", "super",
                     "summer", "sunny", "under", "unit", "empty", "ending", "engine", "obvious", "everybody",
                     "everyone", "everything", "evening", "easy", "early", "ocean", "only"}
# A final syllable spelled like one of these is unstressed.
UNSTRESSED_SUFFIXES = ("ing", "er", "ers", "ed", "es", "y", "ly", "le", "les", "en", "est", "ness", "ful", "less",
                       "ment", "tion", "sion", "ous", "al", "ive", "age", "ance", "ence", "ity", "ty")
DIGRAPHS = ("th", "sh", "ch", "ph", "wh")

ARTICULATION_QN = 0.05   # the gap between syllables, so the singer re-attacks each one
SUNG_SHARE = 0.6         # how much of a line's span the words take before the last one is held
HOLD_SHARE = 0.7         # how much of what's left the last word then holds
BREATH_QN = 1.0          # the rest after a line
HOLD_QN = {"verse": 1.5, "chorus": 2.5, "bridge": 2.0}   # how long a line's last word is held, at least
SHAPE_HEIGHT = {"verse": 0.35, "chorus": 0.65, "bridge": 0.5}
SHAPE_ARC = {"verse": 4, "chorus": 5, "bridge": 4}       # scale steps the line rises over its start
VELOCITY = {"stressed": 100, "unstressed": 76, "final": 90}


# ------------------------------------------------------------------ syllables

# VocalVST ships the CMU dictionary beside its binary and looks a hyphenated word up
# whole, then splits the sounds over the typed syllables: fewer syllables than the word
# has vowels squeezes two vowels onto one note, more pads with the last vowel. So when
# that dictionary is on this machine its syllable count and stresses decide, and the
# spelling rules only shape the pieces (and stand in for words it lacks, and in CI).
_dictionary_cache: dict[str, str] | None = None
_phones_cache: dict[str, str] = {}      # word -> its CMU phones, lower case, no stress digits

# Pronunciation overrides (VocalVST builds from 2026-10-25 evening): 'Sa-tur-day[s ae dx er d ey]'
# replaces the dictionary's sounds for that word; the phonemes are split over the hyphenated
# pieces at the vowels, so the override needs as many vowels as the word has pieces. Symbols are
# lower-case ARPAbet without stress digits plus dx (the American flap) and ax (schwa); one the
# voicebank lacks is substituted or dropped and named on the plugin's Rendered line.
OVERRIDE_RE = re.compile(r"\[([^\]]*)\]")
TOKEN_RE = re.compile(r"[^\s\[\]]*\[[^\]]*\][^\s\[\]]*|\S+")
ARPABET = set("aa ae ah ao aw ay b ch d dh eh er ey f g hh ih iy jh k l m n ng ow oy p r s sh t th uh uw v w y z zh "
              "dx ax".split())
ARPABET_VOWELS = {p for p in ARPABET if p[0] in "aeiou"}
# Overrides picked by ear (the user A/B'd three Saturdays on TIGER disco): the bank's own
# 'saturday' flaps the d of 'day' too, so it sang "Sat-er-ray".
PRONOUNCE = {"saturday": "s ae dx er d ey"}
OVERRIDES_SINCE = 1792976400.0    # 2026-10-26 01:00 UTC (18:00 Pacific): plugin builds older than this read '[s ae]' as words


def tokens(lyrics: str) -> list[str]:
    """A lyric string's tokens: whitespace-separated, except that a pronunciation
    override's brackets hold together ('Sa-tur-day[s ae dx er d ey]' is one token)."""
    return TOKEN_RE.findall(lyrics)


def split_override(token: str) -> tuple[str, list[str] | None]:
    """The token without its override, and the override's phonemes (None when it has
    none): 'Sa-tur-day[S AE1 dx er d ey],' -> ('Sa-tur-day,', ['s', 'ae', 'dx', 'er', 'd', 'ey'])."""
    m = OVERRIDE_RE.search(token)
    if not m:
        return token, None
    phones = [re.sub(r"[0-9]", "", p.lower()) for p in m.group(1).split()]
    return token[:m.start()] + token[m.end():], phones


def has_overrides(lyrics: str) -> bool:
    return bool(OVERRIDE_RE.search(lyrics))


def strip_overrides(lyrics: str) -> str:
    """The lyrics without their overrides (a bracket on its own becomes 'm')."""
    out = []
    for tk in tokens(lyrics):
        plain, phones = split_override(tk)
        out.append(plain or (phones and "".join(p for p in phones if p.isalpha())[:3]) or "m")
    return " ".join(out)


def overrides_supported() -> bool:
    """Whether the installed VocalVST reads pronunciation overrides: its binary is newer
    than OVERRIDES_SINCE. True when no plugin is found (nothing to lose)."""
    for path in _cmudict_paths():
        binary = path.parent / "VocalVST.vst3"
        try:
            if binary.is_file():
                return binary.stat().st_mtime >= OVERRIDES_SINCE
        except OSError:
            continue
    return True


def phones(word: str) -> list[str] | None:
    """A word's CMU phonemes (lower case, no stress) when the dictionary is installed."""
    dictionary()
    found = _phones_cache.get(_dictionary_key(word))
    return found.split() if found else None


def suggest_override(token: str) -> str | None:
    """How to spell a word's sounds for the singer, hyphenated as typed: the override
    picked by ear when there is one (PRONOUNCE), else the dictionary's own phonemes
    (which the bank's dictionary may differ from; a listener decides); None for a word
    nobody has sounds for."""
    plain, _ = split_override(token)
    key = _dictionary_key(plain)
    sounds = PRONOUNCE.get(key) or " ".join(phones(plain) or [])
    if not sounds:
        return None
    return re.sub(r"[^A-Za-z'-]", "", plain) + "[" + sounds + "]"


def _cmudict_paths() -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData/Local"))
    programs = Path(os.environ.get("ProgramFiles") or r"C:\Program Files")
    tail = Path("VocalVST.vst3/Contents/x86_64-win/cmudict.dict")
    paths = [local / "Programs/Common/VST3" / tail, programs / "Common Files/VST3" / tail]
    if os.environ.get("CREAPER_CMUDICT"):
        paths.insert(0, Path(os.environ["CREAPER_CMUDICT"]))
    return paths


def _read_cmudict(path: Path) -> dict[str, str]:
    """word -> its stress digits, one per syllable ('saturday' -> '100'); the first
    pronunciation of a word stands, 'word(2)' variants are skipped."""
    out: dict[str, str] = {}
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip() or line[0] in ";#":
                continue
            word, _, sounds = line.partition(" ")
            if "(" in word:
                continue
            digits = "".join(c for c in sounds if c in "012")
            if digits:
                out[word] = digits
                _phones_cache[word] = re.sub(r"[0-9]", "", sounds.strip().lower())
    return out


def dictionary() -> dict[str, str]:
    """The pronouncing dictionary, read once (126k words, 0.1 s); {} when none is installed."""
    global _dictionary_cache
    if _dictionary_cache is None:
        _dictionary_cache = {}
        for path in _cmudict_paths():
            try:
                if path.is_file():
                    _dictionary_cache = _read_cmudict(path)
                    break
            except OSError:
                continue
    return _dictionary_cache


def _dictionary_key(word: str) -> str:
    return re.sub(r"[^a-z']", "", word.lower())


def _vowel_groups(w: str) -> list[tuple[int, int]]:
    """(start, end) of each vowel group in a lowercase word; y counts as a vowel after
    a consonant, u after q doesn't."""
    groups: list[tuple[int, int]] = []
    i = 0
    while i < len(w):
        c = w[i]
        vowel = c in VOWELS or (c == "y" and i > 0 and w[i - 1] not in VOWELS)
        if c == "u" and i > 0 and w[i - 1] == "q":
            vowel = False
        if vowel:
            j = i + 1
            while j < len(w) and (w[j] in VOWELS or w[j] == "y"):
                j += 1
            groups.append((i, j))
            i = j
        else:
            i += 1
    return groups


def syllabify(word: str) -> list[str]:
    """A word's syllables: 'baby' -> ba-by, 'candle' -> can-dle, 'waiting' -> wait-ing,
    'burned' and 'lines' stay whole. The spelling rules cut the word; the dictionary,
    when installed, says how many pieces there are ('ne-on', 'fi-re', 'eve-ning'). A
    hyphenated word is split as written."""
    word, override = split_override(word)
    pieces = _syllabify_plain(word)
    if override is not None:
        pieces[-1] += "[" + " ".join(override) + "]"
    return pieces


def _syllabify_plain(word: str) -> list[str]:
    if "-" in word.strip("-"):
        return [p for p in word.split("-") if p]
    if not any(c.isalpha() for c in word):
        return [word]
    pieces = _syllabify_by_rule(word)
    want = len(dictionary().get(_dictionary_key(word), ""))
    if want and want != len(pieces):
        pieces = _repiece(word, pieces, want)
    return pieces


def _repiece(word: str, pieces: list[str], want: int) -> list[str]:
    """The word in `want` pieces: more come from cutting the rule's merged endings back
    apart ('fi-re') and then vowel groups between their letters ('ne-on', 'po-em', the
    longest group first); fewer merge the shortest piece into its neighbour ('eve-ning')."""
    bounds = {sum(len(p) for p in pieces[:i]) for i in range(1, len(pieces))}
    while len(bounds) + 1 < want:
        idx = [i for i, c in enumerate(word) if c != "'"]
        core = "".join(word[i] for i in idx).lower()
        groups = _vowel_groups(core)
        candidates = [idx[c] for c in _rule_cuts(core, groups) if idx[c] not in bounds]
        for a, b in sorted(groups, key=lambda g: g[0] - g[1]):          # longest vowel group first
            candidates += [idx[k] for k in range(a + 1, b) if idx[k] not in bounds]
        if not candidates:
            break
        bounds.add(candidates[0])
    while len(bounds) + 1 > want and bounds:
        edges = [0] + sorted(bounds) + [len(word)]
        lengths = [b - a for a, b in zip(edges, edges[1:])]
        i = lengths.index(min(lengths))
        bounds.discard(edges[i + 1] if i == 0 else edges[i])             # the first merges forward, the rest back
    edges = [0] + sorted(bounds) + [len(word)]
    return [word[a:b] for a, b in zip(edges, edges[1:]) if b > a]


def _rule_cuts(core: str, groups: list[tuple[int, int]]) -> list[int]:
    """Where the spelling rules cut between vowel groups (positions in `core`)."""
    cuts: list[int] = []
    for (_, end_a), (start_b, _) in zip(groups, groups[1:]):
        cons = core[end_a:start_b]
        n = len(cons)
        if n <= 1:
            cut = end_a                    # o-pen, ba-by
        elif n == 2:
            if cons in DIGRAPHS or (cons[1] == "l" and core.endswith("le") and start_b == groups[-1][0]):
                cut = end_a                # mo-ther, fa-shion; ta-ble, peo-ple
            elif cons in ("ck", "ng"):
                cut = start_b              # rock-et, sing-ing
            else:
                cut = end_a + 1            # win-dow, sum-mer
        else:
            # Three or more: after the first unless the first two are a digraph (chil-dren, sun-shine, ex-tra).
            cut = end_a + (2 if cons[:2] in DIGRAPHS else 1)
        cuts.append(cut)
    return cuts


def _syllabify_by_rule(word: str) -> list[str]:
    # Work on the letters without apostrophes, cutting the original word at the same letters.
    idx = [i for i, c in enumerate(word) if c != "'"]
    core = "".join(word[i] for i in idx).lower()
    groups = _vowel_groups(core)
    if len(groups) <= 1:
        return [word]
    cuts = [idx[c] for c in _rule_cuts(core, groups)]
    pieces = [p for p in (word[a:b] for a, b in zip([0] + cuts, cuts + [len(word)])) if p]
    if len(pieces) > 1:
        last = pieces[-1].lower().replace("'", "")
        # No syllable of their own: a silent final e (take, whole, you're) unless it's a
        # consonant + le (can-dle, ta-ble); -ed and -es after one consonant (burned, lines)
        # unless that consonant keeps them sounded (wait-ed, fad-ed, plac-es, wish-es).
        silent_e = re.fullmatch(r"[^aeiouy]*e", last) and not re.fullmatch(r"[^aeiouy]+le", last) and not core.endswith(("ee", "ye"))
        ending = re.fullmatch(r"[^aeiouy]?e[ds]", last) and not re.search(r"[td]ed$|[sxzcgh]es$", core)
        if silent_e or ending:
            pieces[-2:] = [pieces[-2] + pieces[-1]]
    return pieces


def stresses(word: str, pieces: list[str]) -> list[bool]:
    """Which syllables of a word are stressed: the dictionary's primary and secondary
    stresses when it knows the word in this many pieces, the spelling rules otherwise."""
    w = _dictionary_key(word)
    n = len(pieces)
    if n == 1:
        return [w not in FUNCTION_WORDS]
    digits = dictionary().get(w, "")
    if len(digits) == n:
        marks = [d != "0" for d in digits]
        if not any(marks):
            marks[0] = True
        return marks
    first = re.sub(r"[^a-z]", "", pieces[0].lower())
    prefixed = first in UNSTRESSED_PREFIXES and w not in PREFIX_EXCEPTIONS
    start = 1 if prefixed else 0
    out = [(i - start) % 2 == 0 and i >= start for i in range(n)]
    last = re.sub(r"[^a-z]", "", pieces[-1].lower())
    if n >= 2 and last.endswith(UNSTRESSED_SUFFIXES) and not (prefixed and n == 2):
        out[-1] = False
    if not any(out):
        out[start] = True
    return out


@dataclass
class Syllable:
    text: str
    stressed: bool
    word_start: bool
    word_end: bool
    line_end: bool = False


def line_syllables(line: str) -> list[Syllable]:
    out: list[Syllable] = []
    for word in tokens(line):
        plain, override = split_override(word)
        if not re.search(r"[A-Za-z]", plain):
            continue
        pieces = _syllabify_plain(plain)
        marks = stresses(plain, pieces)
        for i, (p, s) in enumerate(zip(pieces, marks)):
            text = re.sub(r"[^A-Za-z']", "", p)      # the singer gets letters, not the comma after them
            if text and override is not None and i == len(pieces) - 1:
                text += "[" + " ".join(override) + "]"      # the override rides on the word's last piece
            if text:
                out.append(Syllable(text, s, i == 0, i == len(pieces) - 1))
    if out:
        out[-1].line_end = True
        if out[-1].word_start:
            out[-1].stressed = True      # a line's last word lands on a beat and is held ("for YOU")
    return out


# --------------------------------------------------------------------- rhythm

@dataclass
class Placed:
    syllable: Syllable
    start: float      # QN from the line's downbeat (negative: a pickup)
    length: float


def _durations(syls: list[Syllable], level: int) -> list[float]:
    stressed, unstressed = ((1.0, 0.5), (0.5, 0.5), (0.5, 0.25), (0.25, 0.25))[level]
    return [stressed if s.stressed else unstressed for s in syls]


def place_line(syls: list[Syllable], span_qn: float, hold_qn: float, rng: random.Random,
               syncopation: float = 0.0) -> list[Placed]:
    """Where a line's syllables fall in its span: stressed ones on beats, unstressed
    between, up to two unstressed pickups before the downbeat, the last syllable held
    at least hold_qn and a breath left at the end. Longer lines move to faster values."""
    if not syls:
        return []
    room = span_qn - BREATH_QN
    # The note values: the slowest ones whose sung part leaves the last word room to be
    # held, nearest to SUNG_SHARE of the span. A 7-syllable line over 2 bars then sings in
    # 8ths and holds 'round' for three beats, instead of a quarter note per syllable.
    fits = []
    for level in range(4):
        sung = sum(_durations(syls, level))
        if sung + min(hold_qn, 1.0) <= room + 1e-6:
            fits.append((abs(sung / room - SUNG_SHARE), level))
    for _, level in sorted(fits) or [(0, 3)]:
        durs = _durations(syls, level)
        pickup = 0
        while pickup < min(2, len(syls) - 1) and not syls[pickup].stressed:
            pickup += 1
        placed: list[Placed] = []
        t = -sum(durs[:pickup])
        for i, (s, d) in enumerate(zip(syls, durs)):
            if s.stressed and i >= pickup and t % 1.0 > 1e-6:
                # A stressed syllable waits for the beat; the one before it holds on.
                wait = math.ceil(t - 1e-6) - t
                if placed:
                    placed[-1].length += wait
                t += wait
            if (syncopation and not s.stressed and i > pickup and d >= 0.5 and t % 1.0 < 1e-6
                    and i + 1 < len(syls) and syls[i + 1].stressed and rng.random() < syncopation):
                # Push an unstressed syllable off the beat: the previous one gets the extra 8th.
                if placed:
                    placed[-1].length += 0.5
                t += 0.5
                d = 0.5
            placed.append(Placed(s, t, d))
            t += d
        sung_end = placed[-1].start
        if sung_end + min(hold_qn, 1.0) <= room + 1e-6:
            last = placed[-1]
            # The last word fills most of what's left, then the breath.
            left = room - last.start
            last.length = max(last.length, min(left, max(hold_qn, HOLD_SHARE * left)))
            for p in placed[:-1]:
                p.length = max(0.1, p.length - ARTICULATION_QN)
            return placed
    raise ValueError(f"too many syllables for the line's {span_qn:g} beats: '{' '.join(s.text for s in syls)}' has "
                     f"{len(syls)}; give it more bars (line_bars) or fewer words")


# --------------------------------------------------------------------- pitches

def _pool(key: Key, low: int, high: int) -> list[int]:
    pcs = key.pitch_classes()
    pool = [p for p in range(low, high + 1) if p % 12 in pcs]
    if len(pool) < 5:
        raise ValueError("the range has too few scale notes: widen low/high")
    return pool


def _choose(pool: list[int], target: float, prev: int | None, chord_pcs: set[int], stressed: bool,
            rng: random.Random, want_pcs: set[int] | None = None, avoid_pcs: set[int] = frozenset()) -> int:
    best, best_cost = pool[0], math.inf
    for p in pool:
        if prev is not None and abs(p - prev) > 7:
            continue
        cost = abs(p - target) + (0.35 * abs(p - prev) if prev is not None else 0)
        if want_pcs is not None:
            cost += 0 if p % 12 in want_pcs else 6
        elif p % 12 not in chord_pcs:
            cost += 2.5 if stressed else 0.6
        if p % 12 in avoid_pcs:
            cost += 3
        if prev is not None and abs(p - prev) > 5:
            cost += 1.5
        if prev is not None and p == prev:
            cost += 0.6 if stressed else 1.2    # a line that moves, not one note per word
        cost += rng.uniform(0, 0.5)
        if cost < best_cost:
            best, best_cost = p, cost
    return best


# ------------------------------------------------------------------- the line

@dataclass
class VocalLine:
    text: str
    start: float
    notes: list[dict] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    pickup_qn: float = 0.0
    held_qn: float = 0.0


def _bar_qn(meter: str) -> float:
    return composer._bar_len(meter)


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z' ]", "", text.lower()).strip()


def compose(lines: list[str], events: list[composer.ChordEvent], key: Key, low: int, high: int,
            shape: str = "verse", meter: str = "4/4", line_bars: float | None = None, start: float = 0.0,
            seed: int | None = None, melisma: bool | None = None, syncopation: float = 0.0) -> dict:
    """The sung line for these lyrics over these chords. Returns notes (start in QN from
    the item start, length, pitch, velocity), the lyrics string render_vocalvst takes
    (one token per note, '_' for a held note) and a summary of each line."""
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        raise ValueError("give the words, one line per phrase")
    if not events:
        raise ValueError("give the chords the line sings over")
    rng = random.Random(seed)
    bar = _bar_qn(meter)
    total = events[-1].end - events[0].start
    if line_bars is None:
        per = total / bar / len(lines)
        line_bars = max(1.0, min(4.0, float(2 ** round(math.log2(per))) if per >= 1 else 1.0))
    span = line_bars * bar
    pool = _pool(key, low, high)
    home = int(round((len(pool) - 1) * SHAPE_HEIGHT.get(shape, 0.5)))
    # The arc fits under the top of the range, or a chorus would sit on its top note.
    arc = max(1, min(SHAPE_ARC.get(shape, 3), len(pool) - 1 - home))
    hold = HOLD_QN.get(shape, 1.5)
    if melisma is None:
        melisma = shape == "chorus"
    tonic = key.tonic % 12

    out_lines: list[VocalLine] = []
    seen: dict[str, VocalLine] = {}
    prev_pitch: int | None = None
    for li, text in enumerate(lines):
        line_start = start + li * span
        key_text = _normalise(text)
        vl = VocalLine(text.strip(), line_start)
        if key_text in seen:
            # The same words again sing the same tune: that's what makes a hook.
            earlier = seen[key_text]
            shift = line_start - earlier.start
            vl.notes = [{**n, "start": round(n["start"] + shift, 4)} for n in earlier.notes]
            vl.tokens, vl.pickup_qn, vl.held_qn = list(earlier.tokens), earlier.pickup_qn, earlier.held_qn
            out_lines.append(vl)
            prev_pitch = vl.notes[-1]["pitch"]
            continue
        syls = line_syllables(text)
        if not syls:
            continue
        placed = place_line(syls, span, hold, rng, syncopation)
        if li == 0 and placed[0].start < 0:
            # The first line can't start before the item: no pickup, the downbeat it is.
            shift = -placed[0].start
            for p in placed:
                p.start += shift
        vl.pickup_qn = max(0.0, -placed[0].start)
        last_line = li == len(lines) - 1
        lift = 1 if li >= len(lines) - 2 and len(lines) >= 3 and shape != "verse" else 0
        n = len(placed)
        stressed_idx = [i for i, p in enumerate(placed) if p.syllable.stressed] or [0]
        peak_at = stressed_idx[min(len(stressed_idx) - 1, int(len(stressed_idx) * 0.6))]
        for i, p in enumerate(placed):
            # The contour: up to the peak over the line's first 60%, then down to the end.
            frac = i / peak_at if peak_at and i <= peak_at else (1 - (i - peak_at) / max(1, n - 1 - peak_at))
            target_idx = home + lift + arc * math.sin(frac * math.pi / 2)
            target_idx = max(0, min(len(pool) - 1, target_idx))
            target = pool[int(round(target_idx))]
            t_abs = line_start + p.start
            ev = composer.chord_at(events, t_abs)
            chord_pcs = ev.chord.pitch_classes() if ev else set()
            want: set[int] | None = None
            avoid: set[int] = set()
            if i == n - 1:
                if last_line:
                    want = {tonic} if (not chord_pcs or tonic in chord_pcs) else {next(iter(chord_pcs))}
                else:
                    want = chord_pcs - {ev.chord.root % 12} if ev and len(chord_pcs) > 1 else chord_pcs or None
                    if shape != "chorus":
                        avoid = {tonic}        # a verse line asks a question
            pitch = _choose(pool, target, prev_pitch, chord_pcs, p.syllable.stressed, rng, want, avoid)
            vel = VELOCITY["final"] if i == n - 1 else VELOCITY["stressed" if p.syllable.stressed else "unstressed"]
            if i == 0:
                vel = min(127, vel + 4)
            if i == n - 1 and melisma and p.length >= 2.0 and li % 2 == 1:
                # A fall on the held last word ("yeah-eah"): the word, then a step down on '+'.
                fall = pool[max(0, pool.index(pitch) - 1)] if pitch in pool else pitch - 2
                vl.notes.append({"pitch": pitch, "start": round(p.start, 4), "length": round(p.length - 1.0, 4), "velocity": vel})
                vl.tokens.append(p.syllable.text)
                vl.notes.append({"pitch": fall, "start": round(p.start + p.length - 1.0, 4), "length": 1.0, "velocity": vel - 10})
                vl.tokens.append("_")
            else:
                vl.notes.append({"pitch": pitch, "start": round(p.start, 4), "length": round(p.length, 4), "velocity": vel})
                vl.tokens.append(p.syllable.text)
            prev_pitch = pitch
        vl.held_qn = placed[-1].length
        vl.notes = [{**nt, "start": round(nt["start"] + line_start, 4)} for nt in vl.notes]
        seen[key_text] = vl
        out_lines.append(vl)

    notes = [nt for vl in out_lines for nt in vl.notes]
    tokens = [tk for vl in out_lines for tk in vl.tokens]
    lyrics = _join_tokens(out_lines)
    onsets = [nt["start"] for nt in notes]
    busiest = max((sum(1 for u in onsets if t <= u < t + 4) for t in onsets), default=0) / 4
    return {"notes": notes, "lyrics": lyrics, "tokens": tokens, "line_bars": line_bars,
            "lines": [{"text": vl.text, "start_qn": round(vl.start, 3), "notes": len(vl.notes),
                       "pickup_beats": vl.pickup_qn, "held_beats": round(vl.held_qn, 2)} for vl in out_lines],
            "syllables_per_beat_max": round(busiest, 2),
            "range": (min(nt["pitch"] for nt in notes), max(nt["pitch"] for nt in notes))}


def diatonic_shift(pitch: int, key: Key, steps: int) -> int:
    """The pitch `steps` scale steps away in the key (a third above: 2); a note outside
    the scale moves from its nearest scale note."""
    if steps == 0:
        return pitch
    pcs = sorted(key.pitch_classes())
    if not pcs:
        return pitch + steps * 2
    # The scale laid out around the pitch, the note's own position found or made.
    scale = sorted(p for o in range(-1, 12) for p in (o * 12 + pc for pc in pcs) if 0 <= p < 128)
    nearest = min(scale, key=lambda p: (abs(p - pitch), p))
    i = scale.index(nearest) + steps
    return scale[max(0, min(len(scale) - 1, i))]


HARMONY_STEPS = {"unison": 0, "third above": 2, "third below": -2, "fourth below": -3, "sixth below": -5,
                 "octave above": 7, "octave below": -7}


def _join_tokens(lines: list[VocalLine]) -> str:
    """The render_vocalvst lyric string: syllables of one word joined with hyphens,
    words with spaces, '_' for a held note."""
    words: list[str] = []
    for vl in lines:
        syls = [s for s in line_syllables(vl.text)]
        si = 0
        current: list[str] = []
        for tk in vl.tokens:
            if tk == "_":
                if current:
                    words.append("-".join(current))
                    current = []
                words.append("_")
                continue
            s = syls[si] if si < len(syls) else None
            si += 1
            if s is not None and s.word_start and current:
                words.append("-".join(current))
                current = []
            current.append(tk)
        if current:
            words.append("-".join(current))
    return " ".join(words)


# ------------------------------------------------------------------------ lint

# A listener loses words at consonant pile-ups, at words the singer has to sound out
# letter by letter, and when a syllable's closing consonant is really the next
# syllable's opening one: the singer puts each syllable's onset consonant at the end of
# the note before, so 'Sa-tur-day' held long came back as "Sat turd day".
STOPS = set("tdkgpbq")
ONE_SOUND = ("th", "sh", "ch", "ph", "wh", "ng", "ck", "qu", "gh")
LONG_NOTE_S = 0.45        # a syllable held this long before a stop sounds closed by it
CLUSTER_AT_ONSET = 3      # consonant sounds in a row at a word's start that blur it ('strength')
CLUSTER_ANYWHERE = 4      # ... anywhere in a word or across two ('world's turning')
VOCALISE = {"la", "ooh", "oh", "ah", "na", "da", "mm", "hey", "whoa", "yeah", "woah", "uh", "hmm", "doo", "ba"}


def _consonant_runs(word: str) -> list[int]:
    """The lengths of the consonant-sound runs in a word, start to end (a word that
    starts or ends on a vowel gets a 0 there), digraphs as one sound, 'gh' silent."""
    text = re.sub(r"[^a-z]", "", word.lower())
    for pair in ONE_SOUND:
        text = text.replace(pair, "" if pair == "gh" else pair[0])
    text = re.sub(r"([^aeiouy])\1", r"\1", text)      # a doubled letter is one sound
    runs, current = [], 0
    for c in text:
        if c in "aeiouy":
            runs.append(current)
            current = 0
        else:
            current += 1
    runs.append(current)
    return runs


def lint(lyrics: str, note_seconds: list[float] | None = None) -> dict:
    """What in a render_vocalvst lyric string (hyphenated syllables, '_' holds) a listener
    will struggle to hear, found without a render: words VocalVST's dictionary lacks
    (when it's installed), consonant pile-ups, and a syllable held long before the
    next one's stop consonant (with `note_seconds`, one per token). Empty when clean."""
    words: list[tuple[str, list[str], list[float | None]]] = []      # (word, syllables, seconds per syllable)
    overrides: dict[str, list[str]] = {}                                 # word (as typed, no override) -> phonemes
    at = 0
    for raw in tokens(lyrics):
        if raw in ("_", "-", "+"):
            if words and note_seconds is not None and at < len(note_seconds) and words[-1][2][-1] is not None:
                words[-1][2][-1] += note_seconds[at]
            at += 1
            continue
        tk, override = split_override(raw)
        if override is not None:
            overrides[tk or "[]"] = override
        pieces = [p for p in tk.split("-") if p] or [tk]
        secs = [note_seconds[at + i] if note_seconds is not None and at + i < len(note_seconds) else None
                for i in range(len(pieces))]
        words.append((tk or "[]", pieces, secs))
        at += len(pieces)
    flags: list[str] = []
    bad_symbols, off_count = [], []
    for word, sounds in overrides.items():
        unknown_symbols = [p for p in sounds if p not in ARPABET]
        if unknown_symbols:
            bad_symbols.append(f"'{word}' ({', '.join(unknown_symbols)})")
        vowels = sum(p in ARPABET_VOWELS for p in sounds)
        pieces = len([p for p in word.split("-") if p]) or 1
        if word != "[]" and vowels != pieces:
            off_count.append(f"'{word}' ({vowels} vowel sounds over {pieces} notes)")
    if bad_symbols:
        flags.append("not ARPAbet in the pronunciation of " + ", ".join(bad_symbols) + ": use lower-case ARPAbet "
                     "symbols without stress digits (aa ae ah ao aw ay eh er ey ih iy ow oy uh uw, b ch d dh f g hh jh "
                     "k l m n ng p r s sh t th v w y z zh), dx for a flapped t/d, ax for a schwa")
    if off_count:
        flags.append("the pronunciation of " + ", ".join(off_count) + " doesn't fit its notes: the sounds are split "
                     "over the hyphenated pieces at their vowels, so write one vowel sound per piece")
    if overrides and not overrides_supported():
        flags.append("this VocalVST build predates pronunciation overrides, so the [brackets] would be sung as words; "
                     "creaper drops them for this build. Reinstall the plugin to use them")
    known = dictionary()
    if known:
        unknown = []
        for word, pieces, _ in words:
            key = _dictionary_key(word)
            if key and key not in known and key not in VOCALISE and key not in unknown and word not in overrides and \
                    not all(_dictionary_key(p) in known for p in pieces):
                unknown.append(key)
        if unknown:
            flags.append("the singer's dictionary has no " + ", ".join(f"'{w}'" for w in unknown[:8])
                         + (" ..." if len(unknown) > 8 else "") + ": it sounds them out letter by letter, often "
                         "wrong. Use words it knows (plain English spelling; no slang spellings or made-up names)"
                         + (", or spell the sounds after the word, 'Sa-tur-day[s ae dx er d ey]'"
                            if overrides_supported() else ""))
    if overrides_supported():
        by_ear = [suggest_override(word) for word, _, _ in words
                  if _dictionary_key(word) in PRONOUNCE and word not in overrides]
        if by_ear:
            flags.append("the voicebank mangles " + ", ".join(f"'{w.split('[')[0]}'" for w in dict.fromkeys(by_ear))
                         + " ('Saturday' comes out \"Sat-er-ray\"): write " + ", ".join(dict.fromkeys(by_ear))
                         + ", the pronunciation the user chose by ear")
    piled = []
    for i, (word, _, _) in enumerate(words):
        runs = _consonant_runs(word)
        if runs[0] >= CLUSTER_AT_ONSET or max(runs) >= CLUSTER_ANYWHERE:
            piled.append(word)
        elif i + 1 < len(words) and runs[-1] + _consonant_runs(words[i + 1][0])[0] >= CLUSTER_ANYWHERE:
            piled.append(f"{word} {words[i + 1][0]}")
    if piled:
        flags.append("consonants pile up in " + ", ".join(f"'{w}'" for w in dict.fromkeys(piled[:8]))
                     + ": sung, those run together. Prefer words that open on a vowel or one consonant")
    held = []
    for word, pieces, secs in words:
        for a, b, s in zip(pieces, pieces[1:], secs):
            first = re.sub(r"[^a-z]", "", b.lower())[:1]
            hard_c = first == "c" and not re.match(r"c[eiy]", re.sub(r"[^a-z]", "", b.lower()))
            if s is not None and s >= LONG_NOTE_S and (first in STOPS or hard_c):
                held.append(f"'{word}' ({re.sub(r'[^A-Za-z]', '', a)} held {s:.1f} s before the {first.upper()})")
    if held:
        flags.append(", ".join(held[:6]) + (" ..." if len(held) > 6 else "") + ": the singer sings a syllable's "
                     "opening consonant at the end of the note before it, so a long note before a T, D, K, P or B "
                     "ends on that consonant ('Sa-tur-day' came back 'Sat turd day'). Give those words shorter, "
                     "moving notes, or words whose later syllables open on a vowel, L, M, N, S or W")
    if not flags:
        return {}
    return {"flags": flags, "next": "Fix the words before rendering: a render takes minutes, this took none"}
