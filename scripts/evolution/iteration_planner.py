# -*- coding: utf-8 -*-
"""迭代计划生成器 - Octopus Skill 进化模块

根据反馈和当前项目状态，分析高频问题，生成下一轮迭代计划。
输出保存到 data/evolution/{project_name}_v{version}_plan.md
"""

import argparse
import json
import os
import sys
from collections import Counter

# 导入共享工具模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_warning, print_error, print_info

# 路径配置
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evolution")
PROJECT_STATES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "project_states.json")


def _demo_feedbacks() -> list:
    """生成示例反馈数据"""
    return [
        {"id": "d1", "category": "功能", "rating": 2, "comment": "缺少导出Excel功能", "timestamp": "2026-05-10T10:00:00"},
        {"id": "d2", "category": "功能", "rating": 2, "comment": "不支持多账本管理", "timestamp": "2026-05-10T11:00:00"},
        {"id": "d3", "category": "体验", "rating": 3, "comment": "界面颜色偏暗，希望提供主题切换", "timestamp": "2026-05-11T09:00:00"},
        {"id": "d4", "category": "体验", "rating": 1, "comment": "添加记录的流程太繁琐，需要简化", "timestamp": "2026-05-11T14:00:00"},
        {"id": "d5", "category": "性能", "rating": 4, "comment": "加载速度还行，偶尔卡顿", "timestamp": "2026-05-12T08:00:00"},
        {"id": "d6", "category": "功能", "rating": 3, "comment": "希望增加预算提醒功能", "timestamp": "2026-05-12T16:00:00"},
        {"id": "d7", "category": "体验", "rating": 2, "comment": "图表展示不够直观", "timestamp": "2026-05-13T10:00:00"},
        {"id": "d8", "category": "其他", "rating": 5, "comment": "整体不错，期待后续更新", "timestamp": "2026-05-13T15:00:00"},
    ]


def _estimate_effort(comment: str) -> str:
    """根据评论内容估算工作量"""
    if any(kw in comment for kw in ["导出", "多账本", "架构", "重构", "数据库"]):
        return "大（3-5天）"
    if any(kw in comment for kw in ["图表", "提醒", "主题", "优化", "简化"]):
        return "中（1-3天）"
    return "小（0.5-1天）"


def _analyze_feedbacks(feedbacks: list) -> list:
    """分析反馈，提取改进项并按优先级排序"""
    improvements = []
    for fb in feedbacks:
        if fb["rating"] <= 2:
            priority = "P0" if fb["rating"] == 1 else "P1"
        elif fb["rating"] == 3:
            priority = "P2"
        else:
            continue  # 评分4-5的反馈不需要改进
        improvements.append({
            "priority": priority,
            "category": fb["category"],
            "issue": fb["comment"],
            "effort": _estimate_effort(fb["comment"]),
        })
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    improvements.sort(key=lambda x: priority_order.get(x["priority"], 9))
    return improvements


def generate_plan(project: str, version: str) -> str:
    """生成迭代计划，返回 Markdown 格式内容"""
    feedbacks = load_json(os.path.join(DATA_DIR, f"{project}_feedback.json"), [])
    use_demo = False
    if not feedbacks:
        print_info(f"项目 '{project}' 暂无反馈数据，使用示例数据演示。")
        feedbacks = _demo_feedbacks()
        use_demo = True

    current_stage = load_json(PROJECT_STATES_FILE, {}).get(project, {}).get("stage", "未知")
    improvements = _analyze_feedbacks(feedbacks)
    total = len(feedbacks)
    avg_rating = sum(f["rating"] for f in feedbacks) / total
    p_counts = Counter(i["priority"] for i in improvements)

    # 构建报告
    lines = [
        f"# {project} - 迭代计划 {version}", "",
        f"**生成时间**: {now_iso()[:16].replace('T', ' ')}",
        f"**当前阶段**: {current_stage}",
        f"**数据来源**: {'示例数据（演示）' if use_demo else '真实反馈数据'}", "",
        "## 概览", "",
        f"- 反馈总数: {total}",
        f"- 平均评分: {avg_rating:.1f} / 5.0",
        f"- P0 问题: {p_counts.get('P0', 0)} 个（紧急）",
        f"- P1 问题: {p_counts.get('P1', 0)} 个（重要）",
        f"- P2 问题: {p_counts.get('P2', 0)} 个（一般）", "",
        "## 迭代目标", "",
    ]

    goal_idx = 1
    if p_counts.get("P0", 0) > 0:
        lines.append(f"{goal_idx}. **解决所有 P0 级别问题**，提升核心体验")
        goal_idx += 1
    if p_counts.get("P1", 0) > 0:
        lines.append(f"{goal_idx}. **修复 P1 级别问题**，完善功能")
        goal_idx += 1
    lines.append(f"{goal_idx}. **优化 P2 级别体验**，提升用户满意度")
    lines.extend(["", "## 改进项列表", "",
                   "| 优先级 | 分类 | 问题描述 | 预计工作量 |",
                   "|--------|------|----------|------------|"])
    for item in improvements:
        lines.append(f"| {item['priority']} | {item['category']} | {item['issue']} | {item['effort']} |")

    lines.extend(["", "## 预计工作量", "",
                   f"- 预计总工期: 约 {len(improvements) * 2}-{len(improvements) * 3} 个工作日",
                   "- 建议分批迭代，优先处理 P0 和 P1 项", "",
                   "## 备注", "",
                   "- 本计划基于用户反馈自动生成，建议结合实际情况调整优先级",
                   "- 工作量为估算值，实际开发中可能因技术复杂度有所变化"])
    if use_demo:
        lines.append("- 当前使用示例数据，正式使用请先通过 feedback_collector.py 收集真实反馈")
    lines.append("")

    plan = "\n".join(lines)
    os.makedirs(DATA_DIR, exist_ok=True)
    plan_path = os.path.join(DATA_DIR, f"{project}_v{version}_plan.md")
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(plan)

    print_success(f"迭代计划已保存: {plan_path}")
    print_info(f"{version}: {len(improvements)} 个改进项（P0:{p_counts.get('P0',0)} P1:{p_counts.get('P1',0)} P2:{p_counts.get('P2',0)}）")
    return plan


def main():
    parser = argparse.ArgumentParser(description="迭代计划生成器 - Octopus Skill 进化模块")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--version", required=True, help="目标版本号，如v1.1")
    args = parser.parse_args()
    print(generate_plan(args.project, args.version))


if __name__ == "__main__":
    main()
