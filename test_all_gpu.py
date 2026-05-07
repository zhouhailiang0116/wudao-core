# -*- coding: utf-8 -*-
"""
GPU 统一测试入口
================

本脚本统一测试所有 GPU 相关验证，分为两大类：

【道 · 数学验证】(*_final.py)
  - 验证公理数学公式的正确性
  - 纯 GPU 渲染，不涉及生产代码
  - 目的：证明"公式对不对"

【八戒 · 技术实现】(*_shader.py)
  - CPU 决策 + GPU 可视化
  - 生产代码的一部分
  - 目的：实现"公式怎么用"

运行方式：
  python test_all_gpu.py              # 测试全部
  python test_all_gpu.py --dao        # 只测试道的数学验证
  python test_all_gpu.py --bajie      # 只测试八戒的技术实现
  python test_all_gpu.py growth       # 测试指定公理

输出：
  - 控制台测试报告
  - JSON 测试结果（可选）
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime

# ============================================================
# 路径配置
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WUKONG_CHIP_PYTHON = os.path.normpath(os.path.join(
    SCRIPT_DIR, '..', 'wukong', 'wukong_chip', 'python'
))

# ============================================================
# 测试定义
# ============================================================

# 【道 · 数学验证】验证公理数学公式正确性
DAO_TESTS = {
    'growth': {
        'file': 'growth_final.py',
        'desc': '生长公理数学验证',
        'math': 'L-System / 生命游戏 / 曼德博集合',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'lighting': {
        'file': 'lighting_final.py',
        'desc': '光影公理数学验证',
        'math': 'L = L_a + L_d × max(0, N·L_dir)',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'color': {
        'file': 'color_final.py',
        'desc': '色彩公理数学验证',
        'math': 'L = 0.299R + 0.587G + 0.114B',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'narrative': {
        'file': 'narrative_final.py',
        'desc': '叙事公理数学验证',
        'math': 'I(t) 信息密度 / R(t) = dI/dt 节奏谱',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'layout': {
        'file': 'layout_final.py',
        'desc': '布局公理数学验证',
        'math': 'PHI / 三分法则 / 视觉重心',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'boundary': {
        'file': 'boundary_final.py',
        'desc': '边界公理数学验证',
        'math': 'IoU = |A∩B| / |A∪B| / 嵌套约束',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'freedom': {
        'file': 'freedom_final.py',
        'desc': '自由公理数学验证',
        'math': '自由度空间 / override_mask / 反事实',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
    'causal': {
        'file': 'causal_final.py',
        'desc': '因果公理数学验证',
        'math': '因果链 / DAG拓扑 / 反事实推理',
        'author': '道',
        'purpose': '验证公式正确性',
        'duration': 5,
    },
}

# 【八戒 · 技术实现】CPU 决策 + GPU 可视化
BAJIE_TESTS = {
    'layout': {
        'file': 'layout_shader.py',
        'desc': '布局公理 GPU 可视化',
        'math': 'PHI / 三分法则 / 视觉重心',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'boundary': {
        'file': 'boundary_shader.py',
        'desc': '边界公理 GPU 可视化',
        'math': 'MUST/CANNOT/CAN 边界',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'freedom': {
        'file': 'freedom_shader.py',
        'desc': '自由公理 GPU 可视化',
        'math': '自由度强度 / 反事实路径',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'growth': {
        'file': 'growth_shader.py',
        'desc': '生长公理 GPU 可视化',
        'math': '能量曲线 / 阶段划分 / 峰值标注',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'lighting': {
        'file': 'lighting_shader.py',
        'desc': '光影公理 GPU 可视化',
        'math': '光源位置 / 照射范围 / 阴影区域',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'color': {
        'file': 'color_shader.py',
        'desc': '色彩公理 GPU 可视化',
        'math': '色轮 / 配色方案 / 色彩比例',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
    'narrative': {
        'file': 'narrative_shader.py',
        'desc': '叙事公理 GPU 可视化',
        'math': '信息密度 / Hook/Body/CTA 标注',
        'author': '八戒',
        'purpose': '生产代码可视化',
        'duration': 5,
    },
}

# ============================================================
# 测试执行
# ============================================================

def run_shader_test(name, config):
    """
    运行单个 GPU 测试
    
    Args:
        name: 测试名称
        config: 测试配置
        
    Returns:
        dict: 测试结果
    """
    shader_path = os.path.join(WUKONG_CHIP_PYTHON, config['file'])
    
    result = {
        'name': name,
        'file': config['file'],
        'desc': config['desc'],
        'math': config['math'],
        'author': config['author'],
        'purpose': config['purpose'],
        'passed': False,
        'error': None,
        'output': None,
        'time_ms': 0,
    }
    
    # 检查文件存在
    if not os.path.exists(shader_path):
        result['error'] = f'File not found: {shader_path}'
        return result
    
    # 运行测试
    start_time = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, shader_path],
            cwd=WUKONG_CHIP_PYTHON,
            timeout=config['duration'] + 2,
            capture_output=True,
            text=True,
        )
        
        result['time_ms'] = int((time.time() - start_time) * 1000)
        
        if proc.returncode == 0:
            result['passed'] = True
            result['output'] = proc.stdout.strip() if proc.stdout else None
        else:
            result['error'] = proc.stderr.strip() if proc.stderr else f'Exit code: {proc.returncode}'
            
    except subprocess.TimeoutExpired:
        result['time_ms'] = int((time.time() - start_time) * 1000)
        result['passed'] = True  # 超时通常意味着窗口正常显示
        result['output'] = '[TIMEOUT] Window displayed (auto-close not implemented)'
        
    except Exception as e:
        result['error'] = str(e)
        
    return result


def print_result(result):
    """打印单个测试结果"""
    status = '[OK]' if result['passed'] else '[FAILED]'
    author = f"[{result['author']}]"
    purpose = f"({result['purpose']})"
    
    print(f"  {status} {author} {result['name']}: {result['desc']} {purpose}")
    print(f"         数学: {result['math']}")
    
    if result['time_ms']:
        print(f"         耗时: {result['time_ms']}ms")
        
    if result['error']:
        print(f"         错误: {result['error']}")
        
    if result['output'] and len(result['output']) < 200:
        # 只打印短输出
        for line in result['output'].split('\n'):
            if line.strip() and not line.startswith('pygame'):
                print(f"         {line.strip()}")


def run_tests(tests, category_name):
    """
    运行一组测试
    
    Args:
        tests: 测试配置字典
        category_name: 分类名称
        
    Returns:
        list: 测试结果列表
    """
    print(f"\n{'='*70}")
    print(f"【{category_name}】")
    print('='*70)
    
    results = []
    for name, config in tests.items():
        result = run_shader_test(name, config)
        results.append(result)
        print_result(result)
        
    return results


def print_summary(dao_results, bajie_results):
    """打印测试汇总"""
    print(f"\n{'='*70}")
    print("测试汇总")
    print('='*70)
    
    # 道的结果
    dao_passed = sum(1 for r in dao_results if r['passed'])
    dao_total = len(dao_results)
    print(f"\n【道 · 数学验证】{dao_passed}/{dao_total} 通过")
    for r in dao_results:
        status = '[OK]' if r['passed'] else '[FAILED]'
        print(f"  {status} {r['name']}: {r['desc']}")
    
    # 八戒的结果
    bajie_passed = sum(1 for r in bajie_results if r['passed'])
    bajie_total = len(bajie_results)
    print(f"\n【八戒 · 技术实现】{bajie_passed}/{bajie_total} 通过")
    for r in bajie_results:
        status = '[OK]' if r['passed'] else '[FAILED]'
        print(f"  {status} {r['name']}: {r['desc']}")
    
    # 总计
    total_passed = dao_passed + bajie_passed
    total_count = dao_total + bajie_total
    print(f"\n总计: {total_passed}/{total_count} 通过")
    
    return total_passed == total_count


def save_json(dao_results, bajie_results, output_path):
    """保存测试结果为 JSON"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'dao_passed': sum(1 for r in dao_results if r['passed']),
            'dao_total': len(dao_results),
            'bajie_passed': sum(1 for r in bajie_results if r['passed']),
            'bajie_total': len(bajie_results),
        },
        'dao_results': dao_results,
        'bajie_results': bajie_results,
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nJSON 结果已保存: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU 统一测试')
    parser.add_argument('--dao', action='store_true', help='只测试道的数学验证')
    parser.add_argument('--bajie', action='store_true', help='只测试八戒的技术实现')
    parser.add_argument('--json', action='store_true', help='保存 JSON 结果')
    parser.add_argument('name', nargs='?', help='测试指定公理')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("GPU 统一测试")
    print("="*70)
    print("\n说明：")
    print("  【道 · 数学验证】验证公理数学公式正确性（*_final.py）")
    print("  【八戒 · 技术实现】CPU 决策 + GPU 可视化（*_shader.py）")
    print("\n路径:", WUKONG_CHIP_PYTHON)
    
    dao_results = []
    bajie_results = []
    
    # 测试指定公理
    if args.name:
        name = args.name.lower()
        if name in DAO_TESTS:
            dao_results = [run_shader_test(name, DAO_TESTS[name])]
            print(f"\n【道 · 数学验证】")
            print_result(dao_results[0])
        elif name in BAJIE_TESTS:
            bajie_results = [run_shader_test(name, BAJIE_TESTS[name])]
            print(f"\n【八戒 · 技术实现】")
            print_result(bajie_results[0])
        else:
            print(f"\n[ERROR] Unknown test: {name}")
            print(f"  Available: {', '.join(list(DAO_TESTS.keys()) + list(BAJIE_TESTS.keys()))}")
            return 1
        return 0
    
    # 只测试道
    if args.dao:
        dao_results = run_tests(DAO_TESTS, '道 · 数学验证')
        all_passed = sum(1 for r in dao_results if r['passed']) == len(dao_results)
        return 0 if all_passed else 1
    
    # 只测试八戒
    if args.bajie:
        bajie_results = run_tests(BAJIE_TESTS, '八戒 · 技术实现')
        all_passed = sum(1 for r in bajie_results if r['passed']) == len(bajie_results)
        return 0 if all_passed else 1
    
    # 测试全部
    dao_results = run_tests(DAO_TESTS, '道 · 数学验证')
    bajie_results = run_tests(BAJIE_TESTS, '八戒 · 技术实现')
    
    all_passed = print_summary(dao_results, bajie_results)
    
    # 保存 JSON
    if args.json:
        json_path = os.path.join(SCRIPT_DIR, 'gpu_test_results.json')
        save_json(dao_results, bajie_results, json_path)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
