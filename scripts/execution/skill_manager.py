#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Octopus Skill Manager - Skill 管理工具
用于管理内置和用户安装的 Skill

用法:
    python skill_manager.py --action list
    python skill_manager.py --action search "关键词"
    python skill_manager.py --action install "skill名或URL"
    python skill_manager.py --action uninstall "skill名"
    python skill_manager.py --action info "skill名"
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any

# 基础路径
BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"
BUILTIN_DIR = SKILLS_DIR / "builtin"
INSTALLED_DIR = SKILLS_DIR / "installed"
REGISTRY_FILE = SKILLS_DIR / "registry.json"

# GitHub API 配置
GITHUB_API_BASE = "https://api.github.com"
OFFICIAL_SKILLS_REPO = "anthropics/skills"


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_color(message: str, color: str = None) -> None:
    """打印彩色文本"""
    if color and sys.platform != 'win32':
        print(f"{color}{message}{Colors.ENDC}")
    else:
        print(message)


def load_registry() -> Dict[str, Any]:
    """加载注册表"""
    if REGISTRY_FILE.exists():
        # 使用 utf-8-sig 自动处理 BOM
        with open(REGISTRY_FILE, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    return {"version": "1.0.0", "builtin": [], "installed": []}


def save_registry(registry: Dict[str, Any]) -> None:
    """保存注册表"""
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def list_skills() -> None:
    """列出所有可用的 Skill"""
    print_color("\n=== Octopus Skill 列表 ===\n", Colors.HEADER + Colors.BOLD)
    
    registry = load_registry()
    
    # 内置 Skill
    print_color("【内置 Skill】", Colors.CYAN + Colors.BOLD)
    for skill in registry.get("builtin", []):
        triggers = ", ".join(skill.get("triggers", [])[:3])
        print(f"  * {skill['name']}")
        print(f"    描述: {skill['description']}")
        print(f"    触发词: {triggers}")
        print()
    
    # 已安装 Skill
    installed = registry.get("installed", [])
    if installed:
        print_color("【已安装 Skill】", Colors.CYAN + Colors.BOLD)
        for skill in installed:
            print(f"  * {skill['name']}")
            print(f"    描述: {skill.get('description', 'N/A')}")
            print(f"    来源: {skill.get('source', 'N/A')}")
            print()
    else:
        print_color("【已安装 Skill】", Colors.CYAN + Colors.BOLD)
        print("  (暂无已安装的 Skill)\n")
    
    print_color(f"总计: {len(registry.get('builtin', []))} 个内置, {len(installed)} 个已安装", Colors.YELLOW)


def search_skills(keyword: str) -> None:
    """从 GitHub 搜索 Skill"""
    print_color(f"\n=== 搜索 Skill: {keyword} ===\n", Colors.HEADER + Colors.BOLD)
    
    # 搜索 GitHub 仓库
    search_url = f"{GITHUB_API_BASE}/search/repositories?q={urllib.parse.quote(keyword)}+skill+in:readme,description&sort=stars&order=desc"
    
    try:
        req = urllib.request.Request(search_url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Octopus-Skill-Manager')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        items = data.get('items', [])
        
        if not items:
            print_color("未找到匹配的 Skill", Colors.YELLOW)
            return
        
        print_color(f"找到 {data.get('total_count', 0)} 个结果，显示前 10 个:\n", Colors.GREEN)
        
        for i, item in enumerate(items[:10], 1):
            print_color(f"{i}. {item['full_name']}", Colors.BLUE + Colors.BOLD)
            print(f"   描述: {item.get('description', 'N/A')}")
            print(f"   Stars: {item.get('stargazers_count', 0)} | 语言: {item.get('language', 'N/A')}")
            print(f"   URL: {item['html_url']}")
            print()
            
    except urllib.error.URLError as e:
        print_color(f"网络错误: {e}", Colors.RED)
    except Exception as e:
        print_color(f"搜索失败: {e}", Colors.RED)


def install_skill(skill_ref: str) -> None:
    """安装 Skill"""
    print_color(f"\n=== 安装 Skill: {skill_ref} ===\n", Colors.HEADER + Colors.BOLD)
    
    # 判断是 URL 还是名称
    if skill_ref.startswith('http'):
        # 从 URL 安装
        install_from_url(skill_ref)
    else:
        # 从名称安装（假设是 GitHub 仓库）
        install_from_github(skill_ref)


def install_from_url(url: str) -> None:
    """从 URL 安装 Skill"""
    # 提取仓库名
    parts = url.rstrip('/').split('/')
    if 'github.com' in url and len(parts) >= 5:
        repo_name = parts[-1] or parts[-2]
    else:
        repo_name = url.split('/')[-1] or 'unknown-skill'
    
    target_dir = INSTALLED_DIR / repo_name
    
    if target_dir.exists():
        print_color(f"Skill '{repo_name}' 已存在", Colors.YELLOW)
        return
    
    # 使用 git clone
    try:
        print_color(f"正在克隆 {url}...", Colors.CYAN)
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # 更新注册表
            registry = load_registry()
            registry.setdefault("installed", []).append({
                "name": repo_name,
                "description": f"从 {url} 安装",
                "source": url,
                "path": f"skills/installed/{repo_name}",
                "installed_at": "2026-05-18"
            })
            save_registry(registry)
            print_color(f"成功安装 Skill: {repo_name}", Colors.GREEN)
        else:
            print_color(f"克隆失败: {result.stderr}", Colors.RED)
            # 清理失败的目录
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)
                
    except subprocess.TimeoutExpired:
        print_color("安装超时", Colors.RED)
    except FileNotFoundError:
        print_color("未找到 git 命令，请确保已安装 Git", Colors.RED)
    except Exception as e:
        print_color(f"安装失败: {e}", Colors.RED)


def install_from_github(skill_name: str) -> None:
    """从 GitHub 安装 Skill"""
    # 尝试几种可能的仓库格式
    possible_repos = [
        f"anthropics/{skill_name}",
        f"anthropics/skills/{skill_name}",
        skill_name
    ]
    
    for repo in possible_repos:
        url = f"https://github.com/{repo}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Octopus-Skill-Manager')
            urllib.request.urlopen(req, timeout=5)
            install_from_url(url)
            return
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
    
    print_color(f"未找到 Skill: {skill_name}", Colors.RED)
    print_color("提示: 请使用完整的 GitHub URL 或 仓库名 (如: user/repo)", Colors.YELLOW)


def uninstall_skill(skill_name: str) -> None:
    """卸载已安装的 Skill"""
    print_color(f"\n=== 卸载 Skill: {skill_name} ===\n", Colors.HEADER + Colors.BOLD)
    
    registry = load_registry()
    installed = registry.get("installed", [])
    
    # 查找要卸载的 Skill
    skill_to_remove = None
    for i, skill in enumerate(installed):
        if skill['name'] == skill_name:
            skill_to_remove = (i, skill)
            break
    
    if not skill_to_remove:
        print_color(f"未找到已安装的 Skill: {skill_name}", Colors.RED)
        print_color("注意: 内置 Skill 无法卸载", Colors.YELLOW)
        return
    
    idx, skill = skill_to_remove
    skill_dir = INSTALLED_DIR / skill_name
    
    # 删除目录
    if skill_dir.exists():
        import shutil
        shutil.rmtree(skill_dir)
    
    # 更新注册表
    installed.pop(idx)
    registry["installed"] = installed
    save_registry(registry)
    
    print_color(f"成功卸载 Skill: {skill_name}", Colors.GREEN)


def show_skill_info(skill_name: str) -> None:
    """显示 Skill 详情"""
    print_color(f"\n=== Skill 详情: {skill_name} ===\n", Colors.HEADER + Colors.BOLD)
    
    # 先查找内置 Skill
    skill_md = BUILTIN_DIR / skill_name / "SKILL.md"
    
    # 如果不是内置的，查找已安装的
    if not skill_md.exists():
        skill_md = INSTALLED_DIR / skill_name / "SKILL.md"
    
    if skill_md.exists():
        try:
            with open(skill_md, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            print(content)
        except Exception as e:
            print_color(f"读取失败: {e}", Colors.RED)
    else:
        print_color(f"未找到 Skill: {skill_name}", Colors.RED)
        
        # 显示可用的 Skill
        registry = load_registry()
        all_skills = [s['name'] for s in registry.get('builtin', [])] + \
                     [s['name'] for s in registry.get('installed', [])]
        if all_skills:
            print_color(f"\n可用的 Skill: {', '.join(all_skills)}", Colors.YELLOW)


def main():
    parser = argparse.ArgumentParser(
        description='Octopus Skill Manager - Skill 管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python skill_manager.py --action list
  python skill_manager.py --action search "web testing"
  python skill_manager.py --action install "https://github.com/user/my-skill"
  python skill_manager.py --action uninstall "my-skill"
  python skill_manager.py --action info "frontend-design"
        '''
    )
    
    parser.add_argument(
        '--action',
        required=True,
        choices=['list', 'search', 'install', 'uninstall', 'info'],
        help='要执行的操作'
    )
    
    parser.add_argument(
        '--target',
        required=False,
        help='操作目标（搜索关键词、Skill 名称或 URL）'
    )
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_skills()
    elif args.action == 'search':
        if not args.target:
            print_color("错误: search 操作需要提供搜索关键词", Colors.RED)
            sys.exit(1)
        search_skills(args.target)
    elif args.action == 'install':
        if not args.target:
            print_color("错误: install 操作需要提供 Skill 名称或 URL", Colors.RED)
            sys.exit(1)
        install_skill(args.target)
    elif args.action == 'uninstall':
        if not args.target:
            print_color("错误: uninstall 操作需要提供 Skill 名称", Colors.RED)
            sys.exit(1)
        uninstall_skill(args.target)
    elif args.action == 'info':
        if not args.target:
            print_color("错误: info 操作需要提供 Skill 名称", Colors.RED)
            sys.exit(1)
        show_skill_info(args.target)


if __name__ == '__main__':
    main()
