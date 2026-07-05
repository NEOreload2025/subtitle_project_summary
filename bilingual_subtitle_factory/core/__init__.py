"""
核心子模組
- downloader: 音軌下載
- cc_extractor: 官方字幕擷取
- aligner: 簡單強制對齊
"""
from . import downloader, cc_extractor, aligner

__all__ = ["downloader", "cc_extractor", "aligner"]
