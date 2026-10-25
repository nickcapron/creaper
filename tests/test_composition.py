"""Composition that develops: melodies with a hook, basslines that move, varied grooves."""

import pytest

from creaper import server  # noqa: F401  (import order: server first)
from creaper import composer as C
from creaper import harmony as H
from creaper import theory

KEY = H.parse_key("A minor")
LOOP = [r.chord for r in H.parse_progression("i-VI-III-VII", KEY)]


def events(times=8):
    return C.timeline(LOOP * times, 4.0)


def test_a_melody_comes_back_breathes_and_builds_to_a_late_peak():
    for seed in range(1, 9):
        notes = C.melody(events(), KEY, seed=seed)
        score = C.hook_score(notes)
        assert 0.35 <= score["bar_repetition"] <= 0.8, (seed, score)
        assert score["rest_ratio"] >= 0.08, (seed, score)
        assert score["peak_position"] >= 0.6, (seed, score)
        assert 7 <= score["range"] <= 15, (seed, score)
        assert notes[-1]["pitch"] % 12 == KEY.tonic


def test_phrases_end_as_questions_and_answers():
    notes = C.melody(events(2), KEY, seed=3, phrase_bars=4)     # 8 bars: an A phrase, then its answer
    first = [n for n in notes if n["start"] < 16]
    second = [n for n in notes if 16 <= n["start"] < 32]
    degree = lambda n: (n["pitch"] - KEY.tonic) % 12
    assert degree(first[-1]) in (2, 7)       # the A phrase asks (2nd or 5th)
    assert degree(second[-1]) == 0           # A' answers (the tonic)
    # Each phrase ends on a held note followed by a breath.
    assert first[-1]["start"] + first[-1]["length"] < 16 - 0.25


def test_shape_and_register_lift_move_the_line():
    mean = lambda ns: sum(n["pitch"] for n in ns) / len(ns)
    hook, verse = C.melody(events(4), KEY, seed=2, shape="hook"), C.melody(events(4), KEY, seed=2, shape="verse")
    lifted = C.melody(events(4), KEY, seed=2, shape="verse", register_lift=3)
    assert mean(verse) < mean(hook) - 1.5
    assert mean(lifted) > mean(verse) + 1.5


def test_hook_score_prefers_a_hook_over_a_ramble():
    import random
    rng = random.Random(1)
    ramble = [{"pitch": rng.randint(55, 84), "start": i * 0.5, "length": 0.5} for i in range(128)]
    hook = C.melody(events(), KEY, seed=4)
    assert C.hook_score(hook)["score"] < C.hook_score(ramble)["score"]
    assert C.hook_score(ramble)["bar_repetition"] < 0.2


def test_write_melody_keeps_the_best_candidate_and_can_dry_run(monkeypatch):
    from creaper import music_tools
    monkeypatch.setattr(music_tools, "call", lambda cmd, **kw: {"time_signature": "4/4"})
    out = music_tools.write_melody(item_id="{A}", chords="Am F C G Am F C G", key="A minor", seed=10,
                                   candidates=4, write=False)
    assert out["notes_written"] == 0 and "nothing written" in out["note"]
    assert len(out["candidates"]) == 4
    assert out["hook_score"]["score"] == min(c["score"] for c in out["candidates"])
    assert out["seed"] in range(10, 14)


@pytest.mark.parametrize("style", ["eighths", "syncopated", "808", "octaves", "one_drop"])
def test_a_developed_bass_stops_looping_one_bar(style):
    plain = C.bassline(events(), style, KEY, seed=3)
    moved = C.develop_bass(plain, events(), style, seed=3)
    assert C.bar_variety(moved) >= C.bar_variety(plain) + 0.25 and C.bar_variety(moved) >= 0.5
    assert all(0 <= n["start"] < 128 and n["start"] + n["length"] <= 128 + 1e-6 for n in moved)
    assert C.develop_bass(plain, events(), style, seed=3) == moved          # same seed, same line


def test_approach_notes_lead_into_each_change():
    plain = C.bassline(events(1), "eighths", KEY, seed=1)
    moved = C.develop_bass(plain, events(1), "eighths", seed=1)
    roots = [e.chord.root % 12 for e in events(1)]
    for i, change in enumerate((4.0, 8.0, 12.0)):
        before = max((n for n in moved if n["start"] < change), key=lambda n: n["start"])
        target = roots[i + 1]
        assert (before["pitch"] - target) % 12 in (1, 11, 7), (change, before["pitch"], target)  # a semitone or the 5th


def test_held_and_walking_lines_are_left_alone():
    for style in ("whole", "reese", "root", "walking", "tumbao"):
        plain = C.bassline(events(1), style, KEY, seed=2)
        assert C.develop_bass(plain, events(1), style, seed=2) == plain


def test_the_bass_can_lock_to_or_avoid_the_kick():
    plain = C.bassline(events(1), "eighths", KEY, seed=1)
    locked = C.develop_bass(plain, events(1), "eighths", seed=1, groove=[0, 1, 2, 3], kick="lock")
    avoided = C.develop_bass(plain, events(1), "eighths", seed=1, groove=[0, 1, 2, 3], kick="avoid")
    on = [n for n in locked if abs(n["start"] % 1) < 1e-6]
    off = [n for n in locked if abs(n["start"] % 1) > 1e-6]
    assert sum(n["velocity"] for n in on) / len(on) > sum(n["velocity"] for n in off) / len(off) + 8
    assert sum(1 for n in avoided if abs(n["start"] % 1) < 1e-6) < sum(1 for n in plain if abs(n["start"] % 1) < 1e-6)


# ------------------------------------------------------------------- grooves

@pytest.mark.parametrize("name", ["house", "synthwave", "trap", "rock", "french house"])
def test_a_varied_groove_keeps_changing_over_32_bars(name):
    from creaper import genres, grooves
    g = genres.find(name)
    v = grooves.vary_groove(g.groove["pattern"], g.groove.get("step", 0.25), 32, grooves.fill_style_for(g), seed=1)
    assert grooves.distinct_bars(v, g.groove.get("step", 0.25)) >= 0.4
    assert grooves.vary_groove(g.groove["pattern"], g.groove.get("step", 0.25), 32, grooves.fill_style_for(g), seed=1) == v


def test_fills_land_every_8th_bar_with_a_crash_after():
    from creaper import grooves
    pattern = {"kick": "x...x...x...x...", "snare": "....x.......x...", "closed hat": "x.x.x.x.x.x.x.x."}
    v = grooves.vary_groove(pattern, 0.25, 16, "snare_roll", seed=2)
    bar = lambda lane, b: v[lane][b * 16:(b + 1) * 16]
    assert bar("snare", 7).endswith("X") and bar("snare", 7).count("o") >= 2     # a roll into bar 9
    assert bar("crash", 8)[0] == "X" and "X" not in v["crash"][16 * 9:]          # one crash per fill, not after the last
    assert len(bar("snare", 15).rstrip(".")) > len(bar("snare", 7).rstrip(".")) or \
        bar("snare", 15).count("o") > bar("snare", 7).count("o")                  # the 16-bar fill is bigger
    toms = grooves.vary_groove(pattern, 0.25, 8, "tom", seed=2)
    assert any("tom" in lane for lane in toms) and "x" not in toms["snare"][16 * 7 + 8:16 * 8]  # toms replace the snare
    drop = grooves.vary_groove(pattern, 0.25, 8, "dropout", seed=2)
    assert drop["kick"][16 * 7 + 8:16 * 8] == "." * 8


def test_fills_come_as_often_as_the_energy_wants():
    from creaper import grooves
    pattern = {"kick": "x...x...x...x...", "snare": "....x.......x...", "closed hat": "x.x.x.x.x.x.x.x."}

    def fill_bars(energy):
        v = grooves.vary_groove(pattern, 0.25, 16, "snare_roll", energy=energy, seed=2)
        return [b for b in range(16) if v["snare"][b * 16:(b + 1) * 16].endswith("X")]

    assert fill_bars(None) == [7, 15] == fill_bars(3)       # the stock 8 and 16
    assert fill_bars(1) == [15]                              # a breakdown: one fill, into the next section
    short = grooves.vary_groove(pattern, 0.25, 8, "snare_roll", energy=1, seed=2)["snare"]
    assert short[16 * 7:16 * 8].endswith("X") and "X" not in short[:16 * 7]   # an 8-bar breakdown fills into the drop
    assert fill_bars(2) == [7, 15]
    assert fill_bars(4) == [3, 7, 11, 15]                    # a drop: every 4 bars
    big = grooves.vary_groove(pattern, 0.25, 16, "snare_roll", energy=4, seed=2)["snare"]
    small = grooves.vary_groove(pattern, 0.25, 16, "snare_roll", energy=2, seed=2)["snare"]
    assert big[16 * 7:16 * 8].count("o") > small[16 * 7:16 * 8].count("o")   # the drop's 8th-bar fill is the big one
    assert big[16 * 15:].count("o") == big[16 * 7:16 * 8].count("o")


def test_energy_doubles_the_hats_or_thins_the_kick():
    from creaper import grooves
    pattern = {"kick": "x.x.x.x.x.x.x.x.", "closed hat": "x.x.x.x.x.x.x.x."}
    high = grooves.vary_groove(pattern, 0.25, 1, "none", energy=4)
    low = grooves.vary_groove(pattern, 0.25, 1, "none", energy=1)
    assert high["closed hat"] == ("x" + grooves.SIXTEENTH_HAT) * 8     # 16ths, the off-16ths a touch under, not ghosts
    assert theory.STEP_VELOCITY["o"] < int(grooves.SIXTEENTH_HAT) * 127 // 9 < theory.STEP_VELOCITY["x"]
    assert low["kick"] == "x.......x......."


def test_genre_fill_styles():
    from creaper import arrange_tools, genres, grooves
    assert grooves.fill_style_for(genres.find("house")) == "clap_roll"
    assert grooves.fill_style_for(genres.find("classical")) == "none"
    assert arrange_tools.fill_for("epic", "clap_roll") == {"clap": "o.o.o.o.xxxxXXXX"}   # no toms for house
    assert arrange_tools.fill_for("build", "dropout") is None
    assert arrange_tools.fill_for("epic", None) == arrange_tools.FILLS["epic"]


def test_add_genre_groove_writes_a_whole_varied_section(monkeypatch):
    from creaper import music_tools
    written = {}
    monkeypatch.setattr(music_tools, "call", lambda cmd, **kw: {"time_signature": "4/4"})
    monkeypatch.setattr(music_tools, "add_drum_pattern", lambda **kw: written.update(kw) or {})
    out = music_tools.add_genre_groove(item_id="{A}", genre="house", bars=16, energy=4, seed=3)
    assert written["repeats"] == 1 and len(written["pattern"]["kick"]) == 16 * 16
    assert out["bars"] == 16 and out["fill_style"] == "clap_roll" and out["distinct_bars"] >= 0.3
    music_tools.add_genre_groove(item_id="{A}", genre="house", repeats=4, variations=False)
    assert written["repeats"] == 4 and len(written["pattern"]["kick"].replace(" ", "")) == 16   # the stock bar


# ------------------------------------------------------------------- chords

def test_the_top_voice_moves_and_returning_chords_are_revoiced():
    k = H.parse_key("C major")
    chords = [r.chord for r in H.parse_progression("I-vi-IV-V-I-vi-IV-V", k)]
    v = C.voice_chords(chords, "close", 3)
    tops = [x[-1] for x in v]
    assert all(not (a == b == c) for a, b, c in zip(tops, tops[1:], tops[2:]))
    # The progression comes round again: at least one chord is voiced differently the second time.
    assert any(v[i] != v[i + 4] for i in range(4))
    # Pitch classes are still the chords' own.
    assert all({p % 12 for p in x} <= c.pitch_classes() for x, c in zip(v, chords))


def test_stabs_anticipate_the_changes():
    k = H.parse_key("A minor")
    chords = [r.chord for r in H.parse_progression("i-VI-III-VII", k)]
    ev = C.timeline(chords, 4.0)
    notes = C.comp(ev, C.voice_chords(chords, "close", 3), "stabs")
    pushed = C.develop_comp(notes, ev, "stabs")
    for e in ev[1:]:
        early = [n for n in pushed if abs(n["start"] - (e.start - 0.5)) < 1e-6]
        assert early and {n["pitch"] % 12 for n in early} <= e.chord.pitch_classes()
    # Nothing from the old chord rings over the pushed one.
    for e in ev[1:]:
        assert not [n for n in pushed if n["start"] < e.start - 0.5 - 1e-6 < n["start"] + n["length"] - 0.05]


def test_held_chords_take_a_4_3_suspension_at_phrase_ends():
    k = H.parse_key("C major")
    chords = [r.chord for r in H.parse_progression("I-vi-IV-V", k)]
    ev = C.timeline(chords, 4.0)
    notes = C.develop_comp(C.comp(ev, C.voice_chords(chords, "close", 3), "sustain"), ev, "sustain")
    last = [n for n in notes if n["start"] >= 12 - 1e-6]
    pcs_first_half = {n["pitch"] % 12 for n in last if n["start"] < 13.5}
    pcs_second_half = {n["pitch"] % 12 for n in last if n["start"] >= 13.5}
    assert 0 in pcs_first_half and 11 not in pcs_first_half and pcs_second_half == {11}  # G: C (the 4th) resolves to B


# ------------------------------------------------------------------- harmony

SONG = ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse 2", "Pre-Chorus 2", "Chorus 2", "Bridge", "Final Chorus", "Outro"]


@pytest.mark.parametrize("genre, key", [("synthwave", "A minor"), ("pop", "C major"), ("house", "F minor")])
def test_each_section_gets_its_own_harmony(genre, key):
    from creaper import genres
    k = H.parse_key(key)
    plan = {r["section"]: r for r in C.plan_harmony(list(genres.find(genre).progressions), k, SONG, True, 1)}
    assert plan["Verse"]["chords"] != plan["Chorus"]["chords"]
    assert plan["Bridge"]["chords"] != plan["Verse"]["chords"]
    pre = H.parse_progression(plan["Pre-Chorus"]["numerals"], k)
    assert all(rc.chord.root % 12 != k.tonic for rc in pre)              # the pre-chorus avoids home...
    assert (pre[-1].chord.root - k.tonic) % 12 == 7                        # ...and ends on V
    assert plan["Final Chorus"]["key"] != key and "step up" in plan["Final Chorus"]["how"]
    assert plan["Chorus 2"]["key"] == k.name


def test_a_single_progression_turns_for_the_chorus():
    plan = C.plan_harmony(["I-V-vi-IV"], H.parse_key("C major"), ["Verse", "Chorus"])
    assert plan[1]["numerals"].startswith(("IV", "vi"))


def test_generated_progressions_dont_repeat_or_ping_pong():
    for key in ("C major", "A minor"):
        k = H.parse_key(key)
        for seed in range(40):
            seq = C.generate_progression(k, 8, seed=seed)
            assert all(a != b for a, b in zip(seq, seq[1:])), seq
            assert not any(seq[i] == seq[i + 2] and seq[i + 1] == seq[i + 3] for i in range(len(seq) - 3)), seq


def test_plan_harmony_tool_reads_the_regions(monkeypatch):
    from creaper import music_tools
    monkeypatch.setattr(music_tools, "call", lambda cmd, **kw: {"time_signature": "4/4", "regions": [
        {"name": "Chorus", "start": {"seconds": 16.0, "bar": 9}, "end": {"bar": 17}},
        {"name": "Verse", "start": {"seconds": 0.0, "bar": 1}, "end": {"bar": 9}}]})
    out = music_tools.plan_harmony(genre="pop", key="G major")
    assert [s["section"] for s in out["sections"]] == ["Verse", "Chorus"] and out["key"] == "G major"
    verse = out["sections"][0]
    assert verse["start_bar"] == 1 and verse["bars"] == 8
    assert sum(c["length"] for c in verse["fill"]) == 32                   # the chords fill all 8 bars
    assert " ".join(c["chord"] for c in verse["fill"]).startswith(verse["chords"])


def test_a_split_bridge_keeps_its_timing_in_the_fill(monkeypatch):
    from creaper import music_tools
    monkeypatch.setattr(music_tools, "call", lambda cmd, **kw: {"time_signature": "4/4", "regions": [
        {"name": "Bridge", "start": {"seconds": 0.0, "bar": 1}, "end": {"bar": 9}}]})
    for seed in range(6):
        row = music_tools.plan_harmony(genre="pop", key="A minor", seed=seed)["sections"][0]
        assert "slots" not in row
        assert abs(sum(c["length"] for c in row["fill"]) - 32) < 1e-6
        written = music_tools._events(
            [music_tools.TimedChord(**c) for c in row["fill"]], H.parse_key("A minor"), 4.0)[0]
        assert written[-1].start + written[-1].length == pytest.approx(32)


# ------------------------------------------------------------ second lines

def _overlaps(a, b):
    return a["start"] < b["start"] + b["length"] - 1e-6 and b["start"] < a["start"] + a["length"] - 1e-6


@pytest.mark.parametrize("seed", [3, 5, 7, 9])
def test_a_counter_melody_answers_the_melody_without_doubling_it(seed):
    ev = events(2)
    mel = C.melody(ev, KEY, seed=seed)
    line = C.counter_melody(mel, lambda t: C.chord_at(ev, t).chord.pitch_classes(), KEY, seed=1)
    assert len(line) >= 8, len(line)                       # even a busy melody gets a held line under it
    assert max(n["pitch"] for n in line) < min(n["pitch"] for n in mel)
    for c in line:                                         # never in unison or octaves with what it sounds against
        assert not any(_overlaps(c, m) and (m["pitch"] - c["pitch"]) % 12 == 0 for m in mel), c
    pitches = [n["pitch"] for n in line]
    assert sum(a == b for a, b in zip(pitches, pitches[1:])) <= len(line) // 6
    for c in line:                                         # on the beat: a chord tone
        if c["start"] % 1 == 0:
            assert c["pitch"] % 12 in C.chord_at(ev, c["start"]).chord.pitch_classes(), c


def test_the_counter_melody_moves_where_the_melody_rests():
    mel = [{"pitch": 76, "start": 0.0, "length": 0.5}, {"pitch": 74, "start": 0.5, "length": 0.5},
           {"pitch": 72, "start": 1.0, "length": 3.0}, {"pitch": 76, "start": 6.0, "length": 2.0}]
    line = C.counter_melody(mel, lambda t: None, H.parse_key("C major"), density=1.0, seed=2)
    starts = [n["start"] for n in line]
    assert any(1.0 < s < 4.0 for s in starts)              # under the held note
    assert any(4.0 <= s < 6.0 for s in starts)             # in the gap
    assert not any(s in (0.5, 6.0) for s in starts)        # not where the melody moves


def test_an_answer_turns_the_call_upside_down_and_comes_home():
    call_ = [{"pitch": 69, "start": 0.0, "length": 0.5}, {"pitch": 72, "start": 0.5, "length": 0.5},
             {"pitch": 76, "start": 1.0, "length": 1.0}]
    reply = C.answer(call_, KEY, gap=1.0)
    assert [n["start"] for n in reply] == [3.0, 3.5, 4.0]
    assert reply[1]["pitch"] < reply[0]["pitch"]           # the call went up, the answer comes down
    assert reply[-1]["pitch"] % 12 == KEY.tonic
    home = C.answer([dict(n) for n in call_[:2]] + [{"pitch": 69, "start": 1.0, "length": 1.0}], KEY)
    assert home[-1]["pitch"] % 12 == (KEY.tonic + 7) % 12  # a call that ends home is answered on the 5th


def test_write_counter_melody_and_answer_read_the_parts(monkeypatch):
    from creaper import music_tools
    mel = C.melody(events(1), KEY, seed=4)
    written = {}

    def fake_call(cmd, **kw):
        if cmd == "get_midi_notes":
            return {"notes": mel}
        if cmd == "add_midi_notes":
            written[kw["item_id"]] = kw["notes"]
            return {"notes_added": len(kw["notes"])}
        return {"time_signature": "4/4"}

    monkeypatch.setattr(music_tools, "call", fake_call)
    out = music_tools.write_counter_melody(item_id="{C}", melody_item_id="{M}", chords="Am F C G", key="A minor",
                                           seed=1, feel="none")
    assert out["notes_written"] == len(written["{C}"]) > 0 and out["key"] == "A minor"
    out = music_tools.write_answer(item_id="{R}", motif_item_id="{M}", key="A minor", feel="none")
    assert out["starts_at_qn"] >= max(n["start"] + n["length"] for n in mel) - 1e-6
    assert written["{R}"][-1]["pitch"] % 12 == KEY.tonic or written["{R}"][-1]["pitch"] % 12 == (KEY.tonic + 7) % 12


def test_check_voice_leading_finds_no_parallels_between_the_two_lines():
    for seed in (3, 5, 7, 9):
        ev = events(2)
        mel = C.melody(ev, KEY, seed=seed)
        line = C.counter_melody(mel, lambda t: C.chord_at(ev, t).chord.pitch_classes(), KEY, seed=1)
        pairs = []
        for c in line:
            above = next((m for m in mel if m["start"] <= c["start"] + 1e-6 < m["start"] + m["length"]), None)
            pairs.append([c["pitch"], above["pitch"]] if above else None)
        runs = [[pairs[i], pairs[i + 1]] for i in range(len(pairs) - 1) if pairs[i] and pairs[i + 1]]
        issues = [i for r in runs for i in C.check_voice_leading(r) if "parallel" in i["issue"]]
        assert not issues, (seed, issues)


def test_plan_harmony_keeps_to_the_keys_family():
    pop = ["I-V-vi-IV", "vi-IV-I-V", "minor: i-VI-III-VII"]
    plan = C.plan_harmony(pop, KEY, ["Verse", "Chorus"], default_mode="major")
    assert plan[0]["chords"] == "Am F C G"                  # the genre's minor progression, not I-V-vi-IV on A
    only_major = C.plan_harmony(pop[:2], KEY, ["Verse", "Chorus"], default_mode="major")
    assert only_major[0]["chords"] == "C G Am F" and "relative" in only_major[0]["how"]
    assert only_major[0]["key"] == "A minor"
    for row in only_major:                                    # all in A minor's notes
        for sym in row["chords"].split():
            ch = theory.parse_chord(sym)
            assert {(ch.root + i) % 12 for i in ch.intervals} <= set(KEY.pitch_classes()), sym


def test_a_lifted_chorus_is_spelled_as_musicians_would():
    plan = C.plan_harmony(["minor: i-VI-III-VII"], H.parse_key("F# minor"), ["Chorus", "Chorus"], lift_last_chorus=True)
    assert plan[-1]["key"] == "G# minor" and "Fb" not in plan[-1]["chords"]


# ------------------------------------------------------------ review regressions

def test_a_varied_groove_is_the_same_in_every_process():
    import subprocess
    import sys
    code = ("from creaper import server; from creaper import genres, grooves; "
            "print(grooves.vary_groove(genres.find('house').groove['pattern'], 0.25, 32, 'clap_roll', seed=1))")
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={**__import__("os").environ, "PYTHONHASHSEED": h}).stdout for h in ("1", "2", "3")}
    assert len(outs) == 1 and next(iter(outs)).strip()


def _no_same_pitch_overlaps(notes, end=None):
    ns = sorted(notes, key=lambda n: (n["pitch"], n["start"]))
    for a, b in zip(ns, ns[1:]):
        if a["pitch"] == b["pitch"]:
            assert a["start"] + a["length"] <= b["start"] + 1e-6, (a, b)
    if end is not None:
        assert all(n["start"] + n["length"] <= end + 1e-6 for n in notes)


@pytest.mark.parametrize("rhythm", ["push", "stabs", "pulse_16", "eighths", "strum"])
def test_anticipation_never_doubles_a_note(rhythm):
    ev = events(1)
    notes = C.develop_comp(C.comp(ev, C.voice_chords([e.chord for e in ev], "close", 3), rhythm), ev, rhythm,
                           anticipate=True)
    _no_same_pitch_overlaps(notes)


@pytest.mark.parametrize("style", sorted(C._DEVELOP_STYLES))
@pytest.mark.parametrize("chord_qn,meter", [(4.0, "4/4"), (2.0, "4/4"), (3.0, "3/4")])
def test_a_developed_bass_has_no_overlaps_or_notes_past_the_end(style, chord_qn, meter):
    ev = C.timeline(LOOP * 4, chord_qn)
    for kick in ("lock", "avoid"):
        notes = C.develop_bass(C.bassline(ev, style, KEY, meter=meter, seed=0), ev, style, meter, seed=0,
                               groove=[0, 1, 2], kick=kick)
        _no_same_pitch_overlaps(notes, ev[-1].end)


def test_a_pedal_stays_a_pedal():
    ev = events(2)
    notes = C.develop_bass(C.bassline(ev, "pedal", KEY), ev, "pedal", seed=1)
    assert {n["pitch"] % 12 for n in notes} == {KEY.tonic}


def test_bass_variety_is_measured_before_the_feel(monkeypatch):
    from creaper import music_tools
    monkeypatch.setattr(music_tools, "call", lambda cmd, **kw: {"time_signature": "4/4"} if cmd != "add_midi_notes"
                        else {"added": len(kw["notes"])})
    played, grid = (music_tools.write_bassline(item_id="{B}", chords="Am F C G Am F C G", key="A minor",
                                               style="whole", develop=False, seed=1, feel=f) for f in ("natural", "none"))
    assert played["distinct_bars"] == grid["distinct_bars"] < 1   # the feel's timing doesn't make bars "new"


@pytest.mark.parametrize("length", [2, 3, 4, 5, 8])
def test_a_progression_that_ends_home_has_no_tonic_or_repeat_before_it(length):
    for key in (H.parse_key("C major"), KEY):
        for seed in range(20):
            seq = C.generate_progression(key, length, seed=seed, end_on_tonic=True)
            assert len(seq) == length and seq[-1] in ("I", "i")
            assert all(a != b for a, b in zip(seq, seq[1:])), (seed, seq)


def test_counter_melody_edges():
    mel = [{"pitch": 72, "start": 1.0, "length": 0.5}, {"pitch": 74, "start": 1.5, "length": 0.5},
           {"pitch": 76, "start": 2.0, "length": 0.5}, {"pitch": 77, "start": 2.5, "length": 0.5}]
    line = C.counter_melody(mel, lambda t: None, H.parse_key("C major"), density=1.0, seed=1)
    assert all(n["start"] >= 1.0 for n in line)           # nothing before the melody starts
    assert C.counter_melody([dict(n, muted=True) for n in mel], lambda t: None, H.parse_key("C major")) == []
    low = C.answer([{"pitch": 3, "start": 0.0, "length": 1.0}, {"pitch": 5, "start": 1.0, "length": 1.0}],
                   H.parse_key("C major"))
    assert all(0 <= n["pitch"] <= 127 for n in low)


def test_a_low_line_in_a_narrow_range_keeps_its_contour():
    """Deep Cover's flute (C# dorian, C#4-C#5, a low verse line) circled C#4: every note
    of a cell under the range was clamped onto the bottom note."""
    key = H.parse_key("C# dorian")
    chords = [r.chord for r in H.parse_progression("i-IV-i-bVI", key)]
    for seed in range(50, 66):
        notes = C.melody(C.timeline(chords * 4, 16.0), key, density="sparse", low=61, high=73, shape="verse",
                         seed=seed)
        pitches = [n["pitch"] for n in notes]
        bottom = sum(p == 61 for p in pitches) / len(pitches)
        assert bottom < 0.35, (seed, bottom)
        assert len(set(pitches)) >= 4, (seed, sorted(set(pitches)))
