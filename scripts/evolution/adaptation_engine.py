# -*- coding: utf-8 -*-
"""适应引擎 - Octopus Skill 四层自我进化（第1-2层执行）

根据用户的行为观察结果，自动调整章鱼的行为策略。
将"观察"转化为"行动"——生成调整建议并应用到用户偏好配置。
数据存储在 data/evolution/adaptations.json
"""

import argparse
import json
import os
import sys

# 导入共享工具模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_warning, print_error, print_info

# 路径配置
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "evolution")
ADAPT_FILE = os.path.join(DATA_DIR, "adaptations.json")
SIGNAL_FILE = os.path.join(DATA_DIR, "behavior_signals.json")
PREF_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "preferences.json")


def _demo_behavior() -> dict:
    """生成示例行为分析数据"""
    return {
        "user": "用户A", "total_signals": 8,
        "signal_distribution": {
            "short_reply": 1, "quick_confirm": 1, "long_reply": 1,
            "correction": 1, "enthusiasm": 1, "hesitation": 1,
            "praise": 1, "redirect": 1,
        },
        "communication_style": "混合", "patience_level": "中",
        "engagement_pattern": "混合", "decision_speed": "混合",
        "common_reactions": ["short_reply", "quick_confirm", "long_reply", "correction", "enthusiasm"],
    }


def _get_behavior_analysis(user: str) -> dict:
    """获取用户的行为分析数据，优先从文件读取，否则用示例数据"""
    signal_data = load_json(SIGNAL_FILE)
    signals = [s for s in signal_data.get("signals", []) if s.get("user") == user]

    # 如果有真实信号数据，做简单分析
    if signals:
        from collections import Counter
        counts = Counter(s["signal"] for s in signals)
        short = counts.get("short_reply", 0) + counts.get("quick_confirm", 0)
        long = counts.get("long_reply", 0)
        impatience = counts.get("short_reply", 0) + counts.get("abandonment", 0)
        patience = counts.get("long_reply", 0) + counts.get("quick_confirm", 0)
        active = counts.get("enthusiasm", 0) + counts.get("correction", 0) + counts.get("redirect", 0)
        passive = counts.get("hesitation", 0) + counts.get("skip_question", 0) + counts.get("quick_confirm", 0)
        fast = counts.get("quick_confirm", 0) + counts.get("enthusiasm", 0)
        slow = counts.get("hesitation", 0) + counts.get("redirect", 0)

        return {
            "user": user, "total_signals": len(signals),
            "signal_distribution": dict(counts.most_common()),
            "communication_style": "简洁" if short > long * 2 else ("详细" if long > short * 2 else "混合"),
            "patience_level": "低" if impatience > patience else ("高" if patience > impatience * 2 else "中"),
            "engagement_pattern": "主动" if active > passive else ("被动" if passive > active else "混合"),
            "decision_speed": "快速" if fast > slow * 2 else ("犹豫" if slow > fast else "混合"),
            "common_reactions": [s for s, _ in counts.most_common(5)],
        }

    print_info(f"用户 '{user}' 暂无行为信号数据，使用示例数据演示。")
    demo = _demo_behavior()
    demo["user"] = user
    return demo


def generate_suggestions(user: str) -> dict:
    """根据行为观察数据，生成行为调整建议

    Args:
        user: 用户名

    Returns:
        调整建议 JSON，包含多个维度的建议
    """
    analysis = _get_behavior_analysis(user)
    suggestions = []

    # 追问数量建议
    q_count = {"current": "默认(3)", "suggested": "2", "confidence": 0.7,
               "reason": "根据行为数据自动调整"}
    if analysis["patience_level"] == "低":
        q_count.update(suggested="1", reason="用户耐心较低，建议每次只问1个关键问题", confidence=0.9)
    elif analysis["patience_level"] == "高":
        q_count.update(suggested="3-5", reason="用户耐心较高，可以深入追问", confidence=0.8)
    suggestions.append({"dimension": "question_count", **q_count})

    # 追问深度建议
    q_depth = {"current": "默认(中)", "suggested": "中", "confidence": 0.6,
               "reason": "根据行为数据自动调整"}
    if analysis["engagement_pattern"] == "主动":
        q_depth.update(suggested="深", reason="用户参与积极，可以深入探讨细节", confidence=0.8)
    elif analysis["engagement_pattern"] == "被动":
        q_depth.update(suggested="浅", reason="用户参与较被动，避免过度追问", confidence=0.8)
    suggestions.append({"dimension": "question_depth", **q_depth})

    # 回复长度建议
    r_len = {"current": "默认(适中)", "suggested": "适中", "confidence": 0.6,
             "reason": "根据行为数据自动调整"}
    if analysis["communication_style"] == "简洁":
        r_len.update(suggested="简短", reason="用户偏好简洁沟通，回复应精炼", confidence=0.9)
    elif analysis["communication_style"] == "详细":
        r_len.update(suggested="详细", reason="用户偏好详细沟通，应提供完整说明", confidence=0.9)
    suggestions.append({"dimension": "response_length", **r_len})

    # 主动程度建议
    proact = {"current": "默认(中)", "suggested": "中", "confidence": 0.6,
              "reason": "根据行为数据自动调整"}
    if analysis["engagement_pattern"] == "被动":
        proact.update(suggested="高", reason="用户参与较被动，章鱼需要更主动引导", confidence=0.8)
    elif analysis["engagement_pattern"] == "主动":
        proact.update(suggested="低", reason="用户很主动，章鱼可以跟随用户节奏", confidence=0.7)
    suggestions.append({"dimension": "proactivity", **proact})

    # 交付方式建议
    delivery = {"current": "默认(边做边改)", "suggested": "边做边改", "confidence": 0.6,
                "reason": "根据行为数据自动调整"}
    if analysis["decision_speed"] == "快速" and "praise" in analysis["common_reactions"]:
        delivery.update(suggested="先原型", reason="用户决策快且容易满意，先给原型快速验证", confidence=0.8)
    elif analysis["decision_speed"] == "犹豫" or "redirect" in analysis["common_reactions"]:
        delivery.update(suggested="先方案", reason="用户决策偏犹豫，先给方案充分讨论再动手", confidence=0.8)
    elif analysis["communication_style"] == "详细":
        delivery.update(suggested="一次搞定", reason="用户偏好详细沟通，一次性交付完整方案", confidence=0.7)
    suggestions.append({"dimension": "delivery_style", **delivery})

    # 风险提示建议
    risk = {"current": "默认(看情况)", "suggested": "看情况", "confidence": 0.5,
            "reason": "根据行为数据自动调整"}
    if analysis["patience_level"] == "低":
        risk.update(suggested="是", reason="用户耐心较低，应主动提示风险避免后期返工", confidence=0.8)
    suggestions.append({"dimension": "risk_warning", **risk})

    # 启发建议
    inspire = {"current": "默认(看情况)", "suggested": "看情况", "confidence": 0.5,
               "reason": "根据行为数据自动调整"}
    if analysis["engagement_pattern"] == "主动" and "enthusiasm" in analysis["common_reactions"]:
        inspire.update(suggested="是", reason="用户热情高且参与积极，可以主动启发新思路", confidence=0.8)
    elif analysis["engagement_pattern"] == "被动":
        inspire.update(suggested="否", reason="用户参与较被动，避免过度启发增加认知负担", confidence=0.7)
    suggestions.append({"dimension": "inspiration", **inspire})

    result = {
        "user": user,
        "based_on_signals": analysis["total_signals"],
        "generated_at": now_iso(),
        "suggestions": suggestions,
    }

    # 保存建议
    save_json(ADAPT_FILE, result)
    print_success(f"已生成 {len(suggestions)} 条调整建议，保存至: {ADAPT_FILE}")
    return result


def apply_suggestions(user: str) -> dict:
    """应用调整建议，更新用户的偏好配置

    Args:
        user: 用户名

    Returns:
        更新结果
    """
    # 读取建议
    adapt_data = load_json(ADAPT_FILE)
    if not adapt_data or adapt_data.get("user") != user:
        print_info(f"未找到用户 '{user}' 的调整建议，先生成建议...")
        adapt_data = generate_suggestions(user)

    suggestions = adapt_data.get("suggestions", [])
    if not suggestions:
        print_error("无可用建议。")
        return {}

    # 读取现有偏好配置
    pref_data = load_json(PREF_FILE)
    if "records" not in pref_data:
        pref_data = {"records": []}

    # 将建议映射为偏好记录
    dim_to_category = {
        "question_count": "沟通", "question_depth": "沟通",
        "response_length": "沟通", "proactivity": "流程",
        "delivery_style": "流程", "risk_warning": "流程",
        "inspiration": "流程",
    }

    applied = []
    for s in suggestions:
        dim = s["dimension"]
        pref_value = f"{dim}={s['suggested']}"
        record = {
            "user": user,
            "preference": pref_value,
            "category": dim_to_category.get(dim, "其他"),
            "source": "adaptation_engine",
            "reason": s.get("reason", ""),
            "confidence": s.get("confidence", 0.5),
            "recorded_at": now_iso(),
        }
        pref_data["records"].append(record)
        applied.append(dim)

    save_json(PREF_FILE, pref_data)
    print_success(f"已将 {len(applied)} 条建议应用到偏好配置: {', '.join(applied)}")
    return {"user": user, "applied_dimensions": applied, "total_records": len(pref_data["records"])}


def main():
    parser = argparse.ArgumentParser(description="适应引擎 - Octopus Skill 四层自我进化")
    parser.add_argument("--user", required=True, help="用户名")
    parser.add_argument("--action", required=True, choices=["suggest", "apply"],
                        help="操作类型: suggest(生成建议) / apply(应用建议)")
    args = parser.parse_args()

    if args.action == "suggest":
        result = generate_suggestions(args.user)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = apply_suggestions(args.user)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
