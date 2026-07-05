"""
企業級 Hybrid 對齊模組 (v8)

目前作為相容層，實際邏輯仍在 hybrid_v8_enterprise.py
未來可逐步將 EnterprisePipeline 完整搬遷到這裡。
"""

import sys
from pathlib import Path

# 確保能找到歷史的 hybrid_v8_enterprise.py
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from hybrid_v8_enterprise import (
        EnterprisePipeline,
        PipelineConfig,
        CheckpointManager,
        fmt_ts,
        parse_ts,
        tokenize,
    )
except ImportError:
    # 極端情況
    EnterprisePipeline = None
    PipelineConfig = None
    CheckpointManager = None
    fmt_ts = None
    parse_ts = None
    tokenize = None

__all__ = [
    "EnterprisePipeline",
    "PipelineConfig",
    "CheckpointManager",
]
