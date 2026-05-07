# -*- coding: utf-8 -*-
"""

Axiom 8: Causal - 悟道因果公理（v2.0）

定位：悟道元层
- 读取 wukong/wukong_causality 的 causal_log.jsonl
- 归纳 axiom1~7 之间的跨公理因果规律
- 向 AgentCore 提供约束参数调整建议

数据流：
  wukong_eye verify_all() → wukong_causality CausalLog.write()
    → axiom8 悟道因果读取日志 → 归纳 axiom 间因果律
      → AgentCore 约束参数调整建议

对比悟空因果（wukong_causality）：
  悟空因果：看像素眼输出的视觉特征（具体因果）
  悟道因果：归纳 axiom 间因果规律（元层因果）

"""




import sys as _sys
import os as _os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# ── 路径 setup（统一管理）───────────────────────────────────────────────────
_BR = Path(__file__).resolve().parent.parent          # wudao-core/
_WK = _BR.parent / "wukong"                           # wukong/
_WK_MEMORIAL = _WK / "memory"
_WK_MEMORIAL.mkdir(exist_ok=True)
_CAUSAL_LOG = str(_WK_MEMORIAL / "causal_log.jsonl")

# wukong/ 在 sys.path，wukong_causality 才能作为包被 import
_WK_STR = str(_WK)
if _WK_STR not in _sys.path:
    _sys.path.insert(0, _WK_STR)

try:
    from wukong_causality import (
        CausalLog, CausalSnapshot,
        CausalGraph, CausalComparator,
        correlation, permutation_test,
    )
    _HAS_INFRA = True
except ImportError:
    _HAS_INFRA = False

# axiom_verifier（wukong_eye）
_WK_EYE = str(_WK / "wukong_eye" / "core")
if _WK_EYE not in _sys.path:
    _sys.path.insert(0, _WK_EYE)
try:
    from axiom_verifier import verify_causal
    _HAS_VERIFIER = True
except ImportError:
    _HAS_VERIFIER = False

# ── axiom 名称映射（中文 → 英文 ID）────────────────────────────────────────
AXIOM_ID_MAP = {
    "叙事": "narrative", "色彩": "color", "生长": "growth",
    "布局": "layout", "光影": "light", "边界": "boundary",
    "自由": "freedom", "因果": "causal",
    "光影风格": "light_style",
    "axiom_叙事": "narrative", "axiom_色彩": "color",
    "axiom_生长": "growth", "axiom_布局": "layout",
    "axiom_光影": "light", "axiom_边界": "boundary",
    "axiom_自由": "freedom", "axiom_因果": "causal",
    "axiom_光影风格": "light_style",
    "narrative": "narrative", "color": "color", "growth": "growth",
    "layout": "layout", "light": "light", "boundary": "boundary",
    "freedom": "freedom", "causal": "causal",
    "light_style": "light_style",
}
AXIOM_NAMES = ["growth", "light", "color", "layout", "narrative", "boundary", "freedom", "light_style"]

# ── domain gate（来源：axiom_battle 全量对局战果 + gene_causal 跨界验证）────
# 视觉域 axiom8 被 axiom2(光影) 击穿(90.9%反向帧) → 视觉域降级到弱因果
# 基因域 3/5 ground truth 命中 + PC1 跨域同构 → 基因域保持强因果
# 详见 axiom_battle_constraints.json
DOMAIN_GATE: Dict[str, Dict[str, Any]] = {
    "visual": {
        "confidence_multiplier": 0.3,
        "max_law_type": "CAN",
        "correlation_threshold_multiplier": 2.0,
        "note": "视觉域: axiom_battle 90.9%反向帧 → 弱因果。edge_density→narrative已被处决(PIL噪声假相关)",
    },
    "gene": {
        "confidence_multiplier": 1.2,
        "max_law_type": "MUST",
        "correlation_threshold_multiplier": 0.7,
        "note": "基因域: gene_causal_proof 3/5 ground truth命中 + PC1跨域同构 → 强因果",
    },
    "auto": {
        "confidence_multiplier": 0.6,
        "max_law_type": "CAN",
        "correlation_threshold_multiplier": 1.2,
        "note": "未知域: 保守估计。待 causal_log 积累后升级为 domain 特定",
    },
}
DEFAULT_DOMAIN = "auto"


def _normalize(name: str) -> str:
    return AXIOM_ID_MAP.get(name, name)


# ── 中文名反向映射（用于从 rule_id 找 outputs 键）──────────────────────────
_AXIOM_CHINESE_REVERSE = {
    "narrative": "叙事",
    "color": "色彩",
    "growth": "生长",
    "layout": "布局",
    "light": "光影",
    "boundary": "边界",
    "freedom": "自由",
    "causal": "因果",
    "light_style": "光影风格",
}


def _score_from_event(ev: Dict) -> Optional[float]:
    """
    从 event 的 rule_id 反推 outputs 中 score 键的中文名，
    兼容多种命名格式：
      - 光影_score / 光影风格_score （中文 rule_id 场景）
      - axiom_光影 → 光影_score （axiom_ 前缀场景）
    """
    rule_id = ev.get("rule_id", "")
    outputs = ev.get("outputs", {})

    # 尝试直接找 generic "score"
    s = outputs.get("score")
    if s is not None:
        return s

    # 去掉 axiom_ 前缀
    base = rule_id.removeprefix("axiom_")

    # 直接当作中文名查
    key = base + "_score"
    s = outputs.get(key)
    if s is not None:
        return s

    # 通过 AXIOM_ID_MAP 反查英文→中文，再构造
    normalized = _normalize(rule_id)
    chinese = _AXIOM_CHINESE_REVERSE.get(normalized, normalized)
    key2 = chinese + "_score"
    s = outputs.get(key2)
    if s is not None:
        return s

    return None


# ── 核心类 ───────────────────────────────────────────────────────────────────

class CausalAxiom:
    """
    悟道因果公理（v2.1）

    元层能力：
    1. 读取悟空因果日志，构建 axiom 间因果图
    2. 归纳跨公理因果规律（MUST/CANNOT/CAN）
    3. 提供约束参数调整建议
    4. domain_gate: 视觉域→弱因果, 基因域→强因果 (v2.1 新增)

    execute() 返回值兼容 AxiomVerifier fusion 格式：
      {score, method, pass, detail, causal_links, axiom_influences}
    """

    __battle_status__ = "MODIFIED(最严重)"  # axiom_battle 全量对局: 视觉域被光影击穿90.9%

    def __init__(
        self,
        gpu_shader: Optional[str] = None,
        fallback_method: str = "rule_based",
        log_path: str = _CAUSAL_LOG,
        min_events: int = 3,
        domain: str = DEFAULT_DOMAIN,
    ):
        self.name = "causal"
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
        self.log_path = log_path
        self.min_events = min_events  # 最少事件数才构建图谱
        self.domain = domain  # 当前数据域: visual/gene/auto

        self._log: Optional["CausalLog"] = None
        self._graph: Optional["CausalGraph"] = None
        self._cache: Optional[List[Dict]] = None

    @property
    def _gate(self) -> Dict[str, Any]:
        """当前 domain 的门控参数"""
        return DOMAIN_GATE.get(self.domain, DOMAIN_GATE[DEFAULT_DOMAIN])

    # ── 懒加载 ───────────────────────────────────────────────────────────────

    @property
    def log(self) -> Optional["CausalLog"]:
        if not _HAS_INFRA:
            return None
        if self._log is None:
            self._log = CausalLog(path=self.log_path)
        return self._log

    @property
    def graph(self) -> Optional["CausalGraph"]:
        if not _HAS_INFRA:
            return None
        if self._graph is None:
            self._graph = CausalGraph()
            self._graph.build_from_log(self.log_path, sensitivity_threshold=0.05)
        return self._graph

    def _load(self) -> List[Dict]:
        """读取并缓存因果日志"""
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

    # ── axiom 间因果归纳（核心新增功能）──────────────────────────────────

    def _induce_axiom_laws(self, events: List[Dict]) -> Dict[str, Any]:
        """
        归纳 axiom 间因果规律

        对每个 axiom pair (A, B)：
        - 收集 A 的 score 序列和 B 的 score 序列
        - 计算相关系数
        - 置换检验 → 确认因果显著性
        - 分类为 MUST / CANNOT / CAN

        Returns:
          {
            "axiom_pairs": [{
              "cause": "growth", "effect": "layout",
              "correlation": 0.82, "p_value": 0.003,
              "is_causal": True, "law_type": "MUST",  # or CANNOT / CAN
              "evidence_count": 12
            }, ...],
            "must_laws": [...],    # 必须发生的因果链
            "cannot_laws": [...],  # 不可能发生的因果链
            "can_laws": [...],     # 可能发生的因果链
          }
        """
        # 收集每个 axiom 的 score 时间序列
        axiom_scores: Dict[str, List[float]] = {a: [] for a in AXIOM_NAMES}
        axiom_events: Dict[str, List[Dict]] = {a: [] for a in AXIOM_NAMES}

        for ev in events:
            rule_id = _normalize(ev.get("rule_id", ""))
            score = _score_from_event(ev)
            if rule_id in axiom_scores and score is not None:
                axiom_scores[rule_id].append(score)
                axiom_events[rule_id].append(ev)

        # 两两 axiom 计算因果关系
        pairs = []
        for cause in AXIOM_NAMES:
            for effect in AXIOM_NAMES:
                if cause == effect:
                    continue
                scores_c = axiom_scores.get(cause, [])
                scores_e = axiom_scores.get(effect, [])
                n = min(len(scores_c), len(scores_e))
                if n < 2:
                    continue

                pairs_list = list(zip(scores_c[-20:], scores_e[-20:]))  # 最多20条
                corr = correlation(pairs_list)
                if corr < 0.05:  # 不相关就跳过
                    continue

                p_result = permutation_test(pairs_list, n_permutations=500, significance=0.05)
                p_val = p_result.get("p_value", 1.0)
                is_causal = p_result.get("is_causal", False)

                # 分类
                if is_causal and abs(corr) >= 0.6:
                    law_type = "MUST"
                elif is_causal and abs(corr) < 0.3:
                    law_type = "CANNOT"
                elif is_causal:
                    law_type = "CAN"
                else:
                    law_type = "CORRELATION"  # 仅相关，非因果

                pairs.append({
                    "cause": cause,
                    "effect": effect,
                    "correlation": round(corr, 4),
                    "p_value": round(p_val, 4),
                    "is_causal": is_causal,
                    "law_type": law_type,
                    "evidence_count": n,
                    "direction": "positive" if corr > 0 else "negative",
                })

        # 分类
        must = [p for p in pairs if p["law_type"] == "MUST"]
        cannot = [p for p in pairs if p["law_type"] == "CANNOT"]
        can = [p for p in pairs if p["law_type"] == "CAN"]
        correlation_only = [p for p in pairs if p["law_type"] == "CORRELATION"]

        return {
            "axiom_pairs": pairs,
            "must_laws": must,
            "cannot_laws": cannot,
            "can_laws": can,
            "correlation_only": correlation_only,
        }

    def _causal_path_analysis(self, events: List[Dict]) -> Dict[str, Any]:
        """
        因果路径分析：给定低分 axiom，追溯根因

        场景：axiom8 收到 "growth 分数低" 的反馈
        → 查日志：之前 growth 分数低时，哪些其他 axiom 同时也低？
        → 找到传导链：light → growth（光影差导致生长构图弱）
        """
        axiom_scores = {a: [] for a in AXIOM_NAMES}
        for ev in events:
            rid = _normalize(ev.get("rule_id", ""))
            sc = _score_from_event(ev)
            if rid in axiom_scores and sc is not None:
                axiom_scores[rid].append(sc)

        paths = []
        for cause in AXIOM_NAMES:
            for effect in AXIOM_NAMES:
                if cause == effect:
                    continue
                sc = axiom_scores.get(cause, [])
                se = axiom_scores.get(effect, [])
                n = min(len(sc), len(se))
                if n < 2:
                    continue
                pairs_list = list(zip(sc[-20:], se[-20:]))
                corr = correlation(pairs_list)
                if abs(corr) >= 0.4 and permutation_test(pairs_list, 200, 0.05).get("is_causal"):
                    paths.append({
                        "from": cause, "to": effect,
                        "strength": round(abs(corr), 3),
                        "direction": "positive" if corr > 0 else "negative",
                        "evidence": n,
                    })

        return {"causal_paths": paths}

    # ── axiom 接口 ───────────────────────────────────────────────────────────

    def validate(self, data: dict) -> bool:
        """
        悟道因果不验证具体数据，只检查是否有日志文件。
        无日志时返回 True（允许冷启动）。
        """
        return True

    def compute(self, data: dict, state: Any) -> dict:
        """
        悟道因果计算

        输入 data（可选）：
          - target_axiom: str，指定要分析的目标公理
          - context_scores: Dict[axiom, score]，当前各公理分数
          - focus_law: str，聚焦的因果律类型（MUST/CANNOT/CAN）

        输出：
          - axiom_laws: 归纳出的 axiom 间因果律
          - causal_paths: 因果路径分析
          - suggestions: 约束参数调整建议
          - global_sensitivity: 全局因果强度
          - has_enough_data: 日志数据是否足够
        """
        events = self._load()
        n = len(events)

        # 按 axiom 分组事件
        axiom_events: Dict[str, List[Dict]] = {a: [] for a in AXIOM_NAMES}
        for ev in events:
            rid = _normalize(ev.get("rule_id", ""))
            if rid in axiom_events:
                axiom_events[rid].append(ev)

        # 归纳 axiom 间因果律
        law_result = self._induce_axiom_laws(events)
        path_result = self._causal_path_analysis(events)

        # domain gate v2.1: 根据当前域调整因果可信度
        effective_domain = data.get("domain", self.domain)
        self.domain = effective_domain  # 更新（可能从 data 传入）
        law_result = self._apply_domain_gate(law_result)

        # 构建建议
        suggestions = self._build_suggestions(law_result, data.get("context_scores", {}))

        # 全局敏感度：所有 MUST 律的平均强度
        must_laws = law_result["must_laws"]
        global_sens = (
            sum(abs(p["correlation"]) for p in must_laws) / len(must_laws)
            if must_laws else 0.0
        )

        # 统计覆盖的 axiom
        covered = [a for a in AXIOM_NAMES if axiom_events[a]]

        return {
            "status": "computed",
            "event_count": n,
            "covered_axioms": covered,
            "has_enough_data": n >= self.min_events,
            "axiom_laws": law_result,
            "causal_paths": path_result,
            "suggestions": suggestions,
            "global_sensitivity": round(global_sens * self._gate["confidence_multiplier"], 4),
            "must_count": len(must_laws),
            "cannot_count": len(law_result["cannot_laws"]),
            "can_count": len(law_result["can_laws"]),
            "law_type": law_result["_effective_law_type"],
            "domain": effective_domain,
            "domain_gate_active": effective_domain != DEFAULT_DOMAIN,
        }

    def _apply_domain_gate(self, law_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        domain gate v2.1: 根据当前域降级/升级因果律类型

        规则：
        - visual 域: MUST → CAN, CANNOT → CAN (90.9%反向帧，因果不可信)
        - gene 域: 保持原判 (3/5 ground truth 命中)
        - auto 域: MUST → CAN (保守降级)
        """
        gate = self._gate
        max_law = gate["max_law_type"]
        law_type_rank = {"CORRELATION": 0, "CANNOT": 1, "CAN": 2, "MUST": 3}
        max_rank = law_type_rank.get(max_law, 2)

        # 降级超限的 law_type
        for key in ["axiom_pairs", "must_laws", "cannot_laws", "can_laws"]:
            pairs = law_result.get(key, [])
            for p in pairs:
                current_rank = law_type_rank.get(p.get("law_type", "CAN"), 0)
                if current_rank > max_rank:
                    # 降级: MUST→CAN, CANNOT→CAN
                    p["law_type_original"] = p["law_type"]
                    p["law_type"] = max_law
                    p["domain_gate_applied"] = True

        # 重新分类
        all_pairs = law_result.get("axiom_pairs", [])
        law_result["must_laws"] = [p for p in all_pairs if p.get("law_type") == "MUST"]
        law_result["cannot_laws"] = [p for p in all_pairs if p.get("law_type") == "CANNOT"]
        law_result["can_laws"] = [p for p in all_pairs if p.get("law_type") == "CAN"]
        law_result["correlation_only"] = [p for p in all_pairs if p.get("law_type") == "CORRELATION"]

        # 决定 effective_law_type
        if law_result["must_laws"]:
            effective = "MUST"
        elif law_result["can_laws"]:
            effective = "CAN"
        elif law_result["correlation_only"]:
            effective = "CORRELATION"
        else:
            effective = "NONE"
        law_result["_effective_law_type"] = effective
        law_result["_domain_gate"] = {"domain": self.domain, "max_law_type": max_law}

        return law_result

    def _build_suggestions(
        self, law_result: Dict, context_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        基于归纳出的因果律，为 AgentCore 生成约束参数调整建议

        规则：
        - MUST 律：上游 axiom 调整 → 下游 axiom 被动跟随
          → 建议"优先调整上游"（干预效率更高）
        - CANNOT 律：某些组合不可能同时发生
          → 建议"避免同时优化这两个 axiom"
        - CAN 律：存在可行路径
          → 给出具体参数调整方向
        """
        suggestions = []
        target = context_scores.get("target") if context_scores else None

        for law in law_result["must_laws"]:
            suggestions.append({
                "type": "MUST",
                "from": law["cause"],
                "to": law["effect"],
                "correlation": law["correlation"],
                "direction": law["direction"],
                "advice": (
                    f"优先优化「{law['cause']}」（因果上游），"
                    f"「{law['effect']}」将被动改善"
                    if law["direction"] == "positive" else
                    f"「{law['cause']}」与「{law['effect']}」负相关，"
                    f"需权衡"
                ),
            })

        for law in law_result["cannot_laws"]:
            suggestions.append({
                "type": "CANNOT",
                "axiom_a": law["cause"],
                "axiom_b": law["effect"],
                "correlation": law["correlation"],
                "advice": (
                    f"「{law['cause']}」与「{law['effect']}」难以同时优化，"
                    f"建议分阶段处理"
                ),
            })

        for law in law_result["can_laws"]:
            suggestions.append({
                "type": "CAN",
                "from": law["cause"],
                "to": law["effect"],
                "correlation": law["correlation"],
                "advice": (
                    f"「{law['cause']}」可作为「{law['effect']}」的优化路径之一"
                ),
            })

        return suggestions

    def render(self, result: dict) -> dict:
        """
        渲染为 AxiomVerifier fusion 兼容格式

        score 语义（v2.1 domain gate 调整后）：
          1.0 = 有强 MUST 律（因果可信）→ 仅基因域可达
          0.4-0.8 = 有 CAN 律（弱因果）→ 视觉域上限
          0.2-0.4 = 仅相关，无因果
          0.0-0.2 = 数据不足（冷启动）
        
        domain gate: score *= confidence_multiplier
          - visual: ×0.3 (90.9%反向帧, 弱因果)
          - gene:   ×1.2 (3/5 ground truth, 强因果)
          - auto:   ×0.6 (保守)
        """
        must_n = result.get("must_count", 0)
        can_n = result.get("can_count", 0)
        corr_n = len(result.get("axiom_laws", {}).get("correlation_only", []))
        events = result.get("event_count", 0)
        has_data = result.get("has_enough_data", False)
        domain_tag = result.get("domain", self.domain)

        # 获取 domain gate
        gate = self._gate
        domain_note = gate["note"]

        if not has_data or events == 0:
            score = 0.1
            method = "cold_start"
            detail = "因果日志数据不足，等待积累"
            law_type = "COLD"
        elif must_n > 0:
            score = min(1.0, 0.7 + 0.1 * min(must_n, 3))
            method = f"must_laws({must_n})"
            detail = f"发现 {must_n} 条 MUST 因果律，全局敏感度={result.get('global_sensitivity', 0)}"
            law_type = result.get("law_type", "MUST")
        elif can_n > 0:
            score = min(0.8, 0.4 + 0.1 * min(can_n, 4))
            method = f"can_laws({can_n})"
            detail = f"发现 {can_n} 条 CAN 因果律"
            law_type = "CAN"
        elif corr_n > 0:
            score = 0.35
            method = f"correlation_only({corr_n})"
            detail = f"发现 {corr_n} 条相关关系（未通过因果检验）"
            law_type = "CORRELATION"
        else:
            score = 0.2
            method = "no_pattern"
            detail = " axiom 间无显著因果模式"
            law_type = "NONE"

        # domain gate v2.1: 调整最终分数
        domain_mult = gate["confidence_multiplier"]
        score_raw = score
        score = min(1.0, score * domain_mult)
        pass_threshold = 0.5 * (1.0 if domain_mult >= 1.0 else domain_mult)
        # visual域 pass_threshold=0.15, gene域=0.5, auto域=0.3

        suggestions = result.get("suggestions", [])
        top_advice = suggestions[0]["advice"] if suggestions else detail

        return {
            "score": round(score, 4),
            "score_raw": round(score_raw, 4),
            "domain_multiplier": domain_mult,
            "method": f"{method}[{domain_tag}]",
            "pass": score >= pass_threshold,
            "detail": top_advice,
            "law_type": law_type,
            "domain": domain_tag,
            "domain_note": domain_note,
            "event_count": events,
            "must_count": must_n,
            "can_count": can_n,
            "cannot_count": result.get("cannot_count", 0),
            "global_sensitivity": result.get("global_sensitivity", 0),
            "suggestions": suggestions,
            "axiom_laws_summary": self._summarize_laws(result.get("axiom_laws", {})),
            "status": "rendered",
        }

    def _summarize_laws(self, laws: Dict) -> str:
        parts = []
        for m in laws.get("must_laws", [])[:3]:
            parts.append(
                f"MUST:{m['cause']}→{m['effect']}"
                f"({m['correlation']:.2f})"
            )
        for c in laws.get("can_laws", [])[:3]:
            parts.append(
                f"CAN:{c['cause']}→{c['effect']}"
                f"({c['correlation']:.2f})"
            )
        return " | ".join(parts) if parts else "no_laws"

    def execute(self, task: Any, state: Any = None) -> dict:
        """统一执行入口"""
        data = task.data if hasattr(task, "data") else (task or {})
        if not self.validate(data):
            from core.error_handler import ValidationError
            raise ValidationError(f"[{self.name}] Validation failed")
        result = self.compute(data, state)
        return self.render(result)

    # ── 辅助方法 ─────────────────────────────────────────────────────────────

    def get_causal_path(self, cause_axiom: str, effect_axiom: str) -> List[str]:
        """
        查找两个 axiom 之间的因果路径
        使用 BFS 在归纳出的因果律中搜索
        """
        events = self._load()
        laws = self._induce_axiom_laws(events)
        law_map: Dict[str, List[str]] = defaultdict(list)
        for p in laws["must_laws"] + laws["can_laws"]:
            if p["direction"] == "positive":
                law_map[p["cause"]].append(p["effect"])

        visited = set()
        queue = [(cause_axiom, [cause_axiom])]
        while queue:
            node, path = queue.pop(0)
            if node == effect_axiom:
                return path
            if node in visited:
                continue
            visited.add(node)
            for nxt in law_map.get(node, []):
                if nxt not in visited:
                    queue.append((nxt, path + [nxt]))
        return []

    def trace_low_score(
        self, low_axiom: str, events: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        追溯某个低分 axiom 的根因

        场景：growth 分数低
        → 查之前 growth 低时，哪些 axiom 同时也低？
        → 找到传导源头
        """
        evs = events or self._load()
        laws = self._induce_axiom_laws(evs)

        # 找所有指向 low_axiom 的 MUST/CAN 律
        incoming = [
            p for p in laws["must_laws"] + laws["can_laws"]
            if p["effect"] == low_axiom
        ]
        incoming.sort(key=lambda x: -abs(x["correlation"]))

        if not incoming:
            return {
                "low_axiom": low_axiom,
                "root_causes": [],
                "conclusion": f"{low_axiom} 无上游因果律，可能为独立因素导致",
            }

        roots = [
            {
                "cause": p["cause"],
                "correlation": p["correlation"],
                "strength": abs(p["correlation"]),
                "type": p["law_type"],
            }
            for p in incoming
        ]
        top = roots[0]
        return {
            "low_axiom": low_axiom,
            "root_causes": roots,
            "conclusion": (
                f"「{low_axiom}」低分很可能由「{top['cause']}」传导引起"
                f"（相关系数={top['correlation']:.2f}，类型={top['type']}），"
                f"建议优先优化上游「{top['cause']}」"
            ),
        }

    def score_from_features(self, features: dict) -> dict:
        """
        逆向：图像特征 → 因果公理分数（区域对比 + 连通性）
        
        调用 axiom_verifier.verify_causal() ，
        综合区域标准差 + Sobel 连通性 + 泛化性。
        """
        arr = features.get('arr')
        if arr is None:
            return {'score': 0.5, 'method': 'causal_fallback', 'details': {}}
        if not _HAS_VERIFIER:
            return {'score': 0.5, 'method': 'causal_fallback', 'details': {'reason': 'axiom_verifier not available'}}
        result = verify_causal(arr)
        return {
            'score': float(result.get('score', 0.5)),
            'method': 'verify_causal',
            'region_score': result.get('region_score', 0),
            'connectivity_score': result.get('connectivity_score', 0),
            'generality_score': result.get('generality_score', 0),
            'source': 'wudao_core_causal_v2'
        }

    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "gpu_shader": self.gpu_shader,
            "fallback_method": self.fallback_method,
            "log_path": self.log_path,
            "min_events": self.min_events,
            "has_infrastructure": _HAS_INFRA,
            "version": "2.0",
        }
