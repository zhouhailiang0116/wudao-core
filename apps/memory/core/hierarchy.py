# -*- coding: utf-8 -*-
"""
core/hierarchy.py — 记忆层级模块

忆之法则·法二：遗忘机制

核心：
- 5层记忆结构
- 遗忘规则
- 层级转换
"""

from datetime import datetime, timedelta
from typing import Optional, List


class MemoryLevel:
    """记忆层级定义"""

    M0 = "core"       # 核心身份（永恒）
    M1 = "active"     # 当前项目（活跃）
    M2 = "archive"    # 历史经验（存档）
    M3 = "release"    # 过时框架（主动放下）
    M4 = "log"        # 每日日志（流水）
    M5 = "temp"       # 无足轻重（最先遗忘）

    LABELS = {
        M0: "核心身份",
        M1: "当前项目",
        M2: "历史经验",
        M3: "过时框架",
        M4: "每日日志",
        M5: "无足轻重",
    }

    @classmethod
    def label(cls, level: str) -> str:
        return cls.LABELS.get(level, level)


class MemoryEntry:
    """记忆条目"""

    def __init__(self, content: str, level: str = None, tags: List[str] = None):
        self.id = id(self)
        self.content = content
        self.level = level or MemoryLevel.M4
        self.tags = tags or []
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()
        self.access_count = 0

    def access(self):
        """访问记忆"""
        self.accessed_at = datetime.now()
        self.access_count += 1

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'content': self.content,
            'level': self.level,
            'tags': self.tags,
            'created': self.created_at.isoformat(),
            'accessed': self.accessed_at.isoformat(),
            'access_count': self.access_count,
        }


class MemoryHierarchy:
    """记忆层级管理器"""

    def __init__(self):
        self.stores = {
            MemoryLevel.M0: [],  # 核心身份（不清理）
            MemoryLevel.M1: [],  # 当前项目
            MemoryLevel.M2: [],  # 历史经验
            MemoryLevel.M3: [],  # 过时框架
            MemoryLevel.M4: [],  # 每日日志
            MemoryLevel.M5: [],  # 无足轻重
        }

    def add(self, entry: MemoryEntry):
        """添加记忆"""
        self.stores[entry.level].append(entry)

    def get(self, level: str = None, keyword: str = None) -> List[MemoryEntry]:
        """
        获取记忆
        
        参数：
        - level: 按层级获取
        - keyword: 关键词搜索
        """
        if level:
            entries = self.stores.get(level, [])
        else:
            # 搜索所有层级（从M0到M4，M5默认忽略）
            entries = []
            for lvl in [MemoryLevel.M0, MemoryLevel.M1, MemoryLevel.M2, 
                       MemoryLevel.M3, MemoryLevel.M4]:
                entries.extend(self.stores[lvl])

        if keyword:
            entries = [e for e in entries if keyword in e.content]

        # 更新访问
        for e in entries:
            e.access()

        return entries

    def forget(self, level: str, keep_count: int = 10):
        """
        遗忘指定层级的记忆
        
        参数：
        - level: 要遗忘的层级
        - keep_count: 保留最近N条
        """
        if level == MemoryLevel.M0:
            return  # M0不能清理

        entries = self.stores[level]
        if len(entries) > keep_count:
            # 按访问时间排序，删除最旧的
            entries.sort(key=lambda e: e.accessed_at)
            removed = entries[:-keep_count]
            self.stores[level] = entries[-keep_count:]
            return removed
        return []

    def promote(self, entry: MemoryEntry, target_level: str):
        """
        提升记忆层级（重要化）
        """
        # 从原层级移除
        self.stores[entry.level].remove(entry)
        # 加入新层级
        entry.level = target_level
        self.stores[target_level].append(entry)

    def demote(self, entry: MemoryEntry, target_level: str):
        """
        降级记忆层级（不重要化）
        """
        self.promote(entry, target_level)  # 逻辑相同

    def summary(self) -> dict:
        """记忆统计"""
        return {
            MemoryLevel.label(level): len(entries)
            for level, entries in self.stores.items()
        }


# ==============================================
# 验证
# ==============================================
def verify_hierarchy():
    """验证记忆层级"""
    store = MemoryHierarchy()

    # 添加记忆
    store.add(MemoryEntry("我是道，虾大", MemoryLevel.M0, ["身份"]))
    store.add(MemoryEntry("今天的龙虾训练完成了", MemoryLevel.M1, ["训练"]))
    store.add(MemoryEntry("wukong_poster体系搭建完成", MemoryLevel.M2, ["项目"]))
    store.add(MemoryEntry("很久以前的框架", MemoryLevel.M3, ["旧"]))
    store.add(MemoryEntry("2026-04-04日志", MemoryLevel.M4, ["日志"]))
    store.add(MemoryEntry("一些无足轻重的对话", MemoryLevel.M5, ["临时"]))

    print("=" * 50)
    print("记忆层级验证")
    print("=" * 50)

    summary = store.summary()
    for level, count in summary.items():
        print(f"{level}: {count}条")

    # 搜索
    results = store.get(keyword="龙虾")
    print(f"\n搜索'龙虾': {len(results)}条结果")

    # 遗忘M5
    removed = store.forget(MemoryLevel.M5)
    print(f"遗忘M5: 清理了{len(removed) if removed else 0}条")


if __name__ == "__main__":
    verify_hierarchy()
