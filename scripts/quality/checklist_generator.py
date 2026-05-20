# -*- coding: utf-8 -*-
"""
检查清单生成器 - Octopus Skill "慧眼脑"质量把关
根据项目类型和阶段生成质量检查清单
"""

import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import save_json, now_iso, print_success

# 数据目录
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "quality"
)

# 通用检查项模板（按类别） - 紧凑格式: (name, severity)
_COMMON_RAW = {
    "功能": [("核心功能是否按需求文档实现", "必须"), ("功能边界条件处理是否完善", "必须"),
              ("数据输入校验是否完整", "必须"), ("错误提示信息是否友好且明确", "建议"), ("功能模块间耦合度是否合理", "建议")],
    "性能": [("页面首屏加载时间是否达标(<3秒)", "必须"), ("接口响应时间是否在可接受范围内", "必须"),
              ("大数据量场景下是否进行分页/懒加载", "建议"), ("是否存在内存泄漏风险", "必须"), ("动画/交互是否流畅(60fps)", "建议")],
    "安全": [("用户敏感数据是否加密存储", "必须"), ("接口是否有身份认证和权限校验", "必须"),
              ("是否存在XSS/SQL注入等安全漏洞", "必须"), ("日志中是否避免打印敏感信息", "建议"), ("第三方依赖是否存在已知漏洞", "必须")],
    "体验": [("操作流程是否符合用户习惯", "建议"), ("加载状态/空状态是否有合理展示", "必须"),
              ("文案是否清晰无歧义", "建议"), ("关键操作是否有二次确认", "必须"), ("反馈机制是否及时(toast/动画等)", "建议")],
    "兼容": [("主流浏览器/系统版本是否兼容", "必须"), ("不同屏幕尺寸适配是否正常", "必须"),
              ("网络异常/弱网场景是否处理", "必须"), ("旧版本数据是否兼容迁移", "建议")],
}

# 按阶段补充的检查项 - 紧凑格式
_STAGE_RAW = {
    "design": {
        "功能": [("需求文档是否完整且无歧义", "必须"), ("原型设计是否覆盖所有核心场景", "必须"), ("交互流程是否经过评审", "建议")],
        "体验": [("设计规范是否统一(色彩/字体/间距)", "必须"), ("是否考虑了无障碍访问", "建议")],
    },
    "dev": {
        "功能": [("代码是否遵循项目编码规范", "必须"), ("单元测试覆盖率是否达标", "建议"), ("API接口文档是否完整", "必须")],
        "性能": [("是否避免不必要的重复渲染/请求", "建议")],
    },
    "test": {
        "功能": [("核心流程回归测试是否通过", "必须"), ("边界值测试是否覆盖", "必须"), ("异常场景测试是否充分", "必须")],
        "性能": [("压力测试是否通过", "建议")],
    },
    "deploy": {
        "安全": [("生产环境配置是否正确(关闭debug等)", "必须"), ("HTTPS证书是否有效", "必须")],
        "兼容": [("灰度发布方案是否就绪", "建议"), ("回滚方案是否可行", "必须")],
    },
}

# 按项目类型补充的检查项 - 紧凑格式
_TYPE_RAW = {
    "小程序": {
        "兼容": [("微信/支付宝等平台审核规则是否满足", "必须"), ("小程序包大小是否在限制范围内", "必须"), ("是否适配暗黑模式", "建议")],
        "体验": [("分享/转发功能是否正常", "建议"), ("授权流程是否符合平台规范", "必须")],
    },
    "web": {
        "兼容": [("SEO基础配置是否完善", "建议"), ("PWA配置是否正确(如适用)", "建议")],
        "性能": [("静态资源是否使用CDN加速", "建议")],
    },
    "app": {
        "兼容": [("iOS/Android双平台适配是否完成", "必须"), ("应用商店审核规则是否满足", "必须")],
        "安全": [("本地存储数据是否加密", "必须")],
    },
}

# 按功能关键词补充的检查项 - 紧凑格式: (name, category, severity)
_FEATURE_RAW = {
    "记账": [("金额计算精度是否正确(避免浮点误差)", "功能", "必须"), ("重复记账是否有检测提示", "体验", "建议")],
    "统计": [("统计数据是否支持时间范围筛选", "功能", "建议"), ("图表渲染大数据量时是否流畅", "性能", "建议")],
    "支付": [("支付流程是否有防重复提交机制", "安全", "必须"), ("支付回调是否可靠处理", "功能", "必须")],
    "登录": [("密码强度是否有校验", "安全", "必须"), ("登录失败是否有频率限制", "安全", "必须")],
    "上传": [("文件类型/大小是否有限制", "安全", "必须"), ("大文件是否支持断点续传", "性能", "建议")],
}


def _parse_common(raw):
    return {cat: [{"name": n, "severity": s} for n, s in items] for cat, items in raw.items()}

def _parse_stage_extra(raw):
    return {stage: {cat: [{"name": n, "severity": s} for n, s in items] for cat, items in cats.items()} for stage, cats in raw.items()}

def _parse_type_extra(raw):
    return {pt: {cat: [{"name": n, "severity": s} for n, s in items] for cat, items in cats.items()} for pt, cats in raw.items()}

def _parse_feature_extra(raw):
    return {feat: [{"name": n, "category": c, "severity": s} for n, c, s in items] for feat, items in raw.items()}


COMMON_TEMPLATES = _parse_common(_COMMON_RAW)
STAGE_EXTRA = _parse_stage_extra(_STAGE_RAW)
TYPE_EXTRA = _parse_type_extra(_TYPE_RAW)
FEATURE_EXTRA = _parse_feature_extra(_FEATURE_RAW)



def build_checklist(project_type: str, stage: str, features: list) -> list:
    """根据项目类型、阶段和功能特性构建检查清单"""
    items = []
    item_id = 0

    # 1. 通用模板
    for category, checks in COMMON_TEMPLATES.items():
        for check in checks:
            item_id += 1
            items.append({
                "id": f"CHK-{item_id:03d}",
                "name": check["name"],
                "category": category,
                "severity": check["severity"],
                "checked": False,
            })

    # 2. 阶段补充
    if stage in STAGE_EXTRA:
        for category, checks in STAGE_EXTRA[stage].items():
            for check in checks:
                item_id += 1
                items.append({
                    "id": f"CHK-{item_id:03d}",
                    "name": check["name"],
                    "category": category,
                    "severity": check["severity"],
                    "checked": False,
                })

    # 3. 项目类型补充
    if project_type in TYPE_EXTRA:
        for category, checks in TYPE_EXTRA[project_type].items():
            for check in checks:
                item_id += 1
                items.append({
                    "id": f"CHK-{item_id:03d}",
                    "name": check["name"],
                    "category": category,
                    "severity": check["severity"],
                    "checked": False,
                })

    # 4. 功能特性补充
    for feature in features:
        if feature in FEATURE_EXTRA:
            for check in FEATURE_EXTRA[feature]:
                item_id += 1
                items.append({
                    "id": f"CHK-{item_id:03d}",
                    "name": check["name"],
                    "category": check["category"],
                    "severity": check["severity"],
                    "checked": False,
                })

    return items


def save_checklist(items: list, project_type: str, stage: str) -> str:
    """保存检查清单到JSON文件"""
    filename = f"{project_type}_{stage}_checklist.json"
    filepath = os.path.join(DATA_DIR, filename)

    data = {
        "project_type": project_type,
        "stage": stage,
        "generated_at": now_iso(),
        "total_items": len(items),
        "must_items": sum(1 for i in items if i["severity"] == "必须"),
        "suggest_items": sum(1 for i in items if i["severity"] == "建议"),
        "items": items,
    }

    save_json(filepath, data)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="检查清单生成器 - 根据项目类型和阶段生成质量检查清单")
    parser.add_argument("--type", required=True, help="项目类型（如：小程序/web/app）")
    parser.add_argument("--stage", required=True, choices=["design", "dev", "test", "deploy", "overall"],
                        help="项目阶段")
    parser.add_argument("--features", default="", help="功能特性，逗号分隔（如：记账,统计）")
    args = parser.parse_args()

    features = [f.strip() for f in args.features.split(",") if f.strip()]
    items = build_checklist(args.type, args.stage, features)
    filepath = save_checklist(items, args.type, args.stage)

    must_count = sum(1 for i in items if i["severity"] == "必须")
    suggest_count = sum(1 for i in items if i["severity"] == "建议")

    print_success(f"检查清单已生成: {filepath}")
    print_success(f"总计: {len(items)} 项（必须: {must_count}, 建议: {suggest_count}）")
    for cat in ["功能", "性能", "安全", "体验", "兼容"]:
        cat_items = [i for i in items if i["category"] == cat]
        if cat_items:
            print_success(f"  {cat}: {len(cat_items)} 项")


if __name__ == "__main__":
    main()
