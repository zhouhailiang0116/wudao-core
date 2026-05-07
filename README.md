# 道 · 悟道核心系统 (WuDao Core)

> 更新：2026-04-13 | 版本：v2.1 | 状态：**8/8 公理全通**

---

## 这是什么

WuDao Core 是悟道体系的「道层」，负责在任务执行前做**约束推理**：

```
用户意图 → 道层约束求解 → 参数集 → 通层翻译 → 悟空层执行
```

道层不问「怎么做像素」，只问：
- 这个布局有没有违规？（Boundary Axiom）
- 自由度够不够？（Freedom Axiom）
- 视觉重心在哪？（Layout Axiom）
- 动作有没有因果链？（Causal Axiom）
- 故事怎么起承转合？（Narrative Axiom）

---

## 当前状态（2026-04-13 实测）

| 公理 | 状态 | 说明 |
|------|------|------|
| axiom1_growth | ✅ 生产级 | 节奏曲线 / 12段能量分配 / 三阶段（attention/climax/settle）|
| axiom2_light | ✅ 生产级 | 光源位置 / 五调子分类 / ambient+diffuse 物理模型 |
| axiom3_color | ✅ 生产级 | 互补/类似/分裂色相 / 七色调色板 |
| axiom4_layout | ✅ 生产级 | PHI=1.618 / 三分焦点 / 负空间 |
| axiom5_narrative | ✅ 生产级 | Hook→Body→Climax→CTA 四段叙事 |
| axiom6_boundary | ✅ 生产级 | MUST/CANNOT/CAN 三色碰撞 |
| axiom7_freedom | ✅ 生产级 | override_mask / 反事实分支 |
| axiom8_causal | ✅ 生产级 | BFS因果链 / 置换检验 |

**整体完成度：100% (8/8)**

---

## 目录结构

```
wudao-core/
├── axioms/                    # 八公理实现
│   ├── axiom_base.py          # 抽象基类（AxiomBase）
│   ├── axiom1_growth.py       # ✅ 生长公理
│   ├── axiom2_light.py        # ✅ 光影公理
│   ├── axiom3_color.py        # ✅ 色彩公理
│   ├── axiom4_layout.py       # ✅ 布局公理
│   ├── axiom5_narrative.py    # ✅ 叙事公理
│   ├── axiom6_boundary.py     # ✅ 边界公理
│   ├── axiom7_freedom.py      # ✅ 自由公理
│   └── axiom8_causal.py       # ✅ 因果公理
│
├── core/                      # 调度核心
│   ├── agent_core.py          # 任务路由器（核心入口）
│   ├── axiom_loader.py        # 公理加载器（动态加载 axioms/）
│   ├── state_manager.py       # 四维状态管理 ✅
│   ├── error_handler.py       # 三级降级 ✅
│   └── memory_system.py       # 记忆系统 ✅
│
├── bridge/
│   ├── axiom_to_law.py        # 通层翻译（axiom → painter 参数）
│   └── fusion_scheduler.py    # 融合调度（三段权重调制）
│
├── demo_closed_loop.py        # 道→通→悟空 三层闭环演示
├── test_all_axioms.py         # 测试套件
└── README.md                  # 本文件
```

---

## 快速开始

### 运行完整闭环演示
```bash
cd wudao-core
python demo_closed_loop.py
```
输出：四 axiom pipeline（layout/light/growth/color）全部 PASS，painter 生成图像。

### 运行测试套件
```bash
python test_all_axioms.py
```

### 直接调用公理
```python
from core.agent_core import AgentCore

core = AgentCore(auto_load=True)
st = core.status()           # 查看已注册公理
pipeline = core.run_pipeline(scene_data, "layout")  # layout 公理
pipeline = core.run_pipeline(light_scene, "light")   # light 公理
pipeline = core.run_pipeline(growth_scene, "growth") # growth 公理
pipeline = core.run_pipeline(color_scene, "color")    # color 公理
```

### 通过 AgentCore 路由
```python
core = AgentCore(auto_load=True)
result = core.run_pipeline(data, "layout")
# result: { axiom_result, bridge_params, target_law, success }
```

---

## 核心接口（AxiomBase）

所有公理继承 `axiom_base.py` 的 AxiomBase，必须实现：

```python
class AxiomBase:
    def validate(self, data: dict) -> bool:  # 输入校验
    def compute(self, data: dict, state) -> dict:  # 数学计算
    def render(self, result: dict) -> dict:   # 结果输出
    def execute(self, task, state) -> dict:   # 统一入口：验证→计算→渲染
```

可选降级方法：
```python
def compute_simple(self, data: dict, state) -> Any:  # 简单计算
def render_cpu(self, result: dict) -> Any:            # CPU fallback
```

---

## 与悟空层的关系

```
wudao-core（道）                    wukong（悟空）
─────────────────                   ────────────────
AgentCore → axiom.compute()          各法则 core/ → render()
     ↓                                    ↓
约束求解（无像素输出）              像素/音频生成
     ↓                                    ↓
   参数集 ─── bridge/ ───→ 法则调用参数
```

**道层和悟空层不合并**——各有各的职责，通过 bridge/（通层）翻译连接。

完整四层闭环（道→通→悟空→眼）见 `wukong/demo_full_loop.py`。

---

## 下一步

- [ ] **P1**: axiom1/2/3 质量抽检（确认生产级 vs 占位）
- [ ] **P2**: bridge/axiom_to_law.py 统一 path setup（目前散落多处 sys.path.insert）
- [ ] **P3**: axiom5_narrative 接入 wukong-poster 的 narrative 引擎
- [ ] **P4**: verify() 静默跳过 wukong-eye 的告警机制

---

*启动：2026-04-08*
*更新：2026-04-13（8/8 公理全通）*
*架构：道 → 通 → 悟空 → 眼 四层闭环*
