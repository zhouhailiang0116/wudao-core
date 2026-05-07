# -*- coding: utf-8 -*-
"""
axiom_registry.py — 两套 axiom 体系统一注册表
=============================================

问题背景：
  wudao-core/axioms/ 和 wukong_constraints/axioms/ 各写各的，
  axiom4/6/7 的命名互相打架：
    wudao-core: axiom4=layout, axiom6=boundary, axiom7=freedom
    wukong_constraints: axiom4=boundary, axiom6=freedom, axiom7=causal

  导致：
    - bridge translate() 需要猜测 axiom 名称
    - axiom_verifier.py 里 verify_boundary/verify_freedom 的顺序对不上
    - 新人维护必踩坑

统一编号（标准序号 1-8）：

| 序号 | 英文名   | 中文名 | wudao-core      | wukong_constraints    | 职责层次        |
|------|----------|--------|----------------|---------------------|----------------|
| 1    | growth   | 生长   | axiom1_growth  | axiom1_growth       | 道：约束参数    |
| 2    | light   | 光影   | axiom2_light   | axiom2_light        | 道：约束参数    |
| 3    | color   | 色彩   | axiom3_color   | axiom3_color        | 道：约束参数    |
| 4    | layout  | 布局   | axiom4_layout  | axiom4_layout       | 道：约束参数    |
| 5    | narrative | 叙事 | axiom5_narrative | axiom5_narrative   | 道：约束参数    |
| 6    | boundary | 边界  | axiom6_boundary | axiom4_boundary    | 道：约束参数    |
| 7    | freedom | 自由   | axiom7_freedom  | axiom6_freedom      | 道：约束参数    |
| 8    | causal  | 因果   | axiom8_causal   | axiom7_causal/axiom8_causal | 道：约束参数 |

验证层（wukong_eye/core/axiom_verifier.py）：
  顺序固定，按 verify_all() 里的顺序：
    0=叙事, 1=色彩, 2=生长, 3=布局, 4=光影, 5=边界, 6=自由, 7=因果

  verify 函数名到标准 axiom 的映射：
    verify_narrative → axiom5
    verify_color    → axiom3
    verify_growth  → axiom1
    verify_layout  → axiom4
    verify_light   → axiom2
    verify_boundary → axiom6
    verify_freedom → axiom7
    verify_causal  → axiom8

两套公理体系的关系：
  道层 (wudao-core/axioms/)     → 计算约束参数（教练）
  裁判层 (wukong_constraints/)  → 独立验证逻辑
  验证层 (wukong_eye/core/)     → 消费验证结果

  数据流：道层 compute() → bridge translate() → 悟空渲染 → 眼层 verify() → 道层归纳
"""

from typing import Dict, List, Optional, Tuple


# ── 标准 axiom 定义 ────────────────────────────────────────────────────────

class AxiomDef:
    """单条 axiom 的元信息"""
    def __init__(self,
                 number: int,
                 name_en: str,
                 name_zh: str,
                 wudao_core_file: str,
                 wukong_constraints_file: str,
                 wukong_eye_verify_fn: str,
                 description: str,
                 law: str,           # 对应的法则 (painter/poster/video/creature/causality)
                 ):
        self.number = number
        self.name_en = name_en
        self.name_zh = name_zh
        self.wudao_core_file = wudao_core_file      # "axiomN_name.py"
        self.wukong_constraints_file = wukong_constraints_file
        self.wukong_eye_verify_fn = wukong_eye_verify_fn
        self.description = description
        self.law = law

    @property
    def key(self) -> str:
        """标准 key（用于 API 和映射）"""
        return self.name_en

    def __repr__(self):
        return f"AxiomDef({self.number}={self.name_en})"


# ── 全量注册表 ────────────────────────────────────────────────────────────

REGISTRY: Dict[str, AxiomDef] = {}
REGISTRY_BY_NUMBER: Dict[int, AxiomDef] = {}

# 按标准序号注册（序号 1-8）
for _def in [
    AxiomDef(
        number=1,
        name_en="growth",
        name_zh="生长",
        wudao_core_file="axiom1_growth.py",
        wukong_constraints_file="axiom1_growth.py",
        wukong_eye_verify_fn="verify_growth",
        description="边缘密度 / PCA 生长轴方向",
        law="painter",
    ),
    AxiomDef(
        number=2,
        name_en="light",
        name_zh="光影",
        wudao_core_file="axiom2_light.py",
        wukong_constraints_file="axiom2_light.py",
        wukong_eye_verify_fn="verify_light",
        description="Lambert 漫反射 / 五调子亮度",
        law="painter",
    ),
    AxiomDef(
        number=3,
        name_en="color",
        name_zh="色彩",
        wudao_core_file="axiom3_color.py",
        wukong_constraints_file="axiom3_color.py",
        wukong_eye_verify_fn="verify_color",
        description="HSV 通道均值 / 情绪分类",
        law="painter",
    ),
    AxiomDef(
        number=4,
        name_en="layout",
        name_zh="布局",
        wudao_core_file="axiom4_layout.py",
        wukong_constraints_file="axiom4_layout.py",
        wukong_eye_verify_fn="verify_layout",
        description="分段均值重建 / 黄金比例锚点",
        law="painter",
    ),
    AxiomDef(
        number=5,
        name_en="narrative",
        name_zh="叙事",
        wudao_core_file="axiom5_narrative.py",
        wukong_constraints_file="axiom5_narrative.py",
        wukong_eye_verify_fn="verify_narrative",
        description="Hook / Body / Climax / CTA 四段结构",
        law="poster+video",   # narrative 同时支持 poster 和 video
    ),
    AxiomDef(
        number=6,
        name_en="boundary",
        name_zh="边界",
        wudao_core_file="axiom6_boundary.py",     # 注意：wudao-core 用 boundary
        wukong_constraints_file="axiom4_boundary.py",  # 注意：wukong_constraints 用 axiom4
        wukong_eye_verify_fn="verify_boundary",
        description="OTSU 连通域 / 形状数量",
        law="creature",
    ),
    AxiomDef(
        number=7,
        name_en="freedom",
        name_zh="自由",
        wudao_core_file="axiom7_freedom.py",
        wukong_constraints_file="axiom6_freedom.py",
        wukong_eye_verify_fn="verify_freedom",
        description="HSV 三维离散度 / 色彩自由度",
        law="video",
    ),
    AxiomDef(
        number=8,
        name_en="causal",
        name_zh="因果",
        wudao_core_file="axiom8_causal.py",
        wukong_constraints_file="axiom7_causal.py",
        wukong_eye_verify_fn="verify_causal",
        description="三源证据融合 / 因果链归纳",
        law="causality",
    ),
]:
    REGISTRY[_def.name_en] = _def
    REGISTRY_BY_NUMBER[_def.number] = _def


# ── 别名兼容表 ────────────────────────────────────────────────────────────

# wukong_constraints 文件名 → 标准名称
# （因为 wukong_constraints 的 axiom4=boundary 和 axiom6=freedom 命名不同）
CONSTRAINTS_ALIAS: Dict[str, str] = {
    # wukong_constraints 文件名 → 标准 axiom 名称
    "axiom1_growth":   "growth",
    "axiom2_light":    "light",
    "axiom3_color":    "color",
    "axiom4_boundary": "boundary",   # ← 注意：constraints 用 axiom4=boundary
    "axiom5_narrative": "narrative",
    "axiom6_freedom":  "freedom",     # ← 注意：constraints 用 axiom6=freedom
    "axiom7_causal":   "causal",
    "axiom8_causal":   "causal",
}

# wukong_eye verify 函数名 → 标准 axiom 名称
VERIFY_FN_ALIAS: Dict[str, str] = {
    "verify_growth":    "growth",
    "verify_light":     "light",
    "verify_color":     "color",
    "verify_layout":    "layout",
    "verify_narrative": "narrative",
    "verify_boundary":  "boundary",
    "verify_freedom":   "freedom",
    "verify_causal":    "causal",
}


# ── 查询接口 ──────────────────────────────────────────────────────────────

def get(name_or_number: str | int) -> Optional[AxiomDef]:
    """通过名称或序号查找 axiom"""
    if isinstance(name_or_number, int):
        return REGISTRY_BY_NUMBER.get(name_or_number)
    return REGISTRY.get(name_or_number)


def from_constraints_filename(filename: str) -> Optional[AxiomDef]:
    """通过 wukong_constraints 文件名查找标准 axiom"""
    key = filename.replace(".py", "")
    name = CONSTRAINTS_ALIAS.get(key)
    if name:
        return REGISTRY.get(name)
    return None


def from_verify_fn(fn_name: str) -> Optional[AxiomDef]:
    """通过 wukong_eye 的 verify 函数名查找标准 axiom"""
    name = VERIFY_FN_ALIAS.get(fn_name)
    if name:
        return REGISTRY.get(name)
    return None


def all_axioms() -> List[AxiomDef]:
    """返回所有 axiom（按序号排序）"""
    return [REGISTRY_BY_NUMBER[i] for i in range(1, 9) if i in REGISTRY_BY_NUMBER]


def list_names() -> List[str]:
    """返回所有标准 axiom 名称"""
    return [a.name_en for a in all_axioms()]


# ── 验证工具 ──────────────────────────────────────────────────────────────

def validate_registry() -> Dict[str, any]:
    """
    检查注册表一致性，返回问题列表

    返回:
        {
            "ok": bool,
            "issues": [str, ...],
            "axioms": {name: AxiomDef, ...}
        }
    """
    issues = []
    for num in range(1, 9):
        if num not in REGISTRY_BY_NUMBER:
            issues.append(f"缺少序号 {num}")

    for name, ax in REGISTRY.items():
        if ax.number != num_from_name(name):
            issues.append(f"{name}: 序号 {ax.number} 与标准不符（应为 {num_from_name(name)}）")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "axioms": {a.name_en: {"number": a.number, "law": a.law} for a in all_axioms()}
    }


def num_from_name(name: str) -> int:
    """从名称推断序号（用于校验）"""
    return {"growth": 1, "light": 2, "color": 3, "layout": 4,
            "narrative": 5, "boundary": 6, "freedom": 7, "causal": 8}.get(name, 0)


if __name__ == "__main__":
    result = validate_registry()
    print(f"Registry OK: {result['ok']}")
    for issue in result.get("issues", []):
        print(f"  ISSUE: {issue}")
    print()
    print("Axioms:")
    for ax in all_axioms():
        print(f"  {ax.number}. {ax.name_en} ({ax.name_zh}) → {ax.law}")
        print(f"     wudao-core: {ax.wudao_core_file}")
        print(f"     wukong_constraints: {ax.wukong_constraints_file}")
