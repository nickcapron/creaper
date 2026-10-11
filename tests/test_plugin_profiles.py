import pytest

from creaper import plugin_profiles as pp
from creaper.server import _number


def test_profiles_match_fx_names():
    assert pp.find_profile("VST3: Bus FORCE (Arturia)").name == "Bus FORCE"
    assert pp.find_profile("VST3: Comp FET-76 (Arturia)").role == "compressor"
    assert pp.find_profile("VST: ReaComp (Cockos)").drive == "Threshold"
    assert pp.find_profile("VST3: EQ SITRAL-295 (Arturia)").drive is None
    assert pp.find_profile("VST3: Some Other Plugin") is None
    assert pp.find_profile("VST3i: Piano V3 (Arturia)").role == "instrument"
    assert pp.find_profile("VST3i: Stage-73 V2 (Arturia)") is None
    assert pp.find_profile(None) is None


def test_every_compressor_profile_can_be_calibrated():
    for p in pp.PROFILES:
        if p.role in ("compressor", "bus processor"):
            assert p.drive and p.drive_more in ("up", "down") and p.drive_range
            assert p.drive in p.controls.values()


@pytest.mark.parametrize("name, current, missing, expect", [
    ("Comp VCA-65", 0.0, 1.0, "lower"),   # threshold style: more GR -> lower threshold
    ("Comp FET-76", -24.0, 1.0, "higher"),  # input style: more GR -> more input
])
def test_next_drive_direction(name, current, missing, expect):
    profile = pp.find_profile(name)
    value = pp.next_drive(current, gain_reduction=0.5, target=0.5 + missing, profile=profile)
    assert (value < current) if expect == "lower" else (value > current)


def test_next_drive_stays_in_range():
    profile = pp.find_profile("Comp FET-76")
    assert pp.next_drive(-1.0, 0.0, 10.0, profile) == 0.0       # top of the input range
    assert pp.next_drive(-47.0, 9.0, 0.0, profile) == -48.0      # bottom


def test_bus_force_setup_opens_the_compressor_path():
    setup = {c["parameter"]: c for c in pp.find_profile("Bus FORCE").setup}
    assert setup["Comp Path Mute"]["display_text"] == "Off"
    assert setup["Sat Path Mute"]["display_text"] == "On"  # parallel paths would otherwise double the level


@pytest.mark.parametrize("display, value", [("-18.0 dB", -18.0), ("+0.00", 0.0), ("2.5 kHz", 2500.0), ("4.00", 4.0)])
def test_number(display, value):
    assert _number(display) == value


def test_next_drive_grows_with_scale_and_has_a_minimum_step():
    vca = pp.find_profile("Comp VCA-65")
    small = pp.next_drive(0.0, 1.45, 1.5, vca)              # tiny miss still moves >= 2% of the range
    assert 0.0 - small >= 0.02 * 60 - 1e-9
    assert pp.next_drive(0.0, 0.0, 1.5, vca, scale=4) < pp.next_drive(0.0, 0.0, 1.5, vca)


def test_create_track_says_what_a_known_instrument_is(monkeypatch):
    from creaper import server
    monkeypatch.setattr(server, "call", lambda cmd, **kw: {
        "track": {"name": kw["name"]}, "instrument": {"name": "VST3i: Piano V3 (Arturia)"}})
    result = server.create_track(name="Keys", instrument="Piano V3")
    assert "not the sampled" in result["instrument"]["profile"]["how_it_works"]
    monkeypatch.setattr(server, "call", lambda cmd, **kw: {"track": {"name": kw["name"]}})
    assert "instrument" not in server.create_track(name="Empty")
