# -*- coding: utf-8 -*-
"""意图解析工具 - Octopus Skill 探知脑

解析用户的自然语言输入，识别项目类型、规模、平台等关键信息。
数据存储在 data/intent_history.json
"""

import argparse
import json
import os
import sys

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 数据文件路径
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "intent_history.json")

# 项目类型关键词映射
PROJECT_TYPE_RULES = {
    "游戏": ["游戏", "game", "RPG", "射击", "棋牌", "消除", "闯关", "塔防", "养成"],
    "小程序": ["小程序", "微信小程序", "小程序开发", "轻应用"],
    "APP": ["APP", "app", "应用", "手机应用", "移动端", "安卓", "iOS", "ipa", "apk"],
    "网站": ["网站", "网页", "官网", "门户", "博客", "论坛", "商城网站", "Web"],
    "视频": ["视频", "剪辑", "短片", "宣传片", "动画", "短视频", "vlog"],
    "文档": ["文档", "PPT", "报告", "方案", "手册", "说明书", "白皮书"],
}

# 平台关键词映射
PLATFORM_RULES = {
    "微信": ["微信", "WeChat", "小程序"],
    "Android": ["安卓", "Android", "华为", "小米", "OPPO", "vivo"],
    "iOS": ["iOS", "iPhone", "iPad", "苹果"],
    "Web": ["网页", "Web", "网站", "浏览器", "H5"],
    "PC": ["PC", "桌面", "Windows", "Mac", "客户端", "Electron"],
    "抖音": ["抖音", "TikTok", "短视频平台"],
}

# 复杂度关键词映射
COMPLEXITY_RULES = {
    "复杂": ["大型", "复杂", "完整", "企业级", "高并发", "分布式", "微服务", "全栈"],
    "中等": ["中等", "一般", "标准", "常规", "多功能"],
    "简单": ["简单", "小型", "轻量", "基础", "入门", "Demo", "原型", "MVP"],
}


def _load_history() -> list:
    """加载意图历史记录"""
    return load_json(DATA_FILE, default=[])


def _save_history(history: list) -> None:
    """保存意图历史记录"""
    save_json(DATA_FILE, history)


def _match_keywords(text: str, rules: dict) -> tuple:
    """根据关键词规则匹配，返回 (匹配结果列表, 匹配到的关键词列表)"""
    text_lower = text.lower()
    matched = []
    for category, keywords in rules.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                matched.append((category, kw))
                break  # 每个类别只匹配一次
    categories = [m[0] for m in matched]
    keywords = [m[1] for m in matched]
    return categories, keywords


def _estimate_complexity(text: str, project_types: list) -> str:
    """评估项目复杂度"""
    # 先用关键词匹配
    categories, _ = _match_keywords(text, COMPLEXITY_RULES)
    if categories:
        return categories[0]
    # 根据项目类型推断默认复杂度
    if "游戏" in project_types:
        return "复杂"
    if "APP" in project_types:
        return "中等"
    if "小程序" in project_types or "网站" in project_types:
        return "中等"
    return "简单"


def _calc_confidence(project_types: list, keywords: list) -> str:
    """根据匹配到的信息量计算置信度"""
    if len(project_types) >= 1 and len(keywords) >= 2:
        return "high"
    if len(project_types) >= 1:
        return "medium"
    return "low"


def parse_intent(text: str) -> dict:
    """解析用户输入，提取项目意图信息

    Args:
        text: 用户的自然语言输入

    Returns:
        包含 project_type, platform, keywords, complexity, confidence 的字典
    """
    # 匹配项目类型
    project_types, type_keywords = _match_keywords(text, PROJECT_TYPE_RULES)
    # 匹配平台
    platforms, platform_keywords = _match_keywords(text, PLATFORM_RULES)
    # 合并所有匹配到的关键词
    all_keywords = list(set(type_keywords + platform_keywords))
    # 评估复杂度
    complexity = _estimate_complexity(text, project_types)
    # 计算置信度
    confidence = _calc_confidence(project_types, all_keywords)

    result = {
        "project_type": project_types[0] if project_types else "其他",
        "all_matched_types": project_types,
        "platform": platforms[0] if platforms else "未指定",
        "all_matched_platforms": platforms,
        "keywords": all_keywords,
        "complexity": complexity,
        "confidence": confidence,
        "raw_input": text,
        "parsed_at": now_iso(),
    }
    return result


def parse_and_save(text: str) -> dict:
    """解析意图并保存到历史记录"""
    result = parse_intent(text)
    history = _load_history()
    history.append(result)
    _save_history(history)
    return result


def main():
    parser = argparse.ArgumentParser(description="意图解析工具 - Octopus 探知脑")
    parser.add_argument("--input", required=True, help="用户自然语言输入")
    parser.add_argument("--no-save", action="store_true", help="不保存到历史记录")
    args = parser.parse_args()

    if args.no_save:
        result = parse_intent(args.input)
    else:
        result = parse_and_save(args.input)
        print_success(f"意图记录已追加到 {DATA_FILE}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
