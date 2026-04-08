from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

from .config import Config
from .probe import probe_all, Chapter, audio_streams, sub_streams
from .display import (
    bold, cyan, yellow, red, dim,
    print_streams, print_chapter_table,
    print_disc_episode_mapping, menu_choice,
)
from .generate import generate_disc_script


# ── Episode dataclass ─────────────────────────────────────────────────────────

@dataclass
class Episode:
    number: int
    chapter_start: int   # 1-based, inclusive
    chapter_end: int     # 1-based, inclusive
    chapters: list[Chapter]

    @property
    def duration(self) -> float:
        return sum(ch.duration for ch in self.chapters)

    def duration_str(self) -> str:
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ── Episode detection ─────────────────────────────────────────────────────────

def _autodetect(chapters: list[Chapter], target_minutes: float) -> list[list[Chapter]]:
    """
    Greedily group chapters into episodes by accumulating duration until
    we reach target_minutes (±35%). Orphan chapters at the end are folded
    into the last episode.
    """
    target_sec = target_minutes * 60
    lo, hi = target_sec * 0.65, target_sec * 1.35
    groups: list[list[Chapter]] = []
    group: list[Chapter] = []
    acc = 0.0

    for ch in chapters:
        group.append(ch)
        acc += ch.duration
        if acc >= lo:
            next_idx = chapters.index(ch) + 1
            next_dur = chapters[next_idx].duration if next_idx < len(chapters) else 0.0
            if acc >= target_sec or (acc + next_dur) > hi:
                groups.append(group)
                group, acc = [], 0.0

    if group:
        if groups:
            groups[-1].extend(group)   # fold orphans into last episode
        else:
            groups.append(group)

    return groups


def _groups_to_episodes(groups: list[list[Chapter]], start_ep: int) -> list[Episode]:
    episodes, cursor = [], 1
    for i, group in enumerate(groups):
        episodes.append(Episode(
            number        = start_ep + i,
            chapter_start = cursor,
            chapter_end   = cursor + len(group) - 1,
            chapters      = group,
        ))
        cursor += len(group)
    return episodes


def _fixed_split(chapters: list[Chapter], n: int, start_ep: int) -> list[Episode]:
    groups = [chapters[i:i + n] for i in range(0, len(chapters), n)]
    return _groups_to_episodes(groups, start_ep)


def _manual_entry(chapters: list[Chapter], start_ep: int) -> list[Episode]:
    print(f"\n  Total chapters: {len(chapters)}")
    print("  Enter chapter ranges as  START-END  (e.g. 1-5). Blank line when done.\n")
    episodes: list[Episode] = []
    ep_num = start_ep
    while True:
        raw = input(f"  E{ep_num:02d} chapter range (or blank to finish): ").strip()
        if not raw:
            break
        m = re.match(r"^(\d+)-(\d+)$", raw)
        if not m:
            print(red("  Use format START-END (e.g. 1-5)"))
            continue
        s, e = int(m.group(1)), int(m.group(2))
        if s < 1 or e > len(chapters) or s > e:
            print(red(f"  Out of range — chapters are 1–{len(chapters)}."))
            continue
        episodes.append(Episode(ep_num, s, e, chapters[s - 1:e]))
        ep_num += 1
    return episodes


# ── Confirmation loop ─────────────────────────────────────────────────────────

def _confirm_loop(
    episodes: list[Episode],
    chapters: list[Chapter],
    start_ep: int,
) -> list[Episode]:
    while True:
        print_disc_episode_mapping(episodes)
        choice = menu_choice([
            ("a", "Accept and generate script"),
            ("r", "Re-split with a different target duration"),
            ("f", "Re-split with fixed chapters-per-episode"),
            ("m", "Manually enter chapter ranges"),
            ("q", "Quit"),
        ])

        if choice == "a":
            return episodes

        elif choice == "r":
            try:
                mins = float(input("  Target episode duration (minutes): ").strip())
                episodes = _groups_to_episodes(_autodetect(chapters, mins), start_ep)
            except ValueError:
                print(red("  Invalid number."))

        elif choice == "f":
            try:
                n = int(input("  Chapters per episode: ").strip())
                if n < 1:
                    raise ValueError
                episodes = _fixed_split(chapters, n, start_ep)
            except ValueError:
                print(red("  Invalid number."))

        elif choice == "m":
            result = _manual_entry(chapters, start_ep)
            if result:
                episodes = result

        elif choice == "q":
            print("Aborted.")
            sys.exit(0)


# ── Subcommand entry point ────────────────────────────────────────────────────

def run(args, cfg: Config) -> None:
    # Resolve: CLI arg > config > hardcoded fallback
    season     = args.season    or "01"
    start_ep   = args.start_ep  or 1
    quality    = args.quality   if args.quality  is not None else cfg.quality
    preset     = args.preset    or cfg.preset
    force_crop = cfg.force_crop and not args.allow_crop
    ep_dur     = args.ep_duration if args.ep_duration is not None else cfg.ep_duration
    hb_cmd     = args.handbrake_cmd or cfg.command

    print(bold(f"\n── Disc Mode ── {args.input}"))
    print(f"  Show: {cyan(args.show)}  Season: {cyan(season)}  Start ep: {cyan(str(start_ep))}\n")

    if not os.path.exists(args.input):
        sys.exit(red(f"Error: file not found: {args.input}"))

    print("Probing file…")
    chapters, streams = probe_all(args.input)
    print_streams(streams)
    print_chapter_table(chapters)

    total = sum(ch.duration for ch in chapters)
    tm, ts = divmod(int(total), 60)
    th, tm = divmod(tm, 60)
    print(f"\n  Total chapters : {bold(str(len(chapters)))}")
    print(f"  Total duration : {bold(f'{th}:{tm:02d}:{ts:02d}')}")

    # Initial split
    if args.chapters_per_ep:
        print(f"\n{yellow('Fixed split:')} {args.chapters_per_ep} chapters per episode")
        episodes = _fixed_split(chapters, args.chapters_per_ep, start_ep)
    else:
        print(f"\n{yellow('Auto-detecting')} episode boundaries (target: {ep_dur} min)…")
        episodes = _groups_to_episodes(_autodetect(chapters, ep_dur), start_ep)

    episodes = _confirm_loop(episodes, chapters, start_ep)

    # Resolve output_dir: CLI > config > source file directory
    output_dir = args.output_dir or cfg.output_dir or os.path.dirname(os.path.abspath(args.input))

    audio_tracks = [int(x) for x in args.audio_tracks.split(",")] if args.audio_tracks else None
    sub_tracks   = [] if args.sub_tracks == "0" else ([int(x) for x in args.sub_tracks.split(",")] if args.sub_tracks else None)

    script = generate_disc_script(
        episodes, streams, args.input, args.show, season,
        quality, preset, force_crop, output_dir, hb_cmd,
        audio_tracks, sub_tracks,
    )

    _write_script(script, args.script_out, cfg.script_dir, args.show, season, start_ep)


def _write_script(script: str, script_out: str | None, cfg_script_dir: str,
                  show: str, season: str, start_ep: int) -> None:
    from .display import green, bold, dim
    import stat

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
