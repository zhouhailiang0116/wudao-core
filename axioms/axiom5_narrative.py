# -*- coding: utf-8 -*-
"""
axiom5_narrative.py — 叙事公理
================================

状态：✅ 更新（2026-04-19）— 新增 score_from_features() 接入 axiom_verifier

Hook → Body → Climax → CTA 四段叙事结构验证与生成。

公理接口（AxiomBase）：
  validate(data)           → 检查叙事结构是否完整
  compute(data, state)     → 生成/分析叙事内容
  render(result)           → 输出结构化结果
  score_from_features()   → 图像特征 → 叙事分数（新增，接入 axiom_verifier）

两种方向：
  compute()   → 正向：场景描述 → 叙事内容（已有）
  score_from_features() → 逆向：像素特征 → 叙事分数（新增）
"""

import sys as _sys
import os as _os
from pathlib import Path
from typing import List, Dict

# ── wukong_poster 叙事引擎（正向计算用）─────────────────────────────
_WK_POSTER = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_poster")
if _WK_POSTER not in _sys.path:
    _sys.path.insert(0, _WK_POSTER)

try:
    from core.narrative import HookGenerator, BodyBuilder, CTAGenerator, NarrativeGenerator
    _HAS_NARRATIVE_ENGINE = True
except ImportError:
    _HAS_NARRATIVE_ENGINE = False

# ── narrative_v1_5（逆向评分用）—— axiom_verifier 的计算核心 ──────
_WK_EYE_CORE = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_eye" / "core")
if _WK_EYE_CORE not in _sys.path:
    _sys.path.insert(0, _WK_EYE_CORE)

try:
    from narrative_v1_5 import verify_narrative_v1_5 as _verify_narrative
    _HAS_V15 = True
except ImportError:
    _HAS_V15 = False

# ── axiom_math_bridges（信息熵分析）─────────────────────────────
_WK_MATH = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_math-theory")
if _WK_MATH not in _sys.path:
    _sys.path.insert(0, _WK_MATH)

try:
    from axiom_math_bridges import NarrativeEntropyBridge
    _HAS_ENTROPY_BRIDGE = True
except ImportError:
    _HAS_ENTROPY_BRIDGE = False

from .axiom_base import AxiomBase


class NarrativeAxiom(AxiomBase):
    """
    叙事公理

    约束规则：
      1. Hook 必须在首句（痛点/反常识/数字/疑问）
      2. Body 至少 2 句递进内容
      3. Climax（高潮）可选，用于情绪峰值
      4. CTA 必须有明确行动指向（→ 开头）
      5. 总字数不超过 limit（默认280字）

    叙事质量评分（正向）：
      - 结构完整 +0.3
      - Hook 有力 +0.2
      - 递进有效 +0.2
      - CTA 明确 +0.2
      - 字数控制 +0.1

    叙事分数（逆向 / score_from_features）：
      调用 narrative_v1_5.verify_narrative_v1_5() ，
      综合 spatial_variance + gradient_score + focal_score + entropy
    """

    def __init__(self, gpu_shader=None, fallback_method='auto'):
        self.name = "NarrativeAxiom"
        self.version = "2.0"  # v2.0 = 新增 score_from_features
        self.gpu_shader = gpu_shader
        self.fallback_method = fallback_method
        self._hook_gen = HookGenerator() if _HAS_NARRATIVE_ENGINE else None
        self._cta_gen = CTAGenerator() if _HAS_NARRATIVE_ENGINE else None
        self._narrative_gen = NarrativeGenerator() if _HAS_NARRATIVE_ENGINE else None

    # ═══════════════════════════════════════════════════════════════════
    #  接口：正向（场景 → 叙事内容）
    # ═══════════════════════════════════════════════════════════════════

    def validate(self, data: dict) -> bool:
        """验证叙事输入结构"""
        if not isinstance(data, dict):
            return False
        if "topic" not in data and "content" not in data:
            return False
        limit = data.get("limit", 280)
        if "content" in data and len(data["content"]) > limit:
            return False
        return True

    def compute(self, data: dict, state) -> dict:
        """计算叙事结构（正向：场景描述 → 叙事内容）"""
        topic = data.get("topic", "通用话题")
        hook_type = data.get("hook_type", "counter")
        num_body = data.get("num_body_lines", 3)
        limit = data.get("limit", 280)
        existing_content = data.get("content", "")

        if existing_content:
            return self._analyze_content(existing_content)

        if not _HAS_NARRATIVE_ENGINE:
            return self._compute_fallback(topic, hook_type, num_body)

        hook = self._hook_gen.generate(
            hook_type=hook_type,
            topic=topic,
        )

        body_points = [
            "这不是能力问题，是认知问题。",
            "打破旧框架，才能建立新体系。",
            "每一步都在积累，直到临界点爆发。"
        ][:num_body]

        cta = self._cta_gen.generate(topic=topic)

        lines = [hook] + body_points + [cta]
        full_text = "\n".join(lines)
        total_chars = len(full_text)
        score = self._score_narrative(hook, body_points, cta, total_chars, limit)

        # 构造叙事段落列表（供信息熵分析用）
        narrative_segments = [
            {"text": hook, "role": "hook"},
            *[{"text": p, "role": "body"} for p in body_points],
            {"text": cta, "role": "cta"},
        ]

        return {
            "hook": hook,
            "hook_type": hook_type,
            "body_points": body_points,
            "body_count": len(body_points),
            "cta": cta,
            "full_text": full_text,
            "total_chars": total_chars,
            "limit": limit,
            "within_limit": total_chars <= limit,
            "score": score,
            "score_breakdown": {
                "structure": 0.3 if len(body_points) >= 2 else 0.0,
                "hook": 0.2 if len(hook) > 5 else 0.0,
                "progression": 0.2 if len(body_points) >= 3 else 0.1,
                "cta": 0.2 if cta.startswith("→") else 0.0,
                "limit": 0.1 if total_chars <= limit else 0.0
            },
            "climax": body_points[-1] if body_points else "",
            "status": "success",
            # 信息熵分析（Narrative-Entropy Bridge）
            **self._compute_entropy_analysis(narrative_segments),
        }

    def render(self, result: dict) -> dict:
        """渲染叙事结果"""
        if result.get("status") != "success":
            return {"status": "error", "message": "compute 未成功"}

        output_lines = [
            f"【Hook】{result['hook']}",
            f"【Body】"
        ]
        for i, point in enumerate(result.get("body_points", []), 1):
            output_lines.append(f"  {i}. {point}")
        output_lines.append(f"【CTA】{result['cta']}")
        output_lines.append("")
        output_lines.append(f"字数：{result['total_chars']}/{result.get('limit', 280)} | 得分：{result['score']:.1f}/1.0")

        return {
            "status": "success",
            "text": "\n".join(output_lines),
            "score": result["score"],
            "within_limit": result.get("within_limit", True),
            "hook": result.get("hook", ""),
            "body_points": result.get("body_points", []),
            "cta": result.get("cta", ""),
            "climax": result.get("climax", ""),
        }

    # ═══════════════════════════════════════════════════════════════════
    #  接口：逆向（图像特征 → 叙事分数）— 新增！
    # ═══════════════════════════════════════════════════════════════════

    def score_from_features(self, features: dict) -> dict:
        """
        从像素特征计算叙事分数。

        axiom_verifier.verify_narrative_v2() 提取特征后调用此方法，
        实现 axiom_verifier → wudao-core axiom 的单向闭环。

        参数 features（由 axiom_verifier 传入）：
          arr        : numpy.ndarray  — 灰度图像 (H, W)
          或直接传入以下已计算的数值：
          spatial_variance_score : float
          gradient_score         : float
          focal_score            : float
          norm_entropy           : float

        返回：
          score      : float — 叙事分数 0~1
          method     : str   — 'narrative_v1_5'
          narrative_type : str — 'gradient' / 'focal' / 'uniform' / 'chaotic' / 'L_dark'
          features   : dict  — 使用的所有特征
        """
        gray = features.get('arr')
        if gray is None:
            # 没有图像，退回到文本评分（永远不触发）
            return {
                'score': 0.5,
                'method': 'narrative_fallback',
                'narrative_type': 'unknown',
                'features': features,
                'source': 'wudao_core_narrative_v2'
            }

        if not _HAS_V15:
            return {
                'score': 0.5,
                'method': 'narrative_no_v15',
                'narrative_type': 'unknown',
                'features': {},
                'source': 'wudao_core_narrative_v2'
            }

        result = _verify_narrative(gray)

        return {
            'score': float(result['score']),
            'method': 'narrative_v1_5',
            'narrative_type': result.get('narrative_type', 'unknown'),
            'entropy_type': result.get('entropy_type', 'unknown'),
            'features': result.get('features', {}),
            'source': 'wudao_core_narrative_v2'
        }

    # ═══════════════════════════════════════════════════════════════════
    #  内部方法
    # ═══════════════════════════════════════════════════════════════════

    def _compute_entropy_analysis(self, narrative_segments: List[Dict]) -> dict:
        """
        信息熵分析叙事结构
        
        使用 Shannon 熵衡量叙事的"张力"
        """
        if not _HAS_ENTROPY_BRIDGE:
            return {
                'local_entropy': 0.0,
                'global_entropy': 0.0,
                'entropy_gradient': 0.0,
                'entropy_interpretation': '熵分析不可用'
            }
        
        try:
            bridge = NarrativeEntropyBridge()
            result = bridge.analyze_narrative_structure(narrative_segments)
            
            return {
                'local_entropy': result.local_entropy,
                'global_entropy': result.global_entropy,
                'entropy_gradient': result.entropy_gradient,
                'entropy_interpretation': result.interpretation,
            }
        except Exception as e:
            return {
                'local_entropy': 0.0,
                'global_entropy': 0.0,
                'entropy_gradient': 0.0,
                'entropy_interpretation': f'熵分析不可用: {str(e)[:50]}'
            }

    def _analyze_content(self, content: str) -> dict:
        """分析现有叙事内容"""
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        hook = lines[0] if lines else ""
        body = lines[1:-1] if len(lines) > 2 else lines[1:]
        cta = lines[-1] if lines else ""

        hook_score = 0.2 if any(kw in hook for kw in ["？", "！", "不是", "真正", "只需", "%"]) else 0.1
        cta_score = 0.2 if cta.startswith("→") else 0.1

        return {
            "hook": hook,
            "body_points": body,
            "cta": cta,
            "body_count": len(body),
            "total_chars": len(content),
            "score": hook_score + cta_score + 0.3 + 0.2,
            "analysis": {
                "has_hook": bool(hook),
                "has_body": len(body) > 0,
                "has_cta": bool(cta),
                "cta_starts_arrow": cta.startswith("→")
            },
            "status": "success"
        }

    def _score_narrative(self, hook: str, body: list, cta: str, total: int, limit: int) -> float:
        """叙事质量评分（正向）"""
        score = 0.0
        if len(body) >= 2:
            score += 0.3
        if any(kw in hook for kw in ["？", "！", "不是", "真正", "只需", "%", "为什么", "你以为"]):
            score += 0.2
        score += 0.2 if len(body) >= 3 else 0.1
        if cta.startswith("→"):
            score += 0.2
        if total <= limit:
            score += 0.1
        return min(score, 1.0)

    def _compute_fallback(self, topic: str, hook_type: str, num_body: int) -> dict:
        """无 narrative 引擎时的降级计算"""
        return {
            "hook": f"[{hook_type}] {topic}：打破旧认知",
            "body_points": [
                "这不是能力问题，是认知问题。",
                "打破旧框架，才能建立新体系。",
            ][:num_body],
            "cta": "→ 开始行动，改变从此发生",
            "total_chars": 0,
            "score": 0.5,
            "status": "success",
            "fallback": True
        }

    def info(self) -> dict:
        """公理元信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": "叙事公理 v2.0：Hook→Body→CTA 四段结构 + score_from_features()",
            "inputs_compute": ["topic", "hook_type", "num_body_lines", "content"],
            "inputs_score": ["arr (numpy.ndarray)"],
            "outputs": ["hook", "body_points", "cta", "score"],
            "score_range": "0.0~1.0",
            "wukong_eye_core": "narrative_v1_5.verify_narrative_v1_5"
        }


# ──── 直接运行演示 ────
if __name__ == "__main__":
    import numpy as np

    axiom = NarrativeAxiom()
    print("NarrativeAxiom v2.0 — 叙事公理")
    print("=" * 50)

    # 正向：生成测试
    data = {
        "topic": "认知升级",
        "hook_type": "counter",
        "num_body_lines": 3,
        "limit": 200
    }
    print(f"\n[正向 compute] {data}")
    result = axiom.compute(data, None)
    output = axiom.render(result)
    print(output["text"])
    print(f"质量得分：{result['score']:.1f}/1.0")

    # 逆向：图像特征 → 叙事分数
    print("\n" + "=" * 50)
    print("[逆向 score_from_features]")

    # 构造测试图像：上亮下暗（叙事强）
    img_strong = np.zeros((128, 128), dtype=np.float64)
    img_strong[:64, :] = 0.80
    img_strong[64:, :] = 0.15
    img_strong += np.random.randn(128, 128) * 0.02
    img_strong = np.clip(img_strong, 0, 1)

    # 均匀图
    img_uniform = np.full((128, 128), 0.50, dtype=np.float64)

    for label, img in [("narrative_strong", img_strong), ("uniform", img_uniform)]:
        r = axiom.score_from_features({'arr': img})
        print(f"  {label}: score={r['score']:.3f} type={r['narrative_type']} method={r['method']}")

    print(f"\n元信息：{axiom.info()}")
