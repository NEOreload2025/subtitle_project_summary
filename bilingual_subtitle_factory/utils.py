"""
共用工具函式 (Utils)
"""

import re
from typing import List
from urllib.parse import urlparse, parse_qs


def extract_video_id(url_or_id: str) -> str:
    """從各種 YouTube 網址或直接 ID 取出 video_id"""
    s = url_or_id.strip()
    if re.match(r'^[A-Za-z0-9_-]{11}$', s):
        return s

    # youtu.be/VIDEO_ID
    if "youtu.be/" in s:
        m = re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', s)
        if m:
            return m.group(1)

    # youtube.com/watch?v=VIDEO_ID 或其他
    if "youtube.com" in s or "youtu.be" in s:
        try:
            parsed = urlparse(s)
            if "v" in parse_qs(parsed.query):
                vid = parse_qs(parsed.query)["v"][0]
                if len(vid) == 11:
                    return vid
            path = parsed.path.lstrip("/")
            candidate = path.split("/")[0]
            if len(candidate) == 11:
                return candidate
        except Exception:
            pass

    return s[:11] if len(s) >= 11 else s


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """清理檔名，移除非法字元"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r'\s+', " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    return name or "untitled"


def fmt_ts(s: float) -> str:
    """秒數轉 SRT 時間格式"""
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"


def parse_ts(s: str) -> float:
    """SRT 時間格式轉秒數"""
    h, m, rest = s.split(':')
    sec, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0


def tokenize(line: str) -> List[str]:
    """切分字詞：支援韓文、英文、數字"""
    return re.findall(r'[가-힣]+|[a-zA-Z\']+|[0-9]+', line)


def save_srt(segments: List[dict], output_path: str):
    """將 segments 寫成標準 SRT 檔案"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = fmt_ts(seg["start"])
            end = fmt_ts(seg["end"])
            text = seg.get("text", "").strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
