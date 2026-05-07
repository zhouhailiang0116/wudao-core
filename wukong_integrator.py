# -*- coding: utf-8 -*-
"""
wukong_integrator.py — 道·通·悟 统一入口
==========================================

悟道体系对外暴露的统一 API。

用法：
    from wukong_integrator import WukongIntegrator
    wk = WukongIntegrator()
    result = wk.render(task={"type": "poster", "content": "..."}, axiom="narrative")
    result["image"].save("out.png")

    # 或者批量 axiom
    result = wk.render_multi(task={"canvas": {"width": 512, "height": 512}, ...})

架构位置：
  hermes/用户 → WukongIntegrator → AgentCore.run_pipeline()
                                      → bridge.translate()
                                      → [painter|poster|creature] 渲染
                                      → 图像 / 报告

作者：悟道体系 | 2026-05-07
"""

import sys
import os
from typing import Dict, Any, Optional, List

# ════════════════════════════════════════════════════════════════════════════
# 路径初始化（WSL + Windows 兼容）
# ════════════════════════════════════════════════════════════════════════════

if os.path.exists("/mnt/c/Users"):
    _HOME = "/mnt/c/Users/周海亮"
else:
    _HOME = os.path.expanduser("~")

_QC       = os.path.join(_HOME, ".qclaw")
_WUKONG   = os.path.join(_QC, "workspace", "wukong")
_WUKONG_P = os.path.join(_WUKONG, "wukong_painter")
_WUKONG_O = os.path.join(_WUKONG, "wukong_poster")
_WUKONG_C = os.path.join(_WUKONG, "wukong_creature")
_WUKONG_U = os.path.join(_WUKONG, "wukong_causality")
_WUKONG_V = os.path.join(_WUKONG, "wukong_video")
_WUKONG_BR = os.path.join(_WUKONG, "bridge")
_WDCORE    = os.path.join(_QC, "workspace", "wudao-core")

for _p in [_WUKONG_P, _WUKONG_O, _WUKONG_C, _WUKONG_U, _WUKONG_V, _WUKONG_BR, _WDCORE]:
    if _p not in sys.path:
        sys.path.append(_p)


# ════════════════════════════════════════════════════════════════════════════
# Law → Module 路由表
# ════════════════════════════════════════════════════════════════════════════

LAW_TO_MODULE = {
    "painter":    (_WUKONG_P, "core.painter",       "Painter"),
    "poster":     (_WUKONG_O, "core.poster_engine", "NarrativePoster"),
    "creature":   (_WUKONG_C, "core.creature",      "Creature"),
    "causality":  (_WUKONG_U, "core.causality",    "CausalityEngine"),
    "video":      (_WUKONG_V, "core.video_engine",   "VideoEngine"),
}


# ════════════════════════════════════════════════════════════════════════════
# WukongIntegrator
# ════════════════════════════════════════════════════════════════════════════

class WukongIntegrator:
    """
    悟道体系统一入口。

    使用方式：

    单 axiom 渲染：
        wk = WukongIntegrator()
        result = wk.render(task={"canvas": {...}, "elements": [...]}, axiom="layout")

    多 axiom 联合渲染（fusion）：
        result = wk.render_multi(task={...}, axioms=["layout", "light", "color"])

    返回格式：
        {
            "success": True,
            "axiom": "layout",
            "image": PIL.Image,
            "bridge_params": {...},   # 通层翻译结果
            "axiom_result": {...},    # 道层输出
            "render_time": 0.123,
        }
    """

    def __init__(self, auto_load: bool = True):
        # 延迟导入避免循环依赖
        self._core = None
        self._auto_load = auto_load
        self._loaded = False

    # ── 内部 ────────────────────────────────────────────────────────────

    def _get_core(self):
        if self._core is None:
            os.chdir(_WDCORE)
            from core.agent_core import AgentCore
            self._core = AgentCore(auto_load=self._auto_load)
            self._loaded = True
        return self._core

    def _load_module(self, law: str):
        """动态加载 law 对应的 wukong 模块。"""
        if law not in LAW_TO_MODULE:
            return None
        mod_path, mod_name, cls_name = LAW_TO_MODULE[law]

        # 动态 import
        import importlib
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name, None)
            return cls
        except ImportError as e:
            print(f"[WukongIntegrator] warning: cannot import {mod_name} ({e}), {law} unavailable")
            return None

    # ── 公开 API ───────────────────────────────────────────────────────

    def render(self,
               task: dict,
               axiom: str,
               image_path: str = None,
               block_threshold: float = 0.40) -> dict:
        """
        单 axiom 渲染。

        Args:
            task:        任务数据（符合 axiom 的 input_schema）
            axiom:       axiom 名称（growth/light/color/layout/narrative/boundary/freedom/causal）
            image_path:  可选，验证用图像路径
            block_threshold: verify 阈值

        Returns:
            dict（含 image PIL.Image / error）
        """
        import time
        t0 = time.time()

        core = self._get_core()

        # 道→通 闭环
        pipeline = core.run_pipeline(task, axiom, image=image_path, block_threshold=block_threshold)

        if not pipeline.get("success"):
            return {
                "success": False,
                "axiom": axiom,
                "error": pipeline.get("axiom_result", {}).get("error") or "pipeline failed",
                "axiom_result": pipeline.get("axiom_result"),
                "bridge_params": pipeline.get("bridge_params"),
                "render_time": time.time() - t0,
            }

        axiom_result = pipeline["axiom_result"]
        bp = pipeline["bridge_params"]
        target_law = pipeline.get("target_law", "painter")

        # 悟空层渲染
        img = self._render_wukong(target_law, bp, task)

        return {
            "success": img is not None,
            "axiom": axiom,
            "image": img,
            "bridge_params": bp,
            "axiom_result": axiom_result,
            "target_law": target_law,
            "render_time": time.time() - t0,
        }

    def render_multi(self,
                     task: dict,
                     axioms: List[str],
                     fusion_method: str = "weighted") -> dict:
        """
        多 axiom 联合渲染。

        流程：
          1. 并行运行所有 axiom 的 pipeline
          2. 合并 bridge_params（权重融合）
          3. 调用对应 wukong 模块

        Args:
            task:         任务数据
            axioms:       axiom 名称列表，如 ["layout", "light", "color"]
            fusion_method: 融合方式（weighted / priority）

        Returns:
            同 render()，但 image 由多个 axiom 共同影响
        """
        import time
        t0 = time.time()

        core = self._get_core()
        pipelines = {}
        all_bp = {}

        # Step 1: 各 axiom 独立运行
        for ax in axioms:
            p = core.run_pipeline(task, ax)
            pipelines[ax] = p
            if p.get("success"):
                all_bp[ax] = p.get("bridge_params", {})

        # Step 2: 合并 bridge_params
        merged = self._merge_bridge_params(all_bp, method=fusion_method)

        # Step 3: 推断 target_law（取最高权重 axiom 的 law）
        if pipelines:
            primary_axiom = axioms[0]  # 默认第一个
            for ax in axioms:
                if pipelines[ax].get("success"):
                    primary_axiom = ax
                    break
            target_law = pipelines[primary_axiom].get("target_law", "painter")
        else:
            target_law = "painter"

        # Step 4: 渲染
        img = self._render_wukong(target_law, merged, task)

        return {
            "success": img is not None,
            "axioms": axioms,
            "images": {ax: img for ax in axioms} if img else {},  # 同一张图，多 axiom 共影响
            "bridge_params": merged,
            "pipelines": {ax: {"success": p.get("success"), "target_law": p.get("target_law")}
                          for ax, p in pipelines.items()},
            "target_law": target_law,
            "render_time": time.time() - t0,
        }

    # ── 渲染器实现 ─────────────────────────────────────────────────────

    def _render_wukong(self, law: str, bridge_params: dict, task: dict):
        """
        根据 target_law 分发到对应 wukong 模块渲染。
        """
        import time as _time

        if law == "painter":
            return self._render_painter(bridge_params, task)
        elif law == "poster":
            return self._render_poster(bridge_params, task)
        elif law == "creature":
            return self._render_creature(bridge_params, task)
        elif law == "causality":
            return self._render_causality(bridge_params, task)
        elif law == "video":
            return self._render_video(bridge_params, task)
        else:
            print(f"[WukongIntegrator] unknown law: {law}, fallback to painter")
            return self._render_painter(bridge_params, task)

    def _render_painter(self, bp: dict, task: dict):
        """
        渲染到 painter（光之法则）。

        bridge_params 来自：
          - layout axiom → vp_x, vp_y, phi, anchor_point, aerial_haze
          - light axiom  → light_position, light_direction, light_dz, ambient, roughness, light_temperature
          - color axiom  → base_color, bg_color, shadow_color, saturation
          - growth axiom → form_rx, form_ry, rhythm_pattern
        """
        from core.painter import Painter
        from core.form import Egg

        size = tuple(task.get("canvas", {}).get("width", 512),
                     task.get("canvas", {}).get("height", 512))

        painter = Painter(size=size)

        # 形体（growth axiom）
        form_rx = int(bp.get("form_rx", 80))
        form_ry = int(bp.get("form_ry", 100))
        egg = Egg(cx=size[0]//2, cy=size[1]//2, rx=form_rx, ry=form_ry)
        painter.set_form(egg)

        # 光源（light axiom）
        lp = bp.get("light_position", (400, 100))
        ltx, lty = lp
        tp = bp.get("target_position", (size[0]//2, size[1]//2))
        ldx = (ltx - tp[0]) / max(size[0], 1)
        ldy = (lty - tp[1]) / max(size[1], 1)
        ldz = bp.get("light_dz", 0.5)
        from core.light import Light
        light = Light(dx=ldx, dy=ldy, dz=ldz)
        painter.set_light(light)

        # 颜色（color axiom）
        base_color = bp.get("base_color", (255, 220, 180))
        bg_color   = bp.get("bg_color",   (40, 44, 52))
        shadow_color = bp.get("shadow_color", (20, 22, 26))
        painter.set_material(base_color=base_color, bg_color=bg_color, shadow_color=shadow_color)

        # 空间（layout axiom P4）
        vp_x   = bp.get("vp_x", 0.5)
        vp_y   = bp.get("vp_y", 0.45)
        aerial = bp.get("aerial_haze", 0.0)
        haze_b = bp.get("haze_blue", 0.15)
        if aerial > 0 or vp_x != 0.5:
            painter.set_spatial(vp_x=vp_x, vp_y=vp_y, aerial_haze=aerial, haze_blue=haze_b)

        return painter.render()

    def _render_poster(self, bp: dict, task: dict):
        """
        渲染到 poster（色之法则 / 文之法则）。

        bridge_params 来自 narrative axiom → hook/body_points/cta/climax
        """
        from core.poster_engine import NarrativePoster

        config = bp.get("_meta", {}).get("config", {})

        # 从 bridge_params 提取叙事参数
        hook      = bp.get("hook_text", task.get("hook", "悟道"))
        body_pts  = bp.get("body_points", task.get("body_points", []))
        cta       = bp.get("cta_text",   task.get("cta", "开始"))
        climax    = bp.get("climax_text", task.get("climax", ""))

        canvas_w = task.get("canvas", {}).get("width", 512)
        canvas_h = task.get("canvas", {}).get("height", 512)

        try:
            poster = NarrativePoster(size=(canvas_w, canvas_h))
            poster.set_narrative(hook=hook, body=body_pts, climax=climax, cta=cta)
            return poster.render()
        except Exception as e:
            print(f"[WukongIntegrator] poster render error: {e}")
            return None

    def _render_creature(self, bp: dict, task: dict):
        """渲染到 creature（生之法则）。"""
        print(f"[WukongIntegrator] creature render: {bp.get('safety_radius', 'N/A')}")
        return None  # TODO: 实现

    def _render_causality(self, bp: dict, task: dict):
        """因果链推理。"""
        chains = bp.get("step_sequence", [])
        sensitivity = bp.get("sensitivity_threshold", 0.5)
        print(f"[WukongIntegrator] causality: {len(chains)} chains, sensitivity={sensitivity}")
        return None  # 返回结构化因果报告，不是图像

    def _render_video(self, bp: dict, task: dict):
        """视频生成。"""
        print(f"[WukongIntegrator] video render: {bp.get('topic', 'N/A')}")
        return None  # TODO: 实现

    # ── 工具 ───────────────────────────────────────────────────────────

    def _merge_bridge_params(self, all_bp: dict, method: str = "weighted") -> dict:
        """
        合并多个 axiom 的 bridge_params。

        策略：
          - 数值参数取加权平均（由 axiom 默认权重决定）
          - 颜色参数取主 axiom 的值
          - 字符串参数取主 axiom 的值
          - _meta 携带融合信息
        """
        if not all_bp:
            return {}

        # axiom 优先级（影响颜色/字符串参数取谁的值）
        AXIOM_PRIORITY = ["color", "light", "layout", "growth", "narrative", "boundary", "freedom", "causal"]
        primary = next((ax for ax in AXIOM_PRIORITY if ax in all_bp), list(all_bp.keys())[0])
        merged = dict(all_bp[primary])  # shallow copy

        # 数值融合：跨 axiom 平均（避免冲突）
        numeric_keys = {
            "phi": 1.618, "negative_ratio": 0.4, "anchor_x": 0.5, "anchor_y": 0.5,
            "form_rx": 80, "form_ry": 100, "aerial_haze": 0.0, "haze_blue": 0.15,
            "vp_x": 0.5, "vp_y": 0.45, "ambient": 0.15, "roughness": 0.6,
            "light_intensity": 0.8, "light_dz": 0.5,
        }
        for key, default in numeric_keys.items():
            vals = []
            for bp in all_bp.values():
                if key in bp and isinstance(bp[key], (int, float)):
                    vals.append(bp[key])
            if vals:
                merged[key] = sum(vals) / len(vals)

        merged["_fusion"] = {
            "method": method,
            "axioms": list(all_bp.keys()),
            "primary": primary,
        }
        return merged

    def status(self) -> dict:
        """查看 integrator + AgentCore 状态。"""
        core = self._get_core()
        return {
            "core_loaded": self._loaded,
            "core_status": core.status(),
        }
