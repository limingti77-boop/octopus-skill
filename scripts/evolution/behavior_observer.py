# -*- coding: utf-8 -*-
"""自动行为观测器 - Octopus Skill 四层自我进化（第1-2层基础）

自动观测用户在对话中的行为信号，记录行为模式（不记录对话内容）。
支持记录、分析和报告三种操作。
数据存储在 data/evolution/behavior_signals.json
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
DATA_FILE = os.path.join(DATA_DIR, "behavior_signals.json")

# 内置信号类型及中文说明
SIGNAL_TYPES = {
    "short_reply": "回复很短（可能不耐烦）",
    "long_reply": "回复很详细（很投入）",
    "skip_question": "跳过了问题（不想回答这类问题）",
    "quick_confirm": "快速确认（行/好/可以）",
    "hesitation": "犹豫信号（算了/随便/都行）",
    "enthusiasm": "热情信号（太好了/有意思！）",
    "abandonment": "放弃信号（算了不做了）",
    "redirect": "方向变更（等等，我想换个方向）",
    "correction": "纠正章鱼（不是这样的/我说的是）",
    "praise": "表扬章鱼（这个建议不错）",
}


def _demo_data() -> dict:
    """生成示例数据用于演示"""
    return {
        "signals": [
            {"user": "用户A", "signal": "short_reply", "context": "追问阶段",
             "value": "用户只回了3个字", "timestamp": "2026-05-10T10:00:00"},
            {"user": "用户A", "signal": "quick_confirm", "context": "方案确认",
             "value": "用户说行", "timestamp": "2026-05-10T10:05:00"},
            {"user": "用户A", "signal": "long_reply", "context": "技术讨论",
             "value": "用户写了200字的详细需求", "timestamp": "2026-05-11T09:00:00"},
            {"user": "用户A", "signal": "correction", "context": "代码审查",
             "value": "用户纠正了技术选型", "timestamp": "2026-05-11T14:00:00"},
            {"user": "用户A", "signal": "enthusiasm", "context": "原型展示",
             "value": "用户说太好了", "timestamp": "2026-05-12T10:00:00"},
            {"user": "用户A", "signal": "hesitation", "context": "需求确认",
             "value": "用户说随便吧", "timestamp": "2026-05-12T15:00:00"},
            {"user": "用户A", "signal": "praise", "context": "方案交付",
             "value": "用户说这个建议不错", "timestamp": "2026-05-13T11:00:00"},
            {"user": "用户A", "signal": "redirect", "context": "执行阶段",
             "value": "用户想换个方向", "timestamp": "2026-05-13T16:00:00"},
        ]
    }


def record_signal(user: str, signal: str, context: str, value: str) -> dict:
    """记录一条行为信号"""
    if signal not in SIGNAL_TYPES:
        print_warning(f"信号类型 '{signal}' 不在标准列表中，已记录但建议使用标准类型。")
        print(f"  标准类型: {', '.join(SIGNAL_TYPES.keys())}")

    entry = {
        "user": user, "signal": signal, "context": context,
        "value": value, "timestamp": now_iso(),
    }
    data = load_json(DATA_FILE, {"signals": []})
    data["signals"].append(entry)
    save_json(DATA_FILE, data)
    print_success(f"已记录行为信号: [{signal}] {value}（用户: {user}）")
    return entry


def analyze_behavior(user: str) -> dict:
    """分析用户的行为模式，返回JSON结果"""
    data = load_json(DATA_FILE, {"signals": []})
    signals = [s for s in data.get("signals", []) if s.get("user") == user]

    if not signals:
        print_info(f"用户 '{user}' 暂无行为信号记录，使用示例数据演示。")
        demo = _demo_data()
        signals = [s for s in demo["signals"] if s.get("user") == user]
        if not signals:
            signals = demo["signals"][:5]

    signal_counts = Counter(s["signal"] for s in signals)

    # 沟通风格判断
    short = signal_counts.get("short_reply", 0) + signal_counts.get("quick_confirm", 0)
    long = signal_counts.get("long_reply", 0)
    comm_style = "简洁" if short > long * 2 else ("详细" if long > short * 2 else "混合")

    # 耐心程度判断
    impatience = signal_counts.get("short_reply", 0) + signal_counts.get("abandonment", 0)
    patience = signal_counts.get("long_reply", 0) + signal_counts.get("quick_confirm", 0)
    patience_level = "低" if impatience > patience else ("高" if patience > impatience * 2 else "中")

    # 参与模式判断
    active = signal_counts.get("enthusiasm", 0) + signal_counts.get("correction", 0) + signal_counts.get("redirect", 0)
    passive = signal_counts.get("hesitation", 0) + signal_counts.get("skip_question", 0) + signal_counts.get("quick_confirm", 0)
    engagement = "主动" if active > passive else ("被动" if passive > active else "混合")

    # 决策速度判断
    fast = signal_counts.get("quick_confirm", 0) + signal_counts.get("enthusiasm", 0)
    slow = signal_counts.get("hesitation", 0) + signal_counts.get("redirect", 0)
    decision_speed = "快速" if fast > slow * 2 else ("犹豫" if slow > fast else "混合")

    common_reactions = [s for s, _ in signal_counts.most_common(5)]

    result = {
        "user": user, "total_signals": len(signals),
        "signal_distribution": dict(signal_counts.most_common()),
        "communication_style": comm_style, "patience_level": patience_level,
        "engagement_pattern": engagement, "decision_speed": decision_speed,
        "common_reactions": common_reactions,
        "analyzed_at": now_iso(),
    }
    print_info(f"用户 '{user}' 行为模式: 沟通={comm_style}, 耐心={patience_level}, 参与={engagement}, 决策={decision_speed}")
    return result


def generate_report(user: str) -> str:
    """生成 Markdown 格式的行为观测报告"""
    data = load_json(DATA_FILE, {"signals": []})
    signals = [s for s in data.get("signals", []) if s.get("user") == user]
    if not signals:
        print_info(f"用户 '{user}' 暂无数据，使用示例数据演示。")
        demo = _demo_data()
        signals = [s for s in demo["signals"] if s.get("user") == user]
        if not signals:
            signals = demo["signals"]

    analysis = analyze_behavior(user)
    lines = [
        f"# 行为观测报告 - {user}", "",
        f"**生成时间**: {now_iso()[:16].replace('T', ' ')}",
        f"**信号总数**: {analysis['total_signals']}", "",
        "## 行为模式分析", "",
        "| 维度 | 结果 |", "|------|------|",
        f"| 沟通风格 | {analysis['communication_style']} |",
        f"| 耐心程度 | {analysis['patience_level']} |",
        f"| 参与模式 | {analysis['engagement_pattern']} |",
        f"| 决策速度 | {analysis['decision_speed']} |", "",
        "## 信号分布", "",
    ]
    for signal, count in analysis["signal_distribution"].items():
        desc = SIGNAL_TYPES.get(signal, signal)
        lines.append(f"- **{signal}** ({desc}): {count} 次 {'#' * count}")

    lines.extend(["", "## 近期行为记录", ""])
    recent = sorted(signals, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
    for s in recent:
        ts = s.get("timestamp", "")[:16]
        lines.append(f"- [{ts}] **{s['signal']}** ({s.get('context', '')}): {s.get('value', '')}")

    lines.extend(["", "## 建议", ""])
    if analysis["patience_level"] == "低":
        lines.append("- 用户耐心较低，建议减少追问次数，快速给出结论。")
    if analysis["engagement_pattern"] == "被动":
        lines.append("- 用户参与较被动，建议主动引导并提供明确选项。")
    if analysis["decision_speed"] == "犹豫":
        lines.append("- 用户决策偏犹豫，建议提供对比分析辅助决策。")
    if analysis["communication_style"] == "简洁":
        lines.append("- 用户偏好简洁沟通，建议回复精炼、直奔主题。")
    if analysis["communication_style"] == "详细":
        lines.append("- 用户偏好详细沟通，建议提供完整的思路和背景说明。")

    report = "\n".join(lines)
    os.makedirs(DATA_DIR, exist_ok=True)
    report_path = os.path.join(DATA_DIR, f"{user}_behavior_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print_success(f"行为观测报告已保存: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="自动行为观测器 - Octopus Skill 四层自我进化")
    parser.add_argument("--action", required=True, choices=["record", "analyze", "report"],
                        help="操作类型: record(记录) / analyze(分析) / report(报告)")
    parser.add_argument("--user", default="", help="用户名")
    parser.add_argument("--signal", default="", help="信号类型（record 时必填）")
    parser.add_argument("--context", default="", help="发生场景（record 时必填）")
    parser.add_argument("--value", default="", help="具体描述（record 时必填）")
    args = parser.parse_args()

    if args.action == "record":
        if not all([args.user, args.signal, args.context, args.value]):
            print_error("record 操作需要 --user, --signal, --context, --value 参数。")
            print(f"  标准信号类型: {', '.join(SIGNAL_TYPES.keys())}")
            return
        result = record_signal(args.user, args.signal, args.context, args.value)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == "analyze":
        result = analyze_behavior(args.user or "用户A")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        report = generate_report(args.user or "用户A")
        print(report)


if __name__ == "__main__":
    main()
