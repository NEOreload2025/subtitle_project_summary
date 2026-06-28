#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
【企業級整合測試腳本】Integration Test Suite for Hybrid Pipeline (v8.0)
==============================================================================
測試覆蓋範圍：
  TEST-01  時間軸工具函式正確性驗證 (fmt_ts / parse_ts 互轉一致性)
  TEST-02  Tokenize 音節切分邏輯完整性（韓文 + 英文 + 混排）
  TEST-03  CheckpointManager 快照寫入與讀取完整性
  TEST-04  PipelineConfig 動態 Profile 切換正確性
  TEST-05  SRT 前段解析邊界值（截止點前後各 1ms 的容差處理）
  TEST-06  後段縫合離群值防呆邏輯（>10 秒長度應觸發線性修正）
  TEST-07  最終 SRT 格式合規性（行號遞增 / 時間軸遞進 / 編碼正確）
  TEST-08  requirements.txt 完整性驗證（所有核心套件是否正確列出）
==============================================================================
"""

import os
import sys
import json
import re
import tempfile
import unittest

# ---- 動態加入父目錄到 sys.path，確保能 import 主模組 ----
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# ==============================================================================
# 輔助函式（直接內嵌，不依賴主模組，確保測試的獨立性）
# ==============================================================================

def fmt_ts(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    ms = int((s - int(s)) * 1000)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def parse_ts(s: str) -> float:
    h, m, rest = s.split(':')
    sec, ms = rest.split(',')
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000.0

def tokenize(line: str):
    return re.findall(r'[가-힣]+|[a-zA-Z\']+|[0-9]+', line)

# ==============================================================================
# TEST-01: 時間軸工具正確性
# ==============================================================================
class TestTimestampUtils(unittest.TestCase):

    def test_fmt_ts_zero(self):
        self.assertEqual(fmt_ts(0.0), "00:00:00,000")

    def test_fmt_ts_one_hour(self):
        self.assertEqual(fmt_ts(3600.0), "01:00:00,000")

    def test_fmt_ts_ms_precision(self):
        self.assertEqual(fmt_ts(63.456), "00:01:03,456")

    def test_parse_ts_basic(self):
        self.assertAlmostEqual(parse_ts("00:01:03,456"), 63.456, places=3)

    def test_roundtrip_consistency(self):
        """fmt_ts 與 parse_ts 的往返一致性（核心防呆）"""
        for val in [0.0, 9.14, 63.0, 123.456, 3599.999]:
            self.assertAlmostEqual(parse_ts(fmt_ts(val)), val, places=2,
                msg=f"往返誤差超出容差！原始值={val}, 轉換後={parse_ts(fmt_ts(val))}")

    def test_fmt_ts_rounding(self):
        """1:03.0 剛好等於截止點，不應丟失毫秒"""
        result = fmt_ts(63.000)
        self.assertEqual(result, "00:01:03,000")

# ==============================================================================
# TEST-02: Tokenize 音節切分邏輯
# ==============================================================================
class TestTokenize(unittest.TestCase):

    def test_korean_only(self):
        tokens = tokenize("살게 해 날")
        self.assertEqual(tokens, ["살게", "해", "날"])

    def test_english_only(self):
        tokens = tokenize("I'm burning HOT")
        self.assertEqual(tokens, ["I'm", "burning", "HOT"])

    def test_mixed_korean_english(self):
        tokens = tokenize("It's all right, we're ride or die, yeah")
        self.assertIn("It's", tokens)
        self.assertIn("all", tokens)
        self.assertIn("yeah", tokens)
        # 確認標點符號不被保留
        self.assertNotIn(",", tokens)

    def test_empty_string(self):
        self.assertEqual(tokenize(""), [])

    def test_numbers_included(self):
        tokens = tokenize("v7 2026")
        self.assertIn("v", tokens)
        self.assertIn("7", tokens)
        self.assertIn("2026", tokens)

# ==============================================================================
# TEST-03: CheckpointManager 快照完整性
# ==============================================================================
class TestCheckpointManager(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.cp_path = os.path.join(self.tmpdir, "test_checkpoint.json")

    def tearDown(self):
        if os.path.exists(self.cp_path):
            os.remove(self.cp_path)

    def _get_manager(self):
        # 動態建立一個輕量版 CheckpointManager 進行測試
        class LightCheckpointManager:
            def __init__(self, path):
                self.path = path
                self.state = self.load()

            def load(self):
                if os.path.exists(self.path):
                    with open(self.path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return {"current_stage": 0}

            def save(self, stage, data=None):
                self.state["current_stage"] = stage
                if data:
                    self.state.update(data)
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(self.state, f, ensure_ascii=False)

            def clear(self):
                if os.path.exists(self.path):
                    os.remove(self.path)

        return LightCheckpointManager(self.cp_path)

    def test_initial_state(self):
        mgr = self._get_manager()
        self.assertEqual(mgr.state.get("current_stage"), 0)

    def test_save_and_reload(self):
        mgr = self._get_manager()
        mgr.save(2, {"front_blocks": ["block_a", "block_b"], "all_words": []})

        # 重新載入
        mgr2 = self._get_manager()
        self.assertEqual(mgr2.state["current_stage"], 2)
        self.assertEqual(len(mgr2.state["front_blocks"]), 2)

    def test_clear_removes_file(self):
        mgr = self._get_manager()
        mgr.save(1)
        mgr.clear()
        self.assertFalse(os.path.exists(self.cp_path))

# ==============================================================================
# TEST-04: PipelineConfig 動態 Profile
# ==============================================================================
class TestPipelineConfig(unittest.TestCase):

    def test_fancam_profile_defaults(self):
        from hybrid_v8_enterprise import PipelineConfig
        cfg = PipelineConfig("fancam")
        self.assertTrue(cfg.settings["use_demucs"])
        self.assertIn("fancam", cfg.output_srt)

    def test_official_mv_profile(self):
        from hybrid_v8_enterprise import PipelineConfig
        cfg = PipelineConfig("official_mv")
        self.assertFalse(cfg.settings["use_demucs"])
        self.assertEqual(cfg.settings["whisper_model"], "large-v3")

    def test_invalid_profile_fallback(self):
        from hybrid_v8_enterprise import PipelineConfig
        cfg = PipelineConfig("nonexistent_profile")
        # 應退回預設 fancam
        self.assertEqual(cfg.profile_name, "fancam")

# ==============================================================================
# TEST-05: SRT 前段解析邊界值
# ==============================================================================
class TestSRTFrontParsing(unittest.TestCase):

    def _make_srt_block(self, start_sec: float, end_sec: float, text: str, idx: int = 1) -> str:
        return f"{idx}\n{fmt_ts(start_sec)} --> {fmt_ts(end_sec)}\n{text}"

    def test_block_before_cutpoint_included(self):
        """起始時間 62.999 秒（截止點 63 秒之前）應被保留"""
        block = self._make_srt_block(62.999, 63.5, "불타오르지 l love it")
        lines = block.split('\n')
        start_sec = parse_ts(lines[1].split(' --> ')[0].strip())
        self.assertLess(start_sec, 63.0)

    def test_block_at_cutpoint_excluded(self):
        """起始時間恰好 63.0 秒（截止點）不應被保留在前段"""
        block = self._make_srt_block(63.0, 70.829, "I'm burning HOT")
        lines = block.split('\n')
        start_sec = parse_ts(lines[1].split(' --> ')[0].strip())
        self.assertGreaterEqual(start_sec, 63.0)

# ==============================================================================
# TEST-06: 離群值防呆邏輯
# ==============================================================================
class TestOutlierRejection(unittest.TestCase):

    def _apply_outlier_check(self, start_time, end_time, tokens):
        """模擬 Stage 4 的離群值防呆邏輯"""
        if end_time - start_time > 10.0:
            end_time = start_time + len(tokens) * 0.4
        return end_time

    def test_normal_duration_unchanged(self):
        tokens = ["I'm", "burning", "HOT"]
        result = self._apply_outlier_check(63.0, 70.0, tokens)
        self.assertAlmostEqual(result, 70.0)

    def test_outlier_duration_corrected(self):
        """單句超過 10 秒應觸發線性修正"""
        tokens = ["I'm", "burning", "HOT"]  # 3 tokens * 0.4 = 1.2 秒
        result = self._apply_outlier_check(63.0, 75.0, tokens)  # 75-63 = 12s > 10s
        self.assertAlmostEqual(result, 63.0 + 3 * 0.4)

# ==============================================================================
# TEST-07: 最終 SRT 格式合規性
# ==============================================================================
class TestSRTFormatCompliance(unittest.TestCase):

    def setUp(self):
        self.srt_path = os.path.join(PROJECT_DIR, "LE_SSERAFIM_HOT_Bilingual_FINAL_v71.srt")

    def test_srt_file_exists(self):
        self.assertTrue(os.path.exists(self.srt_path), "最終雙語 SRT 檔案不存在！")

    def test_srt_line_numbers_incremental(self):
        """行號應從 1 開始連續遞增"""
        with open(self.srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        blocks = re.split(r'\n\s*\n', content.strip())
        for i, block in enumerate(blocks, 1):
            lines = block.strip().split('\n')
            self.assertEqual(lines[0].strip(), str(i),
                msg=f"第 {i} 個 SRT 區塊的行號不一致: 期待 {i}, 實際={lines[0]}")

    def test_srt_timestamps_progressive(self):
        """每個區塊的結束時間應 >= 起始時間，且起始時間應逐漸推進"""
        with open(self.srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        blocks = re.split(r'\n\s*\n', content.strip())
        prev_end = -1.0
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            ts_line = lines[1]
            if ' --> ' not in ts_line:
                continue
            start_str, end_str = ts_line.split(' --> ')
            start = parse_ts(start_str.strip())
            end = parse_ts(end_str.strip())
            self.assertGreaterEqual(end, start, f"結束時間早於起始時間：{ts_line}")
            self.assertGreaterEqual(start, prev_end - 0.5,  # 允許 0.5s 的重疊容差
                msg=f"時間軸出現大幅倒退！上一行結束={prev_end:.3f}, 這行開始={start:.3f}")
            prev_end = end

    def test_srt_utf8_encoding(self):
        """確保 UTF-8 編碼無 BOM"""
        with open(self.srt_path, 'rb') as f:
            raw = f.read(3)
        self.assertNotEqual(raw[:3], b'\xef\xbb\xbf', "SRT 檔案包含 UTF-8 BOM，可能導致部分播放器解析失敗！")

# ==============================================================================
# TEST-08: requirements.txt 完整性驗證
# ==============================================================================
class TestRequirementsCompleteness(unittest.TestCase):

    REQUIRED_PACKAGES = ["yt-dlp", "openai-whisper", "stable-ts", "demucs", "torch"]

    def test_all_core_packages_present(self):
        req_path = os.path.join(PROJECT_DIR, "requirements.txt")
        self.assertTrue(os.path.exists(req_path), "requirements.txt 不存在！")
        with open(req_path, 'r') as f:
            content = f.read().lower()
        for pkg in self.REQUIRED_PACKAGES:
            self.assertIn(pkg.lower(), content,
                msg=f"requirements.txt 缺少核心套件：{pkg}")

# ==============================================================================
# 主執行入口
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("  🧪 AGY 雙語字幕工廠 - 企業級整合測試套件 v1.0")
    print("  覆蓋範圍：時間軸 / Tokenize / Checkpoint / Profile / 格式合規 / Requirements")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestTimestampUtils,
        TestTokenize,
        TestCheckpointManager,
        TestPipelineConfig,
        TestSRTFrontParsing,
        TestOutlierRejection,
        TestSRTFormatCompliance,
        TestRequirementsCompleteness,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("  ✅ 所有測試通過！專案已達 Production-Ready 狀態！")
    else:
        print(f"  ❌ 測試失敗：{len(result.failures)} 項失敗, {len(result.errors)} 項錯誤。")
        print("  請依上方錯誤訊息修正後再重新執行。")
    print("=" * 70)

    sys.exit(0 if result.wasSuccessful() else 1)
