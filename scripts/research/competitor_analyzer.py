# -*- coding: utf-8 -*-
"""
竞品分析器 - 提供结构化竞品分析框架
根据项目名称和竞品列表，生成Markdown格式的竞品分析报告。
使用内置示例数据，无需实际爬取。
"""

import argparse
import os
import sys

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
RESEARCH_DIR = os.path.join(DATA_DIR, "research")

# 内置竞品示例数据（常见记账类应用）
BUILTIN_DATA = {
    "随手记": {
        "core_features": ["多账本管理", "图表统计分析", "家庭共享记账", "投资理财追踪", "预算管理"],
        "advantages": ["品牌知名度高，用户基数大", "功能全面，覆盖个人/家庭/企业场景", "数据统计维度丰富"],
        "disadvantages": ["界面较为复杂，学习成本高", "广告推送较多", "部分高级功能需付费"],
        "user_summary": "老牌记账应用，功能强大但略显臃肿，适合有复杂记账需求的用户。",
    },
    "鲨鱼记账": {
        "core_features": ["极速记账", "简洁界面", "分类管理", "月度报表", "数据导出"],
        "advantages": ["界面清爽简洁", "操作流畅快速", "无广告干扰", "启动速度快"],
        "disadvantages": ["功能相对简单", "缺少投资理财模块", "社区互动较少"],
        "user_summary": "轻量级记账工具，主打简洁快速，适合只需基础记账功能的用户。",
    },
    "喵喵记账": {
        "core_features": ["萌系UI设计", "记账提醒", "分类标签", "统计报表", "主题皮肤"],
        "advantages": ["设计风格年轻化，颜值高", "记账体验轻松有趣", "适合年轻用户群体"],
        "disadvantages": ["功能深度不足", "专业数据分析较弱", "用户群体相对局限"],
        "user_summary": "面向年轻用户的萌系记账应用，颜值取胜，适合简单日常记账。",
    },
    "微信记账本": {
        "core_features": ["微信小程序", "快速记账", "群组记账", "简单统计"],
        "advantages": ["无需下载APP，即用即走", "与微信生态深度整合", "操作门槛极低"],
        "disadvantages": ["功能较为基础", "数据分析能力有限", "依赖微信平台"],
        "user_summary": "依托微信生态的轻量记账工具，适合轻度记账需求的微信用户。",
    },
    "网易有钱": {
        "core_features": ["自动记账", "银行卡同步", "资产管理", "理财推荐", "账单分析"],
        "advantages": ["支持自动导入银行流水", "资产管理功能完善", "网易品牌背书"],
        "disadvantages": ["已停止更新维护", "部分银行连接不稳定", "社区支持减少"],
        "user_summary": "曾以自动记账为特色的资产管理工具，目前已停止维护，不建议新用户使用。",
    },
}


def build_report(project: str, competitors: list) -> str:
    """构建竞品分析报告（Markdown格式）"""
    now = now_iso()[:16].replace("T", " ")

    lines = [
        f"# {project} - 竞品分析报告",
        "",
        f"> 生成时间：{now}",
        f"> 分析竞品数量：{len(competitors)}",
        "",
        "---",
        "",
        "## 一、分析概览",
        "",
        f"本项目为 **{project}**，以下对 {len(competitors)} 个主要竞品进行结构化分析。",
        "",
        "## 二、竞品详细分析",
        "",
    ]

    for i, comp_name in enumerate(competitors, 1):
        data = BUILTIN_DATA.get(comp_name)
        if not data:
            data = {
                "core_features": ["待调研"],
                "advantages": ["待调研"],
                "disadvantages": ["待调研"],
                "user_summary": f"竞品「{comp_name}」暂无内置数据，需手动调研补充。",
            }

        lines.append(f"### 2.{i} {comp_name}")
        lines.append("")
        lines.append("**核心功能：**")
        for feat in data["core_features"]:
            lines.append(f"- {feat}")
        lines.append("")
        lines.append("**优势：**")
        for adv in data["advantages"]:
            lines.append(f"- {adv}")
        lines.append("")
        lines.append("**劣势：**")
        for dis in data["disadvantages"]:
            lines.append(f"- {dis}")
        lines.append("")
        lines.append(f"**用户评价摘要：** {data['user_summary']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 差异化机会分析
    lines.append("## 三、差异化机会分析")
    lines.append("")
    lines.append("基于以上竞品分析，建议从以下维度寻找差异化突破口：")
    lines.append("")
    lines.append("| 维度 | 差异化方向 | 说明 |")
    lines.append("|------|-----------|------|")
    lines.append("| 用户体验 | 简洁与功能的平衡 | 在保持功能完整的同时降低学习成本 |")
    lines.append("| 目标人群 | 细分用户群体 | 聚焦特定人群（如学生、自由职业者）提供定制化功能 |")
    lines.append("| 技术创新 | AI辅助记账 | 利用AI技术实现智能分类、语音记账等 |")
    lines.append("| 生态整合 | 跨平台同步 | 提供小程序+APP+Web多端无缝体验 |")
    lines.append("| 商业模式 | 免费增值策略 | 核心功能免费，高级功能合理收费 |")
    lines.append("")
    lines.append("## 四、下一步行动建议")
    lines.append("")
    lines.append("1. 针对排名前3的竞品进行深度体验，记录交互细节")
    lines.append("2. 收集各竞品在应用商店的最新评分和用户评语")
    lines.append("3. 调研竞品的商业模式和盈利方式")
    lines.append("4. 结合自身优势，确定核心差异化定位")
    lines.append("")

    return "\n".join(lines)


def save_report(project: str, report: str) -> str:
    """保存报告到Markdown文件"""
    os.makedirs(RESEARCH_DIR, exist_ok=True)
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(RESEARCH_DIR, f"{safe_name}_competitors.md")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="竞品分析器 - 生成结构化竞品分析报告")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--competitors", required=True, help="竞品名称，逗号分隔")
    args = parser.parse_args()

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
    report = build_report(args.project, competitors)
    filepath = save_report(args.project, report)

    print_success(f"竞品分析报告已生成: {filepath}")
    print(f"分析竞品: {', '.join(competitors)}")


if __name__ == "__main__":
    main()
