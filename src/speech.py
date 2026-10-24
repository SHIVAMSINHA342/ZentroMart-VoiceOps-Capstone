"""Gnani-only speech pipeline for ZentroMart VoiceOps."""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from .answer_engine import answer_customer_question


def _load_gnani_clients():
    """Initialize the official Gnani Vachana SDK clients."""
    if not os.getenv("GNANI_API_KEY"):
        raise RuntimeError(
            "GNANI_API_KEY is missing. Add your authorized key to the "
            "environment or .env file before using speech features."
        )

    try:
        from gnani.stt import GnaniSTTClient
        from gnani.tts import GnaniTTSClient
    except ImportError as exc:
        raise RuntimeError(
            "Gnani SDK is unavailable. Install the gnani-vachana package."
        ) from exc

    return GnaniSTTClient(), GnaniTTSClient()


def process_audio(audio_path, output_dir="sample_outputs", language_code="en-IN"):
    """Transcribe audio, answer the question, synthesize speech and save outputs."""
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    stt, tts = _load_gnani_clients()

    transcription = stt.transcribe(
        str(audio_path),
        language_code=language_code
    )
    transcript = str(transcription.get("transcript", "")).strip()

    if not transcript:
        raise RuntimeError("Gnani STT returned an empty transcript.")

    result = answer_customer_question(transcript)
    reply = result["answer"]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = audio_path.stem + "_" + timestamp

    transcript_path = output_dir / f"{stem}_transcript.txt"
    reply_path = output_dir / f"{stem}_reply.txt"
    result_path = output_dir / f"{stem}_result.json"
    speech_output_path = output_dir / f"{stem}_reply.wav"

    tts.synthesize(
        reply,
        voice="Kaveri",
        model="timbre-v2.5",
        language=language_code,
        output_file=str(speech_output_path)
    )

    transcript_path.write_text(transcript + "\n", encoding="utf-8")
    reply_path.write_text(reply + "\n", encoding="utf-8")

    payload = {
        "input_audio": str(audio_path),
        "transcript": transcript,
        "answer": reply,
        "status": result["status"],
        "evidence_ids": result.get("evidence_ids", []),
        "output_audio": str(speech_output_path),
        "speech_provider": "Gnani",
        "language_code": language_code
    }
    result_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return payload
