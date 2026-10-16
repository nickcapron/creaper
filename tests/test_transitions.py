import numpy as np

from creaper import server  # noqa: F401  (loads the tool modules first)
from creaper import arrange_tools as at
from creaper import ear_candy


def test_section_energy_comes_from_the_names():
    assert at.energy("Intro") == 1 and at.energy("Verse 2") == 2
    assert at.energy("Pre-Chorus") == 3 and at.energy("Drop") == 4 and at.energy("Breakdown") == 1
    assert at.energy("Section A") == 2  # unknown names count as the middle


def test_the_plan_scales_with_the_change_and_varies_repeated_peaks():
    sections = [{"name": "Intro", "bar": 1}, {"name": "Verse", "bar": 9}, {"name": "Chorus", "bar": 25},
                {"name": "Breakdown", "bar": 41}, {"name": "Chorus 2", "bar": 49}]
    plan = {c["bar"]: c for c in at.plan(sections, "build")}
    assert plan[9]["elements"] == ["reverse", "crash", "fill"]               # a small lift: no riser, no impact
    assert plan[25]["elements"] == ["riser", "impact", "crash", "fill", "dropout"]   # the first peak: the full build
    assert plan[41]["direction"] == "down" and "downlifter" in plan[41]["elements"]
    assert plan[49]["elements"] == ["reverse", "impact", "crash", "fill"]     # the next peak: a different build
    assert at.plan(sections, "subtle")[0]["elements"] == ["reverse", "crash"]


def test_impacts_only_land_on_the_peaks():
    sections = [{"name": "Intro", "bar": 1}, {"name": "Pre-Chorus", "bar": 9}, {"name": "Chorus", "bar": 13}]
    plan = {c["bar"]: c for c in at.plan(sections, "epic")}
    assert "impact" not in plan[9]["elements"] and "impact" in plan[13]["elements"]


def test_risers_swell_and_get_brighter_into_the_downbeat():
    fs = ear_candy.FS
    a = ear_candy.riser(2.0)
    assert a.shape == (2 * fs, 2) and abs(20 * np.log10(np.abs(a).max()) + 6) < 0.01

    def centroid(x):
        spec = np.abs(np.fft.rfft(x[:, 0]))
        freqs = np.fft.rfftfreq(len(x), 1 / fs)
        return (spec * freqs).sum() / spec.sum()

    first, last = a[: fs // 2], a[-fs // 2:]
    assert np.sqrt(np.mean(last ** 2)) > 10 * np.sqrt(np.mean(first ** 2))
    assert centroid(last) > centroid(first)


def test_the_reverse_swell_sounds_like_a_cymbal_not_hiss():
    fs = ear_candy.FS
    swell = ear_candy.reverse_swell(2.0)[-fs // 2:, 0]
    spec = np.abs(np.fft.rfft(swell))
    freqs = np.fft.rfftfreq(len(swell), 1 / fs)
    assert 4000 < (spec * freqs).sum() / spec.sum() < 9000   # the first version sat near 13.5 kHz


def test_the_impact_sub_is_short_and_optional():
    fs = ear_candy.FS
    hit = ear_candy.impact()
    assert abs(20 * np.log10(np.abs(hit).max()) + 6) < 0.01
    no_sub = ear_candy.impact(sub=False)[:, 0]
    spec = np.abs(np.fft.rfft(no_sub)) ** 2
    freqs = np.fft.rfftfreq(len(no_sub), 1 / fs)
    assert spec[freqs < 120].sum() / spec.sum() < 0.1


def test_impacts_and_swells_have_the_right_shape():
    hit = ear_candy.impact(2.0)
    assert np.abs(hit[: 4410]).max() > 10 * np.abs(hit[-4410:]).max()      # loud at the hit, dies away
    swell = ear_candy.reverse_swell(1.0)
    assert np.abs(swell[-4410:]).max() > 10 * np.abs(swell[: 4410]).max()  # grows into the downbeat
    assert not any(np.isnan(x).any() for x in (hit, swell, ear_candy.downlifter(1.0)))


def test_add_transitions_places_sounds_and_drum_touches(tmp_path, monkeypatch):
    calls = []
    item = {"id": "{ITEM}", "type": "midi", "start": {"qn": 0.0}, "end": {"qn": 128.0}}

    def fake_call(command, **args):
        calls.append((command, args))
        if command == "get_project_overview":
            return {"time_signature": "4/4", "regions": [
                {"name": "Verse", "start": {"bar": 1}}, {"name": "Chorus", "start": {"bar": 9}}],
                "tracks": [{"guid": "{DRUMS}", "number": 1, "name": "Drums", "item_count": 1}]}
        if command == "create_track":
            return {"track": {"guid": "{FX}", "number": 2, "name": "Transitions"}}
        if command == "project_paths":
            return {}
        if command == "bar_to_qn":
            return {"qn": (args["bar"] - 1) * 4}
        if command == "qn_to_times":
            return [q * 0.5 for q in args["qns"]]
        if command == "get_track_details":
            return {"items": [] if args.get("track") == "{FX}" else [item]}
        if command == "get_instrument_notes":
            return {"instrument": None, "note_names": []}
        return {}

    monkeypatch.setattr(at, "call", fake_call)
    monkeypatch.setattr(server, "call", fake_call)
    monkeypatch.setattr(at, "_fx_folder", lambda: tmp_path)
    result = at.add_transitions(intensity="build")
    change = result["changes"][0]
    assert change["into"] == "Chorus" and change["direction"] == "up"
    assert set(change["added"]) == {"riser", "impact", "crash", "fill", "dropout"}
    inserts = [a for c, a in calls if c == "insert_audio_file"]
    assert {a["start_bar"] for a in inserts} == {7, 9}            # a 2-bar riser into bar 9, the impact on it
    deletes = [a for c, a in calls if c == "delete_midi_notes"]
    drop = next(a for a in deletes if a["pitch"] == 36)
    assert drop["start"] == 30.0 and drop["end"] == 32.0                   # the kick out for 2 beats
    cleared = next(a for a in deletes if a["pitch"] == 38)
    assert cleared["start"] == 30.0 and cleared["end"] == 32.0             # the fill replaces the snare under it
    assert len(list(tmp_path.glob("*.wav"))) == 2


def test_regions_inside_others_and_on_the_same_bar_are_one_section():
    # Regions "Chorus" and "vocals in" both on bar 9 gave a riser and a downlifter on one downbeat.
    regions = [{"name": "Intro", "start": {"bar": 1}, "end": {"bar": 9}},
               {"name": "Chorus", "start": {"bar": 9}, "end": {"bar": 17}},
               {"name": "vocals in", "start": {"bar": 9}, "end": {"bar": 11}},
               {"name": "shot_01", "start": {"bar": 12}, "end": {"bar": 13}},
               {"name": "Verse", "start": {"bar": 17}, "end": {"bar": 25}}]
    assert at.sections_from_regions(regions) == [{"name": "Intro", "bar": 1}, {"name": "Chorus", "bar": 9},
                                                 {"name": "Verse", "bar": 17}]


def test_a_riser_never_reaches_into_an_earlier_section():
    plan = at.plan([{"name": "Verse", "bar": 1}, {"name": "Build", "bar": 9}, {"name": "Drop", "bar": 11}], "epic")
    into_drop = next(c for c in plan if c["bar"] == 11)
    assert into_drop["from_bar"] == 9   # a 4-bar epic riser is cut to the 2-bar build
