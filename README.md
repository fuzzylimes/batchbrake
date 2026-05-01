# batchbrake

Generate HandBrake batch encode scripts for disc rips — TV shows and movies.

## Requirements

- Python 3.11+
- `ffprobe` (install via `sudo apt install ffmpeg`)
- HandBrake CLI (Flatpak or native)
- `pipx` for installation

## Installation

```bash
pipx install git+https://github.com/fuzzylimes/batchbrake.git
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

### disc — encode a single movie file

```bash
batchbrake disc \
  -i "/path/to/file/Interstellar.mkv" \
  --movie "Interstellar"
```

When `--movie` is used, chapter detection and episode numbering are skipped.
The output is written to `$output_dir/Interstellar/Interstellar.mkv`.

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

`--show` and `--movie` are mutually exclusive — exactly one is required.

| Flag | Description |
|------|-------------|
| `--show NAME` | TV show name (mutually exclusive with `--movie`) |
| `--movie NAME` | Movie name — skips season/episode logic (mutually exclusive with `--show`) |
| `--season` | Season number, zero-padded (default: 01; TV shows only) |
| `--start-ep` | First episode number in this batch (default: 1; TV shows only) |
| `--audio-tracks` | Comma-separated audio track numbers to include, e.g. `1,3` (default: all) |
| `--sub-tracks` | Comma-separated subtitle track numbers to include, e.g. `2` (default: all) |
| `--quality` | x265 CRF quality, overrides config |
| `--preset` | HandBrake encoder preset, overrides config |
| `--force-crop` | Force crop to 0:0:0:0 instead of HandBrake auto-detect (off by default) |
| `--decomb` | Enable `--decomb` for interlaced source material (off by default) |
| `--animation` | Add `--encoder-tune animation` |
| `--no-align` | Disable `--align-av` (enabled by default) |
| `--output-dir` | Where HandBrake writes encoded files, overrides config |
| `--script-out` | Full path for generated .sh script |
| `--handbrake-cmd` | HandBrake CLI invocation, overrides config |

Track numbers correspond to the 1-based index within each track type (audio or subtitle),
as shown in the stream list printed at the start of every run. If omitted, all tracks of
that type are included.

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
