#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bilingualize.py - 薄包裝入口點

將純 KR.srt 轉成雙語對照（主要產生高品質 LLM 提示詞）
"""

import argparse
import sys
from pathlib import Path

# 簡單的解析與提示詞產生邏輯保留在此（輕量）
# 未來可移至 bilingual_subtitle_factory/bilingualizer.py

import re


def parse_srt(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    blocks = re.split(r'\n\s*\n', content)
    results = []
    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 3:
            continue
        idx = lines[0]
        ts = lines[1]
        text = '\n'.join(lines[2:])
        results.append((idx, ts, text))
    return results


def generate_translation_prompt(blocks, video_title=""):
    prompt = f"""你是一位專業的 K-pop 歌詞雙語字幕專家。
請將以下韓文歌詞 SRT 轉成高品質的韓中雙語對照字幕。

要求：
- 保留原本的時間軸與行號完全不變
- 每行韓文後面緊接一行用括號包覆的自然繁體中文翻譯
- 翻譯要自然流暢、帶有歌詞韻味
- 專有名詞、人名、英文詞保持原樣

影片標題：{video_title or "（未知）"}

原始 SRT 內容如下：
"""
    for idx, ts, text in blocks:
        prompt += f"\n{idx}\n{ts}\n{text}\n"

    prompt += """
請只輸出完整的雙語 SRT 檔案內容，不要加任何解釋。
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="KR.srt → 雙語提示詞產生器")
    parser.add_argument("input_srt")
    parser.add_argument("--output", "-o")
    parser.add_argument("--prompt", action="store_true")
    parser.add_argument("--title", default="")
    parser.add_argument("--format", default="parentheses")

    args = parser.parse_args()

    input_path = Path(args.input_srt)
    if not input_path.exists():
        print(f"❌ 找不到檔案：{input_path}", file=sys.stderr)
        sys.exit(1)

    blocks = parse_srt(str(input_path))

    if args.prompt:
        prompt = generate_translation_prompt(blocks, args.title)
        print(prompt)
    elif args.output:
        # 簡單骨架
        out = []
        for idx, ts, kr in blocks:
            out.append(f"{idx}\n{ts}\n{kr}\n([待翻譯])\n")
        Path(args.output).write_text("".join(out).strip() + "\n", encoding="utf-8")
        print(f"✅ 雙語骨架已輸出：{args.output}")
    else:
        print("使用 --prompt 產生翻譯提示詞（推薦）")


if __name__ == "__main__":
    main()
