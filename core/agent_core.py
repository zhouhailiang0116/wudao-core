# -*- coding: utf-8 -*-
"""
AgentCore - 公理统一调度核心
============================

职责：
  - 自动加载 axiom（via axiom_loader）
  - 统一调度执行（validate → compute → render）
  - Bridge 翻译（axiom → wukong 法则）
  - 完整闭环（道 → 通 → 悟空）

状态（2026-04-09）：
  P1 阶段：接 axiom_loader + bridge，支持 run_pipeline 闭环
  5/8 axiom 就绪（layout/narrative/boundary/freedom/causal）
  axiom1/2/3 标记 missing，不影响主干运行
"""

import time
import os
import sys
from typing import Dict, Any, Optional, List

from .state_manager import StateManager
from .memory_system import MemorySystem
from .error_handler import ErrorHandler

# ─── Bridge 路径（延迟导入，避免顶层副作用）──────────────────────────────
_BRIDGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bridge"
)


class AgentCore:
    """
    公理统一调度核心

    能力：
      - auto_register()  : 从 axiom_loader 自动加载所有 axiom
      - run(task, axiom) : verify → validate → compute → render
      - run_pipeline()   : run + bridge.translate()  完整闭环
      - verify()         : 用 axiom_verifier 前置验证（验证先于生成）
      - status()         : 查看核心运行状态
    """

    def __init__(self, name: str = "AgentCore", auto_load: bool = True):
        self.name = name
        self.axioms: Dict[str, Any] = {}           # name → instance
        self._axiom_names: Dict[Any, str] = {}      # instance → name（反查）
        self._axiom_config: Dict[str, dict] = {}     # name → 元信息
        self.state = StateManager()
        self.memory = MemorySystem()
        self.errors = ErrorHandler()

        # 验证器：验证先于生成
        self._verifier = None         # AxiomVerifier 实例（延迟初始化）
        self._verify_scores = {}      # axiom_name → {"score": float, "pass": bool, ...}
        self._verify_enabled = False   # 默认关闭，需显式 enable

        self.stats = {
            "tasks_total": 0, "tasks_success": 0, "tasks_failed": 0,
            "tasks_fallback": 0,
            "pipelines_total": 0, "pipelines_success": 0,
            "verify_total": 0, "verify_passed": 0, "verify_blocked": 0,
            "start_time": time.time(),
        }

        if auto_load:
            self.auto_register()

    # ══════════════════════════════════════════════════════════════════
    #  axiom 管理
    # ══════════════════════════════════════════════════════════════════

    def auto_register(self) -> int:
        """从 axiom_loader 加载所有 axiom 并注册。返回成功数。"""
        from .axiom_loader import load_all, list_available

        loaded = load_all(gpu_mode=False)
        available = list_available()
        count = 0
        for name, instance in loaded.items():
            self.axioms[name] = instance
            self._axiom_names[instance] = name
            if name in available:
                self._axiom_config[name] = available[name]
            count += 1
        print(f"[{self.name}] 自动注册 {count} 个 axiom: {list(self.axioms.keys())}")
        return count

    def register(self, name: str, instance: Any, config: dict = None) -> None:
        """手动注册 axiom。"""
        if name in self.axioms:
            print(f"[{self.name}] Warning: axiom '{name}' 已存在，覆盖")
        self.axioms[name] = instance
        self._axiom_names[instance] = name
        if config:
            self._axiom_config[name] = config
        print(f"[{self.name}] Registered: {name}")

    def unregister(self, name: str) -> bool:
        """注销 axiom。"""
        if name in self.axioms:
            inst = self.axioms.pop(name)
            self._axiom_names.pop(inst, None)
            self._axiom_config.pop(name, None)
            return True
        return False

    def get_axiom(self, name: str) -> Optional[Any]:
        """获取 axiom 实例。"""
        return self.axioms.get(name)

    def list_axioms(self) -> List[str]:
        """列出已注册 axiom 名称。"""
        return list(self.axioms.keys())

    # ══════════════════════════════════════════════════════════════════
    #  验证器（验证先于生成）
    # ══════════════════════════════════════════════════════════════════

    def enable_verification(self, enabled: bool = True) -> None:
        """开启/关闭 axiom_verifier 前置验证。"""
        self._verify_enabled = enabled
        print(f"[{self.name}] verify: {'ON' if enabled else 'OFF'}")

    def verify(self, image_path: str, force: bool = False) -> Dict[str, Any]:
        """
        用 axiom_verifier 对输入图像做前置验证。

        返回每个 axiom 的 score（0~1）、pass，以及不通过的公理列表。
        结果缓存到 self._verify_scores（基于文件内容哈希，同一图像只验证一次）。

        缓存 key 采用文件内容哈希而非路径字符串，规避 Windows 路径编码问题。

        Args:
            image_path: 图像路径（str 或 PIL Image / numpy array）
            force:      True=强制重新验证，False=命中缓存则跳过

        Returns:
            {
                "scores":   {axiom_name: {score, pass, detail, ...}, ...},
                "blocked":  [不通过的 axiom 列表],
                "summary":  "X/8 公理通过",
                "cached":   bool,
            }
        """
        import hashlib

        self.stats["verify_total"] += 1

        # ── 计算内容哈希作为缓存 key（规避路径编码问题）───
        cache_key = None
        if isinstance(image_path, str):
            abs_path = os.path.abspath(image_path)
            if os.path.isfile(abs_path):
                try:
                    with open(abs_path, "rb") as f:
                        data = f.read(65536)   # 只读前 64KB（足够区分不同文件）
                    cache_key = "file:" + hashlib.md5(data).hexdigest()
                except Exception:
                    cache_key = "path:" + abs_path  # 读不了就走路径 fallback

        if cache_key is None:
            cache_key = "obj:" + str(hashlib.md5(str(image_path).encode()).hexdigest()[:12])

        # 命中缓存
        if not force and cache_key in self._verify_scores:
            cached = self._verify_scores[cache_key]
            blocked = [n for n, r in cached["scores"].items() if not r.get("pass", True)]
            return {
                "scores": cached["scores"],
                "blocked": blocked,
                "summary": f"{len(cached['scores']) - len(blocked)}/{len(cached['scores'])} 公理通过",
                "cached": True,
            }

        # ── 延迟导入 axiom_verifier（用固定路径避免 __file__ 歧义）───
        _WS_ROOT = os.path.normpath(os.path.join(os.path.dirname(_BRIDGE_DIR), os.pardir))
        _EYE_CORE = os.path.join(_WS_ROOT, "wukong", "wukong_eye", "core")
        try:
            import sys as _sys
            if _EYE_CORE not in _sys.path:
                _sys.path.insert(0, _EYE_CORE)
            from axiom_verifier import AxiomVerifier

            verifier = AxiomVerifier(image_path)
            raw_scores = verifier.verify_all()
        except ImportError:
            print(f"[{self.name}] warning: wukong_eye not found, verify skipped")
            return {"scores": {}, "blocked": [], "summary": "verify unavailable (import failed)"}
        except Exception as e:
            print(f"[{self.name}] verify error: {e}")
            return {"scores": {}, "blocked": [], "summary": f"verify error: {e}"}

        # 缓存
        self._verify_scores[cache_key] = raw_scores
        blocked = [n for n, r in raw_scores.items() if not r.get("pass", True)]

        print(f"[{self.name}] verify: {len(raw_scores) - len(blocked)}/{len(raw_scores)} "
              f"pass | blocked={blocked or 'none'}")
        self.stats["verify_passed"] += len(raw_scores) - len(blocked)
        if blocked:
            self.stats["verify_blocked"] += len(blocked)

        return {
            "scores": raw_scores,
            "blocked": blocked,
            "summary": f"{len(raw_scores) - len(blocked)}/{len(raw_scores)} 公理通过",
            "cached": False,
        }

    def get_verify_score(self, axiom_name: str, image_path: str = None) -> float:
        """
        获取某 axiom 的验证分。优先用最新 verify() 的缓存。

        Returns: 0.0~1.0，0.0 表示未验证或验证失败
        """
        import hashlib

        if not self._verify_scores:
            return 0.0

        if image_path:
            # 用相同哈希逻辑计算 cache_key
            try:
                abs_path = os.path.abspath(str(image_path))
                if os.path.isfile(abs_path):
                    with open(abs_path, "rb") as f:
                        data = f.read(65536)
                    cache_key = "file:" + hashlib.md5(data).hexdigest()
                else:
                    cache_key = "path:" + abs_path
            except Exception:
                cache_key = "path:" + str(image_path)

            if cache_key in self._verify_scores:
                scores = self._verify_scores[cache_key]
                return scores.get(axiom_name, {}).get("score", 0.0)

        # 取最后一条缓存
        last_scores = list(self._verify_scores.values())[-1]
        return last_scores.get(axiom_name, {}).get("score", 0.0)

    # ══════════════════════════════════════════════════════════════════
    #  执行
    # ══════════════════════════════════════════════════════════════════

    def run(self, task_data: dict, axiom_name: str = None,
            image: str = None, block_threshold: float = 0.40) -> dict:
        """
        执行 axiom 计算：verify → validate → compute → render

        Args:
            task_data:       输入数据（dict，需符合 axiom 的 input_schema）
            axiom_name:      axiom 名称；不指定则从 task_data 推断，默认 layout
            image:           图像路径（str），有则先跑 verify 前置验证
            block_threshold:  verify 分数低于此值则阻断该 axiom（默认 0.40）

        Returns:
            render 输出 dict，含 _meta.axiom / _meta.config / _meta.verify
        """
        self.stats["tasks_total"] += 1
        verify_info = None   # 提前声明，确保 except 分支也能访问

        try:
            axiom = self._resolve(axiom_name, task_data)
            a_name = self._axiom_names[axiom]

            # ── 前置验证（可选）：verify → validate → compute
            if self._verify_enabled and image is not None:
                try:
                    v_result = self.verify(image)
                    v_scores = v_result.get("scores", {})
                    v_score = v_scores.get(a_name, {}).get("score", 1.0)  # 未验证则默认高分
                    v_pass  = v_scores.get(a_name, {}).get("pass", True)

                    verify_info = {
                        "score": v_score,
                        "pass":  v_pass,
                        "method": v_scores.get(a_name, {}).get("method", ""),
                        "detail": v_scores.get(a_name, {}).get("detail", ""),
                        "blocked": a_name in v_result.get("blocked", []),
                        "threshold": block_threshold,
                        "verified": True,
                    }

                    # 分数低于阈值 → 阻断，跳入 fallback
                    if v_score < block_threshold and not v_pass:
                        raise ValueError(
                            f"[{a_name}] verify score={v_score:.3f} < {block_threshold} "
                            f"(threshold), blocked"
                        )
                except ValueError:
                    # 阻断异常直接上抛，由下面的 except Exception 统一处理
                    raise
                except Exception as _ve:
                    # verify 本身炸了（图像打不开等），降级但不阻断
                    print(f"[{self.name}] verify warning: {_ve}, continuing without verify")
                    verify_info = {
                        "score": 1.0, "pass": True, "verified": False,
                        "blocked": False, "error": str(_ve), "threshold": block_threshold,
                    }

            # validate
            if hasattr(axiom, "validate"):
                valid = axiom.validate(task_data)
                if not valid:
                    raise ValueError(f"[{a_name}] validate() 返回 False")

            # compute + render
            result = (
                axiom.compute(task_data, None)
                if hasattr(axiom, "compute")
                else {}
            )
            output = (
                axiom.render(result)
                if hasattr(axiom, "render") and result
                else (result or {})
            )
            if isinstance(output, dict):
                meta = {
                    "axiom": a_name,
                    "config": self._axiom_config.get(a_name, {}),
                }
                if verify_info:
                    meta["verify"] = verify_info
                output["_meta"] = meta

            self.memory.log(task_data, output, success=True)
            self.stats["tasks_success"] += 1
            return output

        except Exception as e:
            self.stats["tasks_failed"] += 1
            fallback = self.errors.fallback(e, task_data, self.axioms)
            if fallback is not None:
                self.stats["tasks_fallback"] += 1
                self.stats["tasks_failed"] -= 1
                result = fallback
            else:
                result = {"error": str(e)}
            # verify_info 即使在异常路径也要保留到 _meta
            if isinstance(result, dict):
                if "_meta" not in result:
                    result["_meta"] = {"axiom": axiom_name}
                result["_meta"]["verify"] = verify_info
            return result

    # 英文 axiom 名 → 中文名（用于 verify_scores 映射）
    _EN2ZH = {
        "growth": "生长", "light": "光影", "color": "色彩",
        "layout": "布局", "narrative": "叙事",
        "boundary": "边界", "freedom": "自由", "causal": "因果",
    }

    def run_pipeline(self, task_data: dict, axiom_name: str,
                     image: str = None, block_threshold: float = 0.40) -> dict:
        """
        完整闭环：verify → axiom.run() → bridge.translate()

        道→通→悟空 数据流：
          verify(可选) → compute → render → translate(verify_scores) → wukong 参数

        P2 改造：translate() 接收 verify 验证分，计算融合权重，
                 自动调制输出参数的强度（高置信→不变，低置信→降权）
        """
        self.stats["pipelines_total"] += 1

        # Step 1: 运行 axiom（verify 嵌入 run() 内部）
        axiom_result = self.run(task_data, axiom_name,
                                image=image, block_threshold=block_threshold)
        if "error" in axiom_result:
            return {
                "axiom_result": axiom_result,
                "bridge_params": None,
                "target_law": None,
                "success": False,
            }

        # Step 2: 从 axiom_result._meta 提取 verify 分数
        verify_scores = None
        meta = axiom_result.get("_meta", {})
        v = meta.get("verify") or {}
        if v.get("verified", False) and v.get("score", 0) > 0:
            # 构造 verify_scores 字典（供 bridge 调权）
            # 键名使用英文 axiom_name，与 bridge/_DEFAULT_WEIGHTS 一致
            verify_scores = {
                axiom_name: {
                    "score": v.get("score", 0),
                    "pass": v.get("pass", True),
                    "method": v.get("method", ""),
                    "detail": v.get("detail", ""),
                }
            }

        # Step 3: 翻译到法则参数（含融合权重调制）
        try:
            if _BRIDGE_DIR not in sys.path:
                sys.path.insert(0, _BRIDGE_DIR)
            from axiom_to_law import translate

            params = translate(axiom_name, axiom_result, verify_scores=verify_scores)
            self.stats["pipelines_success"] += 1

            # 融合信息也注入到 axiom_result._meta，方便调用方查看
            if verify_scores:
                meta["fusion_input"] = verify_scores

            return {
                "axiom_result": axiom_result,
                "bridge_params": params,
                "target_law": params.get("_meta", {}).get("law")
                           or params.get("_meta", {}).get("fusion", {}).get("law", "unknown"),
                "verify_scores": verify_scores,   # 原始 verify 分数（用于调试）
                "fusion_info": params.get("_meta", {}).get("fusion", {}),  # 融合结果
                "success": True,
            }
        except Exception as e:
            return {
                "axiom_result": axiom_result,
                "bridge_params": {"error": str(e)},
                "target_law": None,
                "success": False,
            }

    def run_batch(self, tasks: list, axiom_name: str = None) -> list:
        """批量执行。"""
        return [self.run(t, axiom_name) for t in tasks]

    # ══════════════════════════════════════════════════════════════════
    #  内部路由
    # ══════════════════════════════════════════════════════════════════

    def _resolve(self, name: str = None, task_data: dict = None) -> Any:
        """路由到 axiom 实例。"""
        # 指定名称
        if name:
            if name in self.axioms:
                return self.axioms[name]
            raise ValueError(
                f"Axiom '{name}' 未注册。可用: {list(self.axioms.keys())}"
            )

        # 从 task_data 推断
        if isinstance(task_data, dict):
            inferred = task_data.get("axiom") or task_data.get("type")
            if inferred and inferred in self.axioms:
                return self.axioms[inferred]

        # 默认 layout（最常用）
        if "layout" in self.axioms:
            return self.axioms["layout"]

        raise ValueError(f"无 axiom 可用。已注册: {list(self.axioms.keys())}")

    # ══════════════════════════════════════════════════════════════════
    #  状态 / 重置
    # ══════════════════════════════════════════════════════════════════

    def status(self) -> dict:
        """获取核心运行状态（含验证器状态）。"""
        return {
            "name": self.name,
            "axioms": list(self.axioms.keys()),
            "axiom_count": len(self.axioms),
            "verify_enabled": self._verify_enabled,
            "verify_cached": list(self._verify_scores.keys()),
            "tasks_total": self.stats["tasks_total"],
            "tasks_success": self.stats["tasks_success"],
            "tasks_failed": self.stats["tasks_failed"],
            "tasks_fallback": self.stats["tasks_fallback"],
            "pipelines_total": self.stats["pipelines_total"],
            "pipelines_success": self.stats["pipelines_success"],
            "verify_total": self.stats["verify_total"],
            "verify_passed": self.stats["verify_passed"],
            "verify_blocked": self.stats["verify_blocked"],
            "success_rate": self.stats["tasks_success"]
            / max(1, self.stats["tasks_total"]),
            "uptime": time.time() - self.stats["start_time"],
        }

    def reset(self) -> None:
        """重置统计数据。"""
        self.state.reset()
        self._verify_scores.clear()
        for k in (
            "tasks_total", "tasks_success", "tasks_failed", "tasks_fallback",
            "pipelines_total", "pipelines_success",
            "verify_total", "verify_passed", "verify_blocked",
        ):
            self.stats[k] = 0
