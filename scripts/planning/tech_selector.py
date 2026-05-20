# -*- coding: utf-8 -*-
"""技术选型决策 - Octopus Skill 谋略脑

根据项目类型和需求，推荐技术栈组合。
输出JSON格式，包含前端/后端/数据库/部署方案及评分。
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load_json, save_json, now_iso, print_success

# 数据目录
PLANS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plans")

# 内置技术栈数据库：紧凑格式 (name, base_score, pros_str, cons_str)
_TECH_RAW = {
    "小程序": {
        "前端": [
            ("微信原生开发", 8, "性能最优,官方支持完善,API覆盖全面,审核流程成熟", "仅限微信生态,无法跨平台,学习成本较高"),
            ("uni-app (Vue)", 7, "跨平台(H5/APP/小程序),Vue生态丰富,开发效率高,社区活跃", "性能略逊原生,部分API需适配,包体积偏大"),
            ("Taro (React)", 7, "React技术栈,跨平台支持,京东团队维护,组件库丰富", "React学习曲线,编译速度一般,部分平台兼容问题"),
        ],
        "后端": [
            ("微信云开发", 8, "免服务器运维,与小程序深度集成,开箱即用,免费额度充足", "绑定微信生态,灵活性受限,复杂场景支持不足"),
            ("Node.js + Express/Koa", 7, "前后端语言统一,生态丰富,开发效率高,适合IO密集型", "CPU密集型较弱,回调/异步复杂度,类型安全需TS"),
            ("Python Flask/FastAPI", 6, "开发速度快,语法简洁,AI/数据处理友好,FastAPI性能优秀", "性能不如Go/Node,部署稍复杂,并发处理一般"),
        ],
        "数据库": [
            ("MySQL", 8, "成熟稳定,关系型数据支持好,工具链完善,社区庞大", "水平扩展复杂,JSON支持一般,全文搜索较弱"),
            ("MongoDB", 7, "文档模型灵活,Schema自由,水平扩展方便,开发速度快", "事务支持较弱,内存占用大,关联查询复杂"),
        ],
        "部署": [
            ("微信云托管", 8, "与小程序无缝集成,免运维,按量付费,内置CI/CD", "仅限微信生态,成本可能偏高,灵活性受限"),
            ("腾讯云/阿里云轻量服务器", 7, "价格实惠,完全自主控制,可部署任意服务,国内访问快", "需自行运维,需配置SSL/域名,初始配置工作量大"),
        ],
    },
    "APP": {
        "前端": [
            ("Flutter", 8, "高性能渲染,跨平台(iOS/Android/Web),UI一致性,Google维护", "Dart语言小众,包体积偏大,原生插件需开发"),
            ("React Native", 7, "React生态,热更新支持,JavaScript/TypeScript,社区庞大", "性能不如Flutter,原生桥接开销,版本升级频繁"),
            ("原生开发 (Swift + Kotlin)", 6, "性能最优,API完整,用户体验最佳,系统深度集成", "开发成本翻倍,需两套代码,维护成本高"),
        ],
        "后端": [
            ("Node.js + NestJS", 7, "TypeScript全栈,架构规范,模块化设计,生态丰富", "学习曲线较陡,性能中等,调试复杂"),
            ("Go + Gin", 8, "高性能,编译型语言,并发优秀,部署简单(单二进制)", "生态不如Node/Java,错误处理繁琐,ORM不够成熟"),
        ],
        "数据库": [
            ("PostgreSQL", 8, "功能强大,JSON支持好,扩展性强,开源免费", "配置较复杂,垂直扩展上限,Windows支持一般"),
            ("SQLite (本地缓存)", 6, "零配置,嵌入式,轻量快速,适合离线场景", "不支持并发写入,不适合服务端,数据量受限"),
        ],
        "部署": [
            ("Docker + 云服务器", 8, "环境一致性,部署标准化,扩展方便,生态成熟", "学习成本,资源开销,编排复杂"),
            ("Serverless (云函数)", 7, "免运维,按调用付费,自动扩缩,开发快", "冷启动延迟,执行时间限制,调试困难"),
        ],
    },
    "网站": {
        "前端": [
            ("Next.js (React)", 9, "SSR/SSG支持,SEO友好,Vercel部署,生态庞大", "学习曲线,服务端逻辑耦合,构建时间较长"),
            ("Nuxt.js (Vue)", 8, "SSR支持,Vue生态,上手简单,中文社区好", "生态不如React,企业级案例较少,插件质量参差"),
        ],
        "后端": [
            ("Node.js + Next.js API Routes", 7, "全栈统一,开发效率高,部署简单,Serverless友好", "重计算性能差,调试不便,不适合复杂业务"),
            ("Python + FastAPI", 7, "高性能异步,自动文档,类型提示,AI集成方便", "部署稍复杂,前端集成需额外工作,WSGI限制"),
        ],
        "数据库": [
            ("PostgreSQL", 9, "功能全面,性能优秀,扩展丰富,JSON支持", "运维门槛,Windows兼容性,内存占用"),
            ("MySQL", 8, "成熟稳定,运维简单,工具丰富,社区庞大", "功能不如PG,JSON支持弱,扩展性一般"),
        ],
        "部署": [
            ("Vercel / Netlify", 8, "零配置部署,CDN加速,自动HTTPS,免费额度", "国内访问慢,功能限制,绑定平台"),
            ("Nginx + 云服务器", 7, "完全控制,国内访问快,成本低,灵活", "需运维,配置复杂,需手动SSL"),
        ],
    },
    "游戏": {
        "前端": [
            ("Unity", 9, "生态最成熟,跨平台,3D能力强,教程资源丰富", "包体积大,C#学习成本,License费用"),
            ("Cocos Creator", 8, "2D游戏首选,TypeScript开发,包体积小,中文文档好", "3D能力一般,生态不如Unity,大型项目经验少"),
        ],
        "后端": [
            ("Node.js + Socket.IO", 7, "实时通信,开发效率高,事件驱动,适合多人游戏", "CPU密集型弱,单线程限制,安全性需注意"),
            ("Go + WebSocket", 8, "高并发,性能优秀,内存占用低,部署简单", "开发效率一般,游戏框架少,生态不如Node"),
        ],
        "数据库": [
            ("Redis", 8, "极速读写,适合排行榜/会话,数据结构丰富,内存数据库", "数据持久化弱,内存成本,不适合复杂查询"),
            ("MySQL", 7, "持久化可靠,玩家数据存储,事务支持,运维成熟", "读写性能一般,水平扩展复杂,不适合实时数据"),
        ],
        "部署": [
            ("云服务器 + Docker", 8, "灵活可控,游戏服务器常用,可弹性扩展,成本低", "需运维,DDoS防护需额外配置,网络延迟优化"),
        ],
    },
}

# 需求关键词与技术栈的适配度调整
REQ_SCORE_MAP = {
    "快速开发": {"微信原生开发": -1, "uni-app (Vue)": 2, "Taro (React)": 1, "微信云开发": 2},
    "跨平台": {"微信原生开发": -3, "uni-app (Vue)": 2, "Flutter": 3, "React Native": 2},
    "高性能": {"Flutter": 2, "Go + Gin": 2, "Go + WebSocket": 2, "原生开发 (Swift + Kotlin)": 3},
    "低成本": {"微信云开发": 2, "Serverless (云函数)": 2, "SQLite (本地缓存)": 1},
    "SEO友好": {"Next.js (React)": 3, "Nuxt.js (Vue)": 3},
    "实时通信": {"Node.js + Socket.IO": 3, "Go + WebSocket": 2, "Redis": 2},
}
BUDGET_IMPACT = {"low": -1, "medium": 0, "high": 1}


def _parse_raw(raw: list) -> list:
    """将紧凑格式转换为标准字典格式"""
    return [{"name": r[0], "base_score": r[1], "pros": r[2].split(","), "cons": r[3].split(",")} for r in raw]


def _adjust_score(base_score: int, name: str, requirements: list, budget: str) -> int:
    """根据需求和预算调整技术栈评分"""
    score = base_score
    for req in requirements:
        score += REQ_SCORE_MAP.get(req, {}).get(name, 0)
    score += BUDGET_IMPACT.get(budget, 0)
    return max(1, min(10, score))


def select_tech(project_type: str, requirements: str, budget: str) -> dict:
    """根据项目类型和需求推荐技术栈"""
    req_list = [r.strip() for r in requirements.split(",") if r.strip()] if requirements else []
    raw_stacks = _TECH_RAW.get(project_type, _TECH_RAW["网站"])

    result = {
        "project_type": project_type,
        "requirements": req_list,
        "budget": budget,
        "generated_at": now_iso(),
        "recommendations": {},
    }
    for category, raw_options in raw_stacks.items():
        options = _parse_raw(raw_options)
        scored = []
        for opt in options:
            fit_score = _adjust_score(opt["base_score"], opt["name"], req_list, budget)
            scored.append({"name": opt["name"], "pros": opt["pros"], "cons": opt["cons"], "fit_score": fit_score})
        scored.sort(key=lambda x: x["fit_score"], reverse=True)
        result["recommendations"][category] = scored
    return result


def save_result(project_type: str, result: dict) -> str:
    """保存技术选型结果到JSON文件"""
    filepath = os.path.join(PLANS_DIR, f"{project_type}_tech_stack.json")
    save_json(filepath, result)
    return filepath


def main():
    parser = argparse.ArgumentParser(description="技术选型决策 - Octopus 谋略脑")
    parser.add_argument("--type", required=True, help="项目类型(小程序/APP/网站/游戏)")
    parser.add_argument("--requirements", default="", help="需求关键词，逗号分隔(可选)")
    parser.add_argument("--budget", default="medium", choices=["low", "medium", "high"],
                        help="预算级别(默认medium)")
    args = parser.parse_args()

    result = select_tech(args.type, args.requirements, args.budget)
    filepath = save_result(args.type, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print_success(f"技术选型结果已保存: {filepath}")


if __name__ == "__main__":
    main()
