# wukong-memory — 记忆法则

> 记忆不是存储，是关联与遗忘的艺术。

---

## 一、记忆层级（M0-M5）

| 层级 | 内容 | 遗忘周期 |
|------|------|---------|
| M0 | 核心身份（我是谁/跟谁走/根本法则） | 永不遗忘 |
| M1 | 当前项目/策划知识/近期教训 | 月度更新 |
| M2 | 历史经验/工具配置/架构决策 | 季度回顾 |
| M3 | 过时框架/矛盾体系（主动放下） | 随时放下 |
| M4 | 每日对话记录/工作日志 | 周度清理 |
| M5 | 无关紧要的/已过时的热点 | 最先遗忘 |

---

## 二、核心模块

| 模块 | 文件 | 内容 |
|------|------|------|
| hierarchy | hierarchy.py | 遗忘机制、层级定义 |
| search | search.py | 记忆检索 |
| memory_graph | memory_graph.py | **关联图谱**（新增） |

---

## 三、关联图谱（新增）

### 什么是记忆图谱

```
悟道法则 ←→ 数学法则
    ↑           ↑
    ↑———————→  ↑
    光之法则 ←→ 色之法则
```

记忆不是孤立的点，是互相连接的网络。

### 核心功能

```python
graph = MemoryGraph()

# 添加记忆
graph.add('光之法则', 'PIL物理光影渲染', tags=['painter'])
graph.add('色之法则', '配色/字体/布局', tags=['poster'])
graph.add('数学法则', '向量/插值/噪声', tags=['math'])

# 关联
graph.link('光之法则', '色之法则')
graph.link('光之法则', '数学法则')

# 搜索
graph.search('光')  # 返回相关记忆

# 按标签
graph.get_by_tag('math')

# 扩散关联
graph.get_associations('光之法则', depth=1)
```

---

## 四、悟道体系记忆图谱

### 核心节点

| 节点 | 内容 | 标签 |
|------|------|------|
| 光之法则 | PIL物理光影，8课体系 | painter, video |
| 色之法则 | 配色/字体/布局/叙事 | poster |
| 动之法则 | MoviePy+PIL动画，小玉9大技法 | video |
| 数学法则 | 向量/插值/噪声/概率 | math, 底层 |
| 空间组织 | 锚点系统+深度层次+比例参考 | creature |
| 小玉技法 | Perlin噪声/贝塞尔/粒子 | video, math |
| 悟空Avatar | 7头身比例+锚点式部件 | creature, avatar |
| 物理法则 | 数字+物理世界，四步闭环 | physics |

### 关联关系

```
光 ←→ 色 ←→ 悟空Avatar ←→ 空间组织
 ↓       ↓
动 ←→ 数学 ←→ 小玉技法
         ↓
       物理
```

---

## 五、IMA笔记联动

IMA笔记是悟道的外部记忆：
- **folder_id**: 工作日志/内容运营/量化交易/知识库/数字人
- **API**: Client ID + API Key 已配置

```python
# IMA笔记写入
import sys
sys.path.insert(0, r'C:\Users\周海亮\.qclaw\workspace')
from scripts.ima_api import IMAClient

client = IMAClient()
client.create_note(title='新记忆', content='...', folder_id='...')
```

---

*忆之法则：记住该记住的，遗忘该遗忘的，关联该关联的*


---

## 数学依赖

本模块依赖 `wukong-math` 的以下能力：

- graph (关联图谱)

```python
import sys
sys.path.insert(0, r'C:\Users\周海亮\.qclaw\workspace\wukong\wukong-math')
from core import Vec2, lerp, perlin_noise_1d  # 按需导入
```
