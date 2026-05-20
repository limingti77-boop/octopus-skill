# -*- coding: utf-8 -*-
"""用户画像管理工具 - Octopus Skill 记忆管理

管理用户画像信息，包括姓名、技术偏好、沟通风格偏好、历史项目数。
数据存储在 data/user_profiles.json
"""

import argparse
import json
import os
import sys

# 添加父目录到路径以导入 common
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common import load_json, save_json, now_iso, print_success, print_error

# 数据文件路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "user_profiles.json")


def create_user(user: str, tech: str = "", style: str = ""):
    """创建新用户画像

    Args:
        user: 用户名
        tech: 技术偏好（逗号分隔）
        style: 沟通风格偏好

    Returns:
        创建的用户画像，用户已存在时返回 None
    """
    data = load_json(DATA_FILE)
    if user in data:
        print_error(f"用户 '{user}' 已存在，请使用 update 操作。")
        return None

    now = now_iso()
    profile = {
        "name": user,
        "tech_preferences": [t.strip() for t in tech.split(",") if t.strip()],
        "communication_style": style,
        "project_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    data[user] = profile
    save_json(DATA_FILE, data)
    print_success(f"已创建用户画像: {user}")
    return profile


def update_user(user: str, tech: str = "", style: str = "", project_delta: int = 0):
    """更新用户画像

    Args:
        user: 用户名
        tech: 技术偏好（逗号分隔，会追加而非覆盖）
        style: 沟通风格偏好（覆盖更新）
        project_delta: 项目数变化量（正数增加，负数减少）

    Returns:
        更新后的用户画像
    """
    data = load_json(DATA_FILE)
    if user not in data:
        print(f"[提示] 用户 '{user}' 不存在，自动创建。")
        return create_user(user, tech, style)

    profile = data[user]

    # 追加技术偏好（去重）
    if tech:
        new_techs = [t.strip() for t in tech.split(",") if t.strip()]
        existing = set(profile.get("tech_preferences", []))
        profile["tech_preferences"] = sorted(existing | set(new_techs))

    # 更新沟通风格
    if style:
        profile["communication_style"] = style

    # 更新项目数
    if project_delta != 0:
        profile["project_count"] = max(0, profile.get("project_count", 0) + project_delta)

    profile["updated_at"] = now_iso()
    data[user] = profile
    save_json(DATA_FILE, data)
    print_success(f"已更新用户画像: {user}")
    return profile


def get_user(user: str):
    """获取用户画像

    Args:
        user: 用户名

    Returns:
        用户画像字典，不存在则返回 None
    """
    data = load_json(DATA_FILE)
    if user not in data:
        print(f"[提示] 用户 '{user}' 不存在。")
        return None
    print(f"[查询] 用户画像: {user}")
    return data[user]


def list_users() -> list:
    """列出所有用户

    Returns:
        用户画像列表
    """
    data = load_json(DATA_FILE)
    if not data:
        print("[提示] 暂无用户画像记录。")
        return []

    users = list(data.values())
    print(f"[查询] 共 {len(users)} 个用户:")
    for u in users:
        techs = ", ".join(u.get("tech_preferences", []))
        print(f"  - {u['name']} | 技术: {techs or '无'} | 项目: {u.get('project_count', 0)}")
    return users


def delete_user(user: str) -> bool:
    """删除用户画像

    Args:
        user: 用户名

    Returns:
        成功返回 True，不存在返回 False
    """
    data = load_json(DATA_FILE)
    if user not in data:
        print_error(f"用户 '{user}' 不存在。")
        return False

    del data[user]
    save_json(DATA_FILE, data)
    print_success(f"已删除用户画像: {user}")
    return True


def main():
    parser = argparse.ArgumentParser(description="用户画像管理工具")
    parser.add_argument("--action", required=True,
                        choices=["create", "update", "get", "list", "delete"],
                        help="操作类型: create(创建) / update(更新) / get(查询) / list(列出) / delete(删除)")
    parser.add_argument("--user", default="", help="用户名（list 时不需要）")
    parser.add_argument("--tech", default="", help="技术偏好，逗号分隔，如 React,Python")
    parser.add_argument("--style", default="", help="沟通风格偏好，如 简洁、详细")
    parser.add_argument("--projects", type=int, default=0,
                        help="项目数变化量（仅 update 时生效，如 +1 或 -1）")
    args = parser.parse_args()

    if args.action == "list":
        result = list_users()
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.action == "delete":
        if not args.user:
            print_error("delete 操作需要 --user 参数。")
            return
        delete_user(args.user)
        return

    if not args.user:
        print_error(f"{args.action} 操作需要 --user 参数。")
        return

    if args.action == "create":
        result = create_user(args.user, args.tech, args.style)
    elif args.action == "update":
        result = update_user(args.user, args.tech, args.style, args.projects)
    else:
        result = get_user(args.user)

    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
