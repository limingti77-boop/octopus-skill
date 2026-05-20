# -*- coding: utf-8 -*-
"""风险评估 - Octopus Skill 谋略脑

根据项目信息识别潜在风险并给出应对建议。
输出Markdown格式的风险评估报告，保存到 data/plans/{project_name}_risks.md
"""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import now_iso, print_success

# 数据目录
PLANS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plans")

# 风险模板：紧凑格式 (name, category, severity, probability, mitigation)
_RISK_RAW = {
    "小程序": [
        ("微信审核不通过", "法律", "高", "中", "提前研读微信小程序审核规范，避免敏感内容和违规功能；预留1-2周审核缓冲期；准备备用方案。"),
        ("平台政策变更", "市场", "高", "低", "关注微信官方公告和开发者社区；核心功能不依赖单一平台特性；考虑多平台部署策略。"),
        ("云开发资源限制", "技术", "中", "中", "评估免费额度是否满足需求；设计资源降级方案；监控资源使用量，设置告警阈值。"),
        ("用户增长缓慢", "市场", "中", "中", "设计裂变分享机制；利用公众号/社群导流；优化小程序搜索关键词(SEO)。"),
        ("数据安全与隐私", "法律", "高", "低", "遵守《个人信息保护法》；最小化数据采集；用户数据加密存储；提供数据删除功能。"),
        ("开发周期超期", "资源", "中", "中", "采用敏捷开发，分阶段交付；优先完成P0功能；预留20%时间缓冲。"),
    ],
    "APP": [
        ("应用商店审核被拒", "法律", "高", "中", "研读App Store/Google Play审核指南；避免使用私有API；准备审核说明文档；预留审核时间。"),
        ("跨平台兼容性问题", "技术", "高", "中", "选择成熟跨平台框架；在真机上充分测试；建立设备兼容性测试矩阵。"),
        ("性能不达标", "技术", "中", "中", "早期进行性能基准测试；使用性能分析工具(Profiler)；优化关键路径代码。"),
        ("用户获取成本高", "市场", "高", "高", "制定ASO(应用商店优化)策略；利用社交媒体推广；设计口碑传播机制。"),
        ("第三方SDK依赖风险", "技术", "中", "中", "评估SDK的维护状态和社区活跃度；设计抽象层便于替换；定期更新SDK版本。"),
        ("团队人手不足", "资源", "中", "中", "合理裁剪功能范围(MVP优先)；考虑外包非核心模块；使用低代码工具提效。"),
    ],
    "网站": [
        ("SEO效果不佳", "市场", "中", "中", "采用SSR/SSG技术方案；优化页面加载速度；合理使用语义化HTML；建立外链策略。"),
        ("网站被攻击/入侵", "技术", "高", "中", "部署WAF防火墙；定期安全扫描；使用HTTPS；实施SQL注入/XSS防护。"),
        ("高并发性能瓶颈", "技术", "中", "低", "使用CDN加速静态资源；数据库读写分离；引入缓存层(Redis)；设计弹性扩缩容方案。"),
        ("浏览器兼容性问题", "技术", "低", "中", "使用Browserslist定义目标浏览器；CSS添加前缀；Polyfill处理新特性；自动化兼容性测试。"),
        ("内容合规风险", "法律", "高", "低", "建立内容审核机制；遵守《网络安全法》等法规；ICP备案；用户协议和隐私政策完善。"),
        ("域名/服务器故障", "资源", "高", "低", "选择可靠云服务商；配置域名自动续费；设置服务监控告警；准备灾备方案。"),
    ],
    "游戏": [
        ("玩法缺乏吸引力", "市场", "高", "中", "早期原型测试验证核心玩法；收集玩家反馈迭代；参考成功案例但不照搬。"),
        ("美术资源制作超期", "资源", "高", "高", "使用成熟美术风格降低制作难度；优先制作核心资源；考虑购买素材包。"),
        ("性能优化不足", "技术", "高", "中", "建立性能预算(帧率/内存/包体)；持续性能分析；使用LOD/合批等优化技术。"),
        ("版号申请困难", "法律", "高", "高", "提前了解版号政策；准备完整申请材料；考虑海外发行作为备选；先以广告变现模式运营。"),
        ("服务器成本过高", "资源", "中", "中", "设计合理的服务器架构；使用按量付费模式；优化网络协议减少带宽消耗。"),
        ("用户留存率低", "市场", "高", "中", "设计新手引导降低学习成本；加入社交/排行榜增加粘性；定期更新内容保持新鲜感。"),
    ],
}

# 通用风险（所有项目类型适用）
_COMMON_RISKS = [
    ("需求变更频繁", "资源", "中", "高", "建立需求变更流程；使用敏捷开发快速响应；与需求方定期对齐优先级。"),
    ("技术选型失误", "技术", "高", "低", "充分调研和原型验证；参考同类型成功项目；预留技术切换的缓冲时间。"),
]

# 功能关键词触发的额外风险
_FEATURE_RISKS = {
    ("支付", "交易"): ("支付安全风险", "法律", "高", "中",
                       "使用官方支付SDK；交易数据加密传输；实施风控策略；保留交易日志。"),
    ("社交", "社区"): ("内容违规风险", "法律", "高", "中",
                      "接入内容安全审核API；建立举报机制；设置敏感词过滤；制定社区规范。"),
    ("AI", "智能", "推荐"): ("AI模型效果不达预期", "技术", "中", "中",
                             "准备规则兜底方案；持续训练优化模型；设置效果监控指标；分阶段引入AI功能。"),
}

_SEV_ORDER = {"高": 3, "中": 2, "低": 1}
_SEV_TAG = {"高": "[!!!]", "中": "[!! ]", "低": "[!  ]"}


def _parse_risks(raw: list) -> list:
    """将紧凑格式转换为标准字典"""
    return [{"name": r[0], "category": r[1], "severity": r[2], "probability": r[3], "mitigation": r[4]}
            for r in raw]


def _get_feature_risks(features: str) -> list:
    """根据功能关键词匹配额外风险"""
    if not features:
        return []
    feat_list = [f.strip() for f in features.split(",") if f.strip()]
    result = []
    for keywords, risk_tuple in _FEATURE_RISKS.items():
        if any(any(kw in f for kw in keywords) for f in feat_list):
            result.append(_parse_risks([risk_tuple])[0])
    return result


def _get_all_risks(project_type: str, features: str) -> list:
    """获取全部风险列表，按严重程度排序"""
    type_risks = _parse_risks(_RISK_RAW.get(project_type, _RISK_RAW["网站"]))
    common_risks = _parse_risks(_COMMON_RISKS)
    feat_risks = _get_feature_risks(features)
    all_risks = type_risks + feat_risks + common_risks
    all_risks.sort(key=lambda r: (_SEV_ORDER[r["severity"]], _SEV_ORDER[r["probability"]]), reverse=True)
    return all_risks


def generate_report(project: str, project_type: str, features: str) -> str:
    """生成风险评估报告（Markdown格式）"""
    now = now_iso()
    risks = _get_all_risks(project_type, features)
    high_count = sum(1 for r in risks if r["severity"] == "高")
    mid_count = sum(1 for r in risks if r["severity"] == "中")
    low_count = sum(1 for r in risks if r["severity"] == "低")

    lines = [
        f"# {project} - 风险评估报告",
        "", f"> 生成时间：{now}", f"> 项目类型：{project_type}", f"> 识别风险数量：{len(risks)}",
        "", "---", "",
        "## 一、风险概览", "",
        "| 严重程度 | 数量 |", "|---------|------|",
        f"| 高 | {high_count} |", f"| 中 | {mid_count} |", f"| 低 | {low_count} |",
        "", "## 二、风险详情", "",
    ]

    for i, risk in enumerate(risks, 1):
        tag = _SEV_TAG[risk["severity"]]
        lines.extend([
            f"### {i}. {tag} {risk['name']}", "",
            f"- **类别：** {risk['category']}",
            f"- **严重程度：** {risk['severity']}",
            f"- **发生概率：** {risk['probability']}",
            f"- **应对策略：** {risk['mitigation']}", "",
        ])

    lines.extend([
        "## 三、风险应对优先级建议", "",
        "1. **优先处理** 高严重程度 + 高概率的风险，制定详细应对计划",
        "2. **重点关注** 高严重程度的风险，即使概率较低也需准备预案",
        "3. **持续监控** 中等风险，在开发过程中定期回顾",
        "4. **记录跟踪** 所有风险纳入风险登记册，定期更新状态",
        "",
        "## 四、风险监控机制", "",
        "- 每周迭代回顾时检查风险状态",
        "- 发现新风险及时补充到风险列表",
        "- 风险应对措施执行后更新评估结果",
        "- 重大风险升级至项目干系人",
        "", "---",
        "*本文档由 Octopus 谋略脑自动生成，请根据实际情况调整和完善。*", "",
    ])
    return "\n".join(lines)


def save_report(project: str, content: str) -> str:
    """保存风险评估报告到Markdown文件"""
    safe_name = project.replace(" ", "_")
    filepath = os.path.join(PLANS_DIR, f"{safe_name}_risks.md")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print_success(f"风险评估报告已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="风险评估 - Octopus 谋略脑")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--type", required=True, help="项目类型(小程序/APP/网站/游戏)")
    parser.add_argument("--features", default="", help="核心功能，逗号分隔(可选)")
    args = parser.parse_args()

    content = generate_report(args.project, args.type, args.features)
    filepath = save_report(args.project, content)
    print_success(f"风险评估报告已生成: {filepath}")
    print_success(f"项目: {args.project} | 类型: {args.type}")


if __name__ == "__main__":
    main()
