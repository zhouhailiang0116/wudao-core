# -*- coding: utf-8 -*-
"""
core/search.py — 记忆检索模块

忆之法则·法三：检索能力

核心：
- 关键词搜索
- 时间范围
- 标签过滤
- 关联追溯
"""

from datetime import datetime
from typing import List, Optional
import re


class MemorySearcher:
    """记忆检索器"""

    def __init__(self, memory_store):
        self.store = memory_store

    def search(self, query: str, 
               levels: List[str] = None,
               tags: List[str] = None,
               from_date: datetime = None,
               to_date: datetime = None,
               limit: int = 50) -> List[dict]:
        """
        综合检索
        
        参数：
        - query: 搜索词
        - levels: 限定层级
        - tags: 限定标签
        - from_date: 开始时间
        - to_date: 结束时间
        - limit: 返回数量限制
        """
        # 初始化搜索范围
        if levels:
            entries = []
            for level in levels:
                entries.extend(self.store.stores.get(level, []))
        else:
            entries = []
            for lvl in self.store.stores.values():
                entries.extend(lvl)

        # 关键词搜索
        if query:
            query_lower = query.lower()
            entries = [
                e for e in entries
                if query_lower in e.content.lower()
            ]

        # 标签过滤
        if tags:
            entries = [
                e for e in entries
                if any(tag in e.tags for tag in tags)
            ]

        # 时间范围
        if from_date:
            entries = [e for e in entries if e.created_at >= from_date]
        if to_date:
            entries = [e for e in entries if e.created_at <= to_date]

        # 排序：按访问次数和最近访问
        entries.sort(
            key=lambda e: (e.access_count, e.accessed_at.timestamp()),
            reverse=True
        )

        # 更新访问
        for e in entries[:limit]:
            e.access()

        return [e.to_dict() for e in entries[:limit]]

    def search_by_keyword(self, keyword: str) -> List[dict]:
        """纯关键词搜索"""
        return self.search(keyword)

    def search_by_tag(self, tag: str) -> List[dict]:
        """按标签搜索"""
        return self.search("", tags=[tag])

    def search_by_time(self, days: int = 7) -> List[dict]:
        """最近N天的记忆"""
        from datetime import timedelta
        since = datetime.now() - timedelta(days=days)
        return self.search("", from_date=since)


class MemoryIndexer:
    """记忆索引器"""

    def __init__(self):
        self.keywords = {}  # keyword -> [entry_ids]
        self.tags = {}      # tag -> [entry_ids]

    def index(self, entry):
        """为记忆建立索引"""
        # 关键词索引
        words = re.findall(r'\w+', entry.content.lower())
        for word in words:
            if len(word) >= 2:  # 忽略单字
                if word not in self.keywords:
                    self.keywords[word] = []
                self.keywords[word].append(entry.id)

        # 标签索引
        for tag in entry.tags:
            if tag not in self.tags:
                self.tags[tag] = []
            self.tags[tag].append(entry.id)

    def search_index(self, keyword: str) -> List[int]:
        """索引搜索"""
        keyword = keyword.lower()
        return self.keywords.get(keyword, [])


# ==============================================
# 验证
# ==============================================
def verify_search():
    """验证检索"""
    from core.hierarchy import MemoryHierarchy, MemoryEntry, MemoryLevel

    store = MemoryHierarchy()

    # 添加测试数据
    store.add(MemoryEntry("龙虾绘画训练完成了", MemoryLevel.M1, ["训练", "龙虾"]))
    store.add(MemoryEntry("wukong_painter体系完整了", MemoryLevel.M1, ["项目", "绘画"]))
    store.add(MemoryEntry("今天的早报生成了", MemoryLevel.M4, ["日报"]))

    searcher = MemorySearcher(store)

    print("=" * 50)
    print("记忆检索验证")
    print("=" * 50)

    results = searcher.search_by_keyword("龙虾")
    print(f"搜索'龙虾': {len(results)}条")

    results = searcher.search_by_tag("训练")
    print(f"标签'训练': {len(results)}条")

    results = searcher.search_by_time(days=7)
    print(f"最近7天: {len(results)}条")


if __name__ == "__main__":
    verify_search()
