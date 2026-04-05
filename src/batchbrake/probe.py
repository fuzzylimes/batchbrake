from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class Stream:
    index: int
    codec_type: str
    codec_name: str
    language: str
    title: str
    channels: int | None   # audio only


@dataclass
class Chapter:
    index: int        # 1-based
    start: float      # seconds
    end: float        # seconds
    title: str

    @property
    def duration(self) -> float:
        return self.end - self.start

    def duration_str(self) -> str:
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# ── Internal ──────────────────────────────────────────────────────────────────

def _run_ffprobe(extra_args: list[str]) -> dict:
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json"] + extra_args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except FileNotFoundError:
        sys.exit("Error: ffprobe not found. Install ffmpeg: sudo apt install ffmpeg")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error: ffprobe failed:\n{e.stderr}")


def _parse_streams(data: dict) -> list[Stream]:
    streams = []
    for s in data.get("streams", []):
        streams.append(Stream(
            index      = s.get("index", 0),
            codec_type = s.get("codec_type", ""),
            codec_name = s.get("codec_name", "?"),
            language   = s.get("tags", {}).get("language", "?"),
            title      = s.get("tags", {}).get("title", ""),
            channels   = s.get("channels"),
        ))
    return streams


def _parse_chapters(data: dict) -> list[Chapter]:
    chapters = []
    for i, ch in enumerate(data.get("chapters", []), start=1):
        chapters.append(Chapter(
            index = i,
            start = float(ch["start_time"]),
            end   = float(ch["end_time"]),
            title = ch.get("tags", {}).get("title", f"Chapter {i:02d}"),
        ))
    return chapters


# ── Public API ────────────────────────────────────────────────────────────────

def probe_all(path: str) -> tuple[list[Chapter], list[Stream]]:
    """Single ffprobe call — returns (chapters, streams)."""
    data = _run_ffprobe(["-show_chapters", "-show_streams", path])
    return _parse_chapters(data), _parse_streams(data)


def probe_streams(path: str) -> list[Stream]:
    """Probe streams only (used by bulk mode)."""
    data = _run_ffprobe(["-show_streams", path])
    return _parse_streams(data)


# ── Filter helpers ────────────────────────────────────────────────────────────

def audio_streams(streams: list[Stream]) -> list[Stream]:
    return [s for s in streams if s.codec_type == "audio"]


def sub_streams(streams: list[Stream]) -> list[Stream]:
    return [s for s in streams if s.codec_type == "subtitle"]
