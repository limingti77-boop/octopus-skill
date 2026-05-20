# -*- coding: utf-8 -*-
"""Skill调度器 - Octopus Skill 巧手脑

根据任务列表，规划需要调用的Skill及其执行顺序。
输出JSON格式调度计划，保存到 data/execution/{project_name}_schedule.json

支持两种模式：
- plan: 生成调度计划
- execute: 执行调度计划，生成 Skill 调用指令
"""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 数据目录
EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "execution")

# Skill 目录路径
SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "skills")
REGISTRY_FILE = os.path.join(SKILLS_DIR, "registry.json")

# 任务分类到Skill的映射关系
_CATEGORY_SKILL_MAP = {
    "design": {
        "skills": ["frontend-design", "brainstorming"],
        "phase": "设计阶段",
        "can_parallel": True,
    },
    "dev": {
        "skills": ["frontend-skill", "figma"],
        "phase": "开发阶段",
        "can_parallel": True,
    },
    "test": {
        "skills": ["webapp-testing", "dogfood"],
        "phase": "测试阶段",
        "can_parallel": False,
    },
    "deploy": {
        "skills": ["gh-cli"],
        "phase": "部署阶段",
        "can_parallel": False,
    },
}

# 关键词到Skill的精确映射（用于任务名称匹配）
_KEYWORD_SKILL_MAP = {
    "原型": ["brainstorming"],
    "UI": ["frontend-design"],
    "视觉": ["frontend-design"],
    "PRD": ["docx"],
    "文档": ["docx"],
    "测试": ["webapp-testing"],
    "部署": ["gh-cli"],
    "发布": ["gh-cli"],
    "审核": ["gh-cli"],
    "监控": ["webapp-testing"],
    "SEO": ["frontend-skill"],
    "数据库": ["data-analysis"],
    "接口": ["frontend-skill"],
    "联调": ["webapp-testing"],
    "安全": ["security-best-practices"],
    "性能": ["vercel-react-best-practices"],
}


# ============================================================
# Skill 注册表和路径管理
# ============================================================

def load_registry() -> dict:
    """加载 Skill 注册表"""
    return load_json(REGISTRY_FILE, {"builtin": [], "installed": []})


def get_skill_path(skill_name: str) -> str:
    """获取 Skill 的路径（先查 builtin，再查 installed）"""
    builtin_path = os.path.join(SKILLS_DIR, "builtin", skill_name)
    installed_path = os.path.join(SKILLS_DIR, "installed", skill_name)
    if os.path.exists(builtin_path):
        return builtin_path
    elif os.path.exists(installed_path):
        return installed_path
    return None


def get_skill_info(skill_name: str) -> dict:
    """读取 Skill 的 SKILL.md，提取关键信息"""
    skill_path = get_skill_path(skill_name)
    if not skill_path:
        return None
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.exists(skill_md):
        return None
    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()
    # 提取 name 和 description
    name = skill_name
    description = ""
    for line in content.split("\n"):
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip()
    return {
        "name": name,
        "path": skill_path,
        "description": description,
        "content": content
    }


# ============================================================
# 调度计划生成
# ============================================================

def _match_skills(task: dict) -> list:
    """根据任务名称和分类匹配需要调用的Skill"""
    category = task.get("category", "dev")
    name = task.get("name", "")
    matched = set()

    # 先从分类映射获取基础Skill
    cat_skills = _CATEGORY_SKILL_MAP.get(category, {}).get("skills", [])
    matched.update(cat_skills)

    # 再从关键词精确匹配
    for keyword, skills in _KEYWORD_SKILL_MAP.items():
        if keyword in name:
            matched.update(skills)

    return sorted(matched)


def _topological_sort(tasks: list) -> list:
    """拓扑排序，确定任务执行顺序"""
    task_map = {t["id"]: t for t in tasks}
    visited = set()
    order = []

    def visit(tid):
        if tid in visited:
            return
        visited.add(tid)
        task = task_map.get(tid)
        if task:
            for dep in task.get("depends_on", []):
                visit(dep)
        order.append(tid)

    for t in tasks:
        visit(t["id"])
    return order


def schedule(project: str, tasks_data: dict) -> dict:
    """根据任务列表生成调度计划"""
    tasks = tasks_data.get("tasks", [])
    sorted_ids = _topological_sort(tasks)
    task_map = {t["id"]: t for t in tasks}

    # 按阶段分组
    phase_order = ["design", "dev", "test", "deploy"]
    phases = {}

    for tid in sorted_ids:
        task = task_map[tid]
        cat = task.get("category", "dev")
        phase_name = _CATEGORY_SKILL_MAP.get(cat, {}).get("phase", cat)
        skills = _match_skills(task)

        if phase_name not in phases:
            phases[phase_name] = {
                "name": phase_name,
                "category": cat,
                "tasks": [],
                "skills": set(),
                "can_parallel": _CATEGORY_SKILL_MAP.get(cat, {}).get("can_parallel", False),
            }
        phases[phase_name]["tasks"].append({
            "id": tid,
            "name": task["name"],
            "priority": task.get("priority", "P1"),
            "skills": skills,
        })
        phases[phase_name]["skills"].update(skills)

    # 按标准阶段顺序排列
    sorted_phases = []
    for cat in phase_order:
        phase_name = _CATEGORY_SKILL_MAP.get(cat, {}).get("phase", cat)
        if phase_name in phases:
            p = phases[phase_name]
            p["skills"] = sorted(p["skills"])
            sorted_phases.append(p)

    # 收集剩余未分类的阶段
    for name, p in phases.items():
        if p not in sorted_phases:
            p["skills"] = sorted(p["skills"])
            sorted_phases.append(p)

    result = {
        "project": project,
        "generated_at": now_iso(),
        "total_phases": len(sorted_phases),
        "total_tasks": len(tasks),
        "all_skills": sorted(set(s for p in sorted_phases for s in p["skills"])),
        "phases": sorted_phases,
    }
    return result


def save_schedule(project: str, result: dict) -> str:
    """保存调度计划到JSON文件"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_schedule.json")
    save_json(filepath, result)
    return filepath


# ============================================================
# Skill 调用执行
# ============================================================

def generate_skill_call(skill_name: str, task: dict, context: dict) -> dict:
    """生成调用 Skill 的指令
    
    返回格式：
    {
        "skill": skill_name,
        "skill_info": {...},
        "task": task,
        "call_instruction": "给 AI 的调用指令",
        "status": "ready"
    }
    """
    skill_info = get_skill_info(skill_name)
    if not skill_info:
        return {
            "skill": skill_name,
            "status": "not_found",
            "error": f"Skill '{skill_name}' 未找到"
        }
    
    # 生成调用指令
    call_instruction = f"""
[Skill 调用请求]
Skill: {skill_info['name']}
描述: {skill_info['description']}
任务: {task.get('name', '')}
上下文: {context.get('project', '')}

请加载以下 Skill 内容并执行任务：

---
{skill_info['content'][:2000]}
---
"""
    
    return {
        "skill": skill_name,
        "skill_info": {
            "name": skill_info["name"],
            "description": skill_info["description"],
            "path": skill_info["path"]
        },
        "task": task,
        "call_instruction": call_instruction,
        "status": "ready"
    }


def execute_schedule(schedule_data: dict) -> dict:
    """执行调度计划
    
    对每个阶段、每个任务，生成 Skill 调用指令
    返回执行结果
    """
    results = {
        "project": schedule_data.get("project"),
        "executed_at": now_iso(),
        "phases": [],
        "total_calls": 0,
        "status": "ready"
    }
    
    context = {"project": schedule_data.get("project")}
    
    for phase in schedule_data.get("phases", []):
        phase_result = {
            "name": phase["name"],
            "tasks": [],
            "skills": phase["skills"]
        }
        
        for task in phase.get("tasks", []):
            task_result = {
                "id": task["id"],
                "name": task["name"],
                "skill_calls": []
            }
            
            for skill_name in task.get("skills", []):
                call_result = generate_skill_call(skill_name, task, context)
                task_result["skill_calls"].append(call_result)
                results["total_calls"] += 1
            
            phase_result["tasks"].append(task_result)
        
        results["phases"].append(phase_result)
    
    return results


def save_execution_result(project: str, result: dict) -> str:
    """保存执行结果到JSON文件"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(EXEC_DIR, f"{safe_name}_execution.json")
    save_json(filepath, result)
    return filepath


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Skill调度器 - Octopus 巧手脑")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--tasks", help="任务列表JSON文件路径（plan模式需要）")
    parser.add_argument("--schedule", help="调度计划JSON文件路径（execute模式需要）")
    parser.add_argument("--action", choices=["plan", "execute"], default="plan",
                        help="操作类型: plan=生成调度计划, execute=执行调度计划")
    args = parser.parse_args()

    if args.action == "plan":
        # 生成调度计划模式
        if not args.tasks:
            print("错误: plan 模式需要 --tasks 参数")
            sys.exit(1)
        
        # 读取任务列表
        tasks_data = load_json(args.tasks)

        result = schedule(args.project, tasks_data)
        filepath = save_schedule(args.project, result)

        # 打印摘要
        print_success(f"调度计划生成完成: {args.project}")
        print_success(f"阶段数: {result['total_phases']} | 任务数: {result['total_tasks']}")
        print_success(f"涉及Skill: {', '.join(result['all_skills'])}")
        for phase in result["phases"]:
            parallel = "可并行" if phase["can_parallel"] else "串行"
            print_success(f"  [{phase['name']}] {len(phase['tasks'])}个任务 | {parallel} | Skills: {', '.join(phase['skills'])}")
        print_success(f"已保存到: {filepath}")

    elif args.action == "execute":
        # 执行调度计划模式
        if not args.schedule:
            # 尝试从默认路径加载
            safe_name = args.project.replace(" ", "_")
            default_schedule = os.path.join(EXEC_DIR, f"{safe_name}_schedule.json")
            if os.path.exists(default_schedule):
                args.schedule = default_schedule
            else:
                print("错误: execute 模式需要 --schedule 参数，或存在对应的调度计划文件")
                sys.exit(1)
        
        # 读取调度计划
        schedule_data = load_json(args.schedule)
        
        # 执行调度计划
        result = execute_schedule(schedule_data)
        filepath = save_execution_result(args.project, result)
        
        # 打印摘要
        print_success(f"调度计划执行完成: {args.project}")
        print_success(f"总调用数: {result['total_calls']}")
        for phase in result["phases"]:
            ready_calls = sum(
                1 for t in phase["tasks"] 
                for c in t["skill_calls"] if c["status"] == "ready"
            )
            not_found = sum(
                1 for t in phase["tasks"] 
                for c in t["skill_calls"] if c["status"] == "not_found"
            )
            print_success(f"  [{phase['name']}] 就绪: {ready_calls} | 未找到: {not_found}")
        print_success(f"已保存到: {filepath}")


if __name__ == "__main__":
    main()
