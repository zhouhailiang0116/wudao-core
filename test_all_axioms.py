# -*- coding: utf-8 -*-
"""
test_all_axioms.py - 八公理综合测试
===================================

当前状态（2026-04-09 诊断）：
  ✅ axiom4_layout   - 布局公理（PHI=1.618 / 三分焦点 / 负空间 / 黄金矩形）
  ✅ axiom6_boundary  - 边界公理（MUST/CANNOT/CAN 三色碰撞）
  ✅ axiom7_freedom   - 自由公理（override_mask / intensity / 反事实）
  ✅ axiom8_causal    - 因果公理（BFS因果链 / 置换检验 / 反事实推理）
  ❌ axiom1_growth    - 缺失（wukong_constraints 有 lesson 脚本，非生产 axiom）
  ❌ axiom2_light     - 缺失（同上）
  ❌ axiom3_color     - 缺失（同上）
  ⚠️ axiom5_narrative - 体系最缺的一块（wukong_constraints 有 lesson）

整体完成度：62.5% (5/8)
"""
import sys
import os

workspace = os.path.expanduser("~/.qclaw/workspace")
sys.path.insert(0, workspace)


def test_imports():
    """测试1: 模块导入"""
    print("\n" + "="*60)
    print("Test 1: Module Imports")
    print("="*60)
    try:
        from axioms import AxiomBase, LayoutAxiom, BoundaryAxiom, FreedomAxiom, CausalAxiom, NarrativeAxiom, LightAxiom, ColorAxiom, GrowthAxiom
        print("[PASS] 8 axiom modules imported")
        print("  GrowthAxiom    ✅")
        print("  LightAxiom    ✅")
        print("  ColorAxiom    ✅")
        print("  LayoutAxiom   ✅")
        print("  NarrativeAxiom ✅")
        print("  BoundaryAxiom ✅")
        print("  FreedomAxiom  ✅")
        print("  CausalAxiom   ✅")
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


def test_layout_axiom():
    """测试2: 布局公理"""
    print("\n" + "="*60)
    print("Test 2: Layout Axiom (axiom4_layout)")
    print("="*60)
    try:
        from axioms import LayoutAxiom
        axiom = LayoutAxiom()
        data = {
            'elements': [
                {'position': {'x': 200, 'y': 150}, 'size': {'width': 100, 'height': 100}, 'visual_weight': 1.0},
                {'position': {'x': 400, 'y': 300}, 'size': {'width': 150, 'height': 150}, 'visual_weight': 1.5}
            ],
            'canvas': {'width': 800, 'height': 600}
        }
        valid = axiom.validate(data)
        print(f"  Validation: {'PASS' if valid else 'FAIL'}")
        if not valid:
            return False
        result = axiom.compute(data, None)
        print(f"  Visual Center: ({result['visual_center']['x']:.1f}, {result['visual_center']['y']:.1f})")
        print(f"  Negative Space: {result['negative_space_ratio']:.1%}")
        print(f"  Golden Ratio (phi): {result['phi']:.4f}")
        output = axiom.render(result)
        print(f"  Render: {output['status']}")
        return output['status'] == 'success'
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_boundary_axiom():
    """测试3: 边界公理"""
    print("\n" + "="*60)
    print("Test 3: Boundary Axiom (axiom6_boundary)")
    print("="*60)
    try:
        from axioms import BoundaryAxiom
        axiom = BoundaryAxiom()
        data = {
            'boundaries': [
                {'type': 'MUST', 'rect': (100, 100, 200, 200)},
                {'type': 'CANNOT', 'rect': (250, 100, 350, 200)},
                {'type': 'CAN', 'rect': (400, 100, 500, 200)}
            ]
        }
        valid = axiom.validate(data)
        print(f"  Validation: {'PASS' if valid else 'FAIL'}")
        if not valid:
            return False
        result = axiom.compute(data, None)
        print(f"  MUST: {result['must_count']}  CANNOT: {result['cannot_count']}  CAN: {result['can_count']}")
        print(f"  Violations: {len(result['violations'])}")
        output = axiom.render(result)
        print(f"  Render: {output['status']}")
        return output['status'] == 'success'
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_freedom_axiom():
    """测试4: 自由公理"""
    print("\n" + "="*60)
    print("Test 4: Freedom Axiom (axiom7_freedom)")
    print("="*60)
    try:
        from axioms import FreedomAxiom
        axiom = FreedomAxiom()
        data = {
            'freedom': {
                'intensity': 0.7,
                'override_mask': [True, False, True, False, True],
                'alternatives': [
                    {'name': 'path_a', 'probability': 0.4, 'outcome': 'success'},
                    {'name': 'path_b', 'probability': 0.3, 'outcome': 'partial'}
                ]
            },
            'constraints': {'must': [1, 2], 'cannot': [3, 4], 'can': [5, 6, 7, 8, 9]}
        }
        valid = axiom.validate(data)
        print(f"  Validation: {'PASS' if valid else 'FAIL'}")
        if not valid:
            return False
        result = axiom.compute(data, None)
        print(f"  Intensity: {result['intensity']:.2f}  Freedom Space: {result['freedom_space']:.1%}")
        print(f"  Override Ratio: {result['override_ratio']:.1%}  Counterfactuals: {len(result['counterfactuals'])}")
        output = axiom.render(result)
        print(f"  Render: {output['status']}")
        return output['status'] == 'success'
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_narrative_axiom():
    """测试5: 叙事公理"""
    print("\n" + "="*60)
    print("Test 5: Narrative Axiom (axiom5_narrative)")
    print("="*60)
    try:
        from axioms import NarrativeAxiom
        axiom = NarrativeAxiom()
        data = {
            'topic': '认知升级',
            'hook_type': 'counter',
            'num_body_lines': 3,
            'limit': 200
        }
        valid = axiom.validate(data)
        print(f"  Validation: {'PASS' if valid else 'FAIL'}")
        if not valid:
            return False
        result = axiom.compute(data, None)
        print(f"  Hook: {result['hook'][:40]}...")
        print(f"  Body lines: {result['body_count']}  Score: {result['score']:.2f}")
        output = axiom.render(result)
        print(f"  Render: {output['status']}")
        return output['status'] == 'success'
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_causal_axiom():
    """测试6: 因果公理"""
    print("\n" + "="*60)
    print("Test 6: Causal Axiom (axiom8_causal)")
    print("="*60)
    try:
        from axioms import CausalAxiom
        axiom = CausalAxiom()
        data = {
            'causal_chains': [
                {'cause': 'user_input', 'effect': 'AI_response', 'sensitivity': 0.9, 'type': 'MUST'},
                {'cause': 'data_update', 'effect': 'model_refresh', 'sensitivity': 0.7, 'type': 'CAN'},
                {'cause': 'error', 'effect': 'fallback', 'sensitivity': 0.95, 'type': 'MUST'}
            ]
        }
        valid = axiom.validate(data)
        print(f"  Validation: {'PASS' if valid else 'FAIL'}")
        if not valid:
            return False
        result = axiom.compute(data, None)
        print(f"  MUST: {result['must_count']}  Global Sensitivity: {result['global_sensitivity']:.2f}")
        print(f"  Permutation p-value: {result['permutation_p']:.4f}  Significant: {result['significant']}")
        output = axiom.render(result)
        print(f"  Render: {output['status']}")
        return output['status'] == 'success'
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def test_integration():
    """测试6: 集成测试"""
    print("\n" + "="*60)
    print("Test 6: Integration (all 4 axioms)")
    print("="*60)
    try:
        from axioms import LayoutAxiom, BoundaryAxiom, FreedomAxiom, CausalAxiom
        axioms = {
            'layout':   LayoutAxiom(gpu_shader=None, fallback_method='auto'),
            'boundary': BoundaryAxiom(gpu_shader=None, fallback_method='auto'),
            'freedom':  FreedomAxiom(gpu_shader=None, fallback_method='auto'),
            'causal':   CausalAxiom(gpu_shader=None, fallback_method='auto'),
        }
        print(f"  Instantiated {len(axioms)} axiom objects")
        all_ok = True
        for name, axiom in axioms.items():
            try:
                data = {'elements': [], 'canvas': {'width': 800, 'height': 600}} if name == 'layout' \
                    else {'boundaries': []} if name == 'boundary' \
                    else {'freedom': {'intensity': 0.5}} if name == 'freedom' \
                    else {'causal_chains': []}
                result = axiom.execute(type('Task', (), {'data': data})(), None)
                status = result.get('status', 'OK')
                print(f"  {name}: {status}")
                if status != 'success':
                    all_ok = False
            except Exception as e:
                print(f"  {name}: ERROR — {e}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("WuDao Core — Eight Axioms Test Suite")
    print("="*60)

    tests = [
        ("Imports",       test_imports),
        ("Layout Axiom",  test_layout_axiom),
        ("Boundary Axiom", test_boundary_axiom),
        ("Freedom Axiom", test_freedom_axiom),
        ("Narrative Axiom", test_narrative_axiom),
        ("Causal Axiom",  test_causal_axiom),
        ("Integration",   test_integration),
    ]

    passed, failed = 0, 0
    for name, fn in tests:
        try:
            (passed := passed + 1) if fn() else (failed := failed + 1)
        except Exception as e:
            print(f"\n[CRASH] {name}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed}/{len(tests)} passed  {failed} failed")
    print("="*60)

    print("\n[Real Status — 2026-04-09]")
    print("  axiom1_growth    ❌ 缺失（可用 wukong_constraints lesson1 升级）")
    print("  axiom2_light     ❌ 缺失（同上）")
    print("  axiom3_color     ❌ 缺失（同上）")
    print("  axiom4_layout    ✅ 生产级")
    print("  axiom5_narrative ✅ 新写（复用 wukong_poster/narrative.py）")
    print("  axiom6_boundary  ✅ 生产级")
    print("  axiom7_freedom   ✅ 生产级")
    print("  axiom8_causal    ✅ 生产级")
    print("\n  整体完成度: 62.5% (5/8)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
