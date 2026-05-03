import os
import pathlib
import re
import shutil
import json

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

_COOKIES_FILE = os.getenv("YT_COOKIES_FILE", "/app/cookies.txt")

def _yt_dlp_opts(**extra):
    opts = {"quiet": True, "no_warnings": True}
    if pathlib.Path(_COOKIES_FILE).exists():
        opts["cookiefile"] = _COOKIES_FILE
    opts.update(extra)
    return opts

def create_folder(folder_name):
    pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True)
    return True

def delete_folder(folder_name, ignore_error=True):
    shutil.rmtree(folder_name, ignore_errors=ignore_error)
    return True

def _extract_video_id(url):
    m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
    if not m:
        raise ValueError(f"Cannot extract video ID from URL: {url}")
    return m.group(1)

def get_video_info(url):
    with yt_dlp.YoutubeDL(_yt_dlp_opts(skip_download=True)) as ydl:
        info = ydl.extract_info(url, download=False, process=False)
    return info["id"], info["title"]

def download_video(url, destination_folder, filename=None):
    if filename:
        safe_title = filename
        save_path = pathlib.Path(destination_folder) / (safe_title + ".mp4")
        if save_path.exists():
            print(f"Skipping (already exists): {safe_title}")
            return str(save_path)
    else:
        vid_id, title = get_video_info(url)
        safe_title = re.sub(r'[:|]', '', title).strip()
        save_path = pathlib.Path(destination_folder) / (safe_title + ".mp4")
        if save_path.exists():
            print(f"Skipping (already exists): {title}")
            return str(save_path)
    print(f"Downloading: {safe_title}...", end=" ", flush=True)
    ydl_opts = _yt_dlp_opts(
        format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        merge_output_format="mp4",
        outtmpl=str(pathlib.Path(destination_folder) / (safe_title + ".%(ext)s")),
    )
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("Success!")
    return str(save_path)

def download_caption(url, destination_folder, filename=None):
    if filename:
        safe_title = filename
        save_path = pathlib.Path(destination_folder) / (safe_title + ".txt")
        if save_path.exists():
            print(f"Skipping captions (already exists): {safe_title}")
            return str(save_path)
        video_id = _extract_video_id(url)
    else:
        video_id, title = get_video_info(url)
        safe_title = re.sub(r'[:|]', '', title).strip()
        save_path = pathlib.Path(destination_folder) / (safe_title + ".txt")
        if save_path.exists():
            print(f"Skipping captions (already exists): {title}")
            return str(save_path)
    print(f"Downloading captions... ", end=" ", flush=True)
    api = YouTubeTranscriptApi()
    caption = api.fetch(video_id).to_raw_data()
    with open(save_path, 'w') as outfile:
        for segment in caption:
            outfile.write(json.dumps(segment) + "\n")
    print("Success!")
    return str(save_path)
