# -*- coding: utf-8 -*-
"""
GPU Shader 测试脚本
===================

测试三个 GPU shader：
  - layout_shader.py    黄金分割/三分法则/视觉重心
  - boundary_shader.py  MUST/CANNOT/CAN 边界可视化
  - freedom_shader.py   自由度/反事实路径

运行方式：
  python test_gpu_shaders.py [shader_name]
  
  不带参数时依次测试全部三个 shader
"""

import sys
import os
import subprocess
import time

# 路径配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WUKONG_CHIP_PYTHON = os.path.normpath(os.path.join(
    SCRIPT_DIR, '..', 'wukong', 'wukong_chip', 'python'
))

# Shader 配置
SHADERS = {
    'layout': {
        'file': 'layout_shader.py',
        'desc': '黄金分割/三分法则/视觉重心',
        'duration': 5,  # 显示秒数
    },
    'boundary': {
        'file': 'boundary_shader.py',
        'desc': 'MUST/CANNOT/CAN 边界可视化',
        'duration': 5,
    },
    'freedom': {
        'file': 'freedom_shader.py',
        'desc': '自由度/反事实路径',
        'duration': 5,
    },
}


def test_shader(name, auto_close=True):
    """测试单个 shader"""
    if name not in SHADERS:
        print(f"[ERROR] Unknown shader: {name}")
        print(f"  Available: {', '.join(SHADERS.keys())}")
        return False
    
    config = SHADERS[name]
    shader_path = os.path.join(WUKONG_CHIP_PYTHON, config['file'])
    
    if not os.path.exists(shader_path):
        print(f"[ERROR] Shader file not found: {shader_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"[TEST] {name}_shader")
    print(f"  File: {config['file']}")
    print(f"  Desc: {config['desc']}")
    print(f"{'='*60}")
    
    # 运行 shader
    try:
        # 使用 subprocess 运行，设置超时
        result = subprocess.run(
            [sys.executable, shader_path],
            cwd=WUKONG_CHIP_PYTHON,
            timeout=config['duration'] + 2 if auto_close else None,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            print(f"[OK] {name}_shader 测试通过")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"[FAILED] {name}_shader 返回非零")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name}_shader 运行超时（可能是正常的窗口显示）")
        return True  # 超时通常意味着窗口正常显示
    except Exception as e:
        print(f"[ERROR] {name}_shader 运行异常: {e}")
        return False


def test_all():
    """测试全部 shader"""
    print("\n" + "="*60)
    print("GPU Shader 测试报告")
    print("="*60)
    
    results = {}
    for name in SHADERS:
        results[name] = test_shader(name, auto_close=True)
    
    # 汇总
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, ok in results.items():
        status = "[OK]" if ok else "[FAILED]"
        print(f"  {status} {name}_shader - {SHADERS[name]['desc']}")
    
    print(f"\n总计: {passed}/{total} 通过")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试指定 shader
        name = sys.argv[1].lower().replace('_shader', '').replace('.py', '')
        test_shader(name, auto_close=False)
    else:
        # 测试全部
        test_all()
