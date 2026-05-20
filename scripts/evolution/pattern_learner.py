# -*- coding: utf-8 -*-
"""模式学习器 - Octopus Skill 进化脑
分析历史项目数据，发现常见模式和规律，给出优化建议。
支持深层模式发现（行为一致性、成长趋势、痛点模式、潜力领域、协作效率）。"""
import argparse, json, os, sys

# 导入共享工具模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_warning, print_error, print_info
from collections import Counter
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "evolution")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "patterns.json")
SIGNALS_FILE = os.path.join(OUTPUT_DIR, "behavior_signals.json")
STAGE_ORDER = ["需求收集", "规划", "设计", "执行", "测试", "交付"]
TECH_REC = {"Python": ["数据分析", "自动化脚本", "AI/ML"], "Vue": ["Nuxt.js", "Pinia状态管理", "移动端适配"],
            "React": ["Next.js", "React Native", "TypeScript深度"], "Java": ["Spring Boot", "微服务架构", "Kotlin"],
            "TypeScript": ["全栈开发", "Node.js后端", "类型体操"], "Node.js": ["NestJS", "GraphQL", "Serverless"]}
NEG_KW = ["需要更多引导", "需要更仔细理解需求", "偏好简化流程", "太复杂", "不对", "搞错"]


def _demo_data() -> dict:
    """生成示例数据"""
    recs = [("用户A", "简洁沟通", "沟通", "2026-05-01T10:00:00"), ("用户A", "简洁沟通", "沟通", "2026-05-05T14:00:00"),
            ("用户A", "直接给代码", "代码", "2026-05-08T09:00:00"), ("用户B", "详细解释", "沟通", "2026-05-02T11:00:00"),
            ("用户B", "详细解释", "沟通", "2026-05-06T16:00:00"), ("用户B", "先给方案再给代码", "流程", "2026-05-09T10:00:00"),
            ("用户C", "React", "代码", "2026-05-03T08:00:00"), ("用户C", "TypeScript", "代码", "2026-05-07T13:00:00")]
    projs = [("记账小程序", "测试", "2026-04-20T10:00:00"), ("商城系统", "执行", "2026-04-25T10:00:00"),
             ("博客平台", "交付", "2026-04-10T10:00:00"), ("任务管理", "规划", "2026-05-01T10:00:00"),
             ("数据分析工具", "需求收集", "2026-05-10T10:00:00")]
    return {
        "preferences": {"records": [{"user": u, "preference": p, "category": c, "recorded_at": t} for u, p, c, t in recs]},
        "user_profiles": {
            "用户A": {"name": "用户A", "tech_preferences": ["Python", "Vue"], "communication_style": "简洁", "project_count": 5},
            "用户B": {"name": "用户B", "tech_preferences": ["Java", "React"], "communication_style": "详细", "project_count": 3},
            "用户C": {"name": "用户C", "tech_preferences": ["React", "TypeScript", "Node.js"], "communication_style": "简洁", "project_count": 8}},
        "project_states": {n: {"name": n, "stage": s, "created_at": t} for n, s, t in projs}}

def _load_data():
    """加载所有数据源，无数据时使用示例"""
    prefs = load_json(os.path.join(DATA_DIR, "preferences.json"))
    profiles = load_json(os.path.join(DATA_DIR, "user_profiles.json"))
    projects = load_json(os.path.join(DATA_DIR, "project_states.json"))
    use_demo = not prefs and not profiles and not projects
    if use_demo:
        print_info("数据文件不存在，使用示例数据演示。")
        d = _demo_data()
        prefs, profiles, projects = d["preferences"], d["user_profiles"], d["project_states"]
    return prefs, profiles, projects, use_demo

def _analyze_preferences(prefs: dict) -> list:
    """分析用户偏好模式，返回高频偏好列表"""
    records = prefs.get("records", [])
    if not records:
        return []
    user_prefs = {}
    for r in records:
        user_prefs.setdefault(r.get("user", "未知"), []).append(r)
    patterns = []
    for user, items in user_prefs.items():
        top = Counter(i.get("preference", "") for i in items).most_common(1)[0]
        if top[1] >= 2:
            patterns.append({"user": user, "top_preference": top[0], "frequency": top[1],
                             "description": f"用户{user}偏好「{top[0]}」，出现 {top[1]} 次"})
    return patterns

def _analyze_projects(projects: dict) -> list:
    if not projects:
        return []
    sc = Counter(p.get("stage", "未知") for p in projects.values())
    return [{"stage": s, "count": c} for s, c in sc.most_common()]

def _analyze_tech(profiles: dict) -> list:
    if not profiles:
        return []
    tc = Counter()
    for p in profiles.values():
        for t in p.get("tech_preferences", []):
            tc[t] += 1
    return [{"tech": t, "count": c} for t, c in tc.most_common()]

def _detect_common_issues(prefs: dict) -> list:
    records = prefs.get("records", [])
    if not records:
        return []
    cc = Counter(r.get("category", "其他") for r in records)
    return [{"category": cat, "count": cnt} for cat, cnt in cc.most_common()]

def analyze_patterns() -> dict:
    """分析所有历史数据，生成分析报告"""
    prefs, profiles, projects, use_demo = _load_data()
    report = {"generated_at": now_iso(), "data_source": "示例数据（演示）" if use_demo else "真实数据",
              "user_preference_patterns": _analyze_preferences(prefs), "project_type_distribution": _analyze_projects(projects),
              "tech_stack_patterns": _analyze_tech(profiles), "common_issues": _detect_common_issues(prefs)}
    save_json(OUTPUT_FILE, report)
    print_success(f"分析报告已保存: {OUTPUT_FILE}")
    return report

def generate_suggestions(report: dict) -> list:
    """基于分析结果给出优化建议"""
    suggestions = []
    for p in report.get("user_preference_patterns", []):
        u, pref = p["user"], p["top_preference"]
        if "简洁" in pref:
            suggestions.append(f"用户{u}偏好简洁沟通，建议减少追问次数，直接给出结论。")
        elif "详细" in pref:
            suggestions.append(f"用户{u}偏好详细解释，建议在给出方案时附上完整的思路说明。")
        elif "代码" in pref:
            suggestions.append(f"用户{u}偏好代码优先，建议先提供可运行代码，再补充说明。")
    tech = report.get("tech_stack_patterns", [])
    if tech:
        suggestions.append(f"最受欢迎的技术栈是「{tech[0]['tech']}」，建议优先使用该技术栈进行项目规划。")
    proj = report.get("project_type_distribution", [])
    if proj:
        suggestions.append(f"当前项目多处于「{proj[0]['stage']}」阶段，建议准备相应的工具和资源。")
    cat_map = {"沟通": "建议建立标准化的沟通模板，减少理解偏差。", "代码": "建议建立代码审查清单，提前发现潜在问题。",
               "文档": "建议使用统一的文档模板，保持输出格式一致。", "设计": "建议在设计阶段增加确认环节，降低返工风险。",
               "流程": "建议梳理并固化常用工作流程，提升协作效率。"}
    for issue in report.get("common_issues", []):
        if issue["category"] in cat_map:
            suggestions.append(cat_map[issue["category"]])
    if not suggestions:
        suggestions.append("暂无足够数据生成建议，请积累更多使用数据后重试。")
    report["suggestions"] = suggestions
    save_json(OUTPUT_FILE, report)
    return suggestions

def deep_analyze(user: str = "") -> dict:
    """深层模式发现：行为一致性、成长趋势、痛点模式、潜力领域、协作效率"""
    prefs, profiles, projects, _ = _load_data()
    signals = load_json(SIGNALS_FILE)
    records = prefs.get("records", [])
    if user:
        records = [r for r in records if r.get("user") == user]
        profiles = {k: v for k, v in profiles.items() if k == user}
    all_users = list(set(r.get("user", "") for r in records)) if records else list(profiles.keys())
    dims = {}
    # 维度1: 行为一致性
    consistency = {}
    for u in all_users:
        ur = [r for r in records if r.get("user") == u]
        if len(ur) < 2:
            consistency[u] = {"score": "数据不足", "details": "记录少于2条"}
            continue
        ratio = len(set(r.get("preference", "") for r in ur)) / len(ur)
        score = "高" if ratio <= 0.3 else ("中" if ratio <= 0.6 else "低")
        desc = {"高": "行为高度一致，偏好稳定", "中": "行为较为一致，偶有变化", "低": "行为多变，可能在不同场景下有不同需求"}
        consistency[u] = {"score": score, "unique_ratio": round(ratio, 2), "details": desc[score]}
    dims["behavior_consistency"] = consistency
    # 维度2: 成长趋势
    growth = {}
    for u in all_users:
        p = profiles.get(u, {})
        tl = p.get("tech_preferences", [])
        n = len(tl)
        trend = "快速扩展中" if n >= 4 else ("稳步成长中" if n >= 2 else ("专注深耕中" if n == 1 else "待观察"))
        growth[u] = {"tech_stack": tl, "tech_breadth": n, "project_count": p.get("project_count", 0), "growth_trend": trend}
    dims["growth_trend"] = growth
    # 维度3: 痛点模式
    pain = {}
    for u in all_users:
        ur = [r for r in records if r.get("user") == u]
        neg = [r for r in ur if any(kw in r.get("preference", "") for kw in NEG_KW)]
        us = signals.get(u, []) if isinstance(signals, dict) else []
        sn = [s for s in us if s.get("signal", "") in ("frustration", "correction", "hesitation")]
        pc = Counter(r.get("category", "其他") for r in neg)
        pain[u] = {"negative_signal_count": len(neg) + len(sn), "pain_categories": dict(pc.most_common()), "signal_insights": sn[:3]}
    dims["pain_point_patterns"] = pain
    # 维度4: 潜力领域
    potential = {}
    for u in all_users:
        ct = set(profiles.get(u, {}).get("tech_preferences", []))
        recs = []
        for t in ct:
            recs.extend(TECH_REC.get(t, []))
        potential[u] = {"current_tech": list(ct), "recommended_directions": list(set(recs) - ct)[:5]}
    dims["potential_fields"] = potential
    # 维度5: 协作效率
    collab = {}
    for u in all_users:
        ur = [r for r in records if r.get("user") == u]
        if len(ur) < 2:
            collab[u] = {"efficiency": "数据不足", "details": "交互记录不足"}
            continue
        ts = []
        for r in ur:
            try:
                ts.append(datetime.fromisoformat(r.get("recorded_at", "")))
            except (ValueError, TypeError):
                continue
        if len(ts) < 2:
            collab[u] = {"efficiency": "待观察", "details": "有效时间戳不足"}
            continue
        ts.sort()
        span = (ts[-1] - ts[0]).days or 1
        freq = len(ts) / span
        eff = "高效协作" if freq >= 1 else ("正常协作" if freq >= 0.3 else "低频协作")
        up = {k: v for k, v in projects.items() if v.get("user") == u or k.startswith(u)}
        sp = [STAGE_ORDER.index(p.get("stage", "")) for p in up.values() if p.get("stage", "") in STAGE_ORDER]
        collab[u] = {"efficiency": eff, "interaction_frequency": round(freq, 2),
                     "total_interactions": len(ur), "active_span_days": span, "project_progress": sp}
    dims["collaboration_efficiency"] = collab
    report = {"generated_at": now_iso(), "analysis_type": "deep_analysis",
              "target_user": user or "全部用户", "dimensions": dims}
    deep_file = os.path.join(OUTPUT_DIR, "deep_analysis.json")
    save_json(deep_file, report)
    print_info(f"深度分析: 目标: {user or '全部用户'}")
    for i, name in enumerate(["行为一致性", "成长趋势", "痛点模式", "潜力领域", "协作效率"], 1):
        print(f"  {i}. {name}: {len(list(dims.values())[i-1])} 位用户")
    print_success(f"深度分析报告已保存: {deep_file}")
    return report

def main():
    parser = argparse.ArgumentParser(description="模式学习器 - Octopus Skill 进化脑")
    parser.add_argument("--action", required=True, choices=["analyze", "suggest", "deep_analyze"],
                        help="操作类型: analyze(分析) / suggest(建议) / deep_analyze(深层分析)")
    parser.add_argument("--user", default="", help="用户名（deep_analyze 可选）")
    args = parser.parse_args()
    if args.action == "analyze":
        report = analyze_patterns()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.action == "deep_analyze":
        report = deep_analyze(args.user)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                report = json.load(f)
            print_info("已加载已有分析报告。")
        else:
            print_info("未找到分析报告，先执行分析...")
            report = analyze_patterns()
        suggestions = generate_suggestions(report)
        print(f"\n[优化建议] 共 {len(suggestions)} 条:")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")

if __name__ == "__main__":
    main()
