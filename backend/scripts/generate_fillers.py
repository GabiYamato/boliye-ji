#!/usr/bin/env python3
"""Generate filler audio clips for the "thinking" phase.

Uses the live Qwen3-TTS server (must be running on localhost:8880).
Saves WAV files to backend/assets/fillers/.

Usage:
    python scripts/generate_fillers.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

# ── Configuration ────────────────────────────────────────────────────
TTS_BASE = os.getenv("TTS_QWEN_BASE_URL", "http://localhost:8880")
TTS_URL = f"{TTS_BASE.rstrip('/')}/v1/audio/speech"
VOICE = os.getenv("TTS_QWEN_VOICE", "Vivian")
MODEL = os.getenv("TTS_QWEN_MODEL", "qwen3-tts")

FILLERS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fillers"

# The filler messages — short, friendly, conversational
FILLERS = [
    ("hold_on", "Please hold on a moment, while I browse my database."),
    ("almost_there", "Almost there!"),
    ("just_a_little_more", "Just a little more."),
    ("one_moment", "One moment please, let me find that for you."),
    ("searching", "Searching through the schemes for you."),
]


def generate_one(name: str, text: str) -> Path:
    """Call TTS and save the result as a WAV file."""
    out_path = FILLERS_DIR / f"{name}.wav"
    print(f"  Generating: {name}.wav — \"{text}\"")

    payload = {
        "model": MODEL,
        "input": text,
        "voice": VOICE,
        "response_format": "wav",
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer not-needed",
    }

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(TTS_URL, json=payload, headers=headers)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)

    size_kb = out_path.stat().st_size / 1024
    print(f"    ✓ Saved {out_path.name} ({size_kb:.1f} KB)")
    return out_path


def main() -> None:
    FILLERS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n🔊 Generating filler audio clips")
    print(f"   TTS server: {TTS_URL}")
    print(f"   Voice:      {VOICE}")
    print(f"   Output:     {FILLERS_DIR}\n")

    # Quick connectivity check
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{TTS_BASE.rstrip('/')}/v1/models")
            if r.status_code >= 500:
                raise RuntimeError(f"TTS server returned {r.status_code}")
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        print(f"❌ TTS server not reachable at {TTS_BASE}")
        print(f"   Make sure the Qwen3-TTS server is running.")
        sys.exit(1)

    generated = []
    for name, text in FILLERS:
        try:
            path = generate_one(name, text)
            generated.append(path)
        except Exception as exc:
            print(f"    ✗ Failed: {exc}")

    print(f"\n✅ Generated {len(generated)}/{len(FILLERS)} filler clips")
    print(f"   Location: {FILLERS_DIR}")


if __name__ == "__main__":
    main()
