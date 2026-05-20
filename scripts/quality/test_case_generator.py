# -*- coding: utf-8 -*-
"""
测试用例生成器 - Octopus Skill "慧眼脑"质量把关
根据功能列表生成测试用例文档
"""

import argparse
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import now_iso, print_success, print_error

# 数据目录
DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "quality"
)

# 内置常见功能的测试用例模板
# 内置常见功能的测试用例模板 - 紧凑格式: (type, name, precondition, steps, expected_result)
_CASE_RAW = {
    "记账": ("记账功能测试", [
        ("正常流程", "成功添加一笔收入记录", "用户已登录，进入记账页面",
         "1. 选择类型为“收入”\n2. 输入金额 100.00\n3. 选择分类“工资”\n4. 点击保存",
         "记录保存成功，列表中显示新增的收入记录，金额显示正确"),
        ("正常流程", "成功添加一笔支出记录", "用户已登录，进入记账页面",
         "1. 选择类型为“支出”\n2. 输入金额 50.50\n3. 选择分类“餐饮”\n4. 填写备注“午餐”\n5. 点击保存",
         "记录保存成功，列表显示支出记录，备注信息正确展示"),
        ("异常流程", "金额为空时提交", "用户已登录，进入记账页面",
         "1. 不输入金额\n2. 直接点击保存",
         "提示“请输入金额”，不允许保存"),
        ("异常流程", "输入负数金额", "用户已登录，进入记账页面",
         "1. 输入金额 -100\n2. 点击保存",
         "提示“金额必须为正数”，不允许保存"),
        ("边界条件", "输入极大金额", "用户已登录，进入记账页面",
         "1. 输入金额 999999999.99\n2. 点击保存",
         "系统正常处理，金额显示不溢出、不截断"),
        ("边界条件", "输入含多位小数的金额", "用户已登录，进入记账页面",
         "1. 输入金额 10.999\n2. 点击保存",
         "金额自动四舍五入为两位小数(10.00或 11.00，取决于业务规则)"),
    ]),
    "统计": ("统计功能测试", [
        ("正常流程", "查看本月支出统计", "用户已登录，本月有多条记账记录",
         "1. 进入统计页面\n2. 选择时间范围为“本月”",
         "正确展示本月支出总额、分类占比图表，数据与记账记录一致"),
        ("正常流程", "按自定义时间范围筛选", "用户已登录，有多条历史记账记录",
         "1. 进入统计页面\n2. 选择自定义时间范围\n3. 设置起止日期\n4. 点击查询",
         "展示指定时间范围内的统计数据，图表和数字均正确"),
        ("异常流程", "无数据时查看统计", "用户已登录，所选时间范围内无记账记录",
         "1. 进入统计页面\n2. 选择一个无记录的时间范围",
         "展示空状态提示(如“暂无数据”)，图表区域显示占位"),
        ("边界条件", "跨年统计查询", "用户已登录，有跨年度的记账记录",
         "1. 进入统计页面\n2. 选择时间范围跨越两个年份",
         "正确聚合跨年数据，年份维度展示正确"),
    ]),
    "预算": ("预算功能测试", [
        ("正常流程", "设置月度预算", "用户已登录，进入预算设置页面",
         "1. 输入月度预算金额 3000\n2. 选择预算分类“餐饮”\n3. 点击保存",
         "预算设置成功，页面显示已设置的预算金额"),
        ("正常流程", "预算超支提醒", "用户已设置餐饮预算1000元，本月餐饮已消费900元",
         "1. 新增一笔餐饮支出 200 元",
         "系统弹出预算超支提醒，显示当前消费总额和超出金额"),
        ("异常流程", "预算金额为0", "用户已登录，进入预算设置页面",
         "1. 输入预算金额 0\n2. 点击保存",
         "提示“预算金额必须大于0”，不允许保存"),
        ("边界条件", "预算金额刚好用完", "用户已设置预算1000元，已消费999元",
         "1. 新增一笔1元支出",
         "预算刚好用完，显示预算已用尽的提示"),
    ]),
    "登录": ("登录功能测试", [
        ("正常流程", "使用正确账号密码登录", "用户已注册账号",
         "1. 输入正确的用户名\n2. 输入正确的密码\n3. 点击登录",
         "登录成功，跳转到首页"),
        ("异常流程", "密码错误", "用户已注册账号",
         "1. 输入正确的用户名\n2. 输入错误的密码\n3. 点击登录",
         "提示“用户名或密码错误”，停留在登录页"),
        ("异常流程", "账号不存在", "无",
         "1. 输入未注册的用户名\n2. 输入任意密码\n3. 点击登录",
         "提示“用户名或密码错误”(不暴露账号是否存在)"),
        ("边界条件", "连续多次密码错误", "用户已注册账号",
         "1. 连续输入错误密码5次",
         "账号被临时锁定或要求验证码验证"),
    ]),
    "支付": ("支付功能测试", [
        ("正常流程", "完成一笔支付", "用户已登录，账户有足够余额",
         "1. 选择商品/服务\n2. 确认支付金额\n3. 选择支付方式\n4. 输入支付密码\n5. 确认支付",
         "支付成功，显示支付结果页，订单状态更新为已支付"),
        ("异常流程", "余额不足支付", "用户已登录，账户余额不足",
         "1. 选择商品/服务\n2. 确认支付金额\n3. 选择余额支付",
         "提示“余额不足”，引导用户充值或选择其他支付方式"),
        ("异常流程", "支付过程中断网", "用户已登录，正在支付过程中",
         "1. 发起支付\n2. 支付过程中断开网络",
         "提示网络异常，支付状态不明确时提供查询入口"),
        ("边界条件", "重复提交支付", "用户已登录",
         "1. 发起支付\n2. 快速连续点击支付按钮多次",
         "只处理一次支付，有防重复提交机制"),
    ]),
}


def _parse_case_templates(raw):
    """将紧凑格式转为标准字典格式"""
    result = {}
    for feat, (desc, cases) in raw.items():
        result[feat] = {
            "description": desc,
            "cases": [{"type": t, "name": n, "precondition": p, "steps": s, "expected_result": e} for t, n, p, s, e in cases],
        }
    return result


FEATURE_TEMPLATES = _parse_case_templates(_CASE_RAW)



# 通用测试用例模板（用于未内置的功能） - 紧凑格式
_GENERIC_RAW = [
    ("正常流程", "正常使用{feature}功能", "用户已登录，进入{feature}功能页面",
     "1. 按照正常操作流程使用{feature}功能\n2. 完成核心操作",
     "功能正常执行，结果符合预期"),
    ("异常流程", "{feature}功能输入异常数据", "用户已登录，进入{feature}功能页面",
     "1. 输入非法/异常数据\n2. 提交操作",
     "系统给出明确的错误提示，不产生异常崩溃"),
    ("异常流程", "{feature}功能网络异常处理", "用户已登录，网络不稳定",
     "1. 操作{feature}功能\n2. 模拟网络中断",
     "显示网络异常提示，恢复网络后可重试"),
    ("边界条件", "{feature}功能边界值测试", "用户已登录",
     "1. 输入边界值数据(最大值/最小值/空值)\n2. 观察系统表现",
     "系统正确处理边界情况，无溢出或异常"),
]


def _parse_generic(raw):
    return {"cases": [{"type": t, "name": n, "precondition": p, "steps": s, "expected_result": e} for t, n, p, s, e in raw]}


GENERIC_TEMPLATE = _parse_generic(_GENERIC_RAW)


def generate_test_cases(project_name: str, features: list) -> str:
    """生成测试用例Markdown文档"""
    lines = []
    lines.append(f"# {project_name} - 测试用例文档")
    lines.append("")
    lines.append(f"> 生成时间：{now_iso()}")
    lines.append(f"> 功能列表：{', '.join(features)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    case_id = 0
    for feature in features:
        # 查找内置模板或使用通用模板
        template = FEATURE_TEMPLATES.get(feature, GENERIC_TEMPLATE)
        description = template.get("description", f"{feature}功能测试")

        lines.append(f"## {feature} - {description}")
        lines.append("")

        for case in template["cases"]:
            case_id += 1
            case_name = case["name"].replace("{feature}", feature)
            case_pre = case["precondition"].replace("{feature}", feature)
            case_steps = case["steps"].replace("{feature}", feature)
            case_expected = case["expected_result"].replace("{feature}", feature)

            lines.append(f"### TC-{case_id:03d} [{case['type']}] {case_name}")
            lines.append("")
            lines.append(f"- **前置条件**：{case_pre}")
            lines.append("")
            lines.append(f"- **测试步骤**：")
            lines.append("")
            for step in case_steps.split("\n"):
                lines.append(f"  {step}")
            lines.append("")
            lines.append(f"- **预期结果**：{case_expected}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 汇总信息
    lines.append("## 测试用例汇总")
    lines.append("")
    lines.append(f"| 功能模块 | 用例数量 |")
    lines.append(f"| -------- | -------- |")
    for feature in features:
        template = FEATURE_TEMPLATES.get(feature, GENERIC_TEMPLATE)
        lines.append(f"| {feature} | {len(template['cases'])} |")
    total = sum(
        len(FEATURE_TEMPLATES.get(f, GENERIC_TEMPLATE)["cases"]) for f in features
    )
    lines.append(f"| **合计** | **{total}** |")

    return "\n".join(lines)


def save_test_cases(content: str, project_name: str) -> str:
    """保存测试用例文档"""
    filename = f"{project_name}_test_cases.md"
    filepath = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print_success(f"测试用例文档已保存: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="测试用例生成器 - 根据功能列表生成测试用例")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--features", required=True, help="功能列表，逗号分隔（如：记账,统计,预算）")
    args = parser.parse_args()

    features = [f.strip() for f in args.features.split(",") if f.strip()]
    if not features:
        print_error("请至少指定一个功能")
        return

    content = generate_test_cases(args.project, features)
    filepath = save_test_cases(content, args.project)

    total = sum(
        len(FEATURE_TEMPLATES.get(f, GENERIC_TEMPLATE)["cases"]) for f in features
    )
    print_success(f"测试用例文档已生成: {filepath}")
    print_success(f"功能模块: {len(features)} 个")
    print_success(f"测试用例: {total} 个")


if __name__ == "__main__":
    main()
