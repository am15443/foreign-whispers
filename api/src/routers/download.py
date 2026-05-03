"""POST /api/download — download YouTube video + captions."""
import json
import pathlib
import re
from fastapi import APIRouter, HTTPException, Request
from api.src.core.config import settings
from api.src.core.video_registry import get_video
from api.src.schemas.download import CaptionSegment, DownloadRequest, DownloadResponse
from api.src.services.download_service import DownloadService

router = APIRouter(prefix="/api")
_download_service = DownloadService(settings.data_dir)

def _extract_video_id(url):
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    if not m:
        raise ValueError(f"Cannot extract video ID from URL: {url}")
    return m.group(1)

@router.post("/download", response_model=DownloadResponse)
async def download_endpoint(body: DownloadRequest):
    """Download video and captions, returning video_id and caption segments."""
    video_id = _extract_video_id(body.url)
    entry = get_video(video_id)

    videos_dir = settings.videos_dir
    captions_dir = settings.youtube_captions_dir
    videos_dir.mkdir(parents=True, exist_ok=True)
    captions_dir.mkdir(parents=True, exist_ok=True)

    # Check if files already exist using video_id as stem
    video_path = videos_dir / f"{video_id}.mp4"
    caption_path = captions_dir / f"{video_id}.txt"

    # If not found by video_id, try registry title
    if entry and not video_path.exists():
        alt_path = videos_dir / f"{entry.title}.mp4"
        if alt_path.exists():
            video_path = alt_path

    if not video_path.exists():
        # Need to get title from yt-dlp for download
        vid_id, title = _download_service.get_video_info(body.url)
        stem = entry.title if entry else title.replace(":", "")
        video_path = videos_dir / f"{stem}.mp4"
        caption_path = captions_dir / f"{stem}.txt"
        _download_service.download_video(body.url, str(videos_dir), stem)
    else:
        title = entry.title if entry else video_id

    if not caption_path.exists():
        alt_caption = captions_dir / f"{video_id}.txt"
        if not alt_caption.exists():
            _download_service.download_caption(body.url, str(captions_dir), video_id)
        caption_path = captions_dir / f"{video_id}.txt"

    segments = _download_service.read_caption_segments(caption_path)
    return DownloadResponse(
        video_id=video_id,
        title=title,
        caption_segments=segments,
    )
