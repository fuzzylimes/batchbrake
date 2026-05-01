from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "batchbrake" / "config.toml"

_DEFAULT_CONFIG = """\
[handbrake]
command = "flatpak run --command=HandBrakeCLI fr.handbrake.ghb"
quality = 19
preset  = "medium"

[encoding]
# true  = always pass --crop 0:0:0:0 (use for DVD sources)
# false = let HandBrake auto-detect crop values (default)
force_crop = false

[output]
# Directory where generated .sh scripts are written. "." = current working dir.
script_dir = "."
# Directory where HandBrake writes encoded files.
# Leave empty to use the source file's directory (disc mode) or input dir (bulk mode).
output_dir = ""

[disc]
# Default target episode duration in minutes used for auto-detection.
ep_duration = 24
"""


@dataclass
class Config:
    command: str
    quality: int
    preset: str
    force_crop: bool
    script_dir: str
    output_dir: str
    ep_duration: float


def load_config() -> Config:
    """Load config from disk, creating the default file if it doesn't exist."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(_DEFAULT_CONFIG)
        print(f"Created default config at {CONFIG_PATH}\n")

    with open(CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)

    hb   = data.get("handbrake", {})
    enc  = data.get("encoding",  {})
    out  = data.get("output",    {})
    disc = data.get("disc",      {})

    return Config(
        command    = hb.get("command",    "flatpak run --command=HandBrakeCLI fr.handbrake.ghb"),
        quality    = int(hb.get("quality", 19)),
        preset     = hb.get("preset",    "medium"),
        force_crop = bool(enc.get("force_crop", False)),
        script_dir = out.get("script_dir", "."),
        output_dir = out.get("output_dir", ""),
        ep_duration= float(disc.get("ep_duration", 24)),
    )
