# -*- coding: utf-8 -*-
"""
axiom_loader.py — 公理动态加载器
==================================

状态（2026-04-09）：
  [OK] axiom1_growth     — 生产级（内容节奏：慢起→爆发→收敛）
  [OK] axiom2_light      — 生产级（光源位置/色温/强度/阴影）
  [OK] axiom3_color      — 生产级（配色方案：情绪→调色板）
  [OK] axiom4_layout     — 生产级（PHI=1.618 / 三分焦点 / 视觉重心）
  [OK] axiom5_narrative  — 生产级（Hook→Body→CTA）
  [OK] axiom6_boundary   — 生产级（MUST/CANNOT/CAN 三色约束）
  [OK] axiom7_freedom    — 生产级（override_mask / intensity）
  [OK] axiom8_causal     — 生产级（BFS 因果链 / 置换检验）

  整体完成度：100% (8/8) ✅
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional

# ─── 路径设置 ───────────────────────────────────────────────────────────────
WUKONG_CHIP_PYTHON = str(Path(__file__).resolve().parent.parent.parent / "wukong" / "wukong_chip" / "python")
AXIOM_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AXIOM_BASE not in sys.path:
    sys.path.insert(0, AXIOM_BASE)

# ─── GPU Shader 路径映射 ────────────────────────────────────────────────────
GPU_SHADER_PATHS = {
    'layout':    os.path.join(WUKONG_CHIP_PYTHON, 'layout_shader.py'),
    'boundary':  os.path.join(WUKONG_CHIP_PYTHON, 'boundary_shader.py'),
    'freedom':   os.path.join(WUKONG_CHIP_PYTHON, 'freedom_shader.py'),
    'causal':   None,   # 因果公理无独立 GPU shader，走 render_cpu
}
GPU_SHADER_EXISTS = {k: (v is not None and os.path.exists(v)) for k, v in GPU_SHADER_PATHS.items()}

# ─── Axiom 配置（扫描确认的真实接口）──────────────────────────────────────
# 每个 axiom 的标准接口：validate / compute / render / execute
#                      + compute_simple / render_cpu / info
AXIOM_CONFIG = {
    # ─── 缺失 axiom（2026-04-09 标记）───────────────────────────────
    'growth': {
        'class':      'GrowthAxiom',
        'module':     'axioms.axiom1_growth',
        'gpu_shader': None,
        'gpu_ok':     False,
        'description': '内容节奏约束（慢起→爆发→收敛，能量曲线）',
        'input_schema': {
            'content_type': 'str — story/tutorial/marketing/drama/longform',
            'duration': 'float — 总时长（秒/帧数）',
            'segments': 'int — 分段数（默认 10）',
            'mood': 'str — 情绪关键词（dramatic/calm/energetic...）',
            'pattern': 'str — 指定节奏模式（可选）',
        },
    },
    'light': {
        'class':      'LightAxiom',
        'module':     'axioms.axiom2_light',
        'gpu_shader': None,
        'gpu_ok':     False,
        'description': '光源位置/色温/强度/阴影（Tanner Helland RGB）',
        'input_schema': {
            'scene': 'dict — {time, weather, location}',
            'mood':  'str — 情绪关键词（warm/dramatic/fresh...）',
            'canvas': 'dict — {width, height}',
            'light_source': 'dict — {x, y} 手动指定（可选）',
            'target': 'dict — {x, y} 光照目标（可选）',
        },
    },
    'color': {
        'class':      'ColorAxiom',
        'module':     'axioms.axiom3_color',
        'gpu_shader': None,
        'gpu_ok':     False,
        'description': '色彩和谐公理（情绪→调色板：互补/三色/分裂互补/类似）',
        'input_schema': {
            'mood': 'str — 情绪关键词（passion/calm/dramatic/peaceful...）',
            'style': 'str — 风格（realistic/stylized/dramatic）',
            'base_color': 'tuple — 主体基色 RGB（可选，覆盖自动推断）',
            'harmony_type': 'str — 配色类型（complementary/triadic/split_complementary/analogous）',
        },
    },
    # ─── 生产 axiom ─────────────────────────────────────────────────
    'layout': {
        'class':      'LayoutAxiom',
        'module':     'axioms.axiom4_layout',
        'gpu_shader': 'layout_shader.py',
        'gpu_ok':     GPU_SHADER_EXISTS.get('layout', False),
        'description': '黄金分割 / 三分法则 / 视觉中心 / 负空间',
        'input_schema': {
            'elements': 'list[dict] — 布局元素',
            'canvas':   'dict — {width, height}',
        },
    },
    'narrative': {
        'class':      'NarrativeAxiom',
        'module':     'axioms.axiom5_narrative',
        'gpu_shader': None,
        'gpu_ok':     False,
        'description': '叙事公理：Hook→Body→Climax→CTA（复用 wukong_poster/narrative.py）',
        'input_schema': {
            'topic':        'str — 叙事主题',
            'hook_type':    'str — counter|pain|number|question',
            'num_body_lines': 'int — Body 段落数',
            'content':      'str — 待分析内容（可选）',
        },
    },
    'boundary': {
        'class':      'BoundaryAxiom',
        'module':     'axioms.axiom6_boundary',
        'gpu_shader': 'boundary_shader.py',
        'gpu_ok':     GPU_SHADER_EXISTS.get('boundary', False),
        'description': 'MUST 强制 / CANNOT 禁止 / CAN 允许 三色约束',
        'input_schema': {
            'boundaries': 'list[dict] — [{type: MUST|CANNOT|CAN, rect: (x,y,w,h)}]',
        },
    },
    'freedom': {
        'class':      'FreedomAxiom',
        'module':     'axioms.axiom7_freedom',
        'gpu_shader': 'freedom_shader.py',
        'gpu_ok':     GPU_SHADER_EXISTS.get('freedom', False),
        'description': '自由度 intensity / override_mask / 反事实路径',
        'input_schema': {
            'freedom':    'dict — {intensity, override_mask, alternatives}',
            'constraints':'dict — {must, cannot, can}',
        },
    },
    'causal': {
        'class':      'CausalAxiom',
        'module':     'axioms.axiom8_causal',
        'gpu_shader': None,
        'gpu_ok':     False,
        'description': '因果链 / 全局敏感度 / 置换检验 / 反事实',
        'input_schema': {
            'causal_chains': 'list[dict] — [{cause, effect, sensitivity, type}]',
        },
    },
}


# ─── Loader 核心 ─────────────────────────────────────────────────────────────

def load(name: str, gpu_mode: bool = True) -> Optional[Any]:
    """
    加载单个 axiom 实例。

    Args:
        name: axiom 名称
        gpu_mode: 是否尝试使用 GPU shader（无法使用时自动 fallback 到 CPU）

    Returns:
        Axiom 实例，或 None（加载失败）
    """
    if name not in AXIOM_CONFIG:
        print(f"[AxiomLoader] 未知 axiom: {name}")
        print(f"  可用: {list(AXIOM_CONFIG.keys())}")
        return None

    cfg = AXIOM_CONFIG[name]

    # ── missing axiom ──────────────────────────────────────────────
    if cfg.get('status') == 'missing':
        print(f"[AxiomLoader] [WARN] axiom '{name}' 尚未实现（{cfg['description']}）")
        print(f"           → 详见 axiom_loader.py 顶部注释，了解设计方向")
        print(f"           → 当前可用: growth / light / color / layout / narrative / boundary / freedom / causal")
        return None

    # GPU 模式检查
    if gpu_mode and cfg['gpu_shader']:
        if not cfg['gpu_ok']:
            print(f"[AxiomLoader] {name}: GPU shader 不存在 ({cfg['gpu_shader']}), 使用 CPU fallback")
        else:
            print(f"[AxiomLoader] {name}: GPU 模式就绪 ({cfg['gpu_shader']})")

    try:
        from axioms import (
            GrowthAxiom, LightAxiom, ColorAxiom, LayoutAxiom, NarrativeAxiom, BoundaryAxiom, FreedomAxiom, CausalAxiom
        )
        CLASS_MAP = {
            'growth':     GrowthAxiom,
            'light':      LightAxiom,
            'color':      ColorAxiom,
            'layout':     LayoutAxiom,
            'narrative':  NarrativeAxiom,
            'boundary':   BoundaryAxiom,
            'freedom':    FreedomAxiom,
            'causal':     CausalAxiom,
        }
        axiom_class = CLASS_MAP[name]
        # 真实 __init__ 签名: (gpu_shader, fallback_method)
        shader_path = GPU_SHADER_PATHS.get(name) if gpu_mode else None
        instance = axiom_class(gpu_shader=shader_path, fallback_method='auto')
        instance._config = cfg  # 附加元信息
        print(f"[AxiomLoader] [OK] 加载成功: {name}")
        return instance

    except ImportError as e:
        print(f"[AxiomLoader] [ERR] ImportError: {cfg['module']} — {e}")
        return None
    except Exception as e:
        print(f"[AxiomLoader] [ERR] 加载失败: {name} — {e}")
        return None


def load_all(gpu_mode: bool = True) -> Dict[str, Any]:
    """加载全部 axiom（missing 状态会优雅跳过）。"""
    results = {}
    missing = []
    for name, cfg in AXIOM_CONFIG.items():
        if cfg.get('status') == 'missing':
            missing.append(name)
            continue
        inst = load(name, gpu_mode)
        if inst is not None:
            results[name] = inst
    ok = len(results)
    total = len(AXIOM_CONFIG)
    missing_str = f" [WARN] {', '.join(missing)} 待实现" if missing else ""
    status = "[OK]" if not missing else f"({ok}/{total})"
    print(f"\n[AxiomLoader] 整体完成度: {ok}/{total} {status}{missing_str}")
    return results


def list_available() -> Dict[str, Dict]:
    """列出所有 axiom 的配置信息。"""
    return {name: {k: v for k, v in cfg.items() if k != 'input_schema'}
            for name, cfg in AXIOM_CONFIG.items()}


def get_info(name: str) -> Optional[Dict]:
    """获取指定 axiom 的详细信息。"""
    return AXIOM_CONFIG.get(name)


def validate_input(name: str, data: dict) -> tuple[bool, Optional[str]]:
    """
    验证输入数据是否符合 axiom 的 schema。
    Returns: (is_valid, error_message)
    """
    if name not in AXIOM_CONFIG:
        return False, f"未知 axiom: {name}"

    schema = AXIOM_CONFIG[name].get('input_schema', {})
    missing = [k for k in schema if k not in data]
    if missing:
        return False, f"缺少必填字段: {missing}"
    return True, None


# ─── 便捷调用 ────────────────────────────────────────────────────────────────

def run_axiom(name: str, data: dict, gpu_mode: bool = True) -> Optional[dict]:
    """
    一句话调用 axiom：加载 → 验证 → 计算 → 渲染。
    
    Args:
        name: axiom 名称
        data: 输入数据（需符合 input_schema）
        gpu_mode: 是否 GPU 模式
    
    Returns:
        渲染结果，或 None（失败）
    """
    axiom = load(name, gpu_mode)
    if axiom is None:
        return None

    valid, err = validate_input(name, data)
    if not valid:
        print(f"[AxiomLoader] 输入验证失败: {err}")
        return None

    if not axiom.validate(data):
        print(f"[AxiomLoader] validate() 返回 False")
        return None

    result = axiom.compute(data, None)
    output = axiom.render(result)
    output['_meta'] = {
        'axiom': name,
        'gpu_used': gpu_mode and AXIOM_CONFIG[name]['gpu_ok'],
        'shader': AXIOM_CONFIG[name]['gpu_shader'],
    }
    return output


if __name__ == '__main__':
    # 诊断模式：列出所有 axiom 状态
    print("=" * 60)
    print("AxiomLoader 诊断")
    print("=" * 60)
    for name, cfg in AXIOM_CONFIG.items():
        status = cfg.get('status', 'ok')
        if status == 'missing':
            print(f"\n[{name}] [WARN] 缺失")
        else:
            gpu_status = "[OK]" if cfg['gpu_ok'] else "[WARN] 无 GPU shader"
            print(f"\n[{name}] {gpu_status}")
            print(f"  类: {cfg['class']}")
            print(f"  模块: {cfg['module']}")
        print(f"  描述: {cfg['description']}")
        if cfg.get('note'):
            print(f"  注意: {cfg['note']}")
        print(f"  输入: {list(cfg['input_schema'].keys())}")

    print("\n" + "=" * 60)
    print("尝试加载全部 axiom...")
    print("=" * 60)
    axioms = load_all(gpu_mode=False)
    print(f"\n最终结果: {len(axioms)}/{len(AXIOM_CONFIG)} axiom 就绪")
    print("\n缺失 axiom（不影响主干，仍可调用生产 axiom）：")
    for name, cfg in AXIOM_CONFIG.items():
        if cfg.get('status') == 'missing':
            print(f"  [ERR] {name}: {cfg['description']}")


# ─── 兼容类（供 core/__init__.py 导入）─────────────────────────────────────

class AxiomLoader:
    """兼容包装类，代理 axiom_loader 模块的所有函数。"""

    @staticmethod
    def load(name: str, gpu_mode: bool = True):
        return load(name, gpu_mode)

    @staticmethod
    def load_all(gpu_mode: bool = True):
        return load_all(gpu_mode)

    @staticmethod
    def list_available():
        return list_available()

    @staticmethod
    def get_info(name: str):
        return get_info(name)

    @staticmethod
    def validate_input(name: str, data: dict):
        return validate_input(name, data)

    @staticmethod
    def run_axiom(name: str, data: dict, gpu_mode: bool = True):
        return run_axiom(name, data, gpu_mode)

