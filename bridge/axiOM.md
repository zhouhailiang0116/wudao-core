# axiom ↔ Python ↔ GLSL 翻译映射表

> 维护者：八戒
> 最后更新：2026-04-09

---

## axiom → Python → GLSL 完整链路

### axiom1 生长（Growth）

```
数学：分形递归，L-System
Python：axiom1_growth.py
核心函数：generate_l_system(iterations, axiom, rules)
GPU：无（CPU生成顶点数据）
```

### axiom2 光影（Lighting）

```
数学：brightness = ambient + diffuse × max(0, N·L)
Python：axiom2_lighting.py
核心函数：get_diffuse(normal, light_dir)
GPU：shaders/diffuse.glsl
片段着色器：
  N = normalize(frag_normal)
  L = normalize(light_dir)
  NdotL = max(0.0, dot(N, L))
  brightness = ambient + diffuse_strength * NdotL
```

### axiom3 色彩（Color）

```
数学：五调子分类（黑白/灰度/单色/暖色/冷色）
Python：axiom3_color.py
核心函数：get_tone(r, g, b) → tone_name
GPU：shaders/five_tones.glsl
片段着色器：
  brightness = dot(color.rgb, vec3(0.299, 0.587, 0.114))
  五档阈值判断
```

### axiom4 布局（Layout）

```
数学：中心引力 + 边缘排斥 + 黄金比例
Python：axiom4_layout.py
核心函数：compute_layout(width, height)
GPU：layout_shader.glsl
片段着色器：
  gravity = vec2(0.5, 0.5)
  repulsion = 1.0 / (distance^2 + epsilon)
  golden_ratio = 1.618
```

### axiom5 叙事（Narrative）

```
数学：起承转合四阶段
Python：axiom5_narrative.py
核心函数：narrative_step(current_time) → phase
GPU：narrative_shader.glsl
片段着色器：
  phase = mod(time, 4.0)  // 0=起, 1=承, 2=转, 3=合
  color = mix(color_a, color_b, phase_ratio)
```

### axiom6 边界（Boundary）

```
数学：inside/outside 布尔判断
Python：axiom6_boundary.py
核心函数：is_inside(x, y, boundary_func)
GPU：boundary_shader.glsl
片段着色器：
  result = boundary_func(uv)
  if (result > 0.0) discard;
```

### axiom7 自由（Freedom）

```
数学：随机 + 约束平衡
Python：axiom7_freedom.py
核心函数：apply_freedom(base_value, freedom_degree)
GPU：freedom_shader.glsl
片段着色器：
  random = fract(sin(dot(uv, vec2(12.9898, 78.233))) * 43758.5453)
  result = mix(deterministic, random, freedom_degree)
```

### axiom8 因果（Causal）

```
数学：condition → effect 映射
Python：axiom8_causal.py
核心函数：evaluate_causal(condition, effect_rules)
GPU：GPU加速版待实现
```

---

## 通用翻译规则

| axiom层 | Python层 | GLSL层 |
|---------|----------|--------|
| `*_axiom()` | `axiom*.py` 函数 | `*.glsl` 片段着色器 |
| 数学向量 | NumPy array | `vec2/vec3/vec4` |
| 标量 | Python float | `float` |
| 布尔 | Python bool | `if/else` |

---

## 调试技巧

### 1. import冲突
**问题**：NumPy和OpenGL同时导入导致类型冲突
**解决**：先import OpenGL，再import numpy，或调整顺序

### 2. 球体不可见
**问题**：look_at矩阵导致球体被变换到视野外
**解决**：用简化顶点着色器 `gl_Position = vec4(a_position * 0.6, 1.0)`

### 3. 着色器不生效
**检查**：
1. 顶点着色器编译错误 → 看终端输出
2. 片段着色器未链接 → 检查shader program
3. uniform未上传 → 检查 `glUniform*` 调用

---

*八戒维护 · 道记忆*
