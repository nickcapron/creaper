import pytest


@pytest.fixture(autouse=True)
def _no_installed_vocalvst_decides(monkeypatch):
    """Whether VocalVST reads pronunciation overrides depends on the plugin build installed
    on the machine running the tests, and the CMU phonemes on its dictionary. Tests pin
    both (off, empty) and turn them on where they test them."""
    from creaper import lyric_melody

    monkeypatch.setattr(lyric_melody, "overrides_supported", lambda **kw: False)
    monkeypatch.setattr(lyric_melody, "_phones_cache", {})
