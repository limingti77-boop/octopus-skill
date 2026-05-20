# -*- coding: utf-8 -*-
"""需求分析器 - Octopus Skill 探索模块

将收集到的问答记录整理成结构化的需求文档（Markdown格式）。
输出文件保存到 data/requirements/{project_name}.md
"""

import argparse
import json
import os
import sys

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success, print_info

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
REQUIREMENTS_DIR = os.path.join(DATA_DIR, "requirements")

# 示例问答数据（用于演示）
SAMPLE_QA_RECORDS = {
    "project_name": "记账小程序",
    "project_type": "小程序",
    "qa_records": [
        {"question": "这个小程序主要解决什么问题？", "answer": "帮助用户记录日常收支，简单方便"},
        {"question": "目标用户是谁？", "answer": "大学生和刚工作的年轻人，个人使用"},
        {"question": "需要用户登录和个人数据存储吗？", "answer": "需要微信登录，数据存云端"},
        {"question": "有没有参考的同类产品？", "answer": "类似鲨鱼记账，但更简洁"},
        {"question": "具体需要哪些功能模块？", "answer": "记账、分类、统计图表、月度报告"},
        {"question": "数据需要云端存储还是本地即可？", "answer": "云端存储，支持多设备同步"},
        {"question": "对UI风格有什么偏好？", "answer": "简约清新，白色为主色调"},
    ],
}


def _load_qa_records(input_path: str) -> dict:
    """从JSON文件加载问答记录"""
    return load_json(input_path)


def _extract_features(qa_records: list) -> list:
    """从问答记录中提取核心功能列表"""
    features = []
    for record in qa_records:
        answer = record.get("answer", "")
        question = record.get("question", "")
        if any(kw in question for kw in ["功能模块", "哪些功能"]):
            items = answer.replace("、", ",").split(",")
            for item in items:
                item = item.strip()
                if item and len(item) >= 2 and len(item) <= 20:
                    features.append(item)
    return features


def _extract_constraints(qa_records: list) -> list:
    """从问答记录中提取约束条件"""
    # 关键词 -> 输出前缀的映射
    rules = [
        (["技术", "平台", "框架", "栈"], "技术选型"),
        (["风格", "UI", "设计", "偏好"], "设计风格"),
        (["时间", "截止", "周期", "排期"], "时间要求"),
        (["登录"], "平台要求"),
    ]
    constraints = []
    for record in qa_records:
        answer, question = record.get("answer", ""), record.get("question", "")
        for kws, prefix in rules:
            if any(kw in question for kw in kws):
                constraints.append(f"{prefix}：{answer}")
    return constraints


def _extract_target_users(qa_records: list) -> str:
    """从问答记录中提取目标用户描述"""
    for record in qa_records:
        question = record.get("question", "")
        if "用户" in question or "受众" in question or "谁" in question:
            return record.get("answer", "未明确")
    return "未明确"


def _extract_non_functional(qa_records: list) -> list:
    """从问答记录中提取非功能需求"""
    non_func = []
    seen = set()
    for record in qa_records:
        answer = record.get("answer", "")
        question = record.get("question", "")
        if any(kw in question for kw in ["性能", "安全", "隐私", "并发", "SEO"]):
            item = f"{question}：{answer}"
            if item not in seen:
                seen.add(item)
                non_func.append(item)
        if ("云端" in answer or "同步" in answer) and "数据同步" not in seen:
            seen.add("数据同步")
            non_func.append("数据同步：支持云端数据同步")
        if ("简洁" in answer or "简单" in answer) and "易用性" not in seen:
            seen.add("易用性")
            non_func.append("易用性：界面简洁，操作简单直观")
    return non_func


def generate_requirement_doc(project_name: str, qa_data: dict) -> str:
    """根据问答记录生成结构化需求文档

    Args:
        project_name: 项目名称
        qa_data: 问答数据字典，包含 qa_records 列表

    Returns:
        Markdown格式的需求文档内容
    """
    records = qa_data.get("qa_records", [])
    project_type = qa_data.get("project_type", "未指定")

    # 提取结构化信息
    target_users = _extract_target_users(records)
    features = _extract_features(records)
    constraints = _extract_constraints(records)
    non_functional = _extract_non_functional(records)

    # 构建项目概述
    overview = f"一个面向{target_users}的{project_name}"
    if records:
        overview += f"（{records[0].get('answer', '')}）"

    # 辅助函数：生成列表段落
    def _bullet_list(items, numbered=False):
        if not items:
            return ["（待补充）"]
        return [f"{i}. {v}" if numbered else f"- {v}" for i, v in enumerate(items, 1)]

    # 生成Markdown文档
    lines = [
        f"# {project_name} - 需求文档", "",
        f"> 生成时间：{now_iso()[:16].replace('T', ' ')}",
        f"> 项目类型：{project_type}", "", "---", "",
        "## 1. 项目概述", "", overview, "",
        "## 2. 目标用户", "", target_users, "",
        "## 3. 核心功能", "",
    ]
    lines.extend(_bullet_list(features, numbered=True))
    lines.extend(["", "## 4. 非功能需求", ""])
    lines.extend(_bullet_list(non_functional))
    lines.extend(["", "## 5. 约束条件", ""])
    lines.extend(_bullet_list(constraints))

    lines.extend(["", "## 6. 原始问答记录", ""])

    for i, record in enumerate(records, 1):
        lines.append(f"### Q{i}: {record.get('question', '')}")
        lines.append("")
        lines.append(f"**A:** {record.get('answer', '')}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="需求分析器 - Octopus 探索模块")
    parser.add_argument("--project", required=True, help="项目名称，如 '记账小程序'")
    parser.add_argument("--input", default="", help="问答记录JSON文件路径（可选，不提供则使用示例数据）")
    args = parser.parse_args()

    # 加载问答数据
    if args.input:
        qa_data = _load_qa_records(args.input)
    else:
        print_info("未指定输入文件，使用示例数据演示")
        qa_data = SAMPLE_QA_RECORDS.copy()
        qa_data["project_name"] = args.project

    # 生成需求文档
    doc_content = generate_requirement_doc(args.project, qa_data)

    # 保存到文件
    os.makedirs(REQUIREMENTS_DIR, exist_ok=True)
    output_path = os.path.join(REQUIREMENTS_DIR, f"{args.project}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc_content)

    print_success(f"需求文档已生成: {output_path}")
    print("")
    print(doc_content)


if __name__ == "__main__":
    main()
