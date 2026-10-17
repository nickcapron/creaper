"""The opt-in music model: never imported unless used, its maths, and its one line on
the scorecard and the reference comparison."""

import subprocess
import sys

import numpy as np

from creaper import server  # noqa: F401  (import order: server first)
from creaper import embeddings


def test_creaper_never_imports_the_heavy_extra():
    code = "import sys; from creaper import server; print('transformers' in sys.modules, 'torch' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    assert out == "False False"


def test_character_is_a_softmax_over_each_pair():
    audio = np.array([1.0, 0.0, 0.0])
    text = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0],          # realism: close to the praise
                     [0.0, 1.0, 0.0], [0.99, 0.14, 0.0],        # era: close to the complaint
                     [0.6, 0.8, 0.0], [0.6, 0.8, 0.0],          # mix: undecided
                     [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]])
    c = embeddings.character(audio, text)
    assert c["realism"]["share"] > 0.99 and c["realism"]["leans"].startswith("realistic")
    assert c["era"]["share"] < 0.01 and "1990s" in c["era"]["leans"]
    assert c["mix"]["share"] == 0.5
    assert embeddings.similarity(np.array([1.0, 1.0]), np.array([2.0, 2.0])) == 1.0


def test_windows_come_from_the_middle_at_48k():
    x = np.zeros(22050 * 60)
    w = embeddings._windows(x, 22050)
    assert len(w) == 3 and all(len(v) == embeddings.RATE * 10 for v in w)
    assert len(embeddings._windows(np.zeros(22050 * 4), 22050)[0]) == embeddings.RATE * 4


def test_the_scorecard_gets_a_character_line_only_when_installed(monkeypatch, tmp_path):
    import test_song as T
    from creaper import ear_tools, export_tools, music_tools, song_tools

    fake = T.FakeReaper(project=str(tmp_path / "song.rpp"), renders=tmp_path / "renders")
    (tmp_path / "renders").mkdir()
    for m in (server, music_tools, song_tools, ear_tools, export_tools):
        monkeypatch.setattr(m, "call", fake)
    monkeypatch.setattr(server.bridge, "directory", tmp_path, raising=False)
    fake.render_audio = T._song_audio()
    monkeypatch.setattr(embeddings, "available", lambda: False)
    assert "character" not in song_tools.check_song(genre="pop")
    monkeypatch.setattr(embeddings, "available", lambda: True)
    monkeypatch.setattr(embeddings, "describe", lambda mono, fs: {"character": {"realism": {"share": 0.7}}})
    card = song_tools.check_song(genre="pop")
    assert card["character"]["character"]["realism"]["share"] == 0.7
    assert all(r["check"] != "character" for r in card["checks"])      # never a check that can fail
