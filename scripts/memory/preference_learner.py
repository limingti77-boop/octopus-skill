# -*- coding: utf-8 -*-
"""偏好学习工具 - Octopus Skill 记忆管理

记录和分析用户在交互中的偏好，给出个性化建议。
支持自动观察用户回复中的行为信号。
数据存储在 data/preferences.json
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta

# 添加父目录到路径以导入 common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_json, save_json, now_iso, print_success, print_error, print_info

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "preferences.json")

# 预定义分类
CATEGORIES = ["沟通", "代码", "文档", "设计", "流程", "其他"]

# 行为信号检测规则：(信号名, 偏好描述, 分类, 检测函数)
SIGNAL_RULES = [
    ("short_reply", "偏好简洁沟通", "沟通",
     lambda t: len(t) < 10),
    ("long_reply", "偏好详细交流", "沟通",
     lambda t: len(t) > 100),
    ("hesitation", "需要更多引导", "沟通",
     lambda t: any(w in t for w in ["算了", "随便", "都行", "无所谓"])),
    ("quick_confirm", "偏好快速推进", "流程",
     lambda t: len(t) < 15 and any(w in t for w in ["行", "好", "可以", "嗯", "ok"])),
    ("praise", "当前方式有效", "沟通",
     lambda t: any(w in t for w in ["不错", "很好", "厉害", "棒"])),
    ("correction", "需要更仔细理解需求", "沟通",
     lambda t: any(w in t for w in ["不是", "不对", "我说的是", "你搞错了"])),
    ("frustration", "偏好简化流程", "流程",
     lambda t: any(w in t for w in ["太长了", "太复杂了", "能不能简单点"])),
]


def record_preference(user: str, preference: str, category: str = "其他"):
    """记录一条用户偏好

    Args:
        user: 用户名
        preference: 偏好描述
        category: 偏好分类

    Returns:
        新增的偏好记录
    """
    if category not in CATEGORIES:
        print(f"[警告] 分类 '{category}' 不在标准列表中: {CATEGORIES}，已归为 '其他'。")
        category = "其他"

    data = load_json(DATA_FILE, default={"records": []})
    record = {
        "user": user,
        "preference": preference,
        "category": category,
        "recorded_at": now_iso(),
    }
    data["records"].append(record)
    save_json(DATA_FILE, data)
    print_success(f"已记录偏好: [{category}] {preference}（用户: {user}）")
    return record


def auto_observe(user: str, text: str, context: str = ""):
    """自动分析用户回复中的行为信号，并记录为偏好

    Args:
        user: 用户名
        text: 用户的回复内容
        context: 当前对话阶段（可选，辅助判断）

    Returns:
        检测结果，包含信号列表和自动记录的偏好
    """
    text_clean = text.strip()
    detected = []

    for signal, preference, category, check_fn in SIGNAL_RULES:
        if check_fn(text_clean):
            if any(d["signal"] == signal for d in detected):
                continue
            detected.append({
                "signal": signal,
                "preference": preference,
                "category": category,
            })

    # 去重：同一用户同一信号在24小时内不重复记录
    data = load_json(DATA_FILE, default={"records": []})
    records = data.get("records", [])
    now = datetime.now()
    cutoff = (now - timedelta(hours=24)).isoformat()

    existing_signals = set()
    for r in records:
        if r.get("user") == user and r.get("recorded_at", "") >= cutoff:
            existing_signals.add(r.get("preference", ""))

    recorded = []
    for item in detected:
        if item["preference"] in existing_signals:
            print_info(f"去重跳过（24h内已记录）: {item['preference']}")
            continue
        record = record_preference(user, item["preference"], item["category"])
        recorded.append(record)

    result = {
        "user": user,
        "text": text,
        "context": context,
        "text_length": len(text_clean),
        "detected_signals": detected,
        "recorded_preferences": recorded,
    }
    print(f"[观察] 分析用户 '{user}' 的回复（长度: {len(text_clean)}字）:")
    if detected:
        for s in detected:
            print(f"  - 信号: {s['signal']} -> 偏好: {s['preference']}")
        print_success(f"已自动记录 {len(recorded)} 条偏好。")
    else:
        print("  - 未检测到明显行为信号。")
    return result


def analyze_preferences(user: str = ""):
    """分析用户偏好模式，给出建议

    Args:
        user: 用户名（留空则分析所有用户）

    Returns:
        分析结果，包含偏好统计和建议
    """
    data = load_json(DATA_FILE, default={"records": []})
    records = data.get("records", [])

    if user:
        records = [r for r in records if r.get("user") == user]
        if not records:
            print(f"[提示] 用户 '{user}' 暂无偏好记录。")
            return {"user": user, "total": 0, "suggestions": []}

    total = len(records)
    if total == 0:
        print("[提示] 暂无偏好记录。")
        return {"user": user or "全部", "total": 0, "suggestions": []}

    category_counts = Counter(r.get("category", "其他") for r in records)
    pref_counts = Counter(r.get("preference", "") for r in records)

    suggestions = []
    top_category = category_counts.most_common(1)[0]
    suggestions.append(f"最关注的领域是「{top_category[0]}」，共 {top_category[1]} 条记录。")

    top_prefs = pref_counts.most_common(3)
    if top_prefs:
        pref_list = "、".join([f"「{p[0]}」({p[1]}次)" for p in top_prefs])
        suggestions.append(f"高频偏好: {pref_list}")

    cat_map = {
        "沟通": "建议在交互中注意沟通效率，减少不必要的追问。",
        "代码": "建议优先提供可直接运行的代码示例，减少理论说明。",
        "文档": "建议输出结构化的文档，保持格式清晰。",
        "设计": "建议在方案设计阶段多征求确认，避免返工。",
        "流程": "建议遵循用户熟悉的工作流程，减少流程变更。",
    }
    for cat, count in category_counts.most_common(2):
        if cat in cat_map:
            suggestions.append(cat_map[cat])

    result = {
        "user": user or "全部",
        "total_records": total,
        "category_distribution": dict(category_counts.most_common()),
        "top_preferences": [p[0] for p in pref_counts.most_common(5)],
        "suggestions": suggestions,
    }

    print(f"[分析] 共 {total} 条偏好记录:")
    for s in suggestions:
        print(f"  - {s}")
    return result


def main():
    parser = argparse.ArgumentParser(description="偏好学习工具")
    parser.add_argument("--action", required=True,
                        choices=["record", "analyze", "auto_observe"],
                        help="操作类型: record(记录) / analyze(分析) / auto_observe(自动观察)")
    parser.add_argument("--user", default="", help="用户名")
    parser.add_argument("--preference", default="", help="偏好描述（record 时必填）")
    parser.add_argument("--category", default="其他",
                        help=f"偏好分类: {'/'.join(CATEGORIES)}，默认为 其他")
    parser.add_argument("--text", default="", help="用户回复文本（auto_observe 时必填）")
    parser.add_argument("--context", default="", help="当前对话阶段（auto_observe 可选）")
    args = parser.parse_args()

    if args.action == "record":
        if not args.user or not args.preference:
            print_error("record 操作需要 --user 和 --preference 参数。")
            return
        result = record_preference(args.user, args.preference, args.category)
    elif args.action == "auto_observe":
        if not args.user or not args.text:
            print_error("auto_observe 操作需要 --user 和 --text 参数。")
            return
        result = auto_observe(args.user, args.text, args.context)
    else:
        result = analyze_preferences(args.user)

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
