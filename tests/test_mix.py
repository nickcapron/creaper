"""auto_mix's plan: roles, levels, EQ, compression, panning, sends, sidechains."""
from creaper.mix_tools import plan_mix, role_of


def test_roles_from_names_and_sound():
    assert role_of("909 Kick") == "kick" and role_of("Clap") == "snare" and role_of("Open Hat") == "perc"
    assert role_of("Octave Bass") == "bass" and role_of("Bass Duck") == "bass" and role_of("Robot Vocal") == "vocal"
    assert role_of("Strings Pad") == "pad" and role_of("Clav") == "keys" and role_of("Synth Hook") == "lead"
    assert role_of("909 Drums") == "drums" and role_of("Riser FX") == "fx"
    low = {"bands": {"sub (20-60 Hz)": {"share_pct": 40}, "bass (60-250 Hz)": {"share_pct": 35}}}
    assert role_of("Track 7", low) == "bass"
    assert role_of("Track 8", {"bands": {}, "spectral_centroid_hz": 6000}) == "perc"


def channel(name, role, level, **kw):
    return {"name": name, "role": role, "level": level, "peak_db": -3, "crest_db": 15,
            "spectrum": {"bands": {"low mids (250-500 Hz)": {"share_pct": 20}}}, "pan": 0, **kw}


def test_plan_sets_levels_relative_to_the_drums_for_the_genre():
    chans = [channel("Kick", "kick", -10), channel("Bass", "bass", -6), channel("Pad", "pad", -8),
             channel("Vocal", "vocal", -15)]
    plan = plan_mix(chans, {"family": "electronic dance", "mix": {"low_end": "heavy"}})
    gains = {a["name"]: a["gain_db"] for a in plan["channels"]}
    assert plan["anchor_lufs"] == -10
    assert gains == {"Kick": 0, "Bass": -5.0, "Pad": -12.0, "Vocal": 4.0}   # bass -1 LU (heavy low end), pad -10, vocal -1
    assert plan["sidechains"] == [{"source": "Kick", "target": "Bass", "depth": "medium"},
                                  {"source": "Kick", "target": "Pad", "depth": "light"}]
    pop = plan_mix(chans, {"family": "pop", "mix": {"low_end": "moderate"}})
    assert {a["name"]: a["gain_db"] for a in pop["channels"]}["Vocal"] == 6.0 and not pop["sidechains"]


def test_plan_cleans_up_without_touching_what_the_user_set():
    chans = [channel("Kick", "kick", -10),
             channel("Keys", "keys", -15, spectrum={"bands": {"low mids (250-500 Hz)": {"share_pct": 40}}}),
             channel("Keys 2", "keys", -15, pan=-0.5),
             channel("Lead", "lead", -12, has_eq=True, has_comp=True),
             channel("Vocal", "vocal", -12, crest_db=8)]
    acts = {a["name"]: a for a in plan_mix(chans)["channels"]}
    assert acts["Keys"]["highpass_hz"] == 140 and acts["Keys"]["mud_cut_db"] == -3.0 and acts["Keys"]["pan"] == 0.25
    assert "pan" not in acts["Keys 2"]                                   # already panned by the user
    assert "highpass_hz" not in acts["Lead"] and "compress" not in acts["Lead"]   # has its own EQ and compressor
    assert "compress" not in acts["Vocal"]                               # already even (crest 8 dB)
    assert "highpass_hz" not in acts["Kick"] and "reverb_send_db" not in acts["Kick"]
    assert acts["Vocal"]["reverb_send_db"] == -14


def test_silent_tracks_are_left_alone():
    acts = {a["name"]: a for a in plan_mix([channel("Kick", "kick", -10), channel("Ghost", "lead", None)])["channels"]}
    assert acts["Ghost"] == {"name": "Ghost", "role": "lead", "skipped": "silent in this range"}



def test_boosts_are_capped_and_sub_drones_barely_raised():
    sub = {"bands": {"sub (20-60 Hz)": {"share_pct": 70}, "bass (60-250 Hz)": {"share_pct": 20}}}
    acts = {a["name"]: a for a in plan_mix([channel("Kick", "kick", -10), channel("Lead", "lead", -30),
                                             channel("Drone", "other", -30, spectrum=sub)])["channels"]}
    assert acts["Lead"]["gain_db"] == 6.0        # wanted +15
    assert acts["Drone"]["gain_db"] == 2.0       # a K-weighted meter underrates sub: barely raised


def test_highpass_stays_under_a_parts_lowest_notes():
    from creaper.mix_tools import highpass_for
    def octaves(**dbs):
        return {"octave_bands_db": dbs}
    cello = octaves(**{"63 Hz": -6, "125 Hz": -4, "250 Hz": -8, "500 Hz": -14})           # fundamentals from ~65 Hz
    assert highpass_for("pad", cello) is None    # 0.6 x 44.5 Hz is under 40 Hz: no high-pass at all
    viola = octaves(**{"125 Hz": -30, "250 Hz": -6, "500 Hz": -4, "1 kHz": -8})
    assert highpass_for("pad", viola) == 106     # under its lowest strong octave (~177 Hz), not the usual 180
    hats = octaves(**{"2 kHz": -10, "4 kHz": -4, "8 kHz": -3})
    assert highpass_for("perc", hats) == 300     # nothing low: the usual high-pass
    assert highpass_for("bass", cello) is None
