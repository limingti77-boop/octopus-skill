# -*- coding: utf-8 -*-
"""项目状态追踪工具 - Octopus Skill 记忆管理

追踪项目状态，包括项目名、描述、当前阶段、创建时间、最后更新时间。
数据存储在 data/project_states.json
"""

import argparse
import json
import os
import sys

# 添加父目录到路径以导入 common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_json, save_json, now_iso, print_success, print_error, print_warning

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "project_states.json")

# 合法阶段列表
VALID_STAGES = ["需求收集", "调研", "规划", "执行", "测试", "交付"]


def create_project(name: str, description: str = "", stage: str = "需求收集"):
    """创建新项目

    Args:
        name: 项目名
        description: 项目描述
        stage: 初始阶段

    Returns:
        创建的项目状态
    """
    data = load_json(DATA_FILE)
    if name in data:
        print_error(f"项目 '{name}' 已存在，请使用 update 操作。")
        return data[name]

    if stage not in VALID_STAGES:
        print_warning(f"阶段 '{stage}' 不在标准列表中，已使用默认值。")
        stage = "需求收集"

    now = now_iso()
    project = {
        "name": name,
        "description": description,
        "stage": stage,
        "created_at": now,
        "updated_at": now,
    }
    data[name] = project
    save_json(DATA_FILE, data)
    print_success(f"已创建项目: {name}（阶段: {stage}）")
    return project


def update_project(name: str, description: str = "", stage: str = ""):
    """更新项目状态

    Args:
        name: 项目名
        description: 新的项目描述（留空不更新）
        stage: 新的阶段（留空不更新）

    Returns:
        更新后的项目状态，非法阶段时返回 None
    """
    data = load_json(DATA_FILE)
    if name not in data:
        print(f"[提示] 项目 '{name}' 不存在，自动创建。")
        return create_project(name, description, stage or "需求收集")

    project = data[name]

    if description:
        project["description"] = description

    if stage:
        if stage not in VALID_STAGES:
            print_error(f"阶段 '{stage}' 不在标准列表中: {VALID_STAGES}，拒绝更新。")
            return None
        project["stage"] = stage

    project["updated_at"] = now_iso()
    data[name] = project
    save_json(DATA_FILE, data)
    print_success(f"已更新项目: {name}（阶段: {project['stage']}）")
    return project


def get_project(name: str):
    """获取单个项目状态

    Args:
        name: 项目名

    Returns:
        项目状态字典，不存在则返回 None
    """
    data = load_json(DATA_FILE)
    if name not in data:
        print(f"[提示] 项目 '{name}' 不存在。")
        return None
    print(f"[查询] 项目状态: {name}")
    return data[name]


def list_projects() -> list:
    """列出所有项目

    Returns:
        项目列表
    """
    data = load_json(DATA_FILE)
    if not data:
        print("[提示] 暂无项目记录。")
        return []

    projects = list(data.values())
    print(f"[查询] 共 {len(projects)} 个项目:")
    for p in projects:
        print(f"  - {p['name']} | 阶段: {p['stage']} | 更新: {p['updated_at'][:10]}")
    return projects


def delete_project(name: str) -> bool:
    """删除项目

    Args:
        name: 项目名

    Returns:
        成功返回 True，不存在返回 False
    """
    data = load_json(DATA_FILE)
    if name not in data:
        print_error(f"项目 '{name}' 不存在。")
        return False

    del data[name]
    save_json(DATA_FILE, data)
    print_success(f"已删除项目: {name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="项目状态追踪工具")
    parser.add_argument("--action", required=True,
                        choices=["create", "update", "get", "list", "delete"],
                        help="操作类型: create / update / get / list / delete")
    parser.add_argument("--name", default="", help="项目名（list 时不需要）")
    parser.add_argument("--description", default="", help="项目描述")
    parser.add_argument("--stage", default="", help="项目阶段: 需求收集/调研/规划/执行/测试/交付")
    args = parser.parse_args()

    if args.action == "list":
        result = list_projects()
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.action == "delete":
        if not args.name:
            print_error("delete 操作需要 --name 参数。")
            return
        delete_project(args.name)
        return

    if not args.name:
        print_error(f"{args.action} 操作需要 --name 参数。")
        return

    if args.action == "create":
        result = create_project(args.name, args.description, args.stage or "需求收集")
    elif args.action == "update":
        result = update_project(args.name, args.description, args.stage)
    else:
        result = get_project(args.name)

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
