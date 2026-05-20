# -*- coding: utf-8 -*-
"""PRD生成器 - Octopus Skill 谋略脑

根据需求信息生成产品需求文档(PRD)模板。
输出Markdown格式的PRD文档，保存到 data/plans/{project_name}_prd.md
"""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import save_json, now_iso, print_success

# 数据目录
PLANS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plans")

# 按项目类型预设的默认功能列表（含优先级）
DEFAULT_FEATURES = {
    "小程序": [
        ("用户注册/登录", "P0"), ("核心业务功能", "P0"), ("数据展示与列表", "P0"),
        ("搜索功能", "P1"), ("消息通知", "P1"), ("个人中心", "P1"),
        ("分享功能", "P2"), ("主题/皮肤", "P2"), ("数据导出", "P2"),
    ],
    "APP": [
        ("用户注册/登录", "P0"), ("核心业务功能", "P0"), ("推送通知", "P0"),
        ("离线缓存", "P1"), ("多语言支持", "P1"), ("个人中心", "P1"),
        ("社交分享", "P2"), ("深色模式", "P2"), ("无障碍适配", "P2"),
    ],
    "网站": [
        ("首页/导航", "P0"), ("核心内容展示", "P0"), ("搜索功能", "P0"),
        ("用户系统", "P1"), ("响应式适配", "P1"), ("SEO优化", "P1"),
        ("多语言", "P2"), ("CMS后台", "P2"), ("数据分析接入", "P2"),
    ],
    "游戏": [
        ("核心玩法", "P0"), ("用户引导", "P0"), ("存档系统", "P0"),
        ("音效/背景音乐", "P1"), ("排行榜", "P1"), ("成就系统", "P1"),
        ("社交分享", "P2"), ("多语言", "P2"), ("自定义设置", "P2"),
    ],
}

# 按项目类型预设的非功能需求
DEFAULT_NON_FUNC = {
    "小程序": ["启动时间 < 2秒", "页面切换流畅(60fps)", "兼容主流机型(近3年)"],
    "APP": ["启动时间 < 3秒", "崩溃率 < 0.1%", "兼容iOS 15+ / Android 10+"],
    "网站": ["首屏加载 < 3秒", "Lighthouse评分 > 90", "兼容Chrome/Safari/Firefox"],
    "游戏": ["帧率稳定 >= 30fps", "内存占用 < 500MB", "安装包 < 200MB"],
}

# 按项目类型预设的技术建议
DEFAULT_TECH = {
    "小程序": "前端：微信原生 / uni-app / Taro\n后端：Node.js / Python Flask\n数据库：MySQL / 云开发数据库",
    "APP": "前端：React Native / Flutter\n后端：Node.js / Go\n数据库：PostgreSQL / MongoDB",
    "网站": "前端：React / Vue.js + Next.js / Nuxt\n后端：Node.js / Python\n数据库：MySQL / PostgreSQL",
    "游戏": "引擎：Unity / Cocos Creator\n语言：C# / TypeScript\n后端：Node.js / Go",
}


def _get_features(project_type: str, custom_features: str) -> list:
    """获取功能列表，优先使用用户指定的，否则使用默认"""
    if custom_features:
        features = [(f.strip(), "P1") for f in custom_features.split(",") if f.strip()]
        if features:
            features[0] = (features[0][0], "P0")
        return features
    return DEFAULT_FEATURES.get(project_type, DEFAULT_FEATURES["网站"])


def _get_milestones(project_type: str) -> list:
    """根据项目类型生成里程碑计划"""
    base = [
        ("M1 - 需求确认与原型设计", "第1-2周", "完成PRD、原型图、技术方案评审"),
        ("M2 - 核心功能开发", "第3-5周", "完成P0功能开发与自测"),
        ("M3 - 功能完善与联调", "第6-7周", "完成P1功能、接口联调"),
        ("M4 - 测试与优化", "第8-9周", "功能测试、性能优化、Bug修复"),
        ("M5 - 上线与验收", "第10周", "灰度发布、用户验收、正式上线"),
    ]
    if project_type == "游戏":
        base.insert(2, ("M2.5 - 美术资源制作", "第4-5周", "完成核心美术资产、UI设计"))
    return base


def generate_prd(project: str, project_type: str, features: str, audience: str) -> str:
    """生成PRD文档内容（Markdown格式）"""
    now = now_iso()
    feat_list = _get_features(project_type, features)
    non_func = DEFAULT_NON_FUNC.get(project_type, DEFAULT_NON_FUNC["网站"])
    tech_advice = DEFAULT_TECH.get(project_type, DEFAULT_TECH["网站"])
    milestones = _get_milestones(project_type)

    lines = [
        f"# {project} - 产品需求文档(PRD)",
        "",
        f"> 生成时间：{now}",
        f"> 项目类型：{project_type}",
        f"> 目标用户：{audience or '待确认'}",
        "",
        "---",
        "",
        "## 一、项目概述",
        "",
        f"**{project}** 是一款面向{audience or '目标用户'}的{project_type}产品。",
        f"旨在通过核心功能解决用户痛点，提供简洁高效的使用体验。",
        "",
        "## 二、目标用户",
        "",
        f"- **主要用户：** {audience or '待进一步调研确认'}",
        "- **使用场景：** 日常高频使用",
        "- **用户痛点：** 现有解决方案体验不佳、功能缺失",
        "",
        "## 三、核心功能列表",
        "",
        "| 序号 | 功能名称 | 优先级 | 说明 |",
        "|------|---------|--------|------|",
    ]

    for i, (feat, priority) in enumerate(feat_list, 1):
        desc = "核心必备功能" if priority == "P0" else ("重要功能" if priority == "P1" else "锦上添花")
        lines.append(f"| {i} | {feat} | {priority} | {desc} |")

    lines.extend([
        "",
        "## 四、非功能需求",
        "",
    ])
    for req in non_func:
        lines.append(f"- {req}")

    lines.extend([
        "",
        "## 五、技术建议",
        "",
        "```",
        tech_advice,
        "```",
        "",
        "## 六、里程碑计划",
        "",
        "| 阶段 | 时间 | 交付物 |",
        "|------|------|--------|",
    ])
    for name, time_range, deliverable in milestones:
        lines.append(f"| {name} | {time_range} | {deliverable} |")

    lines.extend([
        "",
        "## 七、成功指标",
        "",
        "| 指标 | 目标值 | 说明 |",
        "|------|--------|------|",
        "| 日活跃用户(DAU) | 上线1月内 > 1000 | 核心活跃度指标 |",
        "| 用户留存率(次日) | > 40% | 产品粘性指标 |",
        "| 核心功能使用率 | > 60% | 功能价值验证 |",
        "| 用户满意度(NPS) | > 30 | 用户推荐意愿 |",
        "| 崩溃/错误率 | < 0.5% | 稳定性指标 |",
        "",
        "---",
        "*本文档由 Octopus 谋略脑自动生成，请根据实际情况调整和完善。*",
        "",
    ])

    return "\n".join(lines)


def save_prd(project: str, content: str) -> str:
    """保存PRD到Markdown文件"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(PLANS_DIR, f"{safe_name}_prd.md")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print_success(f"PRD文档已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="PRD生成器 - Octopus 谋略脑")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--type", required=True, help="项目类型(小程序/APP/网站/游戏)")
    parser.add_argument("--features", default="", help="核心功能，逗号分隔(可选)")
    parser.add_argument("--audience", default="", help="目标用户群体(可选)")
    args = parser.parse_args()

    content = generate_prd(args.project, args.type, args.features, args.audience)
    filepath = save_prd(args.project, content)

    print_success(f"PRD文档已生成: {filepath}")
    print_success(f"项目: {args.project} | 类型: {args.type}")


if __name__ == "__main__":
    main()
