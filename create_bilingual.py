#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_bilingual.py - 薄包裝入口點

實際邏輯已重構至 bilingual_subtitle_factory 套件。
安裝套件後也可執行 create-bilingual（同一個 main）。
"""

import logging
import sys

# 在載入套件（會 import yt-dlp 等）之前先打開日誌，與既有腳本行為一致。
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bilingual_factory.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

from bilingual_subtitle_factory.cli import main

if __name__ == "__main__":
    main()
