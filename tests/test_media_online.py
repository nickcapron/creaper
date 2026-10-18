"""A render that comes back silent (media a sync app took offline) brings media online and
renders once more; other renders never run the action, and it isn't retried for a while."""

import numpy as np
import soundfile as sf

from creaper import server


class FakeBridge:
    def __init__(self, tmp_path, silent_until):
        self.directory = tmp_path
        (tmp_path / "renders").mkdir(exist_ok=True)
        self.renders, self.actions, self.silent_until = 0, [], silent_until

    def call(self, cmd, params, timeout=30.0):
        if cmd == "run_action":
            self.actions.append(params["command"])
            return {}
        self.renders += 1
        f = self.directory / "renders" / f"r{self.renders}.wav"
        level = 0.0 if self.renders <= self.silent_until else 0.3
        sf.write(str(f), np.full((4800, 2), level, dtype=np.float32), 48000)
        return {"files": [str(f)]}


def test_a_silent_render_brings_media_online_once(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=1)
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_media_tried", [0.0])
    out = server.call("render_audio", track="master")
    assert fake.actions == [server.MEDIA_ONLINE_ACTION] and fake.renders == 2
    assert out["files"][0].endswith("r2.wav") and not (tmp_path / "renders" / "r1.wav").exists()


def test_a_sounding_render_never_runs_the_action(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=0)
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_media_tried", [0.0])
    server.call("render_audio", track="master")
    assert fake.actions == [] and fake.renders == 1


def test_a_truly_silent_range_is_left_alone_after_one_try(monkeypatch, tmp_path):
    fake = FakeBridge(tmp_path, silent_until=99)
    monkeypatch.setattr(server, "bridge", fake)
    monkeypatch.setattr(server, "_media_tried", [0.0])
    server.call("render_audio", track="master")
    server.call("render_audio", track="master")          # a quiet tail measured again
    assert fake.actions == [server.MEDIA_ONLINE_ACTION]  # tried once, not every time
