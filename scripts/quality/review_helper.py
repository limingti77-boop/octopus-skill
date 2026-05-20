# -*- coding: utf-8 -*-
"""
审查辅助 - Octopus Skill "慧眼脑"质量把关
提供代码/设计/文档审查的检查框架
"""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import now_iso, print_success, print_warning, print_error

# 数据目录
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "quality"
)

# 审查维度定义
# 审查维度定义 - 紧凑格式
REVIEW_DIMENSIONS = {
    "安全": {
        "code": ["输入数据是否经过校验和清洗", "是否存在SQL注入/XSS/CSRF等安全漏洞",
                 "敏感信息(密码、token)是否加密存储和传输", "API接口是否有身份认证和权限校验",
                 "是否使用安全的第三方库版本", "日志中是否避免输出敏感信息"],
        "design": ["用户数据隐私保护方案是否完善", "权限模型设计是否合理(RBAC等)", "敏感操作是否有审计日志"],
        "doc": ["文档中是否避免泄露敏感信息(密钥、内部地址等)", "安全相关配置说明是否完整"],
    },
    "性能": {
        "code": ["是否存在不必要的循环嵌套或重复计算", "数据库查询是否优化(索引、避免N+1)",
                 "是否合理使用缓存机制", "大文件/大数据处理是否使用流式或分页", "前端资源是否压缩和按需加载"],
        "design": ["系统架构是否支持水平扩展", "关键路径的响应时间目标是否明确", "是否考虑了高并发场景的处理方案"],
        "doc": ["性能指标和基准是否明确定义", "性能优化方案是否有文档记录"],
    },
    "可读性": {
        "code": ["变量/函数命名是否清晰表意", "代码逻辑是否简洁易懂，避免过度嵌套",
                 "是否有必要的注释(复杂逻辑、业务规则)", "单个函数是否过长(建议<50行)", "代码风格是否统一(缩进、空行、命名规范)"],
        "design": ["设计文档结构是否清晰、层次分明", "图表和示例是否有助于理解", "术语使用是否一致"],
        "doc": ["文档语言是否简洁明确", "段落结构是否合理", "是否有目录和索引便于查阅"],
    },
    "可维护性": {
        "code": ["代码模块化程度是否合理", "是否存在硬编码(魔法数字、固定字符串)",
                 "错误处理是否完善且统一", "是否遵循DRY原则(避免重复代码)", "配置与代码是否分离"],
        "design": ["模块间耦合度是否低、内聚性是否高", "设计是否便于后续功能扩展", "技术选型是否合理且团队熟悉"],
        "doc": ["文档是否与代码/设计保持同步更新", "是否有变更记录和版本管理"],
    },
    "兼容性": {
        "code": ["是否兼容目标平台/浏览器版本", "API接口是否考虑了版本兼容", "数据格式变更是否有迁移方案"],
        "design": ["不同终端(PC/移动/平板)的适配方案是否完善", "是否考虑了向后兼容"],
        "doc": ["文档是否标注了适用的平台/版本范围"],
    },
    "无障碍": {
        "code": ["图片是否有alt文本", "颜色对比度是否满足WCAG标准", "是否支持键盘导航", "表单是否有正确的label关联"],
        "design": ["交互设计是否考虑了色觉障碍用户", "字体大小是否可调", "动画是否可关闭"],
        "doc": ["文档是否支持屏幕阅读器", "是否有无障碍使用说明"],
    },
}

# 评分标准
SCORE_CRITERIA = {
    5: "优秀 - 完全符合要求，可作为标杆",
    4: "良好 - 基本符合要求，仅有少量可优化点",
    3: "合格 - 满足最低要求，存在一些改进空间",
    2: "待改进 - 存在明显问题，需要修改",
    1: "不合格 - 存在严重问题，必须立即修复",
}


def generate_review_report(project_type: str, category: str, focus: list) -> str:
    """生成审查报告模板"""
    lines = []
    cat_name = {"code": "代码审查", "design": "设计审查", "doc": "文档审查"}.get(category, category)

    lines.append(f"# {project_type} - {cat_name}报告")
    lines.append("")
    lines.append(f"> 审查类型：{cat_name}")
    lines.append(f"> 审查日期：{now_iso()[:10]}")
    lines.append(f"> 审查人：__________")
    lines.append(f"> 审查范围：{', '.join(focus) if focus else '全部维度'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 评分标准说明
    lines.append("## 评分标准")
    lines.append("")
    lines.append("| 分数 | 等级 | 说明 |")
    lines.append("| ---- | ---- | ---- |")
    for score, desc in SCORE_CRITERIA.items():
        level = {5: "优秀", 4: "良好", 3: "合格", 2: "待改进", 1: "不合格"}[score]
        lines.append(f"| {score} | {level} | {desc} |")
    lines.append("")

    # 总体评分
    lines.append("## 总体评分")
    lines.append("")
    lines.append("| 维度 | 评分(1-5) | 备注 |")
    lines.append("| ---- | --------- | ---- |")
    for dim in focus:
        lines.append(f"| {dim} |  |  |")
    lines.append(f"| **综合评分** |  |  |")
    lines.append("")

    # 各维度详细审查
    lines.append("---")
    lines.append("")
    lines.append("## 详细审查")
    lines.append("")

    for dim in focus:
        dim_data = REVIEW_DIMENSIONS.get(dim, {})
        check_points = dim_data.get(category, [])

        lines.append(f"### {dim}")
        lines.append("")

        if not check_points:
            lines.append(f"> 该维度暂无{cat_name}相关的检查要点")
            lines.append("")
            continue

        lines.append("**检查要点：**")
        lines.append("")
        for i, point in enumerate(check_points, 1):
            lines.append(f"{i}. [ ] {point}")
        lines.append("")

        lines.append("**发现问题：**")
        lines.append("")
        lines.append("| 序号 | 问题描述 | 严重程度 | 改进建议 |")
        lines.append("| ---- | -------- | -------- | -------- |")
        lines.append("| 1 |  | 高/中/低 |  |")
        lines.append("")

        lines.append("**改进建议：**")
        lines.append("")
        lines.append("<!-- 在此填写改进建议 -->")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 总结
    lines.append("## 审查总结")
    lines.append("")
    lines.append("**主要优点：**")
    lines.append("")
    lines.append("1. ")
    lines.append("")
    lines.append("**主要问题：**")
    lines.append("")
    lines.append("1. ")
    lines.append("")
    lines.append("**改进优先级建议：**")
    lines.append("")
    lines.append("| 优先级 | 改进项 | 负责人 | 截止日期 |")
    lines.append("| ------ | ------ | ------ | -------- |")
    lines.append("| P0 |  |  |  |")
    lines.append("| P1 |  |  |  |")
    lines.append("| P2 |  |  |  |")
    lines.append("")

    return "\n".join(lines)


def save_review_report(content: str, project_type: str, category: str) -> str:
    """保存审查报告"""
    filename = f"{project_type}_{category}_review.md"
    filepath = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print_success(f"审查报告已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="审查辅助 - 提供代码/设计/文档审查的检查框架")
    parser.add_argument("--type", required=True, help="项目类型（如：小程序/web/app）")
    parser.add_argument("--category", required=True, choices=["code", "design", "doc"],
                        help="审查类别：code=代码审查, design=设计审查, doc=文档审查")
    parser.add_argument("--focus", default="", help="重点关注维度，逗号分隔（如：安全,性能）")
    args = parser.parse_args()

    # 解析关注维度，默认全部
    all_dims = list(REVIEW_DIMENSIONS.keys())
    if args.focus:
        focus = [f.strip() for f in args.focus.split(",") if f.strip()]
        # 校验维度是否有效
        invalid = [f for f in focus if f not in all_dims]
        if invalid:
            print_warning(f"以下维度不存在，已忽略: {', '.join(invalid)}")
        focus = [f for f in focus if f in all_dims]
    else:
        focus = all_dims

    if not focus:
        print_error("无有效的审查维度")
        return

    content = generate_review_report(args.type, args.category, focus)
    filepath = save_review_report(content, args.type, args.category)

    cat_name = {"code": "代码审查", "design": "设计审查", "doc": "文档审查"}[args.category]
    print_success(f"{cat_name}报告已生成: {filepath}")
    print_success(f"审查维度: {len(focus)} 个（{', '.join(focus)}）")


if __name__ == "__main__":
    main()
