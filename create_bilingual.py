#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_bilingual.py - 薄包裝入口點

實際邏輯已重構至 bilingual_subtitle_factory 套件。
"""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bilingual_factory.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

from bilingual_subtitle_factory.cli import create_from_url


def main():
    parser = argparse.ArgumentParser(
        description="雙語字幕工廠 - 從 YouTube URL 產生高品質原文 .KR.srt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  python create_bilingual.py --url https://youtu.be/r9AEGPB6qIU --profile fancam
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

    args = parser.parse_args()

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


if __name__ == "__main__":
    main()
