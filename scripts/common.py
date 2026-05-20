# common.py - Octopus Skill 共享工具模块

import json
import os
import sys
from datetime import datetime

# 数据根目录
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_data_path(filename: str) -> str:
    """获取数据文件的完整路径"""
    return os.path.join(DATA_DIR, filename)


def load_json(filepath: str, default=None) -> dict:
    """安全加载JSON文件，带异常处理
    - 文件不存在返回 default（默认空字典）
    - JSON损坏返回 default 并打印警告
    - 其他异常返回 default 并打印错误
    """
    if default is None:
        default = {}
    try:
        if not os.path.exists(filepath):
            return default
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"[警告] JSON文件损坏: {filepath}，使用默认值")
        return default
    except Exception as e:
        print(f"[错误] 读取文件失败: {filepath} - {e}")
        return default


def save_json(filepath: str, data: dict) -> bool:
    """安全保存JSON文件，带异常处理
    - 自动创建目录
    - 成功返回True
    - 失败返回False并打印错误
    """
    try:
        dir_path = os.path.dirname(filepath)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[错误] 保存文件失败: {filepath} - {e}")
        return False


def now_iso() -> str:
    """返回当前时间的ISO格式字符串"""
    return datetime.now().isoformat()


def print_success(msg: str):
    print(f"[成功] {msg}")


def print_warning(msg: str):
    print(f"[警告] {msg}")


def print_error(msg: str):
    print(f"[错误] {msg}")


def print_info(msg: str):
    print(f"[信息] {msg}")
