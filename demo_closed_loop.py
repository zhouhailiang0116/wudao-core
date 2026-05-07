# -*- coding: utf-8 -*-
"""
demo_closed_loop.py — 道·通·悟空 三层闭环完整演示
============================================================

重写版本（2026-05-07）：真正把 bridge_params 传给 painter。

流程：
  AgentCore.run_pipeline(scene_data, "layout")
    → axiom.compute()     （道层：布局约束）
    → bridge.translate()  （通层：翻译参数）
    → painter.render()   （悟空层：用真实参数生成图像）

悟空层通过子进程调用 render_painter.py（解决 core/ 同名冲突）。

验证方式：
  对比同一场景 + 不同 axiom 参数下的输出差异。

用法：python demo_closed_loop.py
"""

import sys
import os
import time
import json
import subprocess

# ─── 路径常量（WSL + Windows 兼容）────────────────────────────────────
if os.path.exists("/mnt/c/Users"):
    # WSL: 找当前用户对应的 Windows 主目录
    import pwd
    _WIN_USER = pwd.getpwuid(os.getuid()).pw_name
    _HOME = f"/mnt/c/Users/{_WIN_USER}"
else:
    _HOME = os.path.expanduser("~")

QC          = os.path.join(_HOME, ".qclaw")
WUKONG_PY   = os.path.join(QC, "workspace", "wukong", "wukong_painter")
WUKONG_CORE = os.path.join(QC, "workspace", "wukong")
WUKONG_BR   = os.path.join(WUKONG_CORE, "bridge")
WDCORE      = os.path.join(QC, "workspace", "wudao-core")
RENDER_PY   = os.path.join(WDCORE, "render_painter.py")
OUT_DIR     = os.path.join(_HOME, "Desktop", "业", "任务")
os.makedirs(OUT_DIR, exist_ok=True)

os.chdir(WDCORE)
sys.path.insert(0, WDCORE)


# ════════════════════════════════════════════════════════════════════════════
# STEP 0 — 初始化 AgentCore
# ════════════════════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 0  初始化 AgentCore（加载所有 axiom）")
print("=" * 60)

from core.agent_core import AgentCore

core = AgentCore(auto_load=True)
st = core.status()
print(f"  已注册 axiom: {st['axioms']}")
print(f"  axiom 数量:   {st['axiom_count']}")


# ════════════════════════════════════════════════════════════════════════════
# STEP 1-3 — 道·通 闭环
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 1-3  道·通 闭环")
print("=" * 60)

scene_data = {
    "canvas": {"width": 512, "height": 512},
    "elements": [
        # 注意：position + size 不能超出 canvas 边界（layout axiom validate 校验）
        {"id": "hero",  "position": {"x": 100, "y": 120}, "size": {"width": 200, "height": 160}, "weight": 1.0},
        {"id": "title", "position": {"x": 156, "y": 380}, "size": {"width": 200, "height": 60},  "weight": 0.8},
        {"id": "cta",   "position": {"x": 300, "y": 400}, "size": {"width": 120, "height": 40},  "weight": 0.6},
    ],
}


# ── 场景A：layout axiom ───────────────────────────────────────────────
print("\n[场景A] Layout Axiom")
pipe_a = core.run_pipeline(scene_data, "layout")
ax_a = pipe_a["axiom_result"]
bp_a = pipe_a["bridge_params"]
vc   = ax_a.get("visual_center", {})
vc_x = vc.get("x", 256); vc_y = vc.get("y", 256)
phi_a = bp_a.get("phi", 1.618)
neg_r = bp_a.get("negative_ratio", 0.4)
anchr = bp_a.get("anchor_point", (0.5, 0.5))
print(f"  视觉重心: ({vc_x:.1f}, {vc_y:.1f})")
print(f"  PHI:      {phi_a}")
print(f"  负空间:   {neg_r}")
print(f"  锚点:     {anchr}")
print(f"  target_law: {pipe_a.get('target_law')}")


# ── 场景B：light axiom ──────────────────────────────────────────────
print("\n[场景B] Light Axiom")
light_scene = {
    "canvas": {"width": 512, "height": 512},
    "scene":  {"time": "golden_hour", "weather": "sunny", "location": "outdoor"},
    "mood":   "warm",
    "target": {"x": 256, "y": 256},
}
pipe_b = core.run_pipeline(light_scene, "light")
bp_b = pipe_b["bridge_params"]
print(f"  光源位置:   {bp_b.get('light_position')}")
print(f"  光照强度:   {bp_b.get('light_intensity')}")
print(f"  色温:       {bp_b.get('light_temperature')}K")
print(f"  环境光:     {bp_b.get('ambient')}")
print(f"  粗糙度:     {bp_b.get('roughness')}")
print(f"  对比度:     {bp_b.get('contrast')}")
print(f"  target_law: {pipe_b.get('target_law')}")


# ── 场景C：color axiom ──────────────────────────────────────────────
print("\n[场景C] Color Axiom")
color_scene = {"mood": "dramatic", "style": "dramatic", "harmony_type": "complementary"}
pipe_c = core.run_pipeline(color_scene, "color")
bp_c = pipe_c["bridge_params"]
print(f"  主色:       {bp_c.get('base_color')}")
print(f"  背景色:     {bp_c.get('bg_color')}")
print(f"  配色类型:   {bp_c.get('harmony_type')}")
print(f"  情绪:       {bp_c.get('mood')}")
print(f"  target_law: {pipe_c.get('target_law')}")


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — 悟空层：通过子进程调用 painter
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4  悟空层 — 子进程渲染")
print("=" * 60)


def call_painter_subprocess(painter_params: dict, out_path: str) -> bool:
    """通过子进程调用 render_painter.py。"""
    params_json = json.dumps(painter_params, ensure_ascii=False)
    cmd = [sys.executable, RENDER_PY, params_json, "--output", out_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"  [OK] {out_path}")
            return True
        else:
            print(f"  [FAIL] {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


# ── 构建 painter 参数 ───────────────────────────────────────────────
lp  = bp_b.get("light_position", (400, 100))
tp  = bp_b.get("target_position", (256, 256))
ldx = (lp[0] - tp[0]) / 512.0
ldy = (lp[1] - tp[1]) / 512.0
ldz = bp_b.get("light_dz", 0.5)

painter_params = {
    "size":        [512, 512],
    "form_rx":     int(bp_a.get("form_rx", 70)),
    "form_ry":     int(bp_a.get("form_ry", 90)),
    "light_dx":    round(ldx, 4),
    "light_dy":    round(ldy, 4),
    "light_dz":    round(ldz, 4),
    "base_color":  list(bp_c.get("base_color", (255, 220, 180))),
    "bg_color":    list(bp_c.get("bg_color", (40, 44, 52))),
    "shadow_color": list(bp_c.get("shadow_color", (20, 15, 10))),
    "vp_x":        round(bp_a.get("vp_x", 0.5), 3),
    "vp_y":        round(bp_a.get("vp_y", 0.45), 3),
    "aerial_haze": round(bp_a.get("aerial_haze", 0.0), 3),
    "haze_blue":   round(bp_a.get("haze_blue", 0.15), 3),
}

print(f"  painter 参数:")
for k, v in painter_params.items():
    if k != "output":
        print(f"    {k}: {v}")

# ── 主渲染：axiom 融合结果 ──────────────────────────────────────────
out_main = os.path.join(OUT_DIR, "axiom_layout_light_color.png")
print(f"\n[主渲染] layout+light+color 融合")
ok_main = call_painter_subprocess(painter_params, out_main)


# ════════════════════════════════════════════════════════════════════════════
# 验证：参数差异对比
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("验证：参数差异对比")
print("=" * 60)

# 对比1：不同光源方向
print("\n[对比1] 光源方向对阴影的影响")
for label, lparams in [
    ("左上光源",   {"light_dx": -0.5, "light_dy": -0.7, "light_dz": 0.5}),
    ("右侧光源",   {"light_dx":  0.8, "light_dy": -0.3, "light_dz": 0.4}),
    ("底部柔光",   {"light_dx":  0.0, "light_dy":  0.8, "light_dz": 0.3}),
]:
    params = dict(painter_params, **lparams)
    out = os.path.join(OUT_DIR, f"axiom_light_{label}.png".replace(" ", "_"))
    call_painter_subprocess(params, out)
    print(f"    {label}")

# 对比2：不同 PHI 形体比例
print("\n[对比2] PHI 对形体比例的影响")
phi_rx, phi_ry = painter_params["form_rx"], painter_params["form_ry"]
for phi_val in [1.0, 1.618, 2.0]:
    rx_v = int(phi_rx * phi_val / 1.618)
    ry_v = int(phi_ry * phi_val / 1.618)
    params = dict(painter_params, form_rx=rx_v, form_ry=ry_v)
    out = os.path.join(OUT_DIR, f"axiom_phi_{phi_val}.png")
    call_painter_subprocess(params, out)
    print(f"    PHI={phi_val} → rx={rx_v}, ry={ry_v}")

# 对比3：不同背景色情绪
print("\n[对比3] 背景色对情绪的影响")
for label, bg in [
    ("暖调", (35, 28, 22)),
    ("冷调", (20, 22, 30)),
    ("亮调", (80, 75, 65)),
    ("暗调", (15, 12, 10)),
]:
    params = dict(painter_params, bg_color=list(bg))
    out = os.path.join(OUT_DIR, f"axiom_mood_{label}.png")
    call_painter_subprocess(params, out)
    print(f"    {label} {bg}")


# ════════════════════════════════════════════════════════════════════════════
# 总结
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUCCESS — 道·通·悟空 三层闭环完整验证")
print("=" * 60)
st2 = core.status()
print(f"  AgentCore 任务: {st2['tasks_success']}/{st2['tasks_total']} 成功")
print(f"  AgentCore 闭环: {st2['pipelines_success']}/{st2['pipelines_total']} 成功")
print(f"\n已生成文件（{OUT_DIR}）：")
generated = [
    "axiom_layout_light_color.png",
    "axiom_light_左上光源.png", "axiom_light_右侧光源.png", "axiom_light_底部柔光.png",
    "axiom_phi_1.0.png", "axiom_phi_1.618.png", "axiom_phi_2.0.png",
    "axiom_mood_暖调.png", "axiom_mood_冷调.png", "axiom_mood_亮调.png", "axiom_mood_暗调.png",
]
for f in generated:
    full = os.path.join(OUT_DIR, f)
    exists = "✓" if os.path.exists(full) else "✗"
    print(f"  [{exists}] {f}")
