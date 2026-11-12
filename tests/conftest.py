import pytest


@pytest.fixture(autouse=True)
def _no_installed_vocalvst_decides(monkeypatch):
    """Whether VocalVST reads pronunciation overrides depends on the plugin build installed
    on the machine running the tests, and the CMU phonemes on its dictionary. Tests pin
    both (off, empty) and turn them on where they test them."""
    from creaper import lyric_melody, vocal_tools

    monkeypatch.setattr(lyric_melody, "overrides_supported", lambda **kw: False)
    monkeypatch.setattr(vocal_tools, "_HEARD_TAKES", {})     # takes heard per track, kept for a session
    monkeypatch.setattr(lyric_melody, "_phones_cache", {})


@pytest.fixture(autouse=True)
def _no_panel_conversation_of_this_machine(monkeypatch):
    """Tests run as a server outside the chat panel unless they say otherwise: no
    conversation id or status file from the environment, no taskbar flash or sound when a
    test asks a question, and nothing remembered from the test before."""
    from creaper import convstate, server, timing

    monkeypatch.delenv(convstate.ENV, raising=False)
    monkeypatch.delenv(timing.STATUS_FILE_ENV, raising=False)
    monkeypatch.setenv(server.QUESTION_ALERT_ENV, "0")
    monkeypatch.setattr(server, "_made_tracks", set())
    monkeypatch.setattr(server, "_nobody_there", [False])


@pytest.fixture(autouse=True)
def _no_audio_hardware_of_this_machine(monkeypatch):
    """Which audio interface a synth belongs to is worked out from the Windows registry of
    the machine running the tests. Tests start with none and name the hardware they test."""
    from creaper import hardware_setup

    monkeypatch.setattr(hardware_setup, "windows_audio", lambda: {"asio": [], "inputs": []})
    monkeypatch.setattr(hardware_setup, "_sleep", lambda s: None)


@pytest.fixture(autouse=True)
def _no_remembered_render_noise(monkeypatch):
    """batch remembers which tracks render differently every time for a session; each
    test starts without that memory."""
    from creaper import batch

    monkeypatch.setattr(batch, "_noisy", {})
