# -*- coding: utf-8 -*-
"""反馈收集器 - Octopus Skill 进化模块

收集和整理用户对项目成果的反馈，支持按分类/评分收集，并生成汇总报告。
数据存储在 data/evolution/{project_name}_feedback.json
"""

import argparse
import json
import os
import sys
import uuid
from collections import Counter

# 导入共享工具模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_warning, print_error, print_info

# 路径配置
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evolution")

# 合法分类
CATEGORIES = ["功能", "体验", "性能", "其他"]


def _feedback_file(project: str) -> str:
    return os.path.join(DATA_DIR, f"{project}_feedback.json")


def collect_feedback(project: str, category: str, rating: int, comment: str) -> dict:
    """收集一条反馈

    Args:
        project: 项目名
        category: 反馈分类（功能/体验/性能/其他）
        rating: 评分 1-5
        comment: 具体反馈内容

    Returns:
        新增的反馈记录
    """
    if category not in CATEGORIES:
        print_warning(f"分类 '{category}' 不在标准列表中 {CATEGORIES}，已归为 '其他'。")
        category = "其他"
    if not 1 <= rating <= 5:
        print_error("评分必须在 1-5 之间。")
        return {}

    feedback = {
        "id": uuid.uuid4().hex[:8],
        "category": category,
        "rating": rating,
        "comment": comment,
        "timestamp": now_iso(),
    }

    feedbacks = load_json(_feedback_file(project), [])
    feedbacks.append(feedback)
    save_json(_feedback_file(project), feedbacks)

    print_success(f"已收集反馈: [{category}] 评分:{rating} - {comment}")
    return feedback


def summary_feedback(project: str) -> str:
    """汇总反馈，生成摘要报告

    Args:
        project: 项目名

    Returns:
        Markdown 格式的摘要报告内容
    """
    feedbacks = load_json(_feedback_file(project), [])
    if not feedbacks:
        print_info(f"项目 '{project}' 暂无反馈数据。")
        return ""

    total = len(feedbacks)
    avg_rating = sum(f["rating"] for f in feedbacks) / total
    cat_counts = Counter(f["category"] for f in feedbacks)

    # 按分类分组
    by_category = {}
    for fb in feedbacks:
        by_category.setdefault(fb["category"], []).append(fb)

    # 生成报告
    lines = [
        f"# {project} - 反馈摘要报告",
        f"",
        f"**生成时间**: {now_iso()[:16].replace('T', ' ')}",
        f"**反馈总数**: {total}",
        f"**平均评分**: {avg_rating:.1f} / 5.0",
        f"",
        f"## 分类分布",
        f"",
    ]
    for cat in CATEGORIES:
        count = cat_counts.get(cat, 0)
        bar = "#" * count
        lines.append(f"- **{cat}**: {count} 条 {bar}")

    lines.append("")
    lines.append("## 详细反馈")
    lines.append("")

    for cat in CATEGORIES:
        items = by_category.get(cat, [])
        if not items:
            continue
        lines.append(f"### {cat} ({len(items)} 条)")
        lines.append("")
        for fb in items:
            stars = "*" * fb["rating"]
            lines.append(f"- [{stars}] {fb['comment']}（{fb['timestamp'][:10]}）")
        lines.append("")

    # 低分反馈汇总（需要重点关注）
    low_feedbacks = [f for f in feedbacks if f["rating"] <= 2]
    if low_feedbacks:
        lines.append("## 需要重点关注（评分 <= 2）")
        lines.append("")
        for fb in low_feedbacks:
            lines.append(f"- [{fb['category']}] {fb['comment']}")
        lines.append("")

    report = "\n".join(lines)

    # 保存报告
    os.makedirs(DATA_DIR, exist_ok=True)
    report_path = os.path.join(DATA_DIR, f"{project}_feedback_summary.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print_success(f"反馈摘要已保存: {report_path}")
    print_info(f"共 {total} 条反馈，平均评分 {avg_rating:.1f}")
    return report


def main():
    parser = argparse.ArgumentParser(description="反馈收集器 - Octopus Skill 进化模块")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--action", required=True, choices=["collect", "summary"],
                        help="操作类型: collect(收集) / summary(汇总)")
    parser.add_argument("--category", default="其他",
                        help=f"反馈分类: {'/'.join(CATEGORIES)}，默认为 其他")
    parser.add_argument("--rating", type=int, default=3, help="评分 1-5，默认为 3")
    parser.add_argument("--comment", default="", help="具体反馈内容（collect 时必填）")
    args = parser.parse_args()

    if args.action == "collect":
        if not args.comment:
            print_error("collect 操作需要 --comment 参数。")
            return
        result = collect_feedback(args.project, args.category, args.rating, args.comment)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        report = summary_feedback(args.project)
        if report:
            print(report)


if __name__ == "__main__":
    main()
