"""Transcript file parser.

Reads a plain-text transcript file where each line has the format:

    [H:MM:SS - H:MM:SS] SPEAKER_LABEL: transcript text here

The parser extracts the speaker label, start timestamp, end timestamp,
and spoken text from each line.  Malformed lines are logged and skipped.
"""

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Pattern explanation:
#   \[                     – opening bracket
#   (\d+:\d{2}:\d{2})     – start timestamp  (e.g. 0:00:16)
#   \s*-\s*               – dash separator
#   (\d+:\d{2}:\d{2})     – end timestamp    (e.g. 0:00:30)
#   \]                     – closing bracket
#   \s+                    – whitespace
#   ([A-Za-z0-9_]+)       – speaker label    (e.g. SPEAKER_01)
#   :\s*                   – colon + optional whitespace
#   (.+)                   – transcript text
LINE_PATTERN = re.compile(
    r"\[(\d+:\d{2}:\d{2})\s*-\s*(\d+:\d{2}:\d{2})\]\s+([A-Za-z0-9_]+):\s*(.+)"
)


@dataclass
class TranscriptLine:
    """A single parsed line from a transcript file."""

    speaker_label: str
    start_timestamp: str
    end_timestamp: str
    text: str


def parse_line(raw_line: str) -> TranscriptLine | None:
    """Parse a single transcript line.

    Returns a ``TranscriptLine`` on success or ``None`` if the line does
    not match the expected format (the caller should log/skip).
    """
    match = LINE_PATTERN.match(raw_line.strip())
    if match is None:
        return None
    start_ts, end_ts, speaker, text = match.groups()
    return TranscriptLine(
        speaker_label=speaker,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        text=text.strip(),
    )


def parse_transcript(file_path: str) -> list[TranscriptLine]:
    """Read a transcript file and return all successfully parsed lines.

    Blank lines and lines that do not match the expected format are
    skipped with a warning log message.
    """
    lines: list[TranscriptLine] = []
    with open(file_path, encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue  # skip blank lines silently
            parsed = parse_line(raw_line)
            if parsed is None:
                logger.warning(
                    "Skipping malformed line %d: %s",
                    line_number,
                    raw_line[:120],
                )
                continue
            lines.append(parsed)
    logger.info("Parsed %d lines from %s", len(lines), file_path)
    return lines
