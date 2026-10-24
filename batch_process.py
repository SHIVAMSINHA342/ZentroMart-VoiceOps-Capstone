"""Batch-process customer audio using the Gnani-only speech pipeline."""
import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.speech import process_audio

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

def main():
    parser = argparse.ArgumentParser(
        description="Batch-process customer audio with Gnani STT and TTS."
    )
    parser.add_argument("--input-dir", required=True,
                        help="Folder containing customer audio recordings.")
    parser.add_argument("--output-dir", default="sample_outputs/batch",
                        help="Folder for generated transcripts, answers and audio.")
    parser.add_argument("--language", default="en-IN",
                        help="Gnani language code (default: en-IN).")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")

    audio_files = sorted(
        path for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )
    if not audio_files:
        parser.error(f"No supported audio files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "batch_manifest.json"
    records = []

    for index, audio_path in enumerate(audio_files, start=1):
        print(f"[{index}/{len(audio_files)}] Processing {audio_path.name}")
        try:
            result = process_audio(
                audio_path,
                output_dir=output_dir,
                language_code=args.language
            )
            records.append({
                "input_audio": str(audio_path),
                "success": True,
                "transcript": result.get("transcript"),
                "answer": result.get("answer"),
                "status": result.get("status"),
                "evidence_ids": result.get("evidence_ids", []),
                "output_audio": result.get("output_audio"),
                "result_json": result.get("result_json"),
            })
            print("  Success")
        except Exception as exc:
            records.append({
                "input_audio": str(audio_path),
                "success": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            })
            print(f"  Failed: {type(exc).__name__}: {exc}")

        # Save progress after each file so partial results are not lost.
        manifest_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    succeeded = sum(record["success"] for record in records)
    print(f"\nBatch finished: {succeeded}/{len(records)} succeeded.")
    print(f"Manifest: {manifest_path}")
    return 0 if succeeded == len(records) else 1

if __name__ == "__main__":
    raise SystemExit(main())
