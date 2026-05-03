import json
from pyannote.audio import Pipeline

HF_TOKEN = [l.split('=')[1].strip() for l in open('/home/ubuntu/foreign-whispers/.env').read().splitlines() if l.startswith('HF_TOKEN')][0]

audio_file = "/home/ubuntu/foreign-whispers/pipeline_data/api/videos/Strait of Hormuz disruption threatens to shake global economy.mp4"
output_file = "/home/ubuntu/foreign-whispers/pipeline_data/api/diarization.json"

print("Loading pipeline...")
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=HF_TOKEN)

print("Running diarization...")
result = pipeline(audio_file)

# Use the speaker_diarization annotation object
annotation = result.speaker_diarization

segments = []
for turn, _, speaker in annotation.itertracks(yield_label=True):
    segments.append({
        "start": round(turn.start, 3),
        "end": round(turn.end, 3),
        "speaker": speaker
    })
    print(f"  [{turn.start:.1f}s - {turn.end:.1f}s] {speaker}")

with open(output_file, 'w') as f:
    json.dump(segments, f, indent=2)

print(f"\nDone! {len(segments)} segments saved to {output_file}")
