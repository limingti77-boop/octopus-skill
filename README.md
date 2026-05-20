# 🐙 Octopus Skill - 智能项目协作助手

> "你说想法，我办一切"

Octopus 是一个符合 Agent Skills 规范的智能助手，采用**多脑架构**理解需求、规划方案并协调执行。具备**四层自我进化**能力，越用越懂用户。

## ✨ 核心亮点

### 🧠 多脑架构
7个大脑各司其职，像章鱼一样协同工作：
- **主脑**：总指挥 + 记忆库 + 情绪感知
- **探知脑**：需求挖掘 + 主动启发
- **调研脑**：情报收集（竞品、技术、趋势）
- **谋略脑**：方案设计 + 需求裁剪 + 风险预判
- **巧手脑**：调度专业 Skill 执行
- **慧眼脑**：质量把关
- **进化脑**：迭代优化 + 自我学习

### 🪵 四层自我进化（市场首创）
Octopus 像一块原木，在使用过程中被雕刻成最适合你的样子：
- **第1层**：让你更喜欢 → 自动学习沟通偏好
- **第2层**：用得更顺手 → 自动优化协作流程
- **第3层**：帮得更多 → 积累经验，主动发现机会
- **第4层**：比你还懂你 → 发现你自己都没意识到的模式

### 🔧 Skill 管理系统
- 内置 4 个常用 Skill（前端设计、头脑风暴、文档、测试）
- 支持从 GitHub 搜索和安装新 Skill
- 自动调度 Skill 执行任务

## 📁 项目结构

```
octopus/
├── SKILL.md                    # Skill 主文件（含 YAML frontmatter）
├── README.md                   # 项目说明
├── LICENSE                     # MIT License
├── references/                 # 参考文档
│   └── protocol.md            # 大脑协作协议
├── assets/                     # 资源文件
│   └── output_schema.json     # 输出格式标准
├── scripts/                    # 26 个功能脚本
│   ├── common.py              # 共享工具模块
│   ├── memory/                # 主脑 - 记忆管理
│   ├── exploration/           # 探知脑 - 需求挖掘
│   ├── research/              # 调研脑 - 情报收集
│   ├── planning/              # 谋略脑 - 方案设计
│   ├── execution/             # 巧手脑 - 任务调度 + Skill管理
│   ├── quality/               # 慧眼脑 - 质量把关
│   └── evolution/             # 进化脑 - 迭代优化
├── skills/                     # Skill 管理目录
│   ├── builtin/               # 内置 Skill
│   └── installed/             # 用户安装的 Skill
└── data/                       # 运行时数据（自动生成）
```

## 🚀 安装

### 方式一：直接复制
```bash
# 克隆仓库
git clone https://github.com/limingti77-boop/octopus-skill.git

# 复制到对应客户端的 skills 目录
# Claude Code: cp -r octopus-skill ~/.claude/skills/octopus
# Solo: cp -r octopus-skill ~/.trae-cn/skills/octopus
```

### 方式二：使用 skills CLI
```bash
npx skills add YOUR_USERNAME/octopus-skill
```

## 📖 使用示例

### 新用户第一次使用
```
用户：我想做个记账小程序

Octopus：好呀！记账这个需求很实在。先了解几个关键点：
1. 给谁用？
2. 最看重什么功能？
3. 有没有特别烦现有记账软件的地方？
```

### 老用户（已进化）
```
用户：我想做个TODO工具

Octopus：老规矩，先出个原型你看看？
（跳过5轮追问，直接进入执行）
```

### 主动洞察（第4层能力）
```
用户：我想做个天气APP

Octopus：对了，你最近3个项目都跟数据展示有关，
要不要这次也加个数据分析功能？
```

## 🔧 26 个功能脚本

| 模块 | 脚本数 | 核心能力 |
|------|--------|---------|
| memory/ | 3 | 用户画像、项目状态、偏好学习 |
| exploration/ | 3 | 意图解析、问题生成、需求分析 |
| research/ | 3 | 搜索聚合、竞品分析、技术趋势 |
| planning/ | 3 | PRD生成、技术选型、风险评估 |
| execution/ | 4 | 任务拆解、Skill调度、进度监控、Skill管理 |
| quality/ | 3 | 检查清单、测试用例、审查辅助 |
| evolution/ | 6 | 行为观察、适应引擎、反馈收集、迭代计划、模式学习、深度洞察 |

## 🛠️ 技术栈

- **语言**：Python 3.8+
- **数据存储**：JSON
- **依赖**：无第三方依赖

## 📄 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**Octopus 不只是一个工具，它是一个越用越懂你的搭档。** 🐙


