# -*- coding: utf-8 -*-
"""进度监控 - Octopus Skill 巧手脑

跟踪任务执行进度，支持状态更新和进度报告生成。
update: 更新单个任务状态
report: 生成Markdown格式进度报告，保存到 data/execution/{project_name}_progress.md
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_error

# 数据目录
EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "execution")

VALID_STATUSES = ["pending", "in_progress", "done", "blocked"]
_STATUS_LABELS = {"pending": "待开始", "in_progress": "进行中", "done": "已完成", "blocked": "已阻塞"}
_CATEGORY_LABELS = {"design": "设计", "dev": "开发", "test": "测试", "deploy": "部署"}


def update_task(project: str, task_id: str, status: str) -> str:
    """更新指定任务的状态"""
    if status not in VALID_STATUSES:
        raise ValueError(f"无效状态: {status}，有效值为: {', '.join(VALID_STATUSES)}")
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_tasks.json")
    data = load_json(filepath)
    task_map = {t["id"]: t for t in data["tasks"]}
    if task_id not in task_map:
        raise ValueError(f"未找到任务: {task_id}")
    old_status = task_map[task_id]["status"]
    task_map[task_id]["status"] = status
    task_map[task_id]["updated_at"] = now_iso()
    save_json(filepath, data)
    print_success(f"任务 {task_id} 状态已更新: {_STATUS_LABELS[old_status]} -> {_STATUS_LABELS[status]}")
    print_success(f"已保存到: {filepath}")
    return filepath


def generate_report(project: str) -> str:
    """生成Markdown格式的进度报告"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_tasks.json")
    data = load_json(filepath)
    tasks = data["tasks"]
    total = len(tasks)

    # 统计各状态和分类
    status_counts = {s: 0 for s in VALID_STATUSES}
    cat_stats = {}
    for t in tasks:
        status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1
        cat = t["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "done": 0, "blocked": 0}
        cat_stats[cat]["total"] += 1
        if t["status"] == "done":
            cat_stats[cat]["done"] += 1
        if t["status"] == "blocked":
            cat_stats[cat]["blocked"] += 1

    done_count = status_counts["done"]
    progress_pct = round(done_count / total * 100, 1) if total > 0 else 0
    blocked_tasks = [t for t in tasks if t["status"] == "blocked"]
    in_progress_tasks = [t for t in tasks if t["status"] == "in_progress"]

    # 进度条
    bar_len = 20
    filled = int(bar_len * done_count / total) if total > 0 else 0
    bar = "#" * filled + "-" * (bar_len - filled)

    now = now_iso()
    lines = [
        f"# {project} - 进度报告", "",
        f"> 生成时间: {now}  |  项目类型: {data.get('project_type', '未知')}", "",
        "---", "", "## 总体进度", "",
        f"**{progress_pct}%** [{bar}] {done_count}/{total}", "",
        "| 状态 | 数量 | 占比 |", "|------|------|------|",
    ]
    for s in VALID_STATUSES:
        pct = round(status_counts[s] / total * 100, 1) if total > 0 else 0
        lines.append(f"| {_STATUS_LABELS[s]} | {status_counts[s]} | {pct}% |")

    # 各阶段完成情况
    lines.extend(["", "## 各阶段完成情况", "",
                  "| 阶段 | 总数 | 已完成 | 阻塞 | 完成率 |",
                  "|------|------|--------|------|--------|"])
    for cat in ["design", "dev", "test", "deploy"]:
        if cat in cat_stats:
            cs = cat_stats[cat]
            rate = round(cs["done"] / cs["total"] * 100, 1) if cs["total"] > 0 else 0
            lines.append(f"| {_CATEGORY_LABELS[cat]} | {cs['total']} | {cs['done']} | {cs['blocked']} | {rate}% |")

    # 进行中和阻塞任务
    if in_progress_tasks:
        lines.extend(["", "## 进行中的任务", ""])
        for t in in_progress_tasks:
            lines.append(f"- **{t['id']}** {t['name']} ({t.get('priority', '-')})")
    if blocked_tasks:
        lines.extend(["", "## 阻塞任务", ""])
        for t in blocked_tasks:
            deps = ", ".join(t.get("depends_on", []))
            lines.append(f"- **{t['id']}** {t['name']} - 依赖: {deps}")

    # 任务明细
    lines.extend(["", "## 任务明细", "",
                  "| ID | 任务名称 | 分类 | 优先级 | 状态 | 工作量 |",
                  "|----|---------|------|--------|------|--------|"])
    for t in tasks:
        lines.append(f"| {t['id']} | {t['name']} | {_CATEGORY_LABELS.get(t['category'], t['category'])} "
                      f"| {t['priority']} | {_STATUS_LABELS.get(t['status'], t['status'])} | {t.get('estimated_effort', '-')} |")

    lines.extend(["", "---", "*报告由 Octopus 巧手脑自动生成*", ""])
    report = "\n".join(lines)

    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_progress.md")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print_success(f"进度报告已生成: {filepath}")
    print_success(f"总体进度: {progress_pct}% ({done_count}/{total})")
    if blocked_tasks:
        print_success(f"阻塞任务: {len(blocked_tasks)}个")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="进度监控 - Octopus 巧手脑")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--action", required=True, choices=["update", "report"],
                        help="操作类型: update(更新状态) / report(生成报告)")
    parser.add_argument("--task-id", default="", help="任务ID(更新时必填)")
    parser.add_argument("--status", default="", help="新状态: pending/in_progress/done/blocked")
    args = parser.parse_args()

    if args.action == "update":
        if not args.task_id or not args.status:
            parser.error("update操作需要 --task-id 和 --status 参数")
        update_task(args.project, args.task_id, args.status)
    elif args.action == "report":
        generate_report(args.project)


if __name__ == "__main__":
    main()