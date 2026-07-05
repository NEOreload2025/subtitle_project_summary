"""
簡單強制對齊模組 (stable-ts)
"""

import logging
from typing import List

from ..utils import save_srt

logger = logging.getLogger(__name__)

try:
    import stable_whisper
except ImportError:
    stable_whisper = None


def run_simple_alignment(
    audio_path: str,
    lyrics_lines: List[str],
    profile: str = "fancam",
    model_size: str = "medium",
    language: str = "ko",
    output_srt: str = "output.KR.srt"
) -> str:
    """
    使用官方歌詞 + 音軌進行 stable-ts 強制對齊（全曲）。
    """
    if stable_whisper is None:
        raise RuntimeError("請先安裝 stable-ts：pip install stable-ts")

    logger.info(f"🧠 載入 stable-ts 模型：{model_size} （profile={profile}）")

    model = stable_whisper.load_model(model_size)
    full_text = "\n".join(lyrics_lines)

    logger.info("🧠 執行強制對齊（這步可能需要幾分鐘）...")
    result = model.align(
        audio_path,
        full_text,
        language=language,
        vad_filter=(profile == "fancam"),
    )

    segments = []
    for seg in result.segments:
        if hasattr(seg, "words") and seg.words:
            text = " ".join(w.word.strip() for w in seg.words if w.word.strip())
        else:
            text = getattr(seg, "text", "").strip()
        if text:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": text
            })

    save_srt(segments, output_srt)
    logger.info(f"🎉 SRT 已輸出：{output_srt}")
    return output_srt
