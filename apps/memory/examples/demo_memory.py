# -*- coding: utf-8 -*-
"""
wukong_memory/examples/demo_memory.py

悟空记忆法则 — 记忆演示

演示记忆图谱的添加/搜索/关联
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.memory_graph import MemoryGraph

def main():
    print("=== 悟空记忆法则演示 ===\n")

    graph = MemoryGraph()

    # 添加悟道体系记忆
    print("[添加记忆]")
    graph.add('光之法则', 'PIL物理光影渲染，8课体系', tags=['painter', 'video'])
    graph.add('色之法则', '配色/字体/布局/叙事', tags=['poster'])
    graph.add('动之法则', 'MoviePy+PIL动画，小玉9大技法', tags=['video'])
    graph.add('数学法则', '向量/插值/噪声/概率', tags=['math', '底层'])
    graph.add('空间组织', '锚点系统+深度层次+比例参考', tags=['creature', '物理'])
    graph.add('小玉技法', 'Perlin噪声/贝塞尔/粒子系统', tags=['video', 'math'])
    graph.add('悟空Avatar', '7头身比例+锚点式部件', tags=['creature', 'avatar'])

    # 关联记忆
    print("\n[关联记忆]")
    graph.link('光之法则', '色之法则')
    graph.link('光之法则', '动之法则')
    graph.link('动之法则', '数学法则')
    graph.link('数学法则', '小玉技法')
    graph.link('空间组织', '悟空Avatar')
    graph.link('悟空Avatar', '光之法则')
    graph.link('色之法则', '悟空Avatar')

    # 搜索
    print("\n[搜索'光']")
    for key, node, score in graph.search('光'):
        print(f"  [{score}] {key}: {node.content[:30]}...")

    print("\n[搜索'数学']")
    for key, node, score in graph.search('数学'):
        print(f"  [{score}] {key}: {node.content[:30]}...")

    # 按标签
    print("\n[标签=video]")
    for node in graph.get_by_tag('video'):
        print(f"  {node.key}: {node.content[:30]}...")

    # 关联传播
    print("\n[从'悟空Avatar'扩散1层]")
    for key, node in graph.get_associations('悟空Avatar', depth=1):
        print(f"  → {key}: {node.content[:30]}...")

    # 保存
    save_path = r'C:\Users\Public\Pictures\wukong_memory\memory_graph.json'
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    graph.save(save_path)
    print(f"\n[保存] {save_path}")
    print(f"[节点数] {len(graph.nodes)}")

    print("\n演示完成！")

if __name__ == '__main__':
    main()
