import pytest

from creaper import feel


def grid(pitches_by_start, velocity=90, length=0.5):
    return [{"pitch": p, "start": s, "length": length, "velocity": velocity, "channel": 1}
            for s, pitches in pitches_by_start for p in pitches]


def test_none_and_zero_amount_change_nothing():
    notes = grid([(0, [60]), (1, [62])])
    assert feel.apply(notes, "lead", "natural", amount=0) == notes


def test_pitches_order_and_count_never_change():
    notes = grid([(i * 0.5, [60 + i % 5]) for i in range(32)])
    for role in feel.ROLES:
        played = feel.apply(notes, role, "expressive", seed=1)
        assert [n["pitch"] for n in played] == [n["pitch"] for n in notes]
        assert all(0 <= n["start"] and 1 <= n["velocity"] <= 127 for n in played)


def test_same_seed_same_performance():
    notes = grid([(i * 0.25, [36 if i % 4 == 0 else 42]) for i in range(32)])
    assert feel.apply(notes, "drums", "natural", seed=3) == feel.apply(notes, "drums", "natural", seed=3)


def test_laid_back_snare_sits_behind_and_kick_stays_tight():
    notes = grid([(b, [36]) for b in (0, 2)] + [(b, [38]) for b in (1, 3)])
    played = feel.apply(notes, "drums", "laid back", bpm=90, seed=1)
    snare_late = [p["start"] - n["start"] for n, p in zip(notes, played) if n["pitch"] == 38]
    kick_move = [abs(p["start"] - n["start"]) for n, p in zip(notes, played) if n["pitch"] == 36]
    assert all(d > 0.01 for d in snare_late)          # ~14 ms behind at 90 BPM is ~0.02 QN
    assert max(kick_move) < min(snare_late)


def test_hats_are_accented_on_the_beat_and_softer_off_it():
    notes = grid([(i * 0.5, [42]) for i in range(16)], velocity=90)
    played = feel.apply(notes, "drums", "natural", seed=2)
    on = [p["velocity"] for n, p in zip(notes, played) if n["start"] % 1 == 0]
    off = [p["velocity"] for n, p in zip(notes, played) if n["start"] % 1 == 0.5]
    assert sum(on) / len(on) > sum(off) / len(off) + 8


def test_lane_names_tell_a_custom_kit_what_each_note_does():
    # A kit with its snare on note 60: by its lane name it's played as a backbeat.
    notes = grid([(1, [60]), (3, [60])])
    played = feel.apply(notes, "drums", "laid back", bpm=90, seed=1, drum_jobs={60: "backbeat"})
    assert all(p["start"] > n["start"] for n, p in zip(notes, played))
    assert feel.drum_job("Snare 2") == "backbeat" and feel.drum_job("closed hat") == "hats"
    assert feel.drum_job("Kick") == "kick" and feel.drum_job("Cowbell") is None


def test_chords_roll_low_to_high_and_the_top_voice_sings():
    notes = grid([(0, [48, 55, 64, 72])], velocity=80)
    played = sorted(feel.apply(notes, "chords", "natural", bpm=120, seed=1), key=lambda n: n["pitch"])
    starts = [n["start"] for n in played]
    assert starts == sorted(starts) and starts[-1] > starts[0]
    ends = [round(n["start"] + n["length"], 4) for n in played]
    assert max(ends) - min(ends) < 0.01                 # the chord still ends together
    assert played[-1]["velocity"] > played[1]["velocity"]


def test_a_lead_line_is_louder_toward_its_peak():
    line = grid([(i, [60 + i]) for i in range(12)], velocity=90)
    played = feel.apply(line, "lead", "natural", seed=4)
    assert played[-1]["velocity"] > played[0]["velocity"] + 6


def test_pads_stay_smooth():
    notes = grid([(0, [60, 64, 67]), (4, [62, 65, 69])], velocity=70, length=4)
    played = feel.apply(notes, "pad", "expressive", seed=1)
    assert all(abs(p["velocity"] - 70) <= 2 for p in played)


@pytest.mark.parametrize("text,family,name,want", [
    ("four-on-the-floor, straight, driving", "electronic dance", "techno", "tight"),
    ("swung 16ths, lazy behind-the-beat snare", "hip-hop", "boom bap", "laid back"),
    ("one drop: kick and rim together on beat 3", "caribbean", "reggae", "laid back"),
    ("straight and driving; 8th-note palm-muted chug", "metal and punk", "metal", "pushed"),
    ("straight eighths; sparse verses opening into a driving chorus", "pop", "pop", "natural"),
    ("Steady pulse shaped by rubato at phrase ends", "classical", "classical", "expressive"),
])
def test_genres_get_a_feel_from_their_profile(text, family, name, want):
    assert feel.feel_for_genre(text, family, 50, name) == want


def test_every_genre_profile_has_a_feel():
    from creaper import genres
    assert all(feel.feel_for_genre(g.feel, g.family, g.swing, g.name) in feel.FEELS for g in genres.GENRES)
