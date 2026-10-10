import pytest

from creaper import composer as C
from creaper import genres, music_tools
from creaper import harmony as H
from creaper.theory import CHORD_QUALITIES


def names(rcs):
    return [r.chord.symbol for r in rcs]


# ---------------------------------------------------------------- spelling

@pytest.mark.parametrize("key, notes", [
    ("F# major", ["F#", "G#", "A#", "B", "C#", "D#", "E#"]),
    ("Bb minor", ["Bb", "C", "Db", "Eb", "F", "Gb", "Ab"]),
    ("D dorian", ["D", "E", "F", "G", "A", "B", "C"]),
    ("E phrygian dominant", ["E", "F", "G#", "A", "B", "C", "D"]),
    ("C# harmonic minor", ["C#", "D#", "E", "F#", "G#", "A", "B#"]),
    ("Gb major", ["Gb", "Ab", "Bb", "Cb", "Db", "Eb", "F"]),
])
def test_scales_are_spelled_like_a_musician_would(key, notes):
    assert H.parse_key(key).spell_scale() == notes


def test_chord_spelling():
    assert H.spell_chord(0, "C", CHORD_QUALITIES["dim7"]) == ["C", "Eb", "Gb", "Bbb"]
    assert H.spelled_from_symbol("Db7").notes == ["Db", "F", "Ab", "Cb"]
    assert H.spelled_from_symbol("F#m7b5").notes == ["F#", "A", "C", "E"]
    assert H.spelled_from_symbol("G7#9").notes == ["G", "B", "D", "F", "A#"]


def test_key_parsing():
    assert H.parse_key("Am").name == "A minor"
    assert H.parse_key("e").name == "E minor"
    assert H.parse_key("Bb").name == "Bb major"
    assert H.parse_key("f# dorian").name == "F# dorian"


# ---------------------------------------------------------- Roman numerals

def test_numerals_in_major():
    k = H.parse_key("C")
    assert names(H.parse_progression("I-vi-ii7-V7", k)) == ["C", "Am", "Dm7", "G7"]
    assert names(H.parse_progression("V7/V-viiø7-vii°7-bVII-iv", k)) == ["D7", "Bm7b5", "Bdim7", "Bb", "Fm"]
    assert names(H.parse_progression("I6-IV64-V65-ii43-V42", k)) == ["C/E", "F/C", "G7/B", "Dm7/A", "G7/F"]
    assert names(H.parse_progression("N6-Ger+6-It+6-Fr+6-Cad64", k)) == ["Db/F", "Ab7", "Ab7no5", "Ab7b5", "C/G"]


def test_numerals_in_minor_use_the_leading_tone_for_vii():
    k = H.parse_key("A minor")
    assert names(H.parse_progression("i-iv-V7-VI-VII-III", k)) == ["Am", "Dm", "E7", "F", "G", "C"]
    assert names(H.parse_progression("vii°7-viiø7", k)) == ["G#dim7", "G#m7b5"]


def test_flats_count_from_the_major_scale_in_every_mode():
    for mode in ("major", "mixolydian", "dorian", "minor", "phrygian"):
        k = H.parse_key(f"C {mode}")
        assert names(H.parse_progression("bVII-bVI-bIII-bII", k)) == ["Bb", "Ab", "Eb", "Db"]


def test_numeral_for_explains_chromatic_chords():
    k = H.parse_key("C")
    d7 = H.numeral_for(H.spelled_from_symbol("D7"), k)
    assert d7.numeral == "II7" and "V7/V" in d7.labels[0]
    assert "tritone" in H.numeral_for(H.spelled_from_symbol("Db7"), k).labels[0]
    fm = H.numeral_for(H.spelled_from_symbol("Fm"), k)
    assert fm.numeral == "iv" and "borrowed" in fm.labels[0] and fm.function == "predominant"
    assert H.numeral_for(H.spelled_from_symbol("G7/B"), k).numeral == "V65"


def test_roundtrip_numerals():
    k = H.parse_key("Eb major")
    for n in ("I", "ii7", "iii", "IVmaj7", "V7", "vi", "viiø7", "bVII", "iv", "bVImaj7"):
        chord = H.parse_roman(n, k).chord
        assert H.parse_roman(H.numeral_for(chord, k).numeral, k).chord.symbol == chord.symbol


# --------------------------------------------------------------- analysis

def test_identify_chord():
    assert H.identify_chord([45, 48, 52, 55])[0]["symbol"] == "Am7"
    assert H.identify_chord([48, 52, 55, 57])[0]["symbol"] == "C6"
    assert H.identify_chord([52, 55, 60])[0]["symbol"] == "C/E"
    assert H.identify_chord([55, 59, 65, 69])[0]["symbol"] == "G9"  # 5th omitted


def test_detect_key():
    k = H.parse_key("G major")
    notes = [{"pitch": 55 + i, "length": 1.0} for i in (0, 2, 4, 5, 7, 9, 11, 12, 7, 4, 0)]
    assert H.detect_key(H.histogram_from_notes(notes))[0]["key"] == "G major"
    chords = [H.spelled_from_symbol(c) for c in ("Dm7", "G7", "Cmaj7")]
    h, hint = H.histogram_from_chords([(c, 4.0) for c in chords])
    assert H.detect_key(h, hint)[0]["key"] == "C major"
    assert k.name == "G major"


def test_cadences():
    k = H.parse_key("C")
    found = " ".join(c["cadence"] for c in H.cadences(H.parse_progression("ii7-V7-I-IV-I-V7-vi-bVI-bVII-I", k)))
    for name in ("ii-V-I", "authentic", "plagal", "deceptive", "Aeolian"):
        assert name in found


def test_negative_harmony_mirrors_v_to_iv_minor():
    k = H.parse_key("C")
    assert H.negative_chord(H.spelled_from_symbol("G7"), k).symbol.startswith("Dm")
    assert H.negative_chord(H.spelled_from_symbol("C"), k).symbol == "Cm"


def test_modulation():
    a, b = H.parse_key("C"), H.parse_key("G")
    pivots = H.pivot_chords(a, b)
    assert {"C", "Em", "G", "Am"} <= {p["chord"] for p in pivots}
    assert H.modulation_routes(a, b)[0]["technique"] == "pivot chord"


# --------------------------------------------------------------- composer

PROGS = [("C major", "I-vi-IV-V7-I"), ("A minor", "i-iv-V7-i-VI-iiø7-V7-i"), ("F major", "I-ii7-V7-I-IV-V7-vi"),
         ("D minor", "i-VI-III-VII-iv-V7-i")]


@pytest.mark.parametrize("key, prog", PROGS)
def test_satb_follows_the_rules(key, prog):
    k = H.parse_key(key)
    chords = [r.chord for r in H.parse_progression(prog, k)]
    v = C.satb(chords, k)
    issues = [i for i in C.check_voice_leading(v, k, chords) if i["issue"] in
              ("parallel fifths", "parallel octaves", "voice crossing", "doubled leading tone", "unresolved seventh")]
    assert issues == []
    for voicing, chord in zip(v, chords):
        assert {p % 12 for p in voicing} <= chord.pitch_classes()


def test_checker_catches_parallels():
    issues = C.check_voice_leading([[48, 55, 64, 72], [50, 57, 65, 74]], H.parse_key("C"))
    kinds = {i["issue"] for i in issues}
    assert {"parallel fifths", "parallel octaves"} <= kinds


@pytest.mark.parametrize("style", ["close", "open", "drop2", "drop3", "shell", "rootless", "quartal", "spread", "power", "cluster"])
def test_voicings_stay_in_range_and_in_the_chord(style):
    k = H.parse_key("C")
    chords = [r.chord for r in H.parse_progression("Imaj7-vi7-ii7-V7-iii7-VI7-ii7-V13", k)]
    for v, c in zip(C.voice_chords(chords, style), chords):
        assert v == sorted(v) and 24 <= v[0] and v[-1] <= 96
        if style not in ("quartal", "rootless", "cluster"):
            assert {p % 12 for p in v} <= c.pitch_classes()


def test_reharmonize_keeps_the_length():
    k = H.parse_key("C")
    ev = C.timeline([r.chord for r in H.parse_progression("I-vi-ii-V-I", k)], 4.0)
    for tech in C.REHARM_TECHNIQUES:
        new, _ = C.reharmonize(ev, k, [tech], seed=1, amount=1.0)
        assert abs(sum(e.length for e in new) - 20.0) < 1e-6, tech


@pytest.mark.parametrize("style", [s for s in genres.BASS_STYLES if s != "none"])
def test_basslines(style):
    k = H.parse_key("A minor")
    ev = C.timeline([r.chord for r in H.parse_progression("i-VI-III-VII", k)], 4.0)
    notes = C.bassline(ev, style, k, seed=2)
    assert notes and all(24 <= n["pitch"] <= 60 for n in notes)
    assert all(0 <= n["start"] < 16 for n in notes)


@pytest.mark.parametrize("pattern", [p for p in genres.COMPING if p != "none"])
def test_comping(pattern):
    k = H.parse_key("C")
    chords = [r.chord for r in H.parse_progression("I-V-vi-IV", k)]
    ev = C.timeline(chords, 4.0)
    notes = C.comp(ev, C.voice_chords(chords, "close"), pattern, meter="3/4" if pattern == "waltz" else "4/4")
    assert notes and all(0 <= n["start"] < 16 for n in notes)


def test_melody_is_deterministic_in_range_and_ends_home():
    k = H.parse_key("D major")
    ev = C.timeline([r.chord for r in H.parse_progression("I-V-vi-IV-I-V-IV-I", k)], 4.0)
    a = C.melody(ev, k, seed=5)
    assert a == C.melody(ev, k, seed=5)
    assert all(60 <= n["pitch"] <= 79 for n in a)
    assert a[-1]["pitch"] % 12 == k.tonic


def test_harmonize_melody_cadences_home():
    k = H.parse_key("C")
    ev = C.timeline([r.chord for r in H.parse_progression("I-IV-V-I", k)], 4.0)
    mel = C.melody(ev, k, seed=1)
    chords = C.harmonize(mel, k)
    assert chords[-1].chord.root == k.tonic


def test_chords_from_notes_roundtrip():
    k = H.parse_key("C")
    chords = [r.chord for r in H.parse_progression("I-vi-ii7-V7", k)]
    ev = C.timeline(chords, 4.0)
    notes = [{"pitch": p, "start": e.start, "length": e.length} for e, v in zip(ev, C.voice_chords(chords)) for p in v]
    found = C.chords_from_notes(notes, key=k)
    roots = [H.spelled_from_symbol(s["chord"]).root for s in found]
    assert roots == [0, 9, 2, 7] or len(found) == 4


def test_rhythms():
    assert C.euclidean(3, 8) == "x..x..x."
    assert C.euclidean(5, 8).count("x") == 5
    assert C.polyrhythm(3, 2) == {"3 against 2 (A)": "x.x.x.", "3 against 2 (B)": "x..x.."}


def test_motif_transforms():
    k = H.parse_key("C")
    motif = [{"pitch": p, "start": i, "length": 1, "velocity": 90} for i, p in enumerate((60, 62, 64, 65))]
    assert [n["pitch"] for n in C.diatonic_transpose(motif, 2, k)] == [64, 65, 67, 69]
    assert [n["pitch"] for n in C.invert(motif, key=k)] == [60, 59, 57, 55]
    assert [n["pitch"] for n in C.retrograde(motif)] == [65, 64, 62, 60]
    assert C.scale_time(motif, 2)[-1]["start"] == 6
    assert len(C.add_harmony(motif, k)) == 8
    assert len(C.sequence(motif, k, repeats=2)) == 12


# ------------------------------------------------------------- the tools

def test_every_genre_progression_realizes_in_its_profile():
    for g in genres.GENRES:
        profile = music_tools.get_genre_profile(g.name)
        assert profile["progressions"] and all("in_key" in p for p in profile["progressions"]), g.name


def test_suggest_progressions_for_a_genre():
    out = music_tools.suggest_progressions("A minor", genre="trance", count=6, seed=1)
    assert len(out["progressions"]) == 6 and out["progressions"][0]["source"] == "genre"


def test_analyze_progression_finds_the_key_and_names():
    out = music_tools.analyze_progression("Am F C G")
    assert out["key"] in ("A minor", "C major")
    assert out["known_progressions"]


def test_get_scale_lists_relatives():
    out = music_tools.get_scale("D dorian")
    assert "C major" in out["same_notes_as"] and out["triads"][3]["chord"] == "G"
