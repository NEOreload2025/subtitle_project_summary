# 雙語字幕工廠 (Bilingual Subtitle Factory)

針對 YouTube 缺少字幕或缺少雙語對照的影片，產生高品質韓中（或其他語言）對照字幕。

**核心理念**：
- 官方 CC 提供 100% 正確的原文歌詞
- 音軌（經 Demucs 分離後）負責精準時間軸
- stable-ts 強制對齊 + 進階零漂移縫合

## 安裝與環境

```bash
cd ~/gdrive/youtube_summarizer
source activate.sh   # 會啟動專屬 venv
pip install -r requirements.txt
```

主要依賴：
- yt-dlp
- stable-ts
- youtube-transcript-api
- demucs + torch（fancam 模式）

## 快速使用

### 1. 從 URL 產生原文 SRT

```bash
python create_bilingual.py --url "https://youtu.be/r9AEGPB6qIU" --profile fancam
```

常用參數：
- `--profile fancam`（預設，會用 Demucs） / `official_mv`
- `--method simple`（預設） / `hybrid`
- `--prefix-srt` + `--cut-point` （hybrid 模式使用）

### 2. 產生雙語翻譯提示詞（強烈推薦）

```bash
python bilingualize.py 你的影片_KR.srt --prompt > prompt.txt
```

然後把 `prompt.txt` 的內容直接貼給 Grok / Claude / Gemini，即可得到高品質雙語 SRT。

## 專案結構（Phase C 重構後）

```
.
├── bilingual_subtitle_factory/     # 主要套件
│   ├── __init__.py
│   ├── cli.py                      # 主要業務邏輯
│   ├── utils.py                    # 共用工具
│   ├── hybrid.py                   # 進階 hybrid 相容層
│   └── core/
│       ├── downloader.py
│       ├── cc_extractor.py
│       └── aligner.py
├── create_bilingual.py             # 薄 CLI 入口
├── bilingualize.py                 # 雙語提示詞產生器
├── hybrid_v8_enterprise.py         # 舊版進階腳本（仍可用）
├── test_integration_v8.py
├── requirements.txt
├── AGENTS.md
└── README.md
```

## 兩種對齊模式

| 模式     | 適合情境                     | 優點                     |
|----------|------------------------------|--------------------------|
| simple   | 大多數影片                   | 簡單可靠、一鍵完成       |
| hybrid   | fancam 有明顯漂移的長片      | 零漂移縫合（需前段 SRT） |

## 舊版腳本

- `hybrid_v8_enterprise.py` 仍可獨立使用（已支援 CLI 參數）
- 其他歷史腳本保留供參考

## 後續規劃 (C 之後)

- 更完整的 package（支援 `pip install -e .`）
- 更多語言支援
- 批次處理與播放清單
- 更好的輸出格式（ASS 等）

## 授權與致謝

個人專案，歡迎參考。核心技術致謝 stable-ts、yt-dlp、youtube-transcript-api 以及所有測試過的 K-pop 直拍影片。
