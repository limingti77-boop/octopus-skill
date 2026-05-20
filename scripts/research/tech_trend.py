# -*- coding: utf-8 -*-
"""
技术趋势分析 - 根据项目类型推荐技术栈并评估趋势
从 data/tech_stacks.json 加载技术栈数据，提供结构化的技术选型参考。
"""

import argparse
import json
import os
import sys

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "tech_trends.json")
TECH_STACKS_FILE = os.path.join(DATA_DIR, "tech_stacks.json")


def _load_tech_stacks() -> dict:
    """从 JSON 文件加载技术栈数据，文件不存在则返回空字典"""
    return load_json(TECH_STACKS_FILE, default={})


def analyze_trends(proj_type: str, category: str = None) -> dict:
    """分析指定项目类型的技术趋势"""
    all_stacks = _load_tech_stacks()
    stacks = all_stacks.get(proj_type, all_stacks.get("小程序", {}))

    result = {
        "project_type": proj_type,
        "analyzed_at": now_iso(),
        "recommendations": [],
    }

    categories = [category] if category else list(stacks.keys())
    for cat in categories:
        techs = stacks.get(cat, [])
        priority = {"成熟": 0, "成长": 1, "新兴": 2}
        popularity_order = {"high": 0, "medium": 1, "low": 2}
        techs_sorted = sorted(
            techs,
            key=lambda t: (priority.get(t["maturity"], 9), popularity_order.get(t["popularity"], 9)),
        )
        result["recommendations"].extend(techs_sorted)

    return result


def save_trends(data: dict) -> str:
    """保存技术趋势分析结果"""
    existing = load_json(OUTPUT_FILE, default=[])
    existing.append(data)
    save_json(OUTPUT_FILE, existing)
    return OUTPUT_FILE


def main():
    parser = argparse.ArgumentParser(description="技术趋势分析 - 推荐技术栈并评估趋势")
    parser.add_argument("--type", required=True, help="项目类型（小程序/网站/APP/游戏）")
    parser.add_argument("--category", default=None, help="技术分类（frontend/backend/fullstack）")
    args = parser.parse_args()

    result = analyze_trends(args.type, args.category)
    filepath = save_trends(result)

    print_success(f"技术趋势分析已保存到: {filepath}")
    print(f"项目类型: {args.type}")
    print(f"推荐技术数量: {len(result['recommendations'])}")
    print()
    for tech in result["recommendations"]:
        print(f"  [{tech['maturity']}] {tech['name']} ({tech['category']}) - {tech['reason']}")


if __name__ == "__main__":
    main()
