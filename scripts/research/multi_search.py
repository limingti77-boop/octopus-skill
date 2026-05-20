# -*- coding: utf-8 -*-
"""
多源搜索聚合器 - 为项目生成搜索关键词策略
根据项目描述和类型，生成多维度搜索关键词建议，辅助情报收集。
"""

import argparse
import json
import os
import sys
from urllib.parse import quote

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_info

# 数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "search_strategies.json")

# 项目类型与搜索维度映射
TYPE_DIMENSIONS = {
    "小程序": {
        "竞品类": {
            "sources": ["微信搜一搜", "应用商店", "知乎", "小红书"],
            "templates": ["{project}同类产品", "{project}竞品推荐", "{project}哪个好用"]
        },
        "技术类": {
            "sources": ["掘金", "GitHub", "CSDN", "微信开发者社区"],
            "templates": ["{project}开发教程", "{project}技术方案", "{project}架构设计"]
        },
        "趋势类": {
            "sources": ["36氪", "人人都是产品经理", "艾瑞咨询", "QuestMobile"],
            "templates": ["{project}市场趋势", "{project}行业报告", "{project}发展方向"]
        },
        "用户评价类": {
            "sources": ["知乎", "小红书", "应用商店评论", "微博"],
            "templates": ["{project}用户评价", "{project}使用体验", "{project}吐槽"]
        },
    },
    "网站": {
        "竞品类": {
            "sources": ["Google", "Product Hunt", "知乎", "36氪"],
            "templates": ["{project}类似网站", "{project}竞品分析", "{project}替代品"]
        },
        "技术类": {
            "sources": ["GitHub", "Stack Overflow", "掘金", "MDN"],
            "templates": ["{project}技术栈选择", "{project}前端框架", "{project}后端架构"]
        },
        "趋势类": {
            "sources": ["TechCrunch", "InfoQ", "36氪", "Hacker News"],
            "templates": ["{project}行业趋势", "{project}技术趋势", "Web开发趋势"]
        },
        "用户评价类": {
            "sources": ["G2", "Capterra", "知乎", "小红书"],
            "templates": ["{project}用户反馈", "{project}评测", "{project}优缺点"]
        },
    },
    "APP": {
        "竞品类": {
            "sources": ["App Store", "Google Play", "七麦数据", "酷传"],
            "templates": ["{project}同类APP", "{project}排行榜", "{project}下载量排行"]
        },
        "技术类": {
            "sources": ["掘金", "GitHub", "CSDN", "InfoQ"],
            "templates": ["{project}开发框架", "{project}跨平台方案", "{project}性能优化"]
        },
        "趋势类": {
            "sources": ["艾瑞咨询", "QuestMobile", "七麦数据", "36氪"],
            "templates": ["{project}市场分析", "APP行业趋势", "移动应用发展方向"]
        },
        "用户评价类": {
            "sources": ["App Store评论", "应用宝评论", "知乎", "小红书"],
            "templates": ["{project}好不好用", "{project}用户评分", "{project}使用心得"]
        },
    },
}


def generate_strategy(project: str, proj_type: str) -> dict:
    """根据项目信息生成搜索策略"""
    dimensions = TYPE_DIMENSIONS.get(proj_type, TYPE_DIMENSIONS["小程序"])

    strategy = {
        "project": project,
        "type": proj_type,
        "generated_at": now_iso(),
        "strategies": [],
    }

    for dim_name, dim_config in dimensions.items():
        keywords = []
        for tpl in dim_config["templates"]:
            keywords.append(tpl.format(project=project))
        keywords.append(f"{project} {proj_type}")
        keywords.append(f"{project} 最佳实践")

        strategy["strategies"].append({
            "dimension": dim_name,
            "keywords": keywords,
            "purpose": f"从{dim_name}维度收集{project}相关信息",
            "sources": dim_config["sources"],
        })

    return strategy


def save_strategy(strategy: dict) -> str:
    """保存搜索策略到JSON文件"""
    existing = load_json(OUTPUT_FILE, default=[])
    existing.append(strategy)
    save_json(OUTPUT_FILE, existing)
    return OUTPUT_FILE


def generate_search_urls(strategy: dict) -> list:
    """根据搜索策略生成可直接使用的搜索URL列表"""
    urls = []
    for item in strategy.get("strategies", []):
        for keyword in item.get("keywords", []):
            encoded = quote(keyword)
            urls.append({
                "keyword": keyword,
                "dimension": item.get("dimension", ""),
                "google": f"https://www.google.com/search?q={encoded}",
                "baidu": f"https://www.baidu.com/s?wd={encoded}",
                "zhihu": f"https://www.zhihu.com/search?type=content&q={encoded}",
                "github": f"https://github.com/search?q={encoded}",
            })
    return urls


def main():
    parser = argparse.ArgumentParser(description="多源搜索聚合器 - 搜索执行辅助")
    parser.add_argument("--project", required=True, help="项目名称/描述")
    parser.add_argument("--type", default="小程序", help="项目类型（小程序/网站/APP）")
    parser.add_argument("--action", default="plan", choices=["plan", "execute"],
                        help="动作：plan(生成搜索策略) / execute(生成搜索策略+可执行的搜索URL)")
    args = parser.parse_args()

    strategy = generate_strategy(args.project, args.type)
    filepath = save_strategy(strategy)
    print_success(f"搜索策略已生成并保存到: {filepath}")
    print(json.dumps(strategy, ensure_ascii=False, indent=2))

    if args.action == "execute":
        urls = generate_search_urls(strategy)
        print()
        print_info(f"共生成 {len(urls)} 个可执行搜索URL：")
        print()
        for u in urls:
            print(f"  [{u['dimension']}] {u['keyword']}")
            print(f"    Google:  {u['google']}")
            print(f"    Baidu:   {u['baidu']}")
            print(f"    Zhihu:   {u['zhihu']}")
            print(f"    GitHub:  {u['github']}")
            print()


if __name__ == "__main__":
    main()
