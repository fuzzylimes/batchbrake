# batchbrake

Generate HandBrake batch encode scripts for TV discs.

## Requirements

- Python 3.11+
- `ffprobe` (install via `sudo apt install ffmpeg`)
- HandBrake CLI (Flatpak or native)
- `pipx` for installation

## Installation

```bash
pipx install ./batchbrake
```

## Usage

### disc — split a single multi-episode disc file by chapters

```bash
batchbrake disc \
  -i "/path/to/file/InitialD_1-7.mkv" \
  --show "Initial D" \
  --season 01 \
  --start-ep 1
```

batchbrake will probe the file, auto-detect episode boundaries, show you a
chapter table and proposed mapping, and drop you into a confirmation menu
before writing anything.

### bulk — encode individual episode files

```bash
batchbrake bulk \
  -d "/path/to/file" \
  --prefix "Disc 3" \
  --show "Neon Genesis Evangelion" \
  --season 01 \
  --start-ep 11
```

batchbrake will probe the first matched file for stream info, ask which
subtitle track to set as default, show you the file→episode mapping, and
let you confirm before writing the script.

## Common flags (both modes)

| Flag | Description |
|------|-------------|
| `--show` | Show name (required) |
| `--season` | Season number, zero-padded (default: 01) |
| `--start-ep` | First episode number in this batch (default: 1) |
| `--quality` | x265 CRF quality, overrides config |
| `--preset` | HandBrake encoder preset, overrides config |
| `--allow-crop` | Allow HandBrake auto-crop instead of forcing 0:0:0:0 |
| `--output-dir` | Where HandBrake writes encoded files, overrides config |
| `--script-out` | Full path for generated .sh script |
| `--handbrake-cmd` | HandBrake CLI invocation, overrides config |

## disc-only flags

| Flag | Description |
|------|-------------|
| `-i / --input` | Input MKV file (required) |
| `--ep-duration` | Target episode duration in minutes for auto-detect, overrides config |
| `--chapters-per-ep` | Force fixed chapter count per episode, skips auto-detect |

## bulk-only flags

| Flag | Description |
|------|-------------|
| `-d / --dir` | Directory containing source MKV files (required) |
| `--prefix` | Filename prefix to filter files, e.g. "Disc 3" |

## Configuration

A config file is auto-generated on first run at:

```
~/.config/batchbrake/config.toml
```

All config values can be overridden per-run via CLI flags.
Active config values are displayed at the start of every run.
