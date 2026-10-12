"""Motifs saved once and placed in any key, mode, octave and speed."""
from creaper import motif_tools as m

MOTIF = [{"pitch": 60, "start": 0, "length": 1, "velocity": 100},    # C
         {"pitch": 63, "start": 1, "length": 1, "velocity": 100},    # Eb
         {"pitch": 67, "start": 2, "length": 1, "velocity": 100},    # G
         {"pitch": 68, "start": 3, "length": 2, "velocity": 100}]    # Ab


def test_capture_takes_a_range_from_zero():
    notes = [dict(n, start=n["start"] + 8) for n in MOTIF] + [{"pitch": 40, "start": 20, "length": 1}]
    got = m.capture(notes, start=8, end=13)
    assert [n["pitch"] for n in got] == [60, 63, 67, 68] and got[0]["start"] == 0


def test_moves_into_another_key_and_mode_degree_by_degree():
    in_d_minor = m.transform(MOTIF, "C minor", "D minor")
    assert [n["pitch"] for n in in_d_minor] == [62, 65, 69, 70]          # D F A Bb
    in_d_major = m.transform(MOTIF, "C minor", "D major")
    assert [n["pitch"] for n in in_d_major] == [62, 66, 69, 71]          # D F# A B: minor turns major
    low_slow = m.transform(MOTIF, "C minor", "C minor", octave=-1, stretch=2)
    assert [n["pitch"] for n in low_slow] == [48, 51, 55, 56]
    assert [(n["start"], n["length"]) for n in low_slow] == [(0, 2), (2, 2), (4, 2), (6, 4)]


def test_save_list_and_place(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "motifs_file", lambda: tmp_path / "motifs.json")
    calls = []

    def fake_call(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == "get_midi_notes":
            return {"notes": MOTIF}
        return {"note_count": 4}
    monkeypatch.setattr(m, "call", fake_call)
    m.save_motif(name="Title motif", item_id="x", key="C minor", description="the signature")
    assert m.list_motifs()["motifs"][0]["notes"] == ["C4", "Eb4", "G4", "Ab4"]
    placed = m.place_motif(name="title MOTIF", item_id="y", start=4, key="D major")
    assert placed["notes"] == ["D4", "F#4", "A4", "B4"]
    sent = calls[-1][1]["notes"]
    assert sent[0]["start"] == 4 and sent[-1]["start"] == 7
