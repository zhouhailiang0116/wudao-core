# -*- coding: utf-8 -*-
"""
悟空记忆系统
让悟空学会积累经验，第二天不遗忘
"""
import os
import json
from datetime import datetime

MEMORY_DIR = r'C:\Users\周海亮\.qclaw\workspace\scripts\悟空\memory'
os.makedirs(MEMORY_DIR, exist_ok=True)

class WukongMemory:
    def __init__(self):
        self.version = "v8"  # 当前版本
        self.skills = {}     # 学会的技能
        self.lessons = []    # 学到的教训
        self.creations = [] # 创作记录
        self.load()
    
    def load(self):
        """加载记忆"""
        memory_file = os.path.join(MEMORY_DIR, 'wukong_memory.json')
        if os.path.exists(memory_file):
            with open(memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.skills = data.get('skills', {})
                self.lessons = data.get('lessons', [])
                self.creations = data.get('creations', [])
                self.version = data.get('version', 'v1')
    
    def save(self):
        """保存记忆"""
        memory_file = os.path.join(MEMORY_DIR, 'wukong_memory.json')
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': self.version,
                'skills': self.skills,
                'lessons': self.lessons,
                'creations': self.creations,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M')
            }, f, ensure_ascii=False, indent=2)
    
    def learn_skill(self, skill_name, skill_desc, level=1):
        """学会新技能"""
        self.skills[skill_name] = {
            'desc': skill_desc,
            'level': level,
            'learned': datetime.now().strftime('%Y-%m-%d')
        }
        self.save()
        print(f"[记忆] 学会技能: {skill_name} ({level}级)")
    
    def add_lesson(self, lesson):
        """添加教训"""
        self.lessons.append({
            'text': lesson,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        self.save()
        print(f"[记忆] 新教训: {lesson}")
    
    def add_creation(self, name, desc, file_path=""):
        """添加创作记录"""
        self.creations.append({
            'name': name,
            'desc': desc,
            'file': file_path,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        self.save()
        print(f"[记忆] 新创作: {name}")
    
    def get_summary(self):
        """获取记忆摘要"""
        return f"""
=== 悟空记忆系统 ===
版本: {self.version}
技能数: {len(self.skills)}
教训数: {len(self.lessons)}
创作数: {len(self.creations)}

已学会的技能:
{chr(10).join([f'  - {k}: {v["desc"]}' for k, v in self.skills.items()])}

最近教训:
{chr(10).join([f'  - {l["date"]}: {l["text"]}' for l in self.lessons[-3:]])}
"""
    
    def remember(self):
        """唤醒记忆，输出已学内容"""
        if self.skills:
            print(self.get_summary())
        else:
            print("[悟空] 我还没有记忆，从零开始...")

# ========== 测试 ==========
if __name__ == "__main__":
    w = WukongMemory()
    
    # 模拟今天学的内容
    print("=== 悟空唤醒 ===")
    w.remember()
    
    print("\n=== 学习新内容 ===")
    w.learn_skill("camera_vision", "摄像头视觉感知", 2)
    w.learn_skill("narrative", "四格漫画叙事结构", 2)
    w.add_lesson("Pillow的getsize改名为getbbox")
    w.add_creation("灵感猎人", "基于素材库分析的四格漫画")
    
    print("\n=== 再次唤醒 ===")
    w.remember()
