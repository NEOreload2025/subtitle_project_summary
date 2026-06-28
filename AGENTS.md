# AGENTS.md — 雙語字幕工廠 工作守則

> **給 AI 助手(AGY / Antigravity)的指示:**
> 當使用者要在本專案做任何「修改、升級、重跑」之前,**先用下面的守則主動提醒他**,確認方向對了再動手。
> 這些是這個專案踩過坑、驗證過的結論,別讓使用者重蹈覆轍。

---

## 🥇 第一守則:輸入品質 > 模型大小
這個專案最核心的教訓。**字幕跑不好,先檢查「餵進去的聲音對不對」,不要急著換更大的模型。**
- 髒的混音餵 large-v3 → 一樣抓不到;乾淨分離的人聲 + 官方 CC 餵 **medium → 跑得漂亮**。
- 一旦走「官方 CC 歌詞 + stable-ts 強制對齊」,模型大小幾乎沒差。
- **結論:medium 已經夠用,不需要升級 large-v3。** 別為了幾乎看不出的差異多花 VRAM。

## 🎤 第二守則:半開麥 / CD AR 的物理限制
K-pop 現場前奏常是「半開麥 CD 合成軌」,人聲被壓進伴奏裡 —— **那段根本沒有獨立人聲訊號,任何模型都抓不到。**
- 遇到「某段一直抓不到」,**先懷疑是不是 playback/半開麥**,不要硬聽。
- 解法:歌詞改從官方 CC 拿,音訊只負責對時間軸。

## 🧠 第三守則:卡關先講假設,別悶頭硬幹
同一個地方連續失敗第二次時,**先停下來說「我覺得卡住的原因可能是 X(也許這根本無解 / 資料不在那)」**,跟使用者確認,再決定下一步。不要默默換一個更強的工具反覆試。

## 📌 產線技術守則(沿用,別亂改)
1. **歌詞來源**:yt-dlp 抓官方 MV 韓文 CC(100% 正確),不要讓 Whisper 自己猜歌詞。
2. **時間軸來源**:stable-ts 強制對齊「直拍音軌」。**絕不直接套用 MV CC 的時間**(MV 時間 ≠ 直拍時間,會越跑越歪)。
3. **分段對齊防漂移**:整首一次對齊,誤差會累積(後半段可漂移 ~6 秒)。切前後兩段、各自獨立對齊、在縫合點接合。
4. **Whisper 參數**:`task="transcribe"`,**不要** `task="translate"`(translate 會強制只出英文、丟掉原文)。
5. **人聲分離**:Demucs htdemucs 先剝掉尖叫/伴奏,再聽寫。
6. **URL 純淨**:用 `youtu.be/ID` 短網址,**不要帶 `&list=` 參數**(會抓到播放清單其他片的資訊)。

## 🖥️ 硬體限制(RTX 3060 Laptop = 6GB VRAM)
- PyTorch 原版 Whisper large-v3 需 ~10GB → **塞不下**。真要 large-v3 就用 **faster-whisper / whisper.cpp**(量化版,~4-5GB)。
- **分階段跑**(Demucs → 聽寫 → 對齊各自跑),別同時佔 VRAM。

## ✍️ 文件守則
- 自動生成的報告(如 `subtitle_project_summary.html`)**模型標示要按版本分**:v1~v6.2 是 Gemini 3.1 Pro High,v7.0~v7.1 是 Claude Sonnet 4.6 (Thinking),v8.0 企業級重構版 (`hybrid_v8_enterprise.py`) 是 Gemini 3.1 Pro High (架構設計) + Claude Sonnet 4.6 Thinking (審核與測試)。別一概而論。

## 🧪 整合測試守則
- 每次對產線腳本進行重構後，**必須執行**企業級整合測試套件確保核心邏輯無誤：
  ```bash
  cd ~/gdrive/youtube_summarizer
  python3 test_integration_v8.py
  ```
- 測試覆蓋：時間軸工具 / Tokenize / Checkpoint 快照 / Profile 切換 / SRT 格式合規 / Requirements 完整性（共 8 大類）。
- 所有測試通過後才可執行正式產線腳本。

## 📦 依賴管理守則
- **完整依賴清單已更新至** `requirements.txt`，核心套件包含：`yt-dlp`, `openai-whisper`, `stable-ts`, `demucs`, `torch`。
- 新裝置環境安裝請執行：`pip install -r requirements.txt`。
- 注意：`torch` 版本需與 CUDA 版本配對（RTX 3060 建議使用 CUDA 12.x）。

---
*最後更新:2026-06-28 (v8.0 Production-Ready) | 詳細流程見 `AGY_Bilingual_Subtitle_Workflow_Log.md`*
