# -*- coding: utf-8 -*-
"""
MemorySystem - 记忆系统整合
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime


class MemorySystem:
    """
    记忆系统整合
    
    三个层级：
    - MEMORY.md（长期记忆）
    - IMA笔记（云端知识库）
    - 日志文件（运行记录）
    """
    
    def __init__(self, workspace: str = None):
        if workspace is None:
            workspace = os.path.expanduser("~/.qclaw/workspace")
        
        self.workspace = workspace
        self.memory_file = os.path.join(workspace, "MEMORY.md")
        self.log_dir = os.path.join(workspace, "memory")
        
        # 确保目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # IMA API配置（从环境变量读取）
        self.ima_config = {
            'client_id': os.environ.get('IMA_CLIENT_ID', ''),
            'api_key': os.environ.get('IMA_API_KEY', ''),
            'base_url': 'https://ima.qq.com/openapi/note/v1'
        }
    
    def log(self, task: Any, result: Any, success: bool = True) -> None:
        """记录执行日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task': str(task)[:200] if task else None,
            'result': str(result)[:500] if result else None,
            'success': success
        }
        
        # 写入日志文件
        log_file = self._get_log_file()
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def sync(self, state_snapshot: Dict[str, Any]) -> None:
        """同步到三个层级"""
        # 1. 写入日志（已在上面的log方法中完成）
        
        # 2. 定期更新MEMORY.md（每日）
        if self._should_update_memory():
            self._update_memory(state_snapshot)
        
        # 3. 同步到IMA（实时）- 暂时跳过，需要IMA API
        # self._sync_to_ima(state_snapshot)
    
    def _get_log_file(self) -> str:
        """获取今日日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{today}.log")
    
    def _should_update_memory(self) -> bool:
        """判断是否需要更新MEMORY.md"""
        if not os.path.exists(self.memory_file):
            return True
        
        # 检查最后修改时间
        mtime = os.path.getmtime(self.memory_file)
        last_modified = datetime.fromtimestamp(mtime)
        
        # 如果是今天已修改，则不需要再更新
        return last_modified.date() < datetime.now().date()
    
    def _update_memory(self, state_snapshot: Dict[str, Any]) -> None:
        """更新MEMORY.md"""
        # 读取现有内容
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# MEMORY.md\n\n"
        
        # 追加今日更新标记
        today = datetime.now().strftime("%Y-%m-%d")
        update_marker = f"\n\n---\n*Last updated: {today}*\n"
        
        if "*Last updated:" not in content:
            content += update_marker
        else:
            # 更新日期
            import re
            content = re.sub(
                r'\*Last updated:.*?\*',
                f'*Last updated: {today}*',
                content
            )
        
        # 写回文件
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def search(self, query: str, limit: int = 10) -> list:
        """搜索历史日志"""
        results = []
        log_file = self._get_log_file()
        
        if not os.path.exists(log_file):
            return results
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if query.lower() in line.lower():
                    try:
                        entry = json.loads(line.strip())
                        results.append(entry)
                        if len(results) >= limit:
                            break
                    except json.JSONDecodeError:
                        continue
        
        return results
    
    def get_today_stats(self) -> Dict[str, int]:
        """获取今日统计"""
        log_file = self._get_log_file()
        
        if not os.path.exists(log_file):
            return {'total': 0, 'success': 0, 'failed': 0}
        
        total = 0
        success = 0
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    total += 1
                    if entry.get('success'):
                        success += 1
                except json.JSONDecodeError:
                    continue
        
        return {
            'total': total,
            'success': success,
            'failed': total - success
        }
