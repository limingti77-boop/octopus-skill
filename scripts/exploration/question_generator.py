# -*- coding: utf-8 -*-
"""智能问题生成工具 - Octopus Skill 探知脑

根据项目类型和当前已知信息，生成需要追问的问题清单。
内置不同项目类型的问题模板，支持 initial(初始) 和 deep(深入) 两个阶段。
"""

import argparse
import json
import os
import sys

# 添加父目录到路径，以便导入 common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 各项目类型的初始阶段问题模板
INITIAL_QUESTIONS = {
    "游戏": [
        {"question": "这个游戏的核心玩法是什么？（如卡牌、动作、策略等）", "purpose": "确定游戏类型和核心机制", "priority": "high"},
        {"question": "目标玩家群体是谁？（如儿童、休闲玩家、硬核玩家）", "purpose": "明确受众，影响美术风格和难度设计", "priority": "high"},
        {"question": "是单机还是多人游戏？需要联网功能吗？", "purpose": "确定技术架构复杂度", "priority": "high"},
        {"question": "有参考的同类游戏吗？", "purpose": "了解期望的体验标杆", "priority": "medium"},
        {"question": "你希望用什么技术栈开发？（如 Unity、Godot、Cocos）", "purpose": "评估技术可行性", "priority": "medium"},
    ],
    "小程序": [
        {"question": "这个小程序主要解决什么问题？", "purpose": "明确核心价值主张", "priority": "high"},
        {"question": "目标用户是谁？（如学生、上班族、老年人）", "purpose": "影响界面设计和交互复杂度", "priority": "high"},
        {"question": "需要用户登录和个人数据存储吗？", "purpose": "确定是否需要后端服务", "priority": "high"},
        {"question": "有没有参考的同类产品？", "purpose": "了解期望的功能范围和体验", "priority": "medium"},
        {"question": "你打算怎么推广这个小程序？", "purpose": "影响功能设计（如分享机制）", "priority": "low"},
    ],
    "APP": [
        {"question": "这个APP的核心功能是什么？", "purpose": "确定最小可行产品范围", "priority": "high"},
        {"question": "目标平台是 Android、iOS 还是两者都要？", "purpose": "影响技术选型和开发成本", "priority": "high"},
        {"question": "需要后端服务吗？（如用户系统、数据同步、推送通知）", "purpose": "评估整体架构复杂度", "priority": "high"},
        {"question": "有参考的同类APP吗？", "purpose": "了解期望的功能和体验标准", "priority": "medium"},
        {"question": "对性能有什么特殊要求吗？", "purpose": "影响技术方案选择", "priority": "medium"},
    ],
    "网站": [
        {"question": "这个网站的主要用途是什么？（如展示、电商、社区、工具）", "purpose": "确定网站类型和功能范围", "priority": "high"},
        {"question": "目标用户是谁？", "purpose": "影响设计和内容策略", "priority": "high"},
        {"question": "需要后台管理系统吗？", "purpose": "确定是否需要管理端开发", "priority": "high"},
        {"question": "有参考的同类网站吗？", "purpose": "了解期望的设计风格和功能", "priority": "medium"},
        {"question": "对SEO有什么要求吗？", "purpose": "影响技术方案（如SSR/SSG）", "priority": "low"},
    ],
    "视频": [
        {"question": "视频的主题和风格是什么？", "purpose": "确定创意方向", "priority": "high"},
        {"question": "目标时长是多少？", "purpose": "影响内容深度和制作周期", "priority": "high"},
        {"question": "目标受众是谁？", "purpose": "影响叙事方式和视觉风格", "priority": "high"},
        {"question": "有参考的视频作品吗？", "purpose": "了解期望的质量和风格", "priority": "medium"},
        {"question": "需要配音、字幕或特效吗？", "purpose": "评估制作资源需求", "priority": "medium"},
    ],
    "文档": [
        {"question": "文档的用途和受众是什么？", "purpose": "确定文档类型和深度", "priority": "high"},
        {"question": "大致需要多少页/字？", "purpose": "评估工作量", "priority": "high"},
        {"question": "有模板或参考文档吗？", "purpose": "了解期望的格式和风格", "priority": "medium"},
        {"question": "需要包含图表或数据可视化吗？", "purpose": "评估制作复杂度", "priority": "medium"},
        {"question": "交付格式是什么？（如PDF、Word、PPT）", "purpose": "确定输出形式", "priority": "low"},
    ],
    "其他": [
        {"question": "能详细描述一下你想做什么吗？", "purpose": "理解用户的核心需求", "priority": "high"},
        {"question": "这个项目的目标是什么？", "purpose": "明确项目目的", "priority": "high"},
        {"question": "有参考的类似项目吗？", "purpose": "了解期望的产出", "priority": "medium"},
    ],
}

# 深入阶段问题模板
DEEP_QUESTIONS = {
    "游戏": [
        {"question": "游戏中有哪些核心系统？（如背包、任务、成就、商店）", "purpose": "细化功能模块", "priority": "high"},
        {"question": "美术风格偏好是什么？（像素、卡通、写实、低多边形）", "purpose": "确定美术方向和资源需求", "priority": "high"},
        {"question": "对音效和背景音乐有要求吗？", "purpose": "评估音频资源需求", "priority": "medium"},
        {"question": "有没有考虑过商业化模式？（广告、内购、买断）", "purpose": "影响功能设计", "priority": "medium"},
    ],
    "小程序": [
        {"question": "具体需要哪些功能模块？请尽量列出来", "purpose": "细化功能范围", "priority": "high"},
        {"question": "数据需要云端存储还是本地即可？", "purpose": "确定技术架构", "priority": "high"},
        {"question": "对UI风格有什么偏好？（简约、活泼、商务等）", "purpose": "确定设计方向", "priority": "medium"},
        {"question": "需要接入微信支付或其他支付方式吗？", "purpose": "评估合规和开发成本", "priority": "medium"},
    ],
    "APP": [
        {"question": "需要哪些核心页面和功能？请尽量列出来", "purpose": "细化功能范围", "priority": "high"},
        {"question": "对UI/UX设计有什么要求或偏好？", "purpose": "确定设计方向", "priority": "high"},
        {"question": "需要第三方登录吗？（如微信、QQ、手机号）", "purpose": "确定认证方案", "priority": "medium"},
        {"question": "有数据安全和隐私方面的特殊要求吗？", "purpose": "评估合规需求", "priority": "medium"},
    ],
    "网站": [
        {"question": "网站需要哪些核心页面？", "purpose": "细化页面结构", "priority": "high"},
        {"question": "需要哪些交互功能？（如搜索、评论、在线客服）", "purpose": "细化功能需求", "priority": "high"},
        {"question": "对设计风格有偏好吗？（如极简、商务、创意）", "purpose": "确定视觉方向", "priority": "medium"},
        {"question": "预计的日访问量大概是多少？", "purpose": "评估服务器和架构需求", "priority": "medium"},
    ],
    "视频": [
        {"question": "视频的叙事结构是怎样的？（如开头-发展-高潮-结尾）", "purpose": "规划内容结构", "priority": "high"},
        {"question": "需要用到哪些素材？（图片、视频片段、图标、音乐）", "purpose": "评估素材准备量", "priority": "high"},
        {"question": "有没有品牌色或视觉规范需要遵循？", "purpose": "确保品牌一致性", "priority": "medium"},
        {"question": "视频的发布平台是什么？（如B站、抖音、YouTube）", "purpose": "影响尺寸和格式要求", "priority": "medium"},
    ],
    "文档": [
        {"question": "文档的章节结构大致是怎样的？", "purpose": "规划内容框架", "priority": "high"},
        {"question": "需要包含哪些具体内容或数据？", "purpose": "细化内容需求", "priority": "high"},
        {"question": "有没有品牌规范需要遵循？（字体、配色、Logo）", "purpose": "确保视觉一致性", "priority": "medium"},
        {"question": "文档需要定期更新吗？", "purpose": "评估维护需求", "priority": "low"},
    ],
    "其他": [
        {"question": "能描述一下你期望的最终效果吗？", "purpose": "明确产出标准", "priority": "high"},
        {"question": "有什么技术或资源上的限制吗？", "purpose": "评估可行性", "priority": "high"},
        {"question": "项目的截止时间是什么时候？", "purpose": "规划开发节奏", "priority": "medium"},
    ],
}


def generate_questions(project_type: str, known: str = "", stage: str = "initial") -> list:
    """根据项目类型和已知信息生成问题清单

    Args:
        project_type: 项目类型（游戏/小程序/APP/网站/视频/文档/其他）
        known: 已知信息，逗号分隔的关键词
        stage: 阶段，initial(初始核心问题) 或 deep(深入问题)

    Returns:
        按优先级排序的问题列表
    """
    # 获取对应类型的问题模板
    templates = INITIAL_QUESTIONS if stage == "initial" else DEEP_QUESTIONS
    questions = templates.get(project_type, templates["其他"]).copy()

    # 根据已知信息过滤已回答的问题
    known_items = [k.strip() for k in known.split(",") if k.strip()] if known else []
    filtered = []
    for q in questions:
        skip = False
        for item in known_items:
            if item in q["question"] or item in q["purpose"]:
                skip = True
                break
        if not skip:
            filtered.append(q)

    # 按优先级排序：high > medium > low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    filtered.sort(key=lambda x: priority_order.get(x["priority"], 3))

    # 限制问题数量
    result = filtered[:5]
    return result


def main():
    parser = argparse.ArgumentParser(description="智能问题生成工具 - Octopus 探知脑")
    parser.add_argument("--type", required=True, help="项目类型（游戏/小程序/APP/网站/视频/文档/其他）")
    parser.add_argument("--known", default="", help="已知信息，逗号分隔，如 '记账,个人使用'")
    parser.add_argument("--stage", default="initial", choices=["initial", "deep"],
                        help="问题阶段：initial(初始核心问题) / deep(深入问题)")
    args = parser.parse_args()

    questions = generate_questions(args.type, args.known, args.stage)

    output = {
        "project_type": args.type,
        "stage": args.stage,
        "known_info": [k.strip() for k in args.known.split(",") if k.strip()] if args.known else [],
        "question_count": len(questions),
        "questions": questions,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
