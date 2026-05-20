# -*- coding: utf-8 -*-
"""深度用户洞察 - Octopus Skill 四层自我进化（第3-4层核心）

深度分析用户数据，发现用户自己都没意识到的模式和需求。
支持用户画像、预测和主动建议三种操作。
数据存储在 data/evolution/ 目录中
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
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
EVO_DIR = os.path.join(DATA_DIR, "evolution")


def _collect_user_data(user: str) -> dict:
    """收集用户的所有相关数据"""
    # 用户画像
    profiles = load_json(os.path.join(DATA_DIR, "user_profiles.json")) or {}
    profile = profiles.get(user, {})

    # 偏好记录
    prefs = load_json(os.path.join(DATA_DIR, "preferences.json")) or {}
    pref_records = [r for r in prefs.get("records", []) if r.get("user") == user]

    # 行为信号
    signals_data = load_json(os.path.join(EVO_DIR, "behavior_signals.json")) or {}
    signals = [s for s in signals_data.get("signals", []) if s.get("user") == user]

    # 项目状态
    projects = load_json(os.path.join(DATA_DIR, "project_states.json")) or {}

    # 反馈数据
    feedback_files = [f for f in os.listdir(EVO_DIR) if f.endswith("_feedback.json")] if os.path.exists(EVO_DIR) else []
    all_feedback = []
    for ff in feedback_files:
        fb_data = load_json(os.path.join(EVO_DIR, ff)) or []
        all_feedback.extend(fb_data)

    # 适应建议
    adapt = load_json(os.path.join(EVO_DIR, "adaptations.json")) or {}

    return {
        "profile": profile, "preferences": pref_records,
        "signals": signals, "projects": projects,
        "feedback": all_feedback, "adaptations": adapt,
    }


def _demo_user_data() -> dict:
    """生成示例用户数据"""
    return {
        "profile": {
            "name": "用户A", "tech_preferences": ["Python", "Vue", "React"],
            "communication_style": "混合", "project_count": 5,
            "created_at": "2026-03-01T10:00:00",
        },
        "preferences": [
            {"preference": "简洁沟通", "category": "沟通", "recorded_at": "2026-05-01"},
            {"preference": "直接给代码", "category": "代码", "recorded_at": "2026-05-05"},
            {"preference": "先给方案再给代码", "category": "流程", "recorded_at": "2026-05-08"},
        ],
        "signals": [
            {"signal": "short_reply", "context": "追问阶段", "timestamp": "2026-05-10"},
            {"signal": "long_reply", "context": "技术讨论", "timestamp": "2026-05-11"},
            {"signal": "correction", "context": "代码审查", "timestamp": "2026-05-11"},
            {"signal": "enthusiasm", "context": "原型展示", "timestamp": "2026-05-12"},
            {"signal": "hesitation", "context": "需求确认", "timestamp": "2026-05-12"},
            {"signal": "redirect", "context": "执行阶段", "timestamp": "2026-05-13"},
        ],
        "projects": {
            "记账小程序": {"stage": "测试", "created_at": "2026-04-20"},
            "商城系统": {"stage": "执行", "created_at": "2026-04-25"},
            "博客平台": {"stage": "交付", "created_at": "2026-04-10"},
        },
        "feedback": [
            {"category": "功能", "rating": 4, "comment": "功能基本满足需求"},
            {"category": "体验", "rating": 3, "comment": "交互可以更流畅"},
        ],
        "adaptations": {},
    }


def generate_profile(user: str) -> str:
    """生成深度用户画像（Markdown格式）

    Args:
        user: 用户名

    Returns:
        Markdown 格式的深度画像
    """
    data = _collect_user_data(user)
    has_real = bool(data["profile"] or data["signals"] or data["preferences"])

    if not has_real:
        print_info(f"用户 '{user}' 暂无真实数据，使用示例数据演示。")
        data = _demo_user_data()

    profile = data["profile"]
    signals = data["signals"]
    prefs = data["preferences"]
    projects = data["projects"]
    feedback = data["feedback"]

    # 分析信号模式
    sig_counts = Counter(s["signal"] for s in signals)
    pref_cats = Counter(p.get("category", "其他") for p in prefs)

    # 技术背景
    techs = profile.get("tech_preferences", [])
    tech_str = "、".join(techs) if techs else "暂无记录"

    # 行为特征推断
    short_count = sig_counts.get("short_reply", 0) + sig_counts.get("quick_confirm", 0)
    long_count = sig_counts.get("long_reply", 0)
    if short_count > long_count * 2:
        comm_style = "简洁高效型"
    elif long_count > short_count * 2:
        comm_style = "详细思考型"
    else:
        comm_style = "灵活切换型"

    # 决策模式
    if sig_counts.get("hesitation", 0) > sig_counts.get("quick_confirm", 0):
        decision = "深思熟虑型（决策前需要充分信息）"
    elif sig_counts.get("quick_confirm", 0) > 2:
        decision = "快速决断型（偏好快速推进）"
    else:
        decision = "视情况而定"

    # 心理特征
    redirect_count = sig_counts.get("redirect", 0)
    correction_count = sig_counts.get("correction", 0)
    enthusiasm_count = sig_counts.get("enthusiasm", 0)

    if redirect_count >= 2:
        trait = "探索型——喜欢尝试新方向，容易在执行中改变主意"
    elif enthusiasm_count >= 2:
        trait = "热情型——对新事物充满好奇，容易被好想法激发"
    elif correction_count >= 2:
        trait = "严谨型——对细节要求高，会主动纠正偏差"
    else:
        trait = "均衡型——在不同场景下展现不同特质"

    # 能力边界（基于偏好和信号推断）
    strengths = []
    weaknesses = []
    if "代码" in pref_cats and pref_cats["代码"] >= 2:
        strengths.append("技术实现能力较强")
    if "功能" in [f.get("category", "") for f in feedback if f.get("rating", 0) >= 4]:
        strengths.append("对功能需求把握较好")
    if sig_counts.get("hesitation", 0) >= 2:
        weaknesses.append("需求确认阶段容易犹豫")
    if sig_counts.get("redirect", 0) >= 2:
        weaknesses.append("容易在执行中变更方向")
    if "体验" in [f.get("category", "") for f in feedback if f.get("rating", 0) <= 3]:
        weaknesses.append("对用户体验的敏感度可提升")

    # 项目经验
    proj_count = profile.get("project_count", len(projects))
    proj_stages = Counter(p.get("stage", "未知") for p in projects.values())

    lines = [
        f"# 深度用户画像 - {user}", "",
        f"**生成时间**: {now_iso()[:16].replace('T', ' ')}",
        f"**数据来源**: {'真实数据' if has_real else '示例数据（演示）'}", "",
        "## 基本信息", "",
        f"- **技术背景**: {tech_str}",
        f"- **项目经验**: {proj_count} 个项目",
        f"- **首次记录**: {profile.get('created_at', '未知')[:10]}", "",
        "## 行为特征", "",
        f"- **沟通风格**: {comm_style}",
        f"- **决策模式**: {decision}",
        f"- **工作节奏**: {'偏好快速迭代' if short_count > long_count else '偏好充分讨论'}", "",
        "## 能力边界", "",
    ]
    if strengths:
        lines.append("**擅长**: " + "、".join(strengths))
    if weaknesses:
        lines.append("**待提升**: " + "、".join(weaknesses))
    if not strengths and not weaknesses:
        lines.append("数据不足，暂时无法判断能力边界。")

    lines.extend(["", "## 心理特征", "", f"- {trait}", ""])

    # 成长轨迹
    lines.extend(["## 成长轨迹", ""])
    if signals:
        sorted_sigs = sorted(signals, key=lambda x: x.get("timestamp", ""))
        early = sorted_sigs[:len(sorted_sigs)//2] if len(sorted_sigs) > 1 else sorted_sigs
        late = sorted_sigs[len(sorted_sigs)//2:]
        early_counts = Counter(s["signal"] for s in early)
        late_counts = Counter(s["signal"] for s in late)
        lines.append(f"- **早期信号**: {dict(early_counts.most_common(3))}")
        lines.append(f"- **近期信号**: {dict(late_counts.most_common(3))}")
    else:
        lines.append("数据不足，暂时无法分析成长轨迹。")

    report = "\n".join(lines)

    # 保存报告
    os.makedirs(EVO_DIR, exist_ok=True)
    report_path = os.path.join(EVO_DIR, f"{user}_deep_profile.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print_success(f"深度画像已保存: {report_path}")
    return report


def predict_issues(user: str) -> dict:
    """预测用户在下一个项目中可能遇到的问题

    Args:
        user: 用户名

    Returns:
        预测结果 JSON
    """
    data = _collect_user_data(user)
    has_real = bool(data["signals"] or data["preferences"])
    if not has_real:
        print_info(f"用户 '{user}' 暂无数据，使用示例数据演示。")
        data = _demo_user_data()

    signals = data["signals"]
    prefs = data["preferences"]
    sig_counts = Counter(s["signal"] for s in signals)
    pref_cats = Counter(p.get("category", "其他") for p in prefs)

    predictions = []

    # 预测可能放弃的阶段
    if sig_counts.get("hesitation", 0) >= 2:
        predictions.append({
            "type": "放弃风险", "stage": "需求确认/规划阶段",
            "description": "该用户通常在规划阶段出现犹豫信号，可能在此阶段失去耐心",
            "probability": "高",
        })
    if sig_counts.get("redirect", 0) >= 2:
        predictions.append({
            "type": "方向变更", "stage": "执行阶段",
            "description": "该用户经常在执行中变更方向，可能导致项目延期",
            "probability": "高",
        })

    # 预测可能忽略的风险
    if "体验" not in pref_cats or pref_cats.get("体验", 0) == 0:
        predictions.append({
            "type": "忽略风险", "area": "用户体验",
            "description": "该用户很少关注体验相关话题，可能忽略UX风险",
            "probability": "中",
        })
    if sig_counts.get("quick_confirm", 0) >= 2:
        predictions.append({
            "type": "忽略风险", "area": "技术细节",
            "description": "该用户倾向于快速确认，可能忽略技术实现中的细节问题",
            "probability": "中",
        })

    # 预测可能需要的帮助
    if sig_counts.get("hesitation", 0) >= 1:
        predictions.append({
            "type": "需要帮助", "area": "决策支持",
            "description": "该用户在决策时经常犹豫，需要提供对比分析和明确建议",
            "probability": "高",
        })
    if sig_counts.get("correction", 0) >= 1:
        predictions.append({
            "type": "需要帮助", "area": "技术选型",
            "description": "该用户会主动纠正技术方向，说明有明确偏好但需要更好的前期沟通",
            "probability": "中",
        })

    if not predictions:
        predictions.append({
            "type": "数据不足", "area": "综合",
            "description": "暂无足够数据生成预测，建议积累更多使用数据",
            "probability": "低",
        })

    result = {
        "user": user,
        "predicted_at": now_iso(),
        "based_on_signals": len(signals),
        "predictions": predictions,
    }
    print_success(f"已生成 {len(predictions)} 条预测")
    return result


def generate_suggestions(user: str) -> dict:
    """基于深度洞察，给出超出用户预期的主动建议（第4层最高能力）

    Args:
        user: 用户名

    Returns:
        建议列表 JSON
    """
    data = _collect_user_data(user)
    has_real = bool(data["signals"] or data["preferences"] or data["projects"])
    if not has_real:
        print_info(f"用户 '{user}' 暂无数据，使用示例数据演示。")
        data = _demo_user_data()

    signals = data["signals"]
    prefs = data["preferences"]
    projects = data["projects"]
    sig_counts = Counter(s["signal"] for s in signals)
    pref_cats = Counter(p.get("category", "其他") for p in prefs)

    suggestions = []

    # 能力提升建议
    techs = data["profile"].get("tech_preferences", [])
    if len(techs) >= 3:
        top_techs = techs[:2]
        suggestions.append({
            "type": "能力提升",
            "content": f"你常用的技术栈包括{'、'.join(top_techs)}等，建议深入精通其中1-2项，而非广泛涉猎。",
            "reason": f"技术偏好涉及 {len(techs)} 项，专注度可提升",
            "priority": "中",
        })

    # 流程优化建议
    if sig_counts.get("redirect", 0) >= 2:
        suggestions.append({
            "type": "流程优化",
            "content": "你经常在项目执行中变更方向，建议这次先锁定核心功能，2周内不改动。",
            "reason": f"历史记录中有 {sig_counts['redirect']} 次方向变更信号",
            "priority": "高",
        })
    if sig_counts.get("hesitation", 0) >= 2:
        suggestions.append({
            "type": "流程优化",
            "content": "你在需求确认阶段容易犹豫，建议使用'决策清单'——列出必须回答的3个问题再推进。",
            "reason": f"历史记录中有 {sig_counts['hesitation']} 次犹豫信号",
            "priority": "高",
        })

    # 风险预警建议
    proj_stages = Counter(p.get("stage", "") for p in projects.values())
    if proj_stages.get("执行", 0) >= 2:
        suggestions.append({
            "type": "风险预警",
            "content": "你有多个项目处于执行阶段，注意避免同时推进太多项导致精力分散。",
            "reason": f"当前 {proj_stages.get('执行', 0)} 个项目在执行中",
            "priority": "中",
        })

    # 机会发现建议
    all_prefs_text = " ".join(p.get("preference", "") for p in prefs)
    if "数据分析" in all_prefs_text or "data" in all_prefs_text.lower():
        suggestions.append({
            "type": "机会发现",
            "content": "你最近的需求多与数据分析相关，要不要考虑系统学习一下数据分析方法论？",
            "reason": "偏好记录中多次出现数据分析相关关键词",
            "priority": "低",
        })
    if len(techs) >= 2 and ("前端" in str(techs) or "Vue" in str(techs) or "React" in str(techs)):
        suggestions.append({
            "type": "机会发现",
            "content": "你擅长前端开发，建议下次考虑使用 BaaS 服务减少后端工作量，专注前端体验。",
            "reason": "技术栈偏前端，后端可能是瓶颈",
            "priority": "低",
        })

    if not suggestions:
        suggestions.append({
            "type": "数据不足",
            "content": "暂无足够数据生成深度建议，请积累更多使用数据后重试。",
            "reason": "数据量不足",
            "priority": "低",
        })

    # 按优先级排序
    priority_order = {"高": 0, "中": 1, "低": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))

    result = {
        "user": user,
        "suggested_at": now_iso(),
        "total_suggestions": len(suggestions),
        "suggestions": suggestions,
    }
    print_success(f"已生成 {len(suggestions)} 条主动建议")
    return result


def main():
    parser = argparse.ArgumentParser(description="深度用户洞察 - Octopus Skill 四层自我进化")
    parser.add_argument("--user", required=True, help="用户名")
    parser.add_argument("--action", required=True, choices=["profile", "predict", "suggest"],
                        help="操作类型: profile(画像) / predict(预测) / suggest(建议)")
    args = parser.parse_args()

    if args.action == "profile":
        report = generate_profile(args.user)
        print(report)
    elif args.action == "predict":
        result = predict_issues(args.user)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = generate_suggestions(args.user)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
