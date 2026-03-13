# Pipeline

## Overview

This directory contains the diarization and ingestion pipeline for processing podcast audio. The pipeline is designed around a two-tier architecture:

1. **Lightweight Railway Scheduler** — A small, always-on service that monitors RSS feeds for new episodes and dispatches processing jobs.
2. **On-Demand Lambda GPU Instance** — A GPU-equipped instance that spins up only when needed to run the compute-intensive transcription and diarization workloads.

## Diarization Pipeline

The diarization scripts are run in the following order:

1. **`diarization/transcribe.py`** — Runs WhisperX transcription on a downloaded audio file to produce a raw transcript with word-level timestamps.
2. **`diarization/diarize.py`** — Runs pyannote speaker diarization on the audio file and aligns speaker labels with the WhisperX transcript, producing segments with speaker attribution.
3. **`diarization/format_output.py`** — Converts diarized segments into the chunk format expected by the ingestion pipeline.
4. **`diarization/ingest.py`** — Takes the formatted chunks and writes them directly to Supabase using the service role key, bypassing the Railway backend API.

## Directory Structure

```
pipeline/
  diarization/
    __init__.py
    transcribe.py
    diarize.py
    format_output.py
    ingest.py
  scheduler/
    __init__.py
  README.md
```
