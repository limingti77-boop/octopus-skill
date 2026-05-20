# -*- coding: utf-8 -*-
"""任务拆解器 - Octopus Skill 巧手脑

将项目方案拆解为可执行的具体任务列表。
输出JSON格式任务列表，保存到 data/execution/{project_name}_tasks.json
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import save_json, now_iso, print_success

# 数据目录
EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "execution")

# 内置任务模板：按项目类型定义默认任务列表
# 格式: (name, category, depends_on, priority, estimated_effort)
_TASK_TEMPLATES = {
    "小程序": [
        ("需求分析与原型设计", "design", [], "P0", "中"),
        ("UI视觉设计", "design", ["T1"], "P0", "中"),
        ("技术方案设计", "design", ["T1"], "P0", "小"),
        ("项目工程初始化", "dev", ["T3"], "P0", "小"),
        ("用户认证模块开发", "dev", ["T4", "T2"], "P0", "中"),
        ("核心业务功能开发", "dev", ["T4", "T2"], "P0", "大"),
        ("数据展示与列表页", "dev", ["T6"], "P0", "中"),
        ("个人中心开发", "dev", ["T5"], "P1", "中"),
        ("搜索功能开发", "dev", ["T6"], "P1", "小"),
        ("消息通知功能", "dev", ["T5"], "P1", "小"),
        ("接口联调", "dev", ["T5", "T6", "T7", "T8", "T9"], "P0", "中"),
        ("单元测试编写", "test", ["T6", "T7"], "P1", "中"),
        ("集成测试", "test", ["T10"], "P0", "中"),
        ("性能优化", "test", ["T13"], "P1", "中"),
        ("体验走查与Bug修复", "test", ["T13", "T14"], "P0", "中"),
        ("提交审核与发布", "deploy", ["T15"], "P0", "小"),
        ("线上监控配置", "deploy", ["T16"], "P1", "小"),
    ],
    "APP": [
        ("需求分析与原型设计", "design", [], "P0", "中"),
        ("UI视觉设计", "design", ["T1"], "P0", "大"),
        ("技术方案设计", "design", ["T1"], "P0", "中"),
        ("项目工程初始化", "dev", ["T3"], "P0", "小"),
        ("用户认证与权限", "dev", ["T4", "T2"], "P0", "中"),
        ("核心业务功能开发", "dev", ["T4", "T2"], "P0", "大"),
        ("推送通知集成", "dev", ["T5"], "P1", "中"),
        ("离线缓存实现", "dev", ["T6"], "P1", "中"),
        ("个人中心开发", "dev", ["T5"], "P1", "中"),
        ("接口联调", "dev", ["T5", "T6", "T7", "T8", "T9"], "P0", "大"),
        ("单元测试编写", "test", ["T6", "T7"], "P1", "中"),
        ("集成测试", "test", ["T10"], "P0", "中"),
        ("性能优化与内存调优", "test", ["T12"], "P1", "中"),
        ("多机型兼容测试", "test", ["T13"], "P0", "中"),
        ("应用商店提交", "deploy", ["T14"], "P0", "中"),
        ("灰度发布与监控", "deploy", ["T15"], "P1", "小"),
    ],
    "网站": [
        ("需求分析与信息架构", "design", [], "P0", "中"),
        ("UI/UX设计", "design", ["T1"], "P0", "中"),
        ("技术方案设计", "design", ["T1"], "P0", "小"),
        ("项目工程初始化", "dev", ["T3"], "P0", "小"),
        ("首页与导航开发", "dev", ["T4", "T2"], "P0", "中"),
        ("核心内容展示页", "dev", ["T4", "T2"], "P0", "中"),
        ("用户系统开发", "dev", ["T4"], "P1", "中"),
        ("搜索功能开发", "dev", ["T6"], "P1", "小"),
        ("后台管理系统", "dev", ["T5", "T6"], "P1", "大"),
        ("接口联调", "dev", ["T5", "T6", "T7", "T8"], "P0", "中"),
        ("SEO优化实施", "dev", ["T5"], "P1", "小"),
        ("单元测试编写", "test", ["T5", "T6"], "P1", "中"),
        ("端到端测试", "test", ["T10"], "P0", "中"),
        ("性能与Lighthouse优化", "test", ["T12"], "P1", "中"),
        ("安全审计", "test", ["T13"], "P0", "小"),
        ("部署与上线", "deploy", ["T14"], "P0", "小"),
        ("CDN与监控配置", "deploy", ["T15"], "P1", "小"),
    ],
    "游戏": [
        ("游戏策划与核心玩法设计", "design", [], "P0", "大"),
        ("美术风格定义", "design", ["T1"], "P0", "中"),
        ("技术方案设计", "design", ["T1"], "P0", "中"),
        ("项目工程初始化", "dev", ["T3"], "P0", "小"),
        ("核心玩法开发", "dev", ["T4", "T2"], "P0", "大"),
        ("UI系统开发", "dev", ["T5", "T2"], "P0", "中"),
        ("音效与背景音乐集成", "dev", ["T5"], "P1", "小"),
        ("存档系统开发", "dev", ["T5"], "P0", "中"),
        ("关卡/内容制作", "dev", ["T5", "T2"], "P0", "大"),
        ("排行榜系统", "dev", ["T8"], "P1", "中"),
        ("接口联调", "dev", ["T8", "T9", "T10"], "P0", "中"),
        ("功能测试", "test", ["T5", "T6", "T7"], "P1", "中"),
        ("性能与帧率优化", "test", ["T11"], "P0", "大"),
        ("多设备兼容测试", "test", ["T12"], "P0", "中"),
        ("打包与发布", "deploy", ["T13", "T14"], "P0", "中"),
        ("线上监控与热更新", "deploy", ["T15"], "P1", "中"),
    ],
}


def _build_tasks(project_type: str, project: str, custom_features: str) -> list:
    """根据项目类型和自定义功能构建任务列表"""
    template = _TASK_TEMPLATES.get(project_type, _TASK_TEMPLATES["网站"])
    tasks = []

    for i, (name, category, depends_on, priority, effort) in enumerate(template, 1):
        task_id = f"T{i}"
        tasks.append({
            "id": task_id,
            "name": name,
            "description": f"{project} - {name}",
            "category": category,
            "depends_on": depends_on,
            "priority": priority,
            "estimated_effort": effort,
            "status": "pending",
        })

    # 如果用户指定了自定义功能，追加额外开发任务
    if custom_features:
        features = [f.strip() for f in custom_features.split(",") if f.strip()]
        base_id = len(tasks) + 1
        for j, feat in enumerate(features):
            task_id = f"T{base_id + j}"
            tasks.append({
                "id": task_id,
                "name": f"自定义功能: {feat}",
                "description": f"{project} - 自定义功能开发: {feat}",
                "category": "dev",
                "depends_on": ["T4"],
                "priority": "P1",
                "estimated_effort": "中",
                "status": "pending",
            })

    return tasks


def decompose(project: str, project_type: str, features: str) -> dict:
    """执行任务拆解，返回完整结果"""
    tasks = _build_tasks(project_type, project, features)
    result = {
        "project": project,
        "project_type": project_type,
        "generated_at": now_iso(),
        "total_tasks": len(tasks),
        "tasks": tasks,
    }
    return result


def save_tasks(project: str, result: dict) -> str:
    """保存任务列表到JSON文件"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_tasks.json")
    save_json(filepath, result)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="任务拆解器 - Octopus 巧手脑")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--type", required=True, help="项目类型(小程序/APP/网站/游戏)")
    parser.add_argument("--features", default="", help="自定义功能，逗号分隔(可选)")
    args = parser.parse_args()

    result = decompose(args.project, args.type, args.features)
    filepath = save_tasks(args.project, result)

    # 打印摘要
    categories = {}
    for t in result["tasks"]:
        categories[t["category"]] = categories.get(t["category"], 0) + 1
    print_success(f"任务拆解完成: {args.project} ({args.type})")
    print_success(f"总任务数: {result['total_tasks']}")
    print_success(f"分类统计: {json.dumps(categories, ensure_ascii=False)}")
    print_success(f"已保存到: {filepath}")


if __name__ == "__main__":
    main()