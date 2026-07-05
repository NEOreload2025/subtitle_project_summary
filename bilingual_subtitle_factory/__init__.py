"""
雙語字幕工廠 (Bilingual Subtitle Factory)
======================================

統一的 Python package，提供從 YouTube 產生高品質韓中雙語字幕的功能。

主要模組：
- cli: 命令列入口
- core.downloader: yt-dlp 音軌下載
- core.cc_extractor: 官方 CC 擷取
- hybrid: 企業級進階對齊管道 (v8)
- utils: 共用工具函式

快速開始：
    from bilingual_subtitle_factory import create_from_url
    create_from_url("https://youtu.be/xxxxx", profile="fancam")
"""

__version__ = "0.8.0"  # Phase C package version

from .utils import (
    extract_video_id,
    sanitize_filename,
    fmt_ts,
    parse_ts,
    tokenize,
)
from .cli import create_from_url

__all__ = [
    "extract_video_id",
    "sanitize_filename",
    "fmt_ts",
    "parse_ts",
    "tokenize",
    "create_from_url",
]
