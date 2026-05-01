from __future__ import annotations

import argparse

from .config import load_config
from .display import print_header, print_config_summary
from . import disc as disc_cmd
from . import bulk as bulk_cmd


# ── Shared args ───────────────────────────────────────────────────────────────

def _add_common_args(p: argparse.ArgumentParser) -> None:
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--show",  metavar="NAME",
                     help='TV show name, e.g. "Initial D"')
    src.add_argument("--movie", metavar="NAME",
                     help='Movie name, e.g. "Interstellar" (skips season/episode logic)')

    p.add_argument("--season",  default=None,  metavar="NN",
                   help="Season number, zero-padded (default: 01; ignored for --movie)")
    p.add_argument("--start-ep", type=int, default=None, metavar="N",
                   help="First episode number in this batch (default: 1; ignored for --movie)")

    enc = p.add_argument_group("encoding overrides (all default to config values)")
    enc.add_argument("--quality",    type=int, default=None, metavar="N",
                     help="x265 CRF quality")
    enc.add_argument("--preset",     default=None, metavar="PRESET",
                     help="HandBrake encoder preset")
    enc.add_argument("--force-crop", action="store_true", default=False,
                     help="Force crop to 0:0:0:0 instead of HandBrake auto-detect")
    enc.add_argument("--decomb",     action="store_true", default=False,
                     help="Enable --decomb (for interlaced source material; off by default)")
    enc.add_argument("--animation",  action="store_true", default=False,
                     help="Add --encoder-tune animation")
    enc.add_argument("--no-align",   action="store_true", default=False,
                     help="Disable --align-av (included by default)")

    trk = p.add_argument_group("track selection (default: include all tracks)")
    trk.add_argument("--audio-tracks", default=None, metavar="N[,N]",
                     help="Comma-separated audio track numbers to include (e.g. 1,3)")
    trk.add_argument("--sub-tracks",   default=None, metavar="N[,N]",
                     help="Comma-separated subtitle track numbers to include (e.g. 2)")

    out = p.add_argument_group("output overrides (all default to config values)")
    out.add_argument("--output-dir",    default=None, metavar="DIR",
                     help="Directory where HandBrake writes encoded files")
    out.add_argument("--script-out",    default=None, metavar="PATH",
                     help="Full path for generated .sh script")
    out.add_argument("--handbrake-cmd", default=None, metavar="CMD",
                     help="HandBrake CLI invocation")


# ── Parser ────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchbrake",
        description="Generate HandBrake batch encode scripts for disc rips.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  batchbrake disc -i InitialD_1-7.mkv --show 'Initial D' --season 01 --start-ep 1\n"
            "  batchbrake bulk -d /mnt/media/staging/anime --prefix 'Disc 3' \\\n"
            "                  --show 'Neon Genesis Evangelion' --season 01 --start-ep 11\n"
            "  batchbrake disc -i Interstellar.mkv --movie 'Interstellar'\n"
            "  batchbrake disc -i OldAnime.mkv --show 'Old Anime' --season 01 --decomb --animation\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="{disc,bulk}")

    # ── disc ──────────────────────────────────────────────────────────────────
    disc_p = sub.add_parser(
        "disc",
        help="Split a single multi-episode disc file by chapters",
        description="Probe a disc rip, auto-detect episode boundaries, and generate an encode script.",
    )
    disc_p.add_argument("-i", "--input", required=True, metavar="FILE",
                        help="Input MKV file")
    disc_p.add_argument("--ep-duration", type=float, default=None, metavar="MINS",
                        help="Target episode duration in minutes for auto-detect (overrides config)")
    disc_p.add_argument("--chapters-per-ep", type=int, default=None, metavar="N",
                        help="Force a fixed chapter count per episode (skips auto-detect)")
    _add_common_args(disc_p)

    # ── bulk ──────────────────────────────────────────────────────────────────
    bulk_p = sub.add_parser(
        "bulk",
        help="Encode individually-ripped episode files",
        description="Match episode files by prefix, confirm the mapping, and generate an encode script.",
    )
    bulk_p.add_argument("-d", "--dir", required=True, metavar="DIR",
                        help="Directory containing source MKV files")
    bulk_p.add_argument("--prefix", default=None, metavar="PREFIX",
                        help='Filename prefix to filter files, e.g. "Disc 3"')
    _add_common_args(bulk_p)

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    cfg    = load_config()

    print_header()
    print_config_summary(cfg)

    if args.command == "disc":
        disc_cmd.run(args, cfg)
    elif args.command == "bulk":
        bulk_cmd.run(args, cfg)


if __name__ == "__main__":
    main()
