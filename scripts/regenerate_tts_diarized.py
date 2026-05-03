import json, time, requests
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DIARIZATION_FILE = REPO_ROOT / "pipeline_data/api/diarization.json"
TRANSLATIONS_DIR = REPO_ROOT / "pipeline_data/api/translations/argos"
SPEAKERS_DIR = REPO_ROOT / "pipeline_data/speakers"
OUTPUT_DIR = REPO_ROOT / "pipeline_data/api/tts_audio/chatterbox/diarized"
TTS_URL = "http://localhost:8020"
MIN_TEXT_LENGTH = 15

SPEAKER_VOICE = {
    "SPEAKER_00": str(SPEAKERS_DIR / "female.wav"),
    "SPEAKER_01": str(SPEAKERS_DIR / "female.wav"),
    "SPEAKER_02": str(SPEAKERS_DIR / "male.wav"),
}

diarization = json.loads(DIARIZATION_FILE.read_text())
translation_files = list(TRANSLATIONS_DIR.glob("*.json"))
translation = json.loads(translation_files[0].read_text())
segs = translation.get("segments", []) if isinstance(translation, dict) else translation
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_speaker(start, end):
    overlap = {}
    for s in diarization:
        o = max(0.0, min(end, s["end"]) - max(start, s["start"]))
        if o > 0:
            overlap[s["speaker"]] = overlap.get(s["speaker"], 0.0) + o
    return max(overlap, key=overlap.__getitem__) if overlap else "SPEAKER_01"

for i, seg in enumerate(segs):
    out_file = OUTPUT_DIR / f"segment_{i:03d}.wav"
    if out_file.exists():
        continue
    text = seg.get("text", "").strip()
    if len(text) < MIN_TEXT_LENGTH:
        print(f"Seg {i}: skipping short: {repr(text)}")
        continue
    speaker = get_speaker(seg.get("start", 0), seg.get("end", 0))
    voice_path = SPEAKER_VOICE.get(speaker, str(SPEAKERS_DIR / "female.wav"))
    print(f"Seg {i}: {speaker} | {text[:50]}")
    try:
        with open(voice_path, "rb") as vf:
            r = requests.post(f"{TTS_URL}/v1/audio/speech/upload",
                data={"input": text},
                files={"voice_file": (Path(voice_path).name, vf, "audio/wav")},
                timeout=90)
        if r.status_code == 200:
            out_file.write_bytes(r.content)
            print(f"  Saved ({len(r.content):,} bytes)")
        else:
            print(f"  Error {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  Exception: {e}")
    time.sleep(0.5)
print("Done!")
