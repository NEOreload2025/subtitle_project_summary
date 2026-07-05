"""
音軌下載模組 (yt-dlp)
"""

import logging
import os
import subprocess
from typing import Dict

import yt_dlp

logger = logging.getLogger(__name__)


def get_video_info(url: str) -> Dict:
    """用 yt-dlp 取得標題與基本資訊"""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return {
        "id": info.get("id"),
        "title": info.get("title", ""),
        "uploader": info.get("uploader", ""),
        "duration": info.get("duration"),
    }


def download_audio(url: str, output_stem: str, audio_format: str = "mp3") -> str:
    """
    使用 yt-dlp 下載最佳音軌並轉成 mp3。
    回傳實際產生的檔案路徑。
    """
    outtmpl = f"{output_stem}.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": audio_format,
            "preferredquality": "192",
        }],
        "quiet": False,
        "noplaylist": True,
        "extractaudio": True,
    }

    logger.info(f"📥 正在下載音軌：{url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    audio_path = f"{output_stem}.{audio_format}"
    if not os.path.exists(audio_path):
        for ext in ["mp3", "m4a", "webm", "wav"]:
            candidate = f"{output_stem}.{ext}"
            if os.path.exists(candidate):
                if ext != "mp3":
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", candidate, "-q:a", "2", audio_path],
                        check=True, capture_output=True
                    )
                    os.remove(candidate)
                break

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"音軌下載失敗：{audio_path}")

    logger.info(f"✅ 音軌已儲存：{audio_path}")
    return audio_path
