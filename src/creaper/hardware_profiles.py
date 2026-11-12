"""Device profiles for hardware synths: what a profile is, and which ones creaper has.

A profile is OPTIONAL. Every saved MIDI device can be played, auditioned, recorded,
printed and have its latency measured without one (hardware_sound_tools skips reading
and loading sounds, and the user sets the sound on the synth). A profile adds sound
design: reading the patch, parameters by name, recipes, sounds in the library and in
the song, stored programs.

A profile is a module (microkorg.py is the first) with the names listed in `Profile`
below. That class is the one place the interface is written down: hardware_sound_tools
and hardware_tools reach a device's specifics only through these names, and
tests/test_hardware_profiles.py checks every registered profile has them all.

Conventions:
- MIDI messages are hex strings as the bridge's send_midi takes them ("F0 42 30 58 10 F7").
- A patch is `bytes`: the device's whole current sound, PROGRAM_BYTES long.
- A request is (messages to send, the reply codes that answer it). parse_message turns
  an incoming message into (reply code, payload), or None for a message that isn't the
  device's; the matching *_reply / *_error function reads the answer.
- Nothing in a profile talks to REAPER.

Not covered yet (see notes/hardware-synths-plan.md): devices whose sound is a set of
control changes rather than a dump (a "controller map" profile), and devices with one
MIDI channel per part (PARTS > 1)."""

from __future__ import annotations

from types import ModuleType
from typing import Any, Protocol

from . import microkorg


class Profile(Protocol):
    """What hardware_sound_tools asks of a device profile."""

    # ---- what it is
    MODEL: str                 # as save_hardware's `model` and the sound library name it, e.g. "Korg microKORG"
    IDENTITY: dict             # its MIDI identity reply: maker (hex), family, member, kind,
    #                            device_id_is_channel, setup (how to cable and set it, one paragraph)
    SETUP_HELP: str            # what to set on the device when it doesn't answer
    PROTECT_HELP: str          # how the user turns its memory protect off
    PROGRAM_BYTES: int         # the length of a patch
    PARTS: int                 # sounds it plays at once on separate channels (1 = one sound, one channel)
    TEMPO_RANGE: tuple[int, int]
    TEMPO_PARAM: str           # the parameter that holds a patch's tempo (a recipe that sets it keeps it)

    # ---- capabilities: the generic layer skips what a device can't do
    READS_PATCH: bool          # answers read_request with its current sound (False: no read, no backup)
    ACKS_LOAD: bool            # answers load_request (False: a load is sent and taken on trust)

    # ---- messages
    def parse_message(self, hexstr: str) -> tuple[int, bytes] | None: ...
    def read_request(self, channel: int) -> tuple[list[str], set[int]]: ...
    def patch_reply(self, function: int, payload: bytes) -> bytes | None: ...      # None = it reported an error
    def load_request(self, channel: int, data: bytes) -> tuple[list[str], set[int]]: ...
    def load_error(self, function: int) -> str | None: ...                         # None = loaded
    def setup_request(self, channel: int) -> tuple[list[str], set[int]]: ...
    def setup_reply(self, function: int, payload: bytes) -> dict: ...
    def write_request(self, channel: int, number: int) -> tuple[list[str], set[int]]: ...
    def write_error(self, function: int) -> str | None: ...                        # None = written
    def select_program(self, channel: int, number: int) -> list[str]: ...          # bank select included, if any
    def program_dump(self, channel: int, data: bytes) -> str: ...                  # the sound as written into a song
    def patch_in_message(self, hexstr: str) -> bytes | None: ...                   # program_dump's inverse

    # ---- the device's own MIDI settings (setup_reply's dict)
    # Keys the generic layer reads: memory_protect, program_change_enabled.
    def setup_problems(self, setup: dict) -> list[str]: ...
    def live_blocked(self, setup: dict) -> str | None: ...
    def live(self, params: dict[str, Any], timbre: int | str, channel: int,
             setup: dict) -> tuple[list[str], list[str]]: ...                      # (messages, names it can't set live)

    # ---- patches as named parameters
    def decode_program(self, data: bytes) -> dict: ...
    def apply(self, data: bytes, params: dict[str, Any], timbre: int | str = 1) -> bytes: ...
    def init_program(self, template: bytes | None = None, name: str = "creaper") -> bytes: ...
    def click_patch(self, current: bytes | None) -> bytes: ...                     # for calibrate_hardware_latency
    def brief(self, data: bytes) -> dict: ...                                      # facts every result carries
    def flat(self, prog: dict) -> dict: ...                                        # decode_program's dict, one level
    def describe(self) -> dict: ...                                                # every parameter, for the model

    # ---- stored programs
    FACTORY_NOTES: dict[str, str]                                                  # presets worth knowing, by slot name
    def program_number(self, ref: str | int) -> int: ...                           # 'A.11' -> the number sent
    def program_name(self, number: int) -> str: ...

    # ---- recipes: {params, play, kind, style_of?, evidence?, factory?}
    def find_recipe(self, name: str) -> tuple[str, dict]: ...
    def build(self, recipe: dict, template: bytes | None = None) -> bytes: ...
    def describe_recipes(self, kind: str | None = None) -> list[dict]: ...

    # ---- tempo: what in a patch runs at a tempo of the device's own
    def tempo_features(self, data: bytes) -> list[str]: ...                        # empty = nothing does
    def tempo(self, data: bytes) -> int: ...
    def with_tempo(self, data: bytes, bpm: float) -> tuple[bytes, int]: ...        # (patch, the tempo it got)
    def clock_note(self, setup: dict | None) -> str: ...                           # when that tempo counts


INTERFACE = tuple(sorted(n for n in (*Profile.__annotations__, *vars(Profile)) if not n.startswith("_")))

PROFILES: dict[str, ModuleType] = {microkorg.MODEL: microkorg}


def for_model(model: str | None) -> ModuleType | None:
    """The profile for a device's model as the hardware map has it, or None."""
    return PROFILES.get(model or "")


def known_models() -> dict[tuple[str, int, int], dict[str, Any]]:
    """Models told from their identity reply: (maker hex, family, member) -> what scan_hardware says."""
    return {(p.IDENTITY["maker"], p.IDENTITY["family"], p.IDENTITY["member"]):
            {"model": p.MODEL, **{k: v for k, v in p.IDENTITY.items() if k not in ("maker", "family", "member")}}
            for p in PROFILES.values()}
