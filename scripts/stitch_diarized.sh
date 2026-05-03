#!/bin/bash
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SEGMENTS_DIR="$REPO_ROOT/pipeline_data/api/tts_audio/chatterbox/diarized"
VIDEOS_DIR="$REPO_ROOT/pipeline_data/api/videos"
OUTPUT_DIR="$REPO_ROOT/pipeline_data/api/dubbed_videos/diarized"
VIDEO_FILE=$(ls "$VIDEOS_DIR"/*.mp4 | head -1)
VIDEO_NAME=$(basename "$VIDEO_FILE")
CONCAT_LIST=$(mktemp /tmp/ffmpeg_list_XXXX.txt)
ls -1 "$SEGMENTS_DIR"/segment_*.wav | sort | sed "s/^/file '/" | sed "s/$/'/" > "$CONCAT_LIST"
COMBINED_WAV=$(mktemp /tmp/dubbed_audio_XXXX.wav)
ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST" -c copy "$COMBINED_WAV"
mkdir -p "$OUTPUT_DIR"
ffmpeg -y -i "$VIDEO_FILE" -i "$COMBINED_WAV" -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest "$OUTPUT_DIR/$VIDEO_NAME"
rm -f "$CONCAT_LIST" "$COMBINED_WAV"
echo "Done! Output: $OUTPUT_DIR/$VIDEO_NAME"
