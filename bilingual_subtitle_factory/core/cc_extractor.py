"""
官方 CC 字幕擷取模組
"""

import logging
from typing import List, Optional, Tuple

# 0.6 API：get_transcript / list_transcripts。1.x 拿掉了這兩個類別方法，故安裝範圍鎖在 <1。
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter

logger = logging.getLogger(__name__)


def fetch_official_cc(video_id: str, lang: str = "ko") -> Tuple[List[str], Optional[str]]:
    """
    嘗試取得官方字幕。
    回傳 (lyrics_lines, srt_content)
    """
    logger.info(f"🔍 正在擷取官方 CC（video_id={video_id}, lang={lang}）...")

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
    except Exception as e1:
        logger.warning(f"無法取得 {lang} 手動字幕，嘗試其他來源...")
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = None
            for t in transcript_list:
                if t.is_translatable or t.language_code.startswith(lang[:2]):
                    transcript = t.fetch()
                    lang = t.language_code
                    break
            if transcript is None:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e2:
            logger.error(f"完全無法取得字幕：{e2}")
            return [], None

    if not transcript:
        return [], None

    lines = []
    for item in transcript:
        text = item.get("text", "").strip()
        if text:
            lines.append(text)

    try:
        formatter = SRTFormatter()
        srt_content = formatter.format_transcript(transcript)
    except Exception:
        srt_content = None

    logger.info(f"✅ 成功取得官方 CC，共 {len(lines)} 行（語言：{lang}）")
    return lines, srt_content
