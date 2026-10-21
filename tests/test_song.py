"""Whole songs: the arrangement plan, the song map, build_song, the stage gates, the
scorecard and the reference comparison, against an in-memory REAPER."""

import itertools
import math
import statistics

import numpy as np
import pytest
import soundfile as sf

from creaper import server  # noqa: F401  (import order: server first)
from creaper import composer, ear_tools, export_tools, genres, music_tools, song_tools, songmap


class FakeReaper:
    """Tracks, MIDI items and notes, regions and tempo: enough of the bridge for the song tools."""

    def __init__(self, project=None, renders=None):
        self.tracks: list[dict] = []
        self.items: dict[str, dict] = {}
        self.regions: list[dict] = []
        self.bpm, self.meter = 120.0, "4/4"
        self.project = project
        self.renders = renders
        self.render_audio = None
        self.master_fx: list[dict] = []
        self.calls: list[tuple] = []
        self._ids = itertools.count(1)

    def _pos(self, qn):
        return {"qn": qn, "bar": int(qn // 4) + 1, "seconds": round(qn * 60 / self.bpm, 3), "beat": 1}

    def _track(self, ref):
        if ref == "master":
            return {"name": "master", "fx": self.master_fx}
        for t in self.tracks:
            if ref in (t["guid"], t["name"], t["number"]):
                return t
        raise ValueError(f"no track {ref}")

    def add_track(self, name, instrument=None):
        n = len(self.tracks) + 1
        t = {"name": name, "guid": f"{{T{n}}}", "number": n, "instrument": instrument}
        self.tracks.append(t)
        return t

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw))
        if cmd == "get_project_overview":
            return {"tracks": [{k: t[k] for k in ("name", "guid", "number")} for t in self.tracks],
                    "regions": [dict(r) for r in self.regions], "tempo_bpm": self.bpm, "time_signature": self.meter,
                    "length": {"bar": 1 + max([int(i["end"] // 4) for i in self.items.values()] or [0])}}
        if cmd == "project_paths":
            return {"project": self.project, "name": "song.rpp" if self.project else ""}
        if cmd == "set_tempo":
            self.bpm = float(kw["bpm"])
            self.meter = f"{kw.get('numerator', 4)}/{kw.get('denominator', 4)}"
            return {"tempo_bpm": self.bpm}
        if cmd == "get_tempo_map":
            return {"start_tempo_bpm": self.bpm, "start_time_signature": self.meter, "changes": []}
        if cmd == "create_track":
            t = self.add_track(kw["name"], kw.get("instrument"))
            return {"track": {k: t[k] for k in ("name", "guid", "number")}}
        if cmd == "get_track_details":
            t = self._track(kw["track"])
            if t["name"] == "master":
                return {"name": "master", "fx": [dict(f, index=i + 1) for i, f in enumerate(self.master_fx)]}
            items = [{"id": i_id, "type": "midi", "muted": False, "start": self._pos(i["start"]),
                      "end": self._pos(i["end"])} for i_id, i in self.items.items() if i["track"] is t]
            return {"name": t["name"], "items": items, "fx": [],
                    **({"instrument_fx": 1} if t.get("instrument") else {})}
        if cmd == "create_midi_item":
            t = self._track(kw["track"])
            i_id = f"{{I{next(self._ids)}}}"
            start = (kw["start_bar"] - 1) * 4.0
            self.items[i_id] = {"track": t, "start": start, "end": start + kw["length_bars"] * 4.0, "notes": [],
                                "name": kw.get("name")}
            return {"id": i_id}
        if cmd == "delete_item":
            del self.items[kw["item_id"]]
            return {}
        if cmd == "get_midi_notes":
            return {"notes": [dict(n) for n in self.items[kw["item_id"]]["notes"]]}
        if cmd == "add_midi_notes":
            item = self.items[kw["item_id"]]
            if kw.get("replace"):
                item["notes"] = []
            item["notes"] += [dict(n) for n in kw["notes"]]
            return {"added": len(kw["notes"]), "note_count": len(item["notes"])}
        if cmd == "get_instrument_notes":
            return {"instrument": None, "note_names": []}
        if cmd == "add_marker":
            a, b = (kw["start_bar"] - 1) * 4.0, (kw["end_bar"] - 1) * 4.0
            self.regions.append({"name": kw["name"], "start": self._pos(a), "end": self._pos(b)})
            return {}
        if cmd == "time_to_positions":
            return [self._pos(t * self.bpm / 60) for t in kw["times"]]
        if cmd == "render_audio":
            path = self.renders / f"render{next(self._ids)}.wav"
            audio, fs = self.render_audio
            sf.write(str(path), audio, fs)
            return {"files": [str(path)], "track": "master", "start": self._pos(0.0),
                    "end": self._pos(audio.shape[0] / fs * self.bpm / 60)}
        if cmd == "add_fx":
            self.master_fx.insert(kw.get("position", len(self.master_fx) + 1) - 1, {"name": kw["name"]})
            return {"index": kw.get("position", len(self.master_fx))}
        if cmd == "update_fx":
            if kw.get("rename"):
                self.master_fx[kw["fx"] - 1]["name"] = kw["rename"]
            return {}
        if cmd == "remove_fx":
            del self.master_fx[kw["fx"] - 1]
            return {}
        if cmd == "set_fx_parameters":
            self.master_fx[kw["fx"] - 1]["changes"] = kw["changes"]
            return {}
        raise AssertionError(f"unexpected bridge command {cmd}")


@pytest.fixture
def reaper(monkeypatch, tmp_path):
    fake = FakeReaper(renders=tmp_path)
    for module in (server, music_tools, song_tools, ear_tools, export_tools):
        monkeypatch.setattr(module, "call", fake)
    monkeypatch.setattr(server, "confirm_with_user", lambda action: None)
    monkeypatch.setattr(song_tools, "confirm_with_user", lambda action: None)
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)
    (tmp_path / "renders").mkdir()
    fake.renders = tmp_path / "renders"
    return fake


# ------------------------------------------------------------- plan_song

def test_each_kind_of_section_gets_its_own_parts():
    pop = genres.find("pop")
    plan = songmap.plan_song(pop, song_tools._numbered(list(pop.form)), seed=2)
    by = {row["section"]: row for row in plan}
    assert "lead" not in by["Intro"]["parts"] and "drums" in by["Intro"]["parts"]
    hooks = {row["parts"]["lead"]["seed"] for row in plan if row["kind"] == "chorus"}
    assert len(hooks) == 1                                  # the hook comes back in every chorus
    verses = [row["parts"]["lead"]["seed"] for row in plan if row["kind"] == "verse"]
    assert len(set(verses)) == len(verses)                  # a new line each verse
    choruses = [row for row in plan if row["kind"] == "chorus"]
    assert "counter" not in choruses[0]["parts"] and all("counter" in c["parts"] for c in choruses[1:])
    drums = [row["parts"]["drums"]["seed"] for row in plan if "drums" in row["parts"]]
    assert len(set(drums)) == len(drums)
    assert plan[-1]["start_bar"] + plan[-1]["bars"] == 1 + sum(b for _, b in pop.form)


def test_club_songs_start_and_end_on_drums():
    house = genres.find("house")
    plan = songmap.plan_song(house, song_tools._numbered(list(house.form)), seed=1)
    assert set(plan[0]["parts"]) == {"drums"}
    assert "drums" not in next(r for r in plan if r["kind"] == "breakdown")["parts"]
    assert "drums" in plan[-1]["parts"] and "bass" in plan[-1]["parts"]


# ------------------------------------------------------------- song_map

def _bars(pitches, bars, start_bar=0, step=1.0):
    return [{"pitch": pitches[i % len(pitches)], "start": start_bar * 4 + i * step, "length": step * 0.9}
            for i in range(int(bars * 4 / step))]


def test_the_song_map_finds_copies_loops_and_a_flat_arc():
    secs = [{"name": "Verse 1", "start_qn": 0, "end_qn": 32, "energy": 2},
            {"name": "Chorus 1", "start_qn": 32, "end_qn": 64, "energy": 4},
            {"name": "Verse 2", "start_qn": 64, "end_qn": 96, "energy": 2}]
    tracks = {"Bass": _bars([33, 36], 24), "Lead": _bars([50, 53], 24, step=0.5),
              "Pad": [{"pitch": p, "start": b * 4.0, "length": 4.0} for b in range(24) for p in (60, 64, 67)]}
    m = songmap.song_map(tracks, secs)
    v2 = m["sections"][2]["tracks"]
    assert v2["Bass"]["same_as"] == "Verse 1" and v2["Bass"]["copied_share"] == 1.0
    checks = {f["check"] for f in m["findings"]}
    assert {"section copy", "track loop", "density arc", "register"} <= checks
    assert m["sections"][0]["tracks"]["Lead"]["range"] == "D3-F3"


def test_a_developing_song_has_no_findings():
    rng = np.random.default_rng(1)
    secs = [{"name": "Verse", "start_qn": 0, "end_qn": 32, "energy": 2},
            {"name": "Chorus", "start_qn": 32, "end_qn": 64, "energy": 4}]
    lead = [{"pitch": int(rng.integers(67, 84)), "start": i * 0.5, "length": 0.4} for i in range(64)]
    lead += [{"pitch": int(rng.integers(67, 84)), "start": 32 + i * 0.25, "length": 0.2} for i in range(128)]
    pad = [{"pitch": p + b % 5, "start": b * 4.0, "length": 4.0} for b in range(16) for p in (48, 52, 55)]
    assert songmap.song_map({"Lead": lead, "Pad": pad}, secs)["findings"] == []


# ------------------------------------------------------------- build_song

def test_build_song_writes_every_section_as_its_own_variant(reaper):
    out = song_tools.build_song(genre="pop", key="A minor", seed=3)
    pop = genres.find("pop")
    assert [r["name"] for r in reaper.regions] == [n for n, _ in song_tools._numbered(list(pop.form))]
    assert {t["name"] for t in reaper.tracks} == {"Drums", "Bass", "Chords", "Lead", "Counter"}
    assert all(i["notes"] for i in reaper.items.values())
    m = song_tools.song_map()
    assert not [f for f in m["findings"] if f["status"] == "fail"], m["findings"]
    by_energy = {}
    for s in m["sections"]:
        by_energy.setdefault(s["energy"], []).append(s["notes_per_bar"])
    assert statistics.mean(by_energy[4]) > statistics.mean(by_energy[2]) > statistics.mean(by_energy[1])
    # No two sections play the same drums, bass or chords.
    for track in ("Drums", "Bass", "Chords"):
        assert not [s for s in m["sections"] if s["tracks"].get(track, {}).get("same_as")], track
    leads = [s["tracks"]["Lead"] for s in m["sections"] if s["section"].startswith("Chorus") and "Lead" in s["tracks"]]
    assert any(c.get("same_as") for c in leads)             # the hook returns
    assert out["seed"] == 3 and out["key"] == "A minor"
    assert all(n["start"] + n["length"] <= i["end"] - i["start"] + 1e-6
               for i in reaper.items.values() for n in i["notes"])


def test_build_song_is_reproducible_with_a_seed(monkeypatch, tmp_path):
    songs = []
    for _ in range(2):
        fake = FakeReaper()
        for module in (server, music_tools, song_tools, ear_tools):
            monkeypatch.setattr(module, "call", fake)
        song_tools.build_song(genre="house", key="A minor", sections=["Intro:8", "Groove:16", "Drop:16"], seed=9)
        songs.append(sorted((i["name"], tuple(sorted((n["pitch"], round(n["start"], 3)) for n in i["notes"])))
                            for i in fake.items.values()))
    assert songs[0] == songs[1]


def test_build_song_reuses_tracks_and_wont_overwrite_without_asking(reaper):
    reaper.add_track("Bass", instrument="Mini V")
    reaper.add_track("Lead Synth", instrument="Pigments")
    reaper.regions = []
    item = reaper("create_midi_item", track="Bass", start_bar=3, length_bars=2)
    reaper("add_midi_notes", item_id=item["id"], notes=[{"pitch": 40, "start": 0, "length": 1}])
    with pytest.raises(ValueError, match="replace=True"):
        song_tools.build_song(genre="pop", key="C major", sections=["Verse:8", "Chorus:8"], seed=1)
    out = song_tools.build_song(genre="pop", key="C major", sections=["Verse:8", "Chorus:8"], seed=1, replace=True)
    assert item["id"] not in reaper.items
    assert out["tracks"]["bass"] == "Bass" and out["tracks"]["lead"] == "Lead Synth"
    assert [t["name"] for t in reaper.tracks].count("Bass") == 1


def test_build_song_uses_the_regions_already_there(reaper):
    reaper("add_marker", name="Verse", start_bar=1, end_bar=9)
    reaper("add_marker", name="Chorus", start_bar=9, end_bar=17)
    out = song_tools.build_song(genre="rock", key="E minor", seed=4)
    assert [s["section"] for s in out["sections"]] == ["Verse", "Chorus"] and len(reaper.regions) == 2
    assert out["bars"] == 16


# ------------------------------------------------------------- stages

def test_stages_refuse_on_a_fail_and_keep_score(reaper, tmp_path):
    reaper.project = str(tmp_path / "song.rpp")
    out = song_tools.start_song(brief="a test song", genre="pop", length="3 minutes")
    assert out["plan"].endswith("song - creaper song.json")
    with pytest.raises(ValueError, match="named sections"):
        song_tools.finish_stage(stage="form")
    song_tools.build_song(genre="pop", key="A minor", seed=3)
    assert song_tools.finish_stage(stage="form")["done"]
    with pytest.raises(ValueError, match="instrument"):
        song_tools.finish_stage(stage="sounds")              # the new tracks have no instrument yet
    forced = song_tools.finish_stage(stage="sounds", force=True)
    assert forced["forced_past"] and forced["next"] == "parts"
    status = song_tools.song_status()
    assert [s["stage"] for s in status["stages"] if s["done"]] == ["form", "sounds"]
    assert status["stages"][1]["forced"] and status["next"] == "parts"


def test_song_status_needs_a_plan(reaper):
    with pytest.raises(ValueError, match="start_song"):
        song_tools.song_status()


# ------------------------------------------------------------- scorecard

def test_the_scorecard_scores_and_reports_changes():
    rows = [songmap.row("a", "pass"), songmap.row("b", "warn", 0.45, 0.4, "fix b"),
            songmap.row("c", "fail", 0.7, 0.4, "fix c")]
    card = songmap.scorecard(rows)
    assert card["score"] == 5.0 and card["failed"] == 1 and rows[1]["fix"] == "fix b"
    again = songmap.scorecard([songmap.row("a", "pass"), songmap.row("b", "pass", 0.3, 0.4),
                               songmap.row("c", "warn", 0.5, 0.4)], previous=card)
    assert again["score_change"] == 3.3
    assert again["checks"][2]["was"] == "fail" and again["checks"][2]["change"] == -0.2
    assert songmap.graded("x", 0.5, 0.4, 0.6, "f")["status"] == "warn"
    assert songmap.graded("x", 0.3, 0.5, 0.25, "f", higher_is_worse=False)["status"] == "warn"


def _song_audio(fs=16000, bars=32, bpm=120.0):
    """A test master: a kick every beat, a verse tone, a louder chorus with more going on."""
    beat = int(fs * 60 / bpm)
    out = np.zeros((bars * 4 * beat, 2))
    t = np.arange(beat) / fs
    kick = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 18)
    rng = np.random.default_rng(0)
    for b in range(bars * 4):
        out[b * beat:(b + 1) * beat, :] += kick[:, None] * 0.5
        chorus = 8 <= b // 4 < 16 or b // 4 >= 24
        hz = 220 * (1 + (b // 4) % 5 / 8)
        tone = np.sin(2 * np.pi * hz * t) * (0.25 if chorus else 0.1)
        out[b * beat:(b + 1) * beat, 0] += tone + rng.normal(0, 0.01, beat)
        out[b * beat:(b + 1) * beat, 1] += tone * 0.9 + rng.normal(0, 0.01, beat)
    return out.astype(np.float32), fs


def test_check_song_renders_once_and_keeps_a_baseline(reaper, tmp_path):
    reaper.project = str(tmp_path / "song.rpp")
    song_tools.build_song(genre="pop", key="A minor", seed=3,
                          sections=["Verse 1:8", "Chorus 1:8", "Verse 2:8", "Chorus 2:8"])
    reaper.render_audio = _song_audio()
    card = song_tools.check_song(genre="pop")
    renders = [c for c, _ in reaper.calls if c == "render_audio"]
    assert len(renders) == 1
    assert 0 <= card["score"] <= 10 and card["checks"]
    assert {r["stage"] for r in card["checks"]} >= {"form", "parts", "transitions", "mix", "master"}
    assert all(r["status"] in ("pass", "warn", "fail") for r in card["checks"])
    assert (tmp_path / "song - creaper checks.json").exists()
    again = song_tools.check_song(genre="pop")
    assert again["previous_score"] == card["score"] and again["score_change"] == 0


def test_a_second_song_like_the_last_is_flagged(reaper, tmp_path):
    reaper.render_audio = _song_audio()
    reaper.project = str(tmp_path / "one.rpp")
    song_tools.check_song(genre="pop")
    reaper.project = str(tmp_path / "two.rpp")
    card = song_tools.check_song(genre="pop")
    like = next(r for r in card["checks"] if r["check"] == "like the last song")
    assert like["status"] == "warn" and like["value"] < 1.5


# ------------------------------------------------------------- reference

def _noise(fs, seconds, tilt_db_per_octave=0.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(fs * seconds)
    spec = np.fft.rfft(rng.normal(0, 1, n))
    f = np.fft.rfftfreq(n, 1 / fs)
    f[0] = f[1]
    spec *= 10 ** (tilt_db_per_octave * np.log2(f / 1000) / 20)
    x = np.fft.irfft(spec, n)
    x = x / np.max(np.abs(x)) * 0.5
    return np.stack([x, x * 0.98], axis=1)


def test_the_reference_match_is_bounded_and_points_the_right_way():
    fs = 32000
    bright, dark = _noise(fs, 8, +2.0), _noise(fs, 8, -2.0, seed=1)
    ref = {"curve": song_tools.third_octave_curve(bright.mean(axis=1), fs)}
    mix = {"curve": song_tools.third_octave_curve(dark.mean(axis=1), fs)}
    gains = {g["band"]: g["gain_db"] for g in song_tools.match_gains(ref, mix)}
    assert gains["air shelf"] > 0 and gains["low shelf"] < 0
    assert all(abs(v) <= song_tools.MATCH_MAX_DB for v in gains.values())
    assert song_tools.match_gains(ref, ref) == []


def test_compare_to_reference_reads_a_file_and_can_apply(reaper, tmp_path):
    fs = 32000
    ref_path = tmp_path / "reference.wav"
    sf.write(str(ref_path), _noise(fs, 12, +2.0).astype(np.float32), fs)
    reaper.render_audio = (_noise(fs, 12, -2.0, seed=2).astype(np.float32), fs)
    out = song_tools.compare_to_reference(file=str(ref_path), apply=True)
    features = {r["feature"] for r in out["differences"]}
    assert "loudness (LUFS)" in features and any(f.startswith("tone:") for f in features)
    assert any(f.startswith("width") for f in features)
    assert len(out["energy_arc"]["mix"]) == 8
    assert reaper.master_fx[0]["name"] == song_tools.MATCH_FX_NAME
    first = reaper.master_fx[0]["changes"]
    assert {"parameter": "Freq-High Pass 5", "display_value": 20} in first
    song_tools.compare_to_reference(file=str(ref_path), apply=True)
    assert [f["name"] for f in reaper.master_fx].count(song_tools.MATCH_FX_NAME) == 1   # replaced, not stacked
    with pytest.raises(ValueError, match="no file"):
        song_tools.compare_to_reference(file=str(tmp_path / "missing.wav"))


def test_fingerprints_compare_only_like_with_like():
    a = {"curve": {str(i): float(i) for i in range(10)}, "tempo": 120, "meter": "4/4"}
    assert songmap.fingerprint_distance(a, dict(a)) == 0
    assert songmap.fingerprint_distance(a, dict(a, tempo=128)) is None
    assert songmap.fingerprint_distance(a, dict(a, curve={k: v + 2 for k, v in a["curve"].items()})) == 2.0
    assert math.isclose(composer._bar_len("4/4"), 4.0)


def test_a_post_chorus_answers_the_chorus_a_step_down():
    from creaper import arrange_tools
    pop = genres.find("pop")
    layout = [("Chorus 1", 8), ("Post-chorus 1", 8), ("Chorus 2", 8)]
    plan = songmap.plan_song(pop, layout, seed=1, energies=[arrange_tools.energy(n) for n, _ in layout])
    post = plan[1]
    assert post["kind"] == "post" and post["energy"] == 3
    assert post["parts"]["lead"]["shape"] == "answer" and "counter" not in post["parts"]
    assert "counter" in plan[2]["parts"]


def test_build_song_follows_regions_with_gaps_and_wont_double_them(reaper):
    reaper("add_marker", name="Verse", start_bar=1, end_bar=9)
    reaper("add_marker", name="Chorus", start_bar=13, end_bar=21)      # four bars of something else between
    song_tools.build_song(genre="pop", key="C major", seed=2)
    chorus = [i for i in reaper.items.values() if i["name"].startswith("Chorus")]
    assert chorus and all(i["start"] == 48.0 for i in chorus)
    with pytest.raises(ValueError, match="already has regions"):
        song_tools.build_song(genre="pop", sections=["Verse:8"], replace=True)


def test_a_silent_master_fails_instead_of_crashing(reaper, tmp_path):
    reaper.project = str(tmp_path / "song.rpp")
    reaper.render_audio = (np.zeros((16000 * 20, 2), dtype=np.float32), 16000)
    card = song_tools.check_song(genre="pop")
    assert any(r["check"] == "sound" and r["status"] == "fail" for r in card["checks"])


def test_a_mono_mix_reads_as_narrow_not_missing():
    fs = 16000
    mono = _noise(fs, 4)
    mono[:, 1] = mono[:, 0]
    assert all(v == song_tools.MONO_SIDE_DB for v in song_tools.width_by_band(mono, fs).values())


def test_the_bars_of_a_reference_are_found_from_its_beat():
    audio, fs = _song_audio(bpm=120.0)             # a kick every beat at 120 BPM: bars of 2 s
    starts, bpm = song_tools.estimate_bars(audio.mean(axis=1), fs)
    assert bpm == pytest.approx(120, abs=3)
    assert np.median(np.diff(starts)) == pytest.approx(2.0, abs=0.05)
    loop = np.tile(audio[: fs * 8], (8, 1))          # the same 4 bars eight times
    starts, _ = song_tools.estimate_bars(loop.mean(axis=1), fs)
    assert song_tools._repetition(loop.mean(axis=1), fs, starts) > 0.8



# ------------------------------------------------------------- review regressions

def test_tracks_are_matched_by_role_and_claimed_once(reaper):
    for name in ("Bass Drum", "Pad Lead", "Counter Lead", "Sub Bass"):
        reaper.add_track(name, instrument="x")
    found = song_tools._find_tracks(reaper("get_project_overview"), list(songmap.PARTS))
    names = {p: t["name"] for p, t in found.items()}
    assert names == {"bass": "Sub Bass", "chords": "Pad Lead", "counter": "Counter Lead"}   # "Bass Drum" is a kick
    item = reaper("create_midi_item", track="Bass Drum", start_bar=1, length_bars=2)
    reaper("add_midi_notes", item_id=item["id"], notes=[{"pitch": 36, "start": 0, "length": 1}])
    song_tools.build_song(genre="pop", sections=["Verse:8", "Chorus:8"], replace=True, seed=1)
    assert item["id"] in reaper.items                       # not a part's track: left alone


def test_replace_only_clears_midi_inside_the_sections(reaper):
    reaper("add_marker", name="Verse", start_bar=1, end_bar=9)
    reaper("add_marker", name="Chorus", start_bar=13, end_bar=21)
    reaper.add_track("Bass", instrument="x")
    gap = reaper("create_midi_item", track="Bass", start_bar=10, length_bars=2)
    song_tools.build_song(genre="pop", key="C major", seed=1)            # nothing in the way: no replace needed
    assert gap["id"] in reaper.items


def test_empty_stages_fail(reaper, tmp_path):
    reaper.project = str(tmp_path / "song.rpp")
    reaper("add_marker", name="Verse", start_bar=1, end_bar=9)
    reaper("add_marker", name="Chorus", start_bar=9, end_bar=17)
    song_tools.start_song(brief="b", genre="pop")
    for stage in ("sounds", "parts", "feel"):
        with pytest.raises(ValueError, match="isn't finished"):
            song_tools.finish_stage(stage=stage)


def test_structure_findings_go_under_the_right_check():
    class Ctx:
        def render(self):
            return {}, {"near_duplicate_share": 0.2, "longest_loop_bars": 4, "findings": [
                "Chorus 2 plays like Chorus 1 bar for bar: vary it (a lift, new parts, a different groove or voicing)",
                "Chorus should lift from Verse but is +0.2 LU"]}
    rows = {r["check"]: r for r in song_tools._transitions_rows(Ctx())}
    assert rows["section repeats"]["status"] == "warn" and "Chorus 2" in rows["section repeats"]["detail"]
    assert rows["energy arc"]["detail"].startswith("Chorus should lift")
    short = song_tools._transitions_rows(type("C", (), {"render": lambda self: ({}, {"findings": ["too short"]})})())
    assert short[0]["check"] == "structure" and short[0]["status"] == "warn"


def test_the_register_check_sees_rolled_chords_tops():
    chords = [{"pitch": p, "start": b * 4 + i * 0.005, "length": 4} for b in range(16) for i, p in enumerate((52, 55, 60, 64))]
    lead = [{"pitch": 59, "start": b * 4 + 1, "length": 1} for b in range(16)]
    secs = [{"name": "Verse", "start_qn": 0, "end_qn": 64}]
    m = songmap.song_map({"Chords": chords, "Lead": lead}, secs)
    assert any(f["check"] == "register" for f in m["findings"])        # 59 is under the chords' top (64)
    assert songmap._tops(chords)[:2] == [64, 64]


def test_the_last_chorus_lifts_not_the_post_chorus(reaper):
    out = song_tools.build_song(genre="pop", key="C major", lift_last_chorus=True, seed=1,
                                sections=["Verse 1:8", "Chorus 1:8", "Verse 2:8", "Chorus 2:8", "Post-chorus:8"])
    keys = {s["section"]: s["key"] for s in out["sections"]}
    assert keys["Chorus 2"] == "D major" and keys["Post-chorus"] == "C major"
    assert composer.section_kind("Post-chorus") == "post"


def test_regions_keep_their_meter(reaper):
    reaper("add_marker", name="Verse", start_bar=1, end_bar=9)
    reaper("add_marker", name="Chorus", start_bar=9, end_bar=17)
    song_tools.build_song(genre="mariachi", seed=1)
    assert reaper.meter == "4/4"
    assert not any(c == "set_tempo" for c, _ in reaper.calls)


def test_the_plan_length_beats_the_genre_form(reaper, tmp_path):
    assert song_tools.target_bars("a 30 s loop", 120, 4) == 15
    assert song_tools.target_bars("3-4 minutes", 120, 4) == 90
    assert song_tools.target_bars("16 bars", 120, 4) == 16 and song_tools.target_bars("short", 120, 4) is None
    reaper.project = str(tmp_path / "loop.rpp")
    song_tools.start_song(brief="a menu loop", genre="pop", length="16 bars", use="a game menu loop")
    song_tools.build_song(genre="pop", sections=["Verse:8", "Chorus:8"], seed=2)
    rows = song_tools.finish_stage(stage="form")["checks"]
    assert any(r["check"] == "length against the plan" and r["status"] == "pass" for r in rows)


def test_no_chord_part_for_a_genre_without_comping():
    g = next(g for g in genres.GENRES.values() if g.comping == "none") if isinstance(genres.GENRES, dict) else         next(g for g in genres.GENRES if g.comping == "none")
    plan = songmap.plan_song(g, [("Intro", 4), ("Verse", 8), ("Chorus", 8), ("Breakdown", 8), ("Outro", 4)], 1)
    assert not any("chords" in row["parts"] for row in plan)


def test_a_silent_master_is_one_failure(reaper, tmp_path):
    reaper.project = str(tmp_path / "song.rpp")
    reaper.render_audio = (np.zeros((16000 * 20, 2), dtype=np.float32), 16000)
    card = song_tools.check_song(genre="pop")
    assert sum(r["check"] == "sound" for r in card["checks"]) == 1


def test_repeated_checks_compare_with_their_own_previous_row():
    first = songmap.scorecard([songmap.row("energy arc", "pass"), songmap.row("energy arc", "warn")])
    again = songmap.scorecard([songmap.row("energy arc", "warn"), songmap.row("energy arc", "warn")], first)
    assert again["checks"][0]["was"] == "pass" and "was" not in again["checks"][1]


def test_a_silent_reference_is_refused(reaper, tmp_path):
    path = tmp_path / "silent.wav"
    sf.write(str(path), np.zeros((32000 * 4, 2), dtype=np.float32), 32000)
    reaper.render_audio = (_noise(32000, 4), 32000)
    with pytest.raises(ValueError, match="couldn't measure"):
        song_tools.compare_to_reference(file=str(path))


def test_an_empty_midi_item_needs_no_instrument(monkeypatch):
    """A noise generator's track with an empty MIDI item on it isn't a part missing its sound."""
    items = {"Room Tone": [{"type": "midi", "muted": False, "note_count": 0}],
             "Lead": [{"type": "midi", "muted": False, "note_count": 12}],
             "Hook Melody": [{"type": "midi", "muted": False, "note_count": 20}]}
    monkeypatch.setattr(song_tools, "call", lambda cmd, **kw: {"items": items[kw["track"]]})
    # A muted guide for a robot vocal plays nothing either (Claude loaded ReaSynth on one to pass this).
    tracks = [{"name": "Room Tone"}, {"name": "Lead"}, {"name": "Hook Melody", "mute": True}]
    ctx = type("Ctx", (), {"overview": {"tracks": tracks}})()
    rows = song_tools._sounds_rows(ctx)
    assert [(r["track"], r["status"]) for r in rows] == [("Lead", "fail")]


def test_mastering_moves_get_the_balance_checked_again(monkeypatch):
    """Mastering added a limiter to the lead and raised it 3 dB after the mix was signed off;
    nothing checked the balance again and the user found the lead overpowering."""
    from creaper import ear_tools
    snap = song_tools._mix_snapshot({"tracks": [
        {"name": "Drums", "guid": "{D}", "volume_db": -9, "fx": ["ReaComp"]},
        {"name": "Lead", "guid": "{L}", "volume_db": 0, "fx": ["Prophet-5 V"]}]})
    now = {"tracks": [{"name": "Drums", "guid": "{D}", "volume_db": -9.4, "fx": ["ReaComp"]},
                      {"name": "Lead", "guid": "{L}", "volume_db": 3, "fx": ["Prophet-5 V", "VST: ReaLimit (Cockos)"]}]}
    ctx = type("Ctx", (), {"overview": now, "plan": {"stages": {"mix": {"done": True, "tracks": snap}}}})()
    measured = []
    monkeypatch.setattr(ear_tools, "measure_tracks", lambda **kw: measured.append(kw) or {"balance": [
        "Drop 1: Lead is 4.8 LU over its place (a lead part sits about 5 LU under the drums)",
        "Drop 1: Chords is 6.0 LU over its place (a keys part sits about 7 LU under the drums)"]})
    rows = song_tools._balance_rows(ctx)
    assert measured == [{"per_section": True}]
    assert [(r["track"], r["status"]) for r in rows] == [("Lead", "warn")]     # Drums moved under 1 dB
    assert "fader +3.0 dB; added VST: ReaLimit (Cockos)" in rows[0]["detail"] and "Lead is 4.8 LU over" in rows[0]["detail"]
    ctx.overview = {"tracks": [dict(t, volume_db=v) for t, v in zip(snap.values(), (-9, 0))]}
    assert song_tools._balance_rows(ctx) == [] and len(measured) == 1   # nothing moved: nothing rendered
