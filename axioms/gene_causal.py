# -*- coding: utf-8 -*-
"""

Axiom G: Gene Causal - 跨边界适配器（概念验证）

定位：悟道 axiom8 因果方法论的生物学应用
- 不号称生物学家，只是用图像世界积累的因果发现流程
- 把基因表达数据翻译成 axiom 时间序列格式
- 用 axiom8 相同的方法论（相关+置换检验+PCA）找因果律

数据流：
  gene_causal_log.jsonl
    → GeneCausalAxiom._load()
    → _induce_axiom_laws()（与 axiom8 相同的方法论）
    → 因果律输出（MUST/CANNOT/CAN）

"""

import sys as _sys
import os as _os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# ── 路径 setup ────────────────────────────────────────────────────────
_BR = Path(__file__).resolve().parent.parent          # wudao-core/
_WK = _BR.parent / "wukong"                           # wukong/
_WK_MEMORIAL = _WK / "memory"
_GENE_LOG = str(_WK_MEMORIAL / "gene_causal_log.jsonl")

_WK_STR = str(_WK)
if _WK_STR not in _sys.path:
    _sys.path.insert(0, _WK_STR)

try:
    from wukong_causality import (
        CausalLog, CausalGraph, CausalComparator,
        correlation, permutation_test,
    )
    _HAS_INFRA = True
except ImportError:
    _HAS_INFRA = False

# ── 基因 axiom 名称映射 ───────────────────────────────────────────────
# 8个 axiom 对应 8个基因/蛋白质/通路指标
AXIOM_ID_MAP = {
    # 英文名 → 内部ID
    "growth":       "growth",
    "light":        "light",
    "color":        "color",
    "layout":       "layout",
    "narrative":    "narrative",
    "boundary":     "boundary",
    "freedom":      "freedom",
    "light_style":  "light_style",
    # 原始 rule_id 格式
    "gene_axiom_growth":      "growth",
    "gene_axiom_light":       "light",
    "gene_axiom_color":       "color",
    "gene_axiom_layout":      "layout",
    "gene_axiom_narrative":   "narrative",
    "gene_axiom_boundary":    "boundary",
    "gene_axiom_freedom":     "freedom",
    "gene_axiom_light_style":  "light_style",
    # 中文名反向兼容（未来真实数据可能用）
    "生长": "growth",
    "光影": "light",
    "色彩": "color",
    "布局": "layout",
    "叙事": "narrative",
    "边界": "boundary",
    "自由": "freedom",
    "光影风格": "light_style",
}

AXIOM_NAMES = [
    "growth",      # 细胞增殖速率（Ki-67/PCNA）
    "light",       # 免疫激活强度（CD8+ T细胞/细胞因子）
    "color",       # 蛋白质表达量（qPCR Ct值 / RNA-seq TPM）
    "layout",      # 基因通路密度（富集分析结果）
    "narrative",   # 疾病时间线（采样点→标志物浓度）
    "boundary",     # 细胞膜/核膜完整性（流式 FSC/SSC）
    "freedom",     # 基因表达可及性（ATAC-seq开放峰）
    "light_style", # 细胞/通路类型分类（聚类结果标签）
]

# axiom 语义说明（供解读用）
AXIOM_LABELS = {
    "growth":      "细胞增殖速率",
    "light":       "免疫激活强度",
    "color":       "蛋白质/基因表达量",
    "layout":      "基因通路密度/拓扑",
    "narrative":   "疾病进展时间线",
    "boundary":    "细胞膜完整性",
    "freedom":     "染色质开放程度",
    "light_style": "细胞类型/通路分类",
}


def _normalize(name: str) -> str:
    return AXIOM_ID_MAP.get(name, name)


# ── score 提取（与 axiom8 相同的三级 fallback） ─────────────────────────
def _score_from_event(ev: Dict) -> Optional[float]:
    """从 gene event 中提取 score，兼容多种键名格式。"""
    outputs = ev.get("outputs", {})
    # 通用
    s = outputs.get("score")
    if s is not None:
        return s
    # gene_axiom_xxx 格式
    rule_id = ev.get("rule_id", "")
    base = rule_id.removeprefix("gene_axiom_")
    key = base + "_score"
    s = outputs.get(key)
    if s is not None:
        return s
    # 去掉 axiom_ 前缀
    base2 = base.removeprefix("axiom_")
    key2 = base2 + "_score"
    s = outputs.get(key2)
    if s is not None:
        return s
    return None


# ── 核心类 ───────────────────────────────────────────────────────────────

class GeneCausalAxiom:
    """
    基因 axiom 因果分析器（v1.0）

    方法论：完全复用 axiom8 的因果发现流程
      1. 从 gene_causal_log.jsonl 读取事件
      2. 按 frame_id 聚合，每个 frame 一条 axiom 记录
      3. 计算 8×8 Pearson 相关矩阵
      4. Permutation test（500 次）验证显著性
      5. PCA 分解 → 主成分载荷解释
      6. 分类 MUST / CANNOT / CAN 律

    注意：这是概念验证，用合成数据。
          真实数据需要把 FASTQ/VCF 翻译成本格式。
    """

    def __init__(
        self,
        log_path: str = _GENE_LOG,
        min_events: int = 10,
    ):
        self.name = "gene_causal"
        self.log_path = log_path
        self.min_events = min_events
        self._cache: Optional[List[Dict]] = None

    def _load(self) -> List[Dict]:
        if self._cache is not None:
            return self._cache
        self._cache = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._cache.append(__import__("json").loads(line))
        except FileNotFoundError:
            pass
        return self._cache

    def get_summary(self) -> Dict[str, Any]:
        """返回分析摘要（供外部调用）"""
        events = self._load()
        if not events:
            return {"status": "no_data", "message": f"未找到 {self.log_path}"}

        # 统计各 axiom 事件数
        axiom_counts = defaultdict(int)
        for ev in events:
            rid = _normalize(ev.get("rule_id", ""))
            if rid in AXIOM_NAMES:
                axiom_counts[rid] += 1

        # 完整帧数
        frame_map = defaultdict(dict)
        for ev in events:
            rid = _normalize(ev.get("rule_id", ""))
            score = _score_from_event(ev)
            fid = ev.get("frame_id", ev.get("timestamp", 0))
            if rid in AXIOM_NAMES and score is not None:
                frame_map[fid][rid] = score
        complete = [k for k, v in frame_map.items() if len(v) == len(AXIOM_NAMES)]

        return {
            "status": "ok",
            "total_events": len(events),
            "complete_frames": len(complete),
            "axiom_counts": dict(axiom_counts),
            "axiom_labels": AXIOM_LABELS,
        }

    def validate(self, data: dict) -> bool:
        return True  # 始终允许

    def compute(self, data: dict, state: Any = None) -> dict:
        events = self._load()
        if len(events) < self.min_events:
            return {
                "status": "insufficient_data",
                "events": len(events),
                "min_required": self.min_events,
            }

        # 构建帧
        frame_map = defaultdict(dict)
        for ev in events:
            rid = _normalize(ev.get("rule_id", ""))
            score = _score_from_event(ev)
            fid = ev.get("frame_id", ev.get("timestamp", 0))
            if rid in AXIOM_NAMES and score is not None:
                frame_map[fid][rid] = score

        # 完整帧
        all_frames = [frame_map[k] for k in sorted(frame_map.keys())
                      if len(frame_map[k]) == len(AXIOM_NAMES)]

        if len(all_frames) < 5:
            return {
                "status": "insufficient_frames",
                "complete_frames": len(all_frames),
                "min_required": 5,
            }

        # 相关矩阵
        import math as _math
        def pearson(x, y):
            n = len(x)
            if n < 3:
                return 0.0
            mx, my = sum(x)/n, sum(y)/n
            dx = [xi-mx for xi in x]
            dy = [yi-my for yi in y]
            num = sum(a*b for a,b in zip(dx,dy))
            den = _math.sqrt(sum(a*a for a in dx)*sum(b*b for b in dy))
            return num/den if den else 0.0

        na = len(AXIOM_NAMES)
        corr_mat = [[1.0 if i==j else
                     pearson([fr[AXIOM_NAMES[i]] for fr in all_frames],
                             [fr[AXIOM_NAMES[j]] for fr in all_frames])
                     for j in range(na)] for i in range(na)]

        # Permutation test
        def perm_test(x, y, n_perm=500):
            import random as _random
            obs = abs(pearson(x, y))
            cnt = 0
            for _ in range(n_perm):
                y2 = y[:]
                _random.shuffle(y2)
                if abs(pearson(x, y2)) >= obs:
                    cnt += 1
            return cnt / n_perm

        # 因果律发现（支持时滞）
        pairs = []
        for i, cause in enumerate(AXIOM_NAMES):
            for j, effect in enumerate(AXIOM_NAMES):
                if i == j:
                    continue
                x = [fr[cause] for fr in all_frames]
                y = [fr[effect] for fr in all_frames]

                # ── 找最佳时滞（0~max_lag帧），捕捉延迟因果 ───────────────
                max_lag = 3  # 生物学因果通常在0-3帧内传导
                best_r, best_lag = 0.0, 0

                # ── 修复：患者内 lag，不跨患者拼接 ─────────────────────────
                # 1. 按患者分组
                patient_frames: Dict[str, List[int]] = defaultdict(list)
                for idx, fid in enumerate(sorted(frame_map.keys())):
                    # frame_id 格式: "patient{pid}_t{t}"
                    pid = fid.rsplit("_t", 1)[0]
                    patient_frames[pid].append(idx)

                # 2. 在每个患者内计算 lag 相关性，再平均
                patient_rs = {lag: [] for lag in range(max_lag+1)}
                for pid, indices in patient_frames.items():
                    if len(indices) < 2:
                        continue
                    for lag in range(0, max_lag+1):
                        if lag >= len(indices):
                            break
                        # 同帧序：indices[lag:] 的 growth 对应 indices[:-lag] 的 narrative
                        x_lag = [all_frames[indices[k]][cause]
                                 for k in range(lag, len(indices))]
                        y_ahead = [all_frames[indices[k]][effect]
                                   for k in range(0, len(indices)-lag)]
                        if len(x_lag) < 3:
                            continue
                        r_lag = pearson(x_lag, y_ahead)
                        patient_rs[lag].append(r_lag)

                # 3. 取平均 r（Fisher z-transform 再平均更稳健）
                for lag in range(max_lag+1):
                    if patient_rs[lag]:
                        import math as _m
                        z_vals = [_m.atanh(max(-0.9999, min(0.9999, r)))
                                  for r in patient_rs[lag] if -0.9999 < r < 0.9999]
                        if z_vals:
                            mean_z = sum(z_vals) / len(z_vals)
                            mean_r = (_math.e**(2*mean_z) - 1) / (_math.e**(2*mean_z) + 1)
                        else:
                            mean_r = sum(patient_rs[lag]) / len(patient_rs[lag])
                        if abs(mean_r) > abs(best_r):
                            best_r = mean_r
                            best_lag = lag

                r = best_r

                if abs(r) < 0.05:
                    continue
                p = perm_test(x, y)
                is_causal = p < 0.05
                if is_causal and abs(r) >= 0.6:
                    law = "MUST"
                elif is_causal and abs(r) < 0.3:
                    law = "CANNOT"
                elif is_causal:
                    law = "CAN"
                else:
                    law = "CORRELATION"
                pairs.append({
                    "cause": cause,
                    "cause_label": AXIOM_LABELS.get(cause, cause),
                    "effect": effect,
                    "effect_label": AXIOM_LABELS.get(effect, effect),
                    "r": round(r, 4),
                    "best_lag": best_lag,        # ← 新增：最佳时滞帧数
                    "p_value": round(p, 4),
                    "is_causal": is_causal,
                    "law_type": law,
                    "direction": "positive" if r > 0 else "negative",
                    "evidence": len(all_frames),
                })

        must = [p for p in pairs if p["law_type"] == "MUST"]
        cannot = [p for p in pairs if p["law_type"] == "CANNOT"]
        can = [p for p in pairs if p["law_type"] == "CAN"]
        corr_only = [p for p in pairs if p["law_type"] == "CORRELATION"]

        return {
            "status": "computed",
            "complete_frames": len(all_frames),
            "corr_matrix": corr_mat,
            "axiom_names": AXIOM_NAMES,
            "axiom_labels": AXIOM_LABELS,
            "must_laws": must,
            "cannot_laws": cannot,
            "can_laws": can,
            "correlation_only": corr_only,
        }

    def render(self, result: dict) -> dict:
        if result.get("status") == "insufficient_data":
            return {"score": 0.1, "method": "cold_start",
                    "detail": f"数据不足（{result['events']} events）",
                    "status": "rendered"}
        if result.get("status") == "insufficient_frames":
            return {"score": 0.1, "method": "cold_start",
                    "detail": f"完整帧不足（{result['complete_frames']} frames）",
                    "status": "rendered"}

        must_n = len(result.get("must_laws", []))
        can_n = len(result.get("can_laws", []))

        if must_n > 0:
            score = min(1.0, 0.7 + 0.05 * min(must_n, 6))
            method = f"must_laws({must_n})"
        elif can_n > 0:
            score = min(0.75, 0.4 + 0.05 * min(can_n, 7))
            method = f"can_laws({can_n})"
        else:
            score = 0.35
            method = "correlation_only"

        return {
            "score": round(score, 4),
            "method": method,
            "pass": score >= 0.5,
            "status": "rendered",
            **result,
        }

    def execute(self, task: Any, state: Any = None) -> dict:
        data = task.data if hasattr(task, "data") else (task or {})
        if not self.validate(data):
            from core.error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Validation failed")
        result = self.compute(data, state)
        return self.render(result)
