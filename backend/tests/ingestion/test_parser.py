from pathlib import Path

from app.ingestion.parser import parse_transcript


# poetry run pytest tests/ingestion/test_parser.py -v
def test_parse_basic():
    """Test parsing a simple transcript with two lines."""
    data_file = Path(__file__).parent / "test_parser.txt"
    lines = parse_transcript(str(data_file))

    assert len(lines) == 3
    assert lines[0].text == "This one is valid."
    assert lines[1].speaker_label == "SPEAKER_01"
    assert lines[1].text == "Hello, welcome to the show."
    assert lines[2].speaker_label == "SPEAKER_02"

def test_parse_timestamps():
    """Verify timestamps are parsed correctly."""
    data_file = Path(__file__).parent / "test_parser.txt"
    lines = parse_transcript(str(data_file))

    assert lines[1].start_timestamp == "0:00:16"
    assert lines[1].end_timestamp == "0:00:30"

# Scenario 1
# data_file = Path(__file__).parent / "test_parser.txt"
# lines = parse_transcript(str(data_file))
# print(lines)
# Scenario 2
# chunks = build_chunks(lines, chunk_size=2, chunk_overlap=1)
# for i, chunk in enumerate(chunks):
#     print(
#         f"Chunk {i}: start={chunk.start_timestamp}, "
#         f"end={chunk.end_timestamp}, "
#         f"speaker={chunk.speaker_label}"
#     )

# Scenario 4
# Run the parser and confirm the malformed lines are skipped (not in the output)
#  and that a warning/log message is printed for each one.
#  The valid line should still be parsed correctly.

# Output:
# Skipping malformed line 1: This line has no timestamp or speaker at all.
# Skipping malformed line 2: [broken - format] no colon here
# [TranscriptLine(
#     speaker_label='SPEAKER_01',
#     start_timestamp='0:00:00', end_timestamp='0:00:15',
#     text='This one is valid.'),
#  TranscriptLine(
#     speaker_label='SPEAKER_01',
#     start_timestamp='0:00:16', end_timestamp='0:00:30',
#     text='Hello, welcome to the show.'),
#  TranscriptLine(
#     speaker_label='SPEAKER_02',
#     start_timestamp='0:00:31', end_timestamp='0:00:45',
#     text='Thanks for having me.')]
# Chunk 0: start=0:00:00, end=0:00:30, speaker=SPEAKER_01
# Chunk 1: start=0:00:16, end=0:00:45, speaker=SPEAKER_01

# ----------------------------------------------------------

# Scenario 3
# poetry run python -m app.ingestion.ingest_transcript <episode_id> <transcript_file>

# Then query Supabase directly (in the dashboard or via
# the client) to confirm rows exist in
# `transcript_chunks` with non-null `embedding`, correct
# `start_timestamp`, `end_timestamp`, `speaker`, and
# sequential `chunk_index` values.

# cd C:\r\me\realaf-podcast\The-Book-of-Andy-frontend\backend\

# cd backend
# $env:PYTHONPATH = "."      # Powershell
# poetry run python tests\ingestion\parser.test.py
# [TranscriptLine(
#     speaker_label='SPEAKER_01',
#     start_timestamp='0:00:16', end_timestamp='0:00:30',
#     text='Hello, welcome to the show.'),
#  TranscriptLine(
#     speaker_label='SPEAKER_02',
#     start_timestamp='0:00:31', end_timestamp='0:00:45',
#     text='Thanks for having me.')]
