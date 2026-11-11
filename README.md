# 雙語字幕工廠 (Bilingual Subtitle Factory)

針對 YouTube 缺少字幕或缺少雙語對照的影片，產生高品質韓中（或其他語言）對照字幕。

**核心理念**：
- 官方 CC 提供 100% 正確的原文歌詞
- 音軌（經 Demucs 分離後）負責精準時間軸
- stable-ts 強制對齊 + 進階零漂移縫合

## 安裝與環境

Python 3.9 以上。在這個儲存庫的工作副本裡建立虛擬環境後安裝（`pyproject.toml` 會註冊命令列進入點）：

```bash
git clone https://github.com/NEOreload2025/subtitle_project_summary.git
cd subtitle_project_summary
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
```

`pip install -e ".[full]"`（或正式安裝 `pip install ".[full]"`）會安裝本套件、`create-bilingual` / `bilingualize` 進入點，以及 `requirements.txt` 裡的產線依賴：yt-dlp、youtube-transcript-api、stable-ts、openai-whisper、demucs、torch、torchaudio 等。`youtube-transcript-api` 維持 0.6 系列（`<1`），官方 CC 擷取仍使用 `get_transcript`。

只安裝套件與 CLI、稍後再補對齊模型：

```bash
pip install .
```

這一步包含 yt-dlp 與 youtube-transcript-api。強制對齊與人聲分離請再安裝 `.[full]`。

在儲存庫目錄直接跑腳本、不註冊進入點時，也可以只裝依賴：

```bash
pip install -r requirements.txt
python create_bilingual.py --help
```

下載轉檔、Demucs 與對齊需要系統上的 `ffmpeg`。

`activate.sh` 會啟動舊環境 `/home/hinet/.venvs/youtube_summarizer`，給當初掛在 Google Drive 的那份工作副本用。這個儲存庫用上面的 `.venv`。

## 快速使用

### 1. 從 URL 產生原文 SRT

安裝完成後，在任何目錄：

```bash
create-bilingual --url "https://youtu.be/r9AEGPB6qIU" --profile fancam
```

在儲存庫目錄裡，原本的進入方式仍然可用，參數與輸出相同：

```bash
python create_bilingual.py --url "https://youtu.be/r9AEGPB6qIU" --profile fancam
python -m bilingual_subtitle_factory --url "https://youtu.be/r9AEGPB6qIU" --profile fancam
```

常用參數：
- `--profile fancam`（預設，會用 Demucs） / `official_mv`
- `--method simple`（預設） / `hybrid`
- `--prefix-srt` + `--cut-point` （hybrid 模式使用）

fancam 與 hybrid 對齊需要 `pip install ".[full]"`。

### 2. 產生雙語翻譯提示詞（強烈推薦）

```bash
bilingualize 你的影片_KR.srt --prompt > prompt.txt
```

或在儲存庫目錄：

```bash
python bilingualize.py 你的影片_KR.srt --prompt > prompt.txt
```

然後把 `prompt.txt` 的內容直接貼給 Grok / Claude / Gemini，即可得到高品質雙語 SRT。

## 測試

在儲存庫根目錄執行，不需要 API 金鑰：

```bash
python test_integration_v8.py
```

格式合規測試會讀取本機產線成品 `LE_SSERAFIM_HOT_Bilingual_FINAL_v71.srt`。檔案不在這個版本庫時，該組測試會略過，其餘測試照常執行。

GitHub Actions（`.github/workflows/ci.yml`）在 push 到 `main` 與 pull request 時執行 `pip install .`、編譯並從已安裝套件匯入模組、跑上面的測試。這個 workflow 不部署 GitHub Pages。

## 專案結構（Phase C 重構後）

```
.
├── bilingual_subtitle_factory/     # 主要套件
│   ├── __init__.py
│   ├── __main__.py                 # python -m bilingual_subtitle_factory
│   ├── cli.py                      # 主要業務邏輯與 create-bilingual 進入點
│   ├── utils.py                    # 共用工具
│   ├── hybrid.py                   # 進階 hybrid 相容層
│   └── core/
│       ├── downloader.py
│       ├── cc_extractor.py
│       └── aligner.py
├── create_bilingual.py             # 薄 CLI 入口（與 create-bilingual 相同）
├── bilingualize.py                 # 雙語提示詞產生器（進入點同名）
├── hybrid_v8_enterprise.py         # 舊版進階腳本（仍可用，並隨套件安裝）
├── test_integration_v8.py
├── pyproject.toml
├── requirements.txt
├── .github/workflows/ci.yml
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

- 更多語言支援
- 批次處理與播放清單
- 更好的輸出格式（ASS 等）

可安裝套件（`pip install .` / `pip install -e .`，含 CLI 進入點）已完成，見上方安裝方式。

## 授權與致謝

個人專案，歡迎參考。核心技術致謝 stable-ts、yt-dlp、youtube-transcript-api 以及所有測試過的 K-pop 直拍影片。
