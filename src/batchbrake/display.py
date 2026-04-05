from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config
    from .probe import Stream, Chapter

# ── ANSI colour helpers ───────────────────────────────────────────────────────

_USE_COLOR = sys.stdout.isatty()


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def bold(t: str)   -> str: return _c(t, "1")
def green(t: str)  -> str: return _c(t, "32")
def yellow(t: str) -> str: return _c(t, "33")
def cyan(t: str)   -> str: return _c(t, "36")
def red(t: str)    -> str: return _c(t, "31")
def dim(t: str)    -> str: return _c(t, "2")


# ── Header / config summary ───────────────────────────────────────────────────

def print_header() -> None:
    print(bold("\n╔══════════════════════════════════════╗"))
    print(bold("║        batchbrake  v0.1.0            ║"))
    print(bold("╚══════════════════════════════════════╝"))


def print_config_summary(cfg: Config) -> None:
    from .config import CONFIG_PATH
    crop_str  = "forced 0:0:0:0" if cfg.force_crop else "auto-detect"
    out_str   = cfg.output_dir if cfg.output_dir else "(source dir)"
    print(bold(f"\n── Config ({CONFIG_PATH}) ─────────────────"))
    print(f"  HandBrake : {dim(cfg.command)}")
    print(f"  Quality   : {cyan(str(cfg.quality))}   Preset : {cyan(cfg.preset)}   Crop : {cyan(crop_str)}")
    print(f"  Script dir: {cyan(cfg.script_dir)}   Output dir: {cyan(out_str)}")
    print(f"  Ep dur    : {cyan(str(cfg.ep_duration))} min  (disc auto-detect target)")


# ── Stream tables ─────────────────────────────────────────────────────────────

def print_streams(streams: list[Stream]) -> None:
    from .probe import audio_streams, sub_streams
    audio = audio_streams(streams)
    subs  = sub_streams(streams)

    print(bold("\n── Audio Tracks ──────────────────────────────────────"))
    if audio:
        for i, s in enumerate(audio, start=1):
            ch  = f"{s.channels}ch" if s.channels else ""
            ttl = f"  {dim(s.title)}" if s.title else ""
            print(green(f"  [{i}] {s.codec_name.upper()} {ch}  lang={s.language}{ttl}"))
    else:
        print(dim("  (none)"))

    print(bold("\n── Subtitle Tracks ───────────────────────────────────"))
    if subs:
        for i, s in enumerate(subs, start=1):
            ttl = f"  {dim(s.title)}" if s.title else ""
            print(yellow(f"  [{i}] {s.codec_name}  lang={s.language}{ttl}"))
    else:
        print(dim("  (none)"))


# ── Chapter table ─────────────────────────────────────────────────────────────

def print_chapter_table(chapters: list[Chapter]) -> None:
    print(bold("\n── Chapters ─────────────────────────────────────────"))
    print(f"  {'#':>3}  {'Duration':>8}  {'Cumulative':>10}  Title")
    print(f"  {'─'*3}  {'─'*8}  {'─'*10}  {'─'*20}")
    cumulative = 0.0
    for ch in chapters:
        cumulative += ch.duration
        cm, cs = divmod(int(cumulative), 60)
        ch_h, ch_m = divmod(cm, 60)
        cum_str = f"{ch_h}:{ch_m:02d}:{cs:02d}" if ch_h else f"{cm}:{cs:02d}"
        print(f"  {ch.index:>3}  {ch.duration_str():>8}  {cum_str:>10}  {dim(ch.title)}")


# ── Episode mapping tables ────────────────────────────────────────────────────

def print_disc_episode_mapping(episodes: list) -> None:
    print(bold("\n── Proposed Episode Mapping ─────────────────────────"))
    print(f"  {'Ep':>4}  {'Chapters':>12}  {'Duration':>9}  {'# Chs':>6}")
    print(f"  {'─'*4}  {'─'*12}  {'─'*9}  {'─'*6}")
    for ep in episodes:
        print(f"  E{ep.number:02d}   {ep.chapter_start:>3} → {ep.chapter_end:<3}   {ep.duration_str():>9}  {len(ep.chapters):>6}")


def print_bulk_episode_mapping(episodes: list) -> None:
    print(bold("\n── File → Episode Mapping ────────────────────────────"))
    print(f"  {'Ep':>4}   Filename")
    print(f"  {'─'*4}   {'─'*52}")
    for ep in episodes:
        print(f"  E{ep.episode_number:02d}   {dim(ep.filename)}")


# ── Interactive menu ──────────────────────────────────────────────────────────

def menu_choice(options: list[tuple[str, str]]) -> str:
    """Display a labelled menu and return the chosen key."""
    print()
    for key, label in options:
        colour = green if key == "a" else (red if key == "q" else yellow)
        print(f"  {colour(key)} {label}")
    print()
    valid = {k for k, _ in options}
    while True:
        choice = input(f"  Choice [{'/'.join(k for k, _ in options)}]: ").strip().lower()
        if choice in valid:
            return choice
        print(red(f"  Please enter one of: {', '.join(sorted(valid))}"))
