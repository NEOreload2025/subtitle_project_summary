"""
統一 CLI 邏輯
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from .utils import extract_video_id, sanitize_filename
from .core.downloader import download_audio, get_video_info
from .core.cc_extractor import fetch_official_cc
from .core.aligner import run_simple_alignment

logger = logging.getLogger(__name__)


def create_from_url(
    url: str,
    profile: str = "fancam",
    model: Optional[str] = None,
    lang: str = "ko",
    output: Optional[str] = None,
    output_dir: str = ".",
    method: str = "simple",
    cut_point: Optional[float] = None,
    prefix_srt: Optional[str] = None,
    skip_download: bool = False,
) -> str:
    """
    從 YouTube URL 產生 KR.srt 的主要入口函式。
    """
    video_id = extract_video_id(url)
    logger.info(f"🎬 處理影片 ID: {video_id}")

    try:
        info = get_video_info(url)
        title = info.get("title", video_id)
    except Exception:
        title = video_id

    safe_title = sanitize_filename(title)
    work_dir = Path(output_dir).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    default_model = "medium" if profile == "fancam" else "large-v3"
    model_size = model or default_model

    base_name = f"{safe_title}_{video_id}"
    audio_stem = str(work_dir / f"{base_name}_audio")
    kr_srt_path = output or str(work_dir / f"{base_name}_KR.srt")

    # 下載音軌
    audio_path = f"{audio_stem}.mp3"
    if not skip_download or not os.path.exists(audio_path):
        audio_path = download_audio(url, audio_stem)
    else:
        logger.info(f"⏭️ 使用已存在音軌：{audio_path}")

    # 擷取 CC
    lyrics_lines, cc_srt = fetch_official_cc(video_id, lang)

    if not lyrics_lines:
        logger.error("❌ 無法取得官方字幕。")
        raise RuntimeError("No official subtitles found")

    if cc_srt:
        cc_path = str(work_dir / f"{base_name}_Official_CC_{lang}.srt")
        with open(cc_path, "w", encoding="utf-8") as f:
            f.write(cc_srt)
        logger.info(f"📄 官方 CC 已備份：{cc_path}")

    # 對齊
    if method == "simple":
        run_simple_alignment(
            audio_path=audio_path,
            lyrics_lines=lyrics_lines,
            profile=profile,
            model_size=model_size,
            language=lang,
            output_srt=kr_srt_path,
        )
    else:
        # Hybrid 模式：委派給 hybrid 模組
        try:
            from .hybrid import EnterprisePipeline
        except ImportError:
            # 向後相容：直接從歷史檔案 import
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from hybrid_v8_enterprise import EnterprisePipeline

        official_cc_path = str(work_dir / f"{base_name}_Official_CC_KR.ko.srt")
        if cc_srt:
            with open(official_cc_path, "w", encoding="utf-8") as f:
                f.write(cc_srt)

        pipeline = EnterprisePipeline(
            profile=profile,
            audio_path=audio_path,
            prefix_srt=prefix_srt,
            output_srt=kr_srt_path,
            cut_point_seconds=cut_point,
            video_id=video_id,
        )
        pipeline.run()

    return kr_srt_path


def configure_logging() -> None:
    """檔案 + stdout 日誌。根 logger 已有 handler 時 basicConfig 不會覆寫。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("bilingual_factory.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    """CLI 進入點。`create-bilingual` 與 `python create_bilingual.py` 都呼叫這裡。"""
    configure_logging()
    parser = argparse.ArgumentParser(
        description="雙語字幕工廠 - 從 YouTube URL 產生高品質原文 .KR.srt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python create_bilingual.py --url https://youtu.be/r9AEGPB6qIU --profile fancam
  create-bilingual --url https://youtu.be/r9AEGPB6qIU --profile fancam
  python create_bilingual.py --url https://youtu.be/xxxxx --profile official_mv --model large-v3
  python create_bilingual.py --url https://youtu.be/xxxxx --method hybrid --prefix-srt front.srt --cut-point 63
"""
    )
    parser.add_argument("--url", required=True, help="YouTube 網址或 video_id")
    parser.add_argument("--profile", choices=["fancam", "official_mv"], default="fancam")
    parser.add_argument("--model", default=None)
    parser.add_argument("--lang", default="ko")
    parser.add_argument("--output", default=None)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--method", choices=["simple", "hybrid"], default="simple")
    parser.add_argument("--cut-point", type=float, default=None)
    parser.add_argument("--prefix-srt", default=None)

    args = parser.parse_args(argv)

    try:
        output_path = create_from_url(
            url=args.url,
            profile=args.profile,
            model=args.model,
            lang=args.lang,
            output=args.output,
            output_dir=args.output_dir,
            method=args.method,
            cut_point=args.cut_point,
            prefix_srt=args.prefix_srt,
            skip_download=args.skip_download,
        )
        print("\n" + "=" * 60)
        print("✅ 完成！")
        print(f"   輸出 SRT：{output_path}")
        print(f"   方法：{args.method}")
        if args.method == "hybrid" and not args.prefix_srt:
            print("⚠️  hybrid 模式強烈建議提供 --prefix-srt")
        print("\n下一步：使用 bilingualize.py 產生翻譯提示詞")
        print("=" * 60)
    except Exception as e:
        logging.exception(str(e))
        sys.exit(1)
