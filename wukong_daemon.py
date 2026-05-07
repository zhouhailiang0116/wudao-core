# -*- coding: utf-8 -*-
"""
wukong_daemon.py — 悟道体系任务守护进程
==========================================

守护进程模式：持续监听任务队列，触发道→通→悟闭环。

触发方式（被动监听，不主动创造任务）：
  1. 文件队列：queue/in/ 目录放入 JSON 任务文件
  2. 处理结果写入 queue/out/ 目录

守护进程不自己生成内容，只负责：
  - 接收任务（通过 queue/in/*.json）
  - 跑 AgentCore 闭环
  - 输出结果（queue/out/*.json + 可选图像文件）
  - 记录日志

用法：
  python wukong_daemon.py                    # 前台运行
  python wukong_daemon.py --background      # 守护进程模式
  python wukong_daemon.py --task '{"type":"poster","content":"测试"}'  # 单次任务

作者：悟道体系 | 2026-05-07
"""

import os
import sys
import json
import time
import uuid
import argparse
import threading
from pathlib import Path

# ─── 路径（WSL + Windows 兼容）────────────────────────────────────────────
if os.path.exists("/mnt/c/Users"):
    _HOME = "/mnt/c/Users/周海亮"
else:
    _HOME = os.path.expanduser("~")

_QC      = os.path.join(_HOME, ".qclaw")
QUEUE_IN  = os.path.join(_QC, "workspace", "wudao-core", "queue", "in")
QUEUE_OUT = os.path.join(_QC, "workspace", "wudao-core", "queue", "out")
LOG_DIR   = os.path.join(_QC, "workspace", "wudao-core", "logs")

for _d in [QUEUE_IN, QUEUE_OUT, LOG_DIR]:
    os.makedirs(_d, exist_ok=True)

_WUKONG   = os.path.join(_QC, "workspace", "wukong")
_WUKONG_P = os.path.join(_WUKONG, "wukong_painter")
_WUKONG_O = os.path.join(_WUKONG, "wukong_poster")
_WUKONG_C = os.path.join(_WUKONG, "wukong_creature")
_WUKONG_U = os.path.join(_WUKONG, "wukong_causality")
_WUKONG_V = os.path.join(_WUKONG, "wukong_video")
_WUKONG_BR = os.path.join(_WUKONG, "bridge")
_WDCORE    = os.path.join(_QC, "workspace", "wudao-core")

for _p in [_WUKONG_P, _WUKONG_O, _WUKONG_C, _WUKONG_U, _WUKONG_V, _WUKONG_BR, _WDCORE]:
    if _p not in sys.path:
        sys.path.append(_p)

os.chdir(_WDCORE)


# ════════════════════════════════════════════════════════════════════════════
# 日志
# ════════════════════════════════════════════════════════════════════════════

def log(msg: str, level: str = "INFO"):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    log_file = os.path.join(LOG_DIR, f"wukong_daemon_{time.strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ════════════════════════════════════════════════════════════════════════════
# 任务处理
# ════════════════════════════════════════════════════════════════════════════

def process_task(task: dict, task_id: str = None) -> dict:
    """
    处理单个任务：道→通→悟闭环。

    Args:
        task: 任务 dict，格式：
          {
            "axiom": "layout",           # 或 ["layout","light","color"]
            "task": {...},               # 传给 AgentCore.run_pipeline 的 scene_data
            "image_path": "...",         # 可选，验证用图像
            "output_path": "...",         # 可选，输出图像路径
            "mode": "single" | "multi",  # single=单 axiom，multi=多 axiom 联合
          }
        task_id: 任务 ID（用于日志）

    Returns:
        {
          "success": bool,
          "task_id": str,
          "image_path": str | None,
          "bridge_params": dict,
          "axiom_result": dict,
          "error": str | None,
          "duration": float,
        }
    """
    import time as _time
    t0 = _time.time()

    from wukong_integrator import WukongIntegrator

    axiom_name = task.get("axiom", "layout")
    scene_data = task.get("task", task)
    image_path = task.get("image_path")
    output_path = task.get("output_path")

    log(f"[{task_id}] axiom={axiom_name}, task_keys={list(scene_data.keys())}")

    try:
        wk = WukongIntegrator()

        if isinstance(axiom_name, list):
            # 多 axiom 模式
            result = wk.render_multi(task=scene_data, axioms=axiom_name)
        else:
            # 单 axiom 模式
            result = wk.render(task=scene_data, axiom=axiom_name, image_path=image_path)

        duration = _time.time() - t0

        img = result.get("image")
        result_image_path = None

        if img and output_path:
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            img.save(output_path)
            result_image_path = output_path
            log(f"[{task_id}] image saved → {output_path}")

        return {
            "success": result.get("success", False),
            "task_id": task_id,
            "image_path": result_image_path,
            "bridge_params": result.get("bridge_params"),
            "axiom_result": result.get("axiom_result"),
            "error": result.get("error"),
            "duration": duration,
        }

    except Exception as e:
        import traceback
        duration = _time.time() - t0
        log(f"[{task_id}] ERROR: {e}", "ERROR")
        traceback.print_exc()
        return {
            "success": False,
            "task_id": task_id,
            "image_path": None,
            "bridge_params": None,
            "axiom_result": None,
            "error": str(e),
            "duration": duration,
        }


# ════════════════════════════════════════════════════════════════════════════
# 队列监听
# ════════════════════════════════════════════════════════════════════════════

def scan_queue(poll_interval: float = 2.0):
    """
    持续监听 queue/in/ 目录，有新 JSON 文件就处理。

    文件格式（任务）：
      queue/in/<uuid>.json
      {
        "axiom": "layout",
        "task": {...},
        "image_path": "...",
        "output_path": "..."
      }

    处理完后：
      queue/out/<uuid>.json  ← 结果 JSON
      图像文件 → output_path（如果指定）
    """
    log(f"守护进程启动，监听 {QUEUE_IN}")
    log(f"输出目录: {QUEUE_OUT}")

    processed = set()

    while True:
        try:
            # 扫描输入队列
            for fname in sorted(os.listdir(QUEUE_IN)):
                if not fname.endswith(".json"):
                    continue
                if fname in processed:
                    continue

                fpath = os.path.join(QUEUE_IN, fname)
                task_id = fname[:-5]  # 去掉 .json

                # 读取任务
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        task_data = json.load(f)
                except Exception as e:
                    log(f"[{task_id}] 读取任务失败: {e}", "ERROR")
                    # 移入 out（标记为失败）
                    out_path = os.path.join(QUEUE_OUT, fname)
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump({"success": False, "error": f"读取失败: {e}"}, f, ensure_ascii=False)
                    os.rename(fpath, fpath + ".broken")
                    continue

                processed.add(fname)

                # 处理任务
                result = process_task(task_data, task_id=task_id)

                # 写结果
                out_fname = f"{task_id}.json"
                out_path = os.path.join(QUEUE_OUT, out_fname)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                # 删除输入文件（表示已处理）
                os.remove(fpath)
                log(f"[{task_id}] 完成: success={result['success']}, duration={result['duration']:.3f}s")

        except Exception as e:
            log(f"scan_queue error: {e}", "ERROR")
            time.sleep(5)

        time.sleep(poll_interval)


# ════════════════════════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="悟道体系任务守护进程")
    parser.add_argument("--background", action="store_true", help="守护进程模式")
    parser.add_argument("--task", type=str, help="单次任务（JSON 字符串）")
    parser.add_argument("--poll", type=float, default=2.0, help="轮询间隔（秒）")
    args = parser.parse_args()

    if args.task:
        # 单次任务模式
        task_data = json.loads(args.task)
        task_id = str(uuid.uuid4())[:8]
        result = process_task(task_data, task_id=task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.background:
        # 守护进程模式
        import daemon
        log("启动守护进程...")
        with daemon.DaemonContext():
            scan_queue(poll_interval=args.poll)
    else:
        # 前台监听模式
        scan_queue(poll_interval=args.poll)


if __name__ == "__main__":
    main()
