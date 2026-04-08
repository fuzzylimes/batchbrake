from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

from .config import Config
from .probe import probe_streams, Stream, sub_streams
from .display import (
    bold, cyan, yellow, red, dim,
    print_streams, print_bulk_episode_mapping, menu_choice,
)
from .generate import generate_bulk_script


# ── Episode file dataclass ────────────────────────────────────────────────────

@dataclass
class EpisodeFile:
    path: str
    filename: str
    episode_number: int


# ── File discovery ────────────────────────────────────────────────────────────

def _discover(directory: str, prefix: str | None) -> list[str]:
    if not os.path.isdir(directory):
        sys.exit(red(f"Error: directory not found: {directory}"))
    files = []
    for fname in sorted(os.listdir(directory)):
        if not fname.lower().endswith(".mkv"):
            continue
        if prefix and not fname.startswith(prefix):
            continue
        files.append(os.path.join(directory, fname))
    return files


def _build_list(files: list[str], start_ep: int) -> list[EpisodeFile]:
    return [
        EpisodeFile(path=f, filename=os.path.basename(f), episode_number=start_ep + i)
        for i, f in enumerate(files)
    ]


# ── Subtitle default prompt ───────────────────────────────────────────────────

def _prompt_subtitle_default(streams: list[Stream]) -> int | None:
    subs = sub_streams(streams)
    if not subs:
        print(dim("\n  No subtitle tracks found — skipping subtitle-default."))
        return None

    print(bold("\n── Subtitle Default ──────────────────────────────────"))
    print("  Which subtitle track should be the default?")
    for i, s in enumerate(subs, start=1):
        ttl = f"  {dim(s.title)}" if s.title else ""
        print(yellow(f"  [{i}] {s.codec_name}  lang={s.language}{ttl}"))
    print(dim("  [0] None — don't set a default"))
    print()

    while True:
        raw = input(f"  Choice [0–{len(subs)}]: ").strip()
        if raw == "0":
            return None
        try:
            n = int(raw)
            if 1 <= n <= len(subs):
                return n
        except ValueError:
            pass
        print(red(f"  Enter a number between 0 and {len(subs)}."))


# ── Confirmation loop ─────────────────────────────────────────────────────────

def _reorder(episodes: list[EpisodeFile]) -> list[EpisodeFile]:
    print(bold("\n  Current files:"))
    for i, ep in enumerate(episodes, start=1):
        print(f"    {i}) {dim(ep.filename)}")
    raw = input("\n  New order (space-separated numbers, e.g. 3 1 2): ").strip()
    try:
        indices = [int(x) - 1 for x in raw.split()]
        if sorted(indices) != list(range(len(episodes))):
            print(red("  Must include each file exactly once."))
            return episodes
        return _build_list(
            [episodes[i].path for i in indices],
            episodes[0].episode_number,
        )
    except (ValueError, IndexError):
        print(red("  Invalid input — keeping original order."))
        return episodes


def _confirm_loop(episodes: list[EpisodeFile]) -> list[EpisodeFile]:
    while True:
        print_bulk_episode_mapping(episodes)
        choice = menu_choice([
            ("a", "Accept and generate script"),
            ("s", "Change starting episode number"),
            ("r", "Remove a file from the list"),
            ("o", "Re-order files"),
            ("q", "Quit"),
        ])

        if choice == "a":
            return episodes

        elif choice == "s":
            try:
                new_start = int(input("  New starting episode number: ").strip())
                episodes = _build_list([e.path for e in episodes], new_start)
            except ValueError:
                print(red("  Invalid number."))

        elif choice == "r":
            try:
                ep_num = int(input("  Episode number to remove: ").strip())
                trimmed = [e for e in episodes if e.episode_number != ep_num]
                if len(trimmed) == len(episodes):
                    print(red(f"  No episode {ep_num} in list."))
                else:
                    episodes = _build_list(
                        [e.path for e in trimmed],
                        trimmed[0].episode_number,
                    )
            except ValueError:
                print(red("  Invalid number."))

        elif choice == "o":
            episodes = _reorder(episodes)

        elif choice == "q":
            print("Aborted.")
            sys.exit(0)


# ── Subcommand entry point ────────────────────────────────────────────────────

def run(args, cfg: Config) -> None:
    season     = args.season   or "01"
    start_ep   = args.start_ep or 1
    quality    = args.quality  if args.quality is not None else cfg.quality
    preset     = args.preset   or cfg.preset
    force_crop = cfg.force_crop and not args.allow_crop
    hb_cmd     = args.handbrake_cmd or cfg.command

    prefix_note = f"  prefix: {cyan(args.prefix)}" if args.prefix else ""
    print(bold(f"\n── Bulk Mode ── {args.dir}"))
    print(f"  Show: {cyan(args.show)}  Season: {cyan(season)}  Start ep: {cyan(str(start_ep))}{prefix_note}\n")

    files = _discover(args.dir, args.prefix)
    if not files:
        hint = f' matching prefix "{args.prefix}"' if args.prefix else ""
        sys.exit(red(f"Error: no .mkv files found in {args.dir}{hint}"))

    print(f"Found {bold(str(len(files)))} file(s).")
    print(f"Probing streams from: {dim(os.path.basename(files[0]))}…")
    streams = probe_streams(files[0])
    print_streams(streams)

    subtitle_default = _prompt_subtitle_default(streams)

    episodes = _build_list(files, start_ep)
    episodes = _confirm_loop(episodes)

    # Resolve output_dir: CLI > config > input directory
    output_dir = args.output_dir or cfg.output_dir or args.dir

    audio_tracks = [int(x) for x in args.audio_tracks.split(",")] if args.audio_tracks else None
    sub_tracks   = [int(x) for x in args.sub_tracks.split(",")]   if args.sub_tracks   else None

    script = generate_bulk_script(
        episodes, streams, subtitle_default, args.show, season,
        quality, preset, force_crop, output_dir, hb_cmd,
        audio_tracks, sub_tracks,
    )

    _write_script(script, args.script_out, cfg.script_dir, args.show, season, start_ep)


def _write_script(script: str, script_out: str | None, cfg_script_dir: str,
                  show: str, season: str, start_ep: int) -> None:
    from .display import green, bold, dim

    if script_out:
        path = script_out
    else:
        safe = re.sub(r"[^\w\-]", "_", show)
        path = os.path.join(cfg_script_dir, f"encode_{safe}_S{season}_E{start_ep:02d}.sh")

    with open(path, "w") as f:
        f.write(script)
    os.chmod(path, 0o755)

    print(green(f"\n✓ Script written to: {bold(path)}"))
    print(dim("  Review it, then run it when ready.\n"))
