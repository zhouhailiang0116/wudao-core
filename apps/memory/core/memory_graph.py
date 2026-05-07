# -*- coding: utf-8 -*-
"""
wukong_memory/core/memory_graph.py

悟空记忆法则 — 记忆关联图谱

来源：MEMORY.md的记忆层级体系
联动：wukong_math（概率+图论）
"""

import os
import json
from datetime import datetime


class MemoryNode:
    """记忆节点"""
    def __init__(self, key, content, level='M1', tags=None):
        self.key = key
        self.content = content
        self.level = level  # M0-M5
        self.tags = tags or []
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()
        self.access_count = 0
        self.associations = []  # 关联节点key列表
    
    def access(self):
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def to_dict(self):
        return {
            'key': self.key,
            'content': self.content[:100],
            'level': self.level,
            'tags': self.tags,
            'created': self.created_at.isoformat(),
            'accessed': self.accessed_at.isoformat(),
            'access_count': self.access_count,
            'associations': self.associations,
        }


class MemoryGraph:
    """
    记忆关联图谱
    
    用法：
    graph = MemoryGraph()
    graph.add('光之法则', 'PIL物理光影渲染', tags=['painter', 'video'])
    graph.link('光之法则', '色之法则')
    results = graph.search('光')
    """
    
    def __init__(self):
        self.nodes = {}  # key -> MemoryNode
        self.tag_index = {}  # tag -> [key]
    
    def add(self, key, content, level='M1', tags=None):
        """添加记忆节点"""
        node = MemoryNode(key, content, level, tags)
        self.nodes[key] = node
        
        # 标签索引
        if tags:
            for tag in tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(key)
        
        return node
    
    def link(self, key1, key2):
        """关联两个记忆节点"""
        if key1 in self.nodes and key2 in self.nodes:
            if key2 not in self.nodes[key1].associations:
                self.nodes[key1].associations.append(key2)
            if key1 not in self.nodes[key2].associations:
                self.nodes[key2].associations.append(key1)
    
    def get(self, key):
        """获取记忆"""
        if key in self.nodes:
            self.nodes[key].access()
        return self.nodes.get(key)
    
    def search(self, query, limit=10):
        """搜索记忆"""
        results = []
        query_lower = query.lower()
        
        for key, node in self.nodes.items():
            score = 0
            if query_lower in key.lower():
                score += 10
            if query_lower in node.content.lower():
                score += 5
            if any(query_lower in tag.lower() for tag in node.tags):
                score += 3
            if score > 0:
                results.append((key, node, score))
        
        results.sort(key=lambda x: (-x[2], -x[1].access_count))
        return results[:limit]
    
    def get_by_tag(self, tag):
        """按标签获取记忆"""
        keys = self.tag_index.get(tag, [])
        return [self.nodes[k] for k in keys if k in self.nodes]
    
    def get_associations(self, key, depth=1):
        """获取记忆关联（深度遍历）"""
        if key not in self.nodes:
            return []
        
        visited = {key}
        frontier = [key]
        result = []
        
        for _ in range(depth):
            next_frontier = []
            for k in frontier:
                node = self.nodes.get(k)
                if not node:
                    continue
                for assoc_key in node.associations:
                    if assoc_key not in visited:
                        visited.add(assoc_key)
                        next_frontier.append(assoc_key)
                        result.append((assoc_key, self.nodes[assoc_key]))
            frontier = next_frontier
        
        return result
    
    def save(self, filepath):
        """保存到文件"""
        data = {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'tag_index': self.tag_index,
        }
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath):
        """从文件加载"""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for key, d in data.get('nodes', {}).items():
            node = MemoryNode(d['key'], d['content'], d['level'], d['tags'])
            node.access_count = d.get('access_count', 0)
            node.associations = d.get('associations', [])
            self.nodes[key] = node
        
        self.tag_index = data.get('tag_index', {})
