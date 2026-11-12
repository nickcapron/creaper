"""REAPER's audio and MIDI setup for the hardware tests: what the bridge's list_inputs,
hardware_status and hardware_open_prefs answer, and the audio hardware Windows reported
on the machine these tools were first used on (2026-11-11: a laptop with an SSL 2+)."""

MIC = "WASAPI Microphone Array (Intel® Smart Sound Technology for Digital Microphones)"
SSL_WASAPI = "WASAPI Input (SSL 2+ USB Audio Device)"
SSL_ASIO = "ASIO SSL ASIO Driver 1"

_SSL_DLL = r"c:\program files\solid state logic\sslusbaudiodriver\x64\sslusbdriverasio_x64.dll"
WINDOWS = {
    "asio": [
        {"name": "Elektron Digitone", "dll": r"c:\program files\elektron overbridge\elektronoverbridge_dn_x64.dll"},
        {"name": "Elektron Digitone II", "dll": r"c:\program files\elektron overbridge\elektronoverbridge_dnii_x64.dll"},
        {"name": "Elektron Analog Four", "dll": r"c:\program files\elektron overbridge\elektronoverbridge_af_x64.dll"},
        {"name": "JD-08", "dll": r"C:\windows\system32\RDAS1232.DLL"},
        {"name": "SSL ASIO Driver 2", "dll": _SSL_DLL}, {"name": "SSL ASIO Driver 1", "dll": _SSL_DLL},
        {"name": "SSL ASIO Driver 3", "dll": _SSL_DLL}, {"name": "SSL ASIO Driver 4", "dll": _SSL_DLL},
        {"name": "ASIO4ALL v2", "dll": r"c:\program files (x86)\asio4all v2\asio4all64.dll"},
    ],
    "inputs": [
        {"name": "Line", "device": "SSL 2+ USB Audio Device", "bus": "TUSBAUDIO_ENUM", "active": False},
        {"name": "Input 1", "device": "SSL 2+ USB Audio Device", "bus": "TUSBAUDIO_ENUM", "active": True},
        {"name": "Microphone Array", "device": "Intel® Smart Sound Technology for Digital Microphones",
         "bus": "INTELAUDIO", "active": True},
        {"name": "Input 2", "device": "SSL 2+ USB Audio Device", "bus": "TUSBAUDIO_ENUM", "active": True},
        {"name": "Input", "device": "SSL 2+ USB Audio Device", "bus": "TUSBAUDIO_ENUM", "active": True},
        {"name": "Headset", "device": "Jabra Elite 4 Active Hands-Free", "bus": "BTHHFENUM", "active": False},
    ],
}


class Reaper:
    """The setup side of a fake bridge. Defaults: an interface the tests don't know by
    name, running, every port enabled, neither of the in-the-way settings on."""

    def __init__(self, midi_outputs=None, midi_inputs=None):
        self.running, self.opens = True, True
        self.mode, self.input, self.output = "ASIO", "ASIO Test Interface", "ASIO Test Interface"
        self.sample_rate, self.block_size = 48000, 512
        self.midi_outputs = midi_outputs if midi_outputs is not None else [
            {"device": 0, "name": "Microsoft GS Wavetable Synth"}, {"device": 1, "name": "UM-ONE"}]
        self.midi_inputs = midi_inputs if midi_inputs is not None else [{"device": 0, "name": "UM-ONE"}]
        self.settings = {"promptendrec": False, "audiocloseinactive": False}
        self.can_change = True               # REAPER 7.74+: set_config_var_string is there
        self.session: dict[str, int] = {}    # the originals of what was turned off for the session
        self.version = "7.85/win64"
        self.prefs_opened: list[str] = []
        self.user_does = None                # what the user changes once a settings page is open
        self.has_status = True               # False: a bridge from before hardware_status
        self.status_calls: list[dict] = []

    def list_inputs(self):
        return {"audio_inputs": [{"channel": 1, "name": "Input 1"}, {"channel": 2, "name": "Input 2"}] if self.running else [],
                "midi_inputs": self.midi_inputs, "midi_outputs": self.midi_outputs}

    def _ports(self, ports):
        return [{"device": p["device"], "name": p["name"], "present": p.get("present", True),
                 "enabled": p.get("enabled", True)} for p in ports]

    def status(self, params=None):
        from creaper.bridge import BridgeError
        params = params or {}
        if not self.has_status:
            raise BridgeError("this bridge (v0.59.1) doesn't know 'hardware_status'; update creaper_bridge.lua")
        self.status_calls.append(params)
        if params.get("open_audio") and self.opens:
            self.running = True
        restored = None
        if params.get("session") == "begin" and self.can_change:
            for key, on in self.settings.items():
                if on:
                    self.session[key] = 1
                    self.settings[key] = False
        if params.get("session") == "end" and self.session:
            restored = {key: True for key in self.session}
            for key in self.session:
                self.settings[key] = True
            self.session = {}
        out = {
            "reaper_version": self.version,
            "audio": {"running": self.running, "mode": self.mode if self.running else None,
                      "input": self.input if self.running else None, "output": self.output if self.running else None,
                      "sample_rate": self.sample_rate, "block_size": self.block_size, "input_channels": 2},
            "midi": {"inputs": self._ports(self.midi_inputs), "outputs": self._ports(self.midi_outputs),
                     "input_enables_known": True, "output_enables_known": True},
            "settings": {**self.settings, "can_change": self.can_change,
                         "changed_for_session": dict(self.session) or None},
        }
        if restored:
            out["restored"] = restored
        return out

    def open_prefs(self, params):
        self.prefs_opened.append(params["page"])
        if self.user_does:
            self.user_does(self)
        return {**self.status(), "opened": "audio device page", "held_seconds": 0.0}

    def answer(self, cmd, params):
        """The answer to a setup command, or None when the command isn't one."""
        if cmd == "list_inputs":
            return self.list_inputs()
        if cmd == "hardware_status":
            return self.status(params)
        if cmd == "hardware_open_prefs":
            return self.open_prefs(params)
        return None
