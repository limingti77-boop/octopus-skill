# Octopus 大脑协作协议

本文档详细定义了 Octopus 7个大脑之间的协作规则、状态流转和调用时机。

## 状态定义

```python
class OctopusState:
    IDLE = "idle"                    # 空闲，等待输入
    EXPLORING = "exploring"          # 探知脑工作中（需求挖掘）
    RESEARCHING = "researching"      # 调研脑工作中（情报收集）
    PLANNING = "planning"            # 谋略脑工作中（方案设计）
    EXECUTING = "executing"          # 巧手脑工作中（任务执行）
    REVIEWING = "reviewing"          # 慧眼脑工作中（质量检查）
    EVOLVING = "evolving"            # 进化脑工作中（反馈收集）
```

## 状态流转图

```
                    +--------+
                    |  IDLE  |
                    +----+---+
                         |
                         | 用户输入
                         v
              +----------+-----------+
              |      主脑判断        |
              |  1. 识别意图         |
              |  2. 检查记忆         |
              |  3. 感知情绪         |
              +----------+-----------+
                         |
            +------------+------------+
            |                         |
    新项目/需求不清              继续项目/需求明确
            |                         |
            v                         v
    +-------+--------+        +-------+--------+
    |  EXPLORING     |        |  直接到对应阶段 |
    |  探知脑工作    |        |  (RESEARCHING/  |
    +-------+--------+        |   PLANNING/     |
            |                |   EXECUTING)    |
    需求明确后                +-------+--------+
            |                         |
            +------------+------------+
                         |
                         v
              +----------+-----------+
              |    RESEARCHING       |
              |    调研脑工作        |
              |  (可跳过)            |
              +----------+-----------+
                         |
            调研完成或跳过
                         |
                         v
              +----------+-----------+
              |     PLANNING         |
              |     谋略脑工作       |
              |  (可跳过)            |
              +----------+-----------+
                         |
            方案确认或跳过
                         |
                         v
              +----------+-----------+
              |    EXECUTING         |
              |    巧手脑工作        |
              +----------+-----------+
                         |
            阶段性完成或全部完成
                         |
                         v
              +----------+-----------+
              |    REVIEWING         |
              |    慧眼脑工作        |
              +----------+-----------+
                         |
            质量通过
                         |
                         v
              +----------+-----------+
              |     EVOLVING         |
              |     进化脑工作       |
              +----------+-----------+
                         |
                         v
                    +----+---+
                    |  IDLE  |  (等待下一次输入)
                    +--------+
```

## 大脑调用规则

### 主脑（MasterBrain）

**调用时机**：每次用户输入后立即调用

**职责**：
1. 识别用户意图（新项目/继续项目/反馈/闲聊）
2. 加载用户记忆（偏好、历史项目、行为模式）
3. 感知用户情绪（通过回复内容分析）
4. 决定下一步调用哪个大脑

**决策逻辑**：
```python
def master_brain_decide(user_input, context):
    # 1. 意图识别
    intent = parse_intent(user_input)
    
    # 2. 加载记忆
    user_profile = load_user_profile(context.user_id)
    current_project = load_project_state(context.project_id)
    
    # 3. 情绪感知
    emotion = detect_emotion(user_input)
    if emotion in ["frustrated", "impatient"]:
        adaptation_engine.suggest_adjustment(context.user_id)
    
    # 4. 决策
    if intent == "new_project":
        if has_clear_requirements(user_input):
            return State.RESEARCHING
        else:
            return State.EXPLORING
    elif intent == "continue_project":
        return recover_state(current_project.last_state)
    elif intent == "feedback":
        return State.EVOLVING
    else:
        return handle_casual_chat()
```

**输出格式**：
```json
{
  "intent": "new_project|continue|feedback|chat",
  "next_state": "exploring|researching|planning|executing|reviewing|evolving",
  "emotion": "engaged|impatient|frustrated|excited|neutral",
  "adjustments": ["减少追问", "加快速度", "增加解释"],
  "context": {
    "user_id": "xxx",
    "project_id": "xxx",
    "session_count": 5
  }
}
```

### 探知脑（ExplorerBrain）

**调用时机**：主脑判断需求不明确时

**触发条件**：
- 用户说"我想做个XX"但缺少关键信息（给谁用、核心功能、平台等）
- 用户回复很模糊（"随便""都行""你定"）
- 用户主动要求"帮我想想"

**工作流程**：
1. 调用 intent_parser.py 解析意图
2. 调用 question_generator.py 生成问题
3. 根据用户回答，动态调整追问策略
4. 调用 requirement_analyzer.py 整理需求

**结束条件**（满足任一）：
- 用户回答了所有关键问题
- 用户说"先这样""差不多够了"
- 连续3轮追问后用户仍很模糊 → 进入谋略脑直接给方案
- 检测到用户不耐烦信号 → 减少追问，快速推进

**输出格式**：
```json
{
  "state": "exploring",
  "progress": "30%",
  "questions_asked": 3,
  "questions_answered": 2,
  "requirements": {
    "project_type": "小程序",
    "target_user": "个人用户",
    "core_features": ["记账", "统计"],
    "platform": "微信",
    "missing_info": ["预算", "时间"]
  },
  "next_action": "continue_exploring|proceed_to_research|proceed_to_plan"
}
```

### 调研脑（ResearchBrain）

**调用时机**：需求明确后，或用户主动要求调研

**触发条件**：
- 探知脑完成，需求已明确
- 用户说"帮我看看市场上有什么"
- 用户问"这个技术方案怎么样"

**工作流程**：
1. 调用 multi_search.py 生成搜索策略
2. 调用 competitor_analyzer.py 分析竞品（如有竞品名）
3. 调用 tech_trend.py 分析技术趋势

**结束条件**：
- 调研完成
- 用户说"不用调研了，直接做"
- 用户说"我已有方案"

**输出格式**：
```json
{
  "state": "researching",
  "competitors": [...],
  "tech_trends": [...],
  "market_gaps": [...],
  "recommendations": [...]
}
```

### 谋略脑（StrategyBrain）

**调用时机**：调研完成，或跳过调研，需要制定方案

**触发条件**：
- 调研脑完成
- 用户说"帮我规划一下"
- 用户说"直接做"（快速模式）

**工作流程**：
1. 调用 prd_generator.py 生成PRD
2. 调用 tech_selector.py 选择技术栈
3. 调用 risk_assessor.py 评估风险
4. 整合成完整方案

**结束条件**：
- 用户确认方案
- 用户说"直接做"（接受默认方案）
- 用户提出修改意见 → 调整后再次确认

**输出格式**：
```json
{
  "state": "planning",
  "prd": {...},
  "tech_stack": {...},
  "risks": [...],
  "milestones": [...],
  "confirmed": false
}
```

### 巧手脑（ExecutionBrain）

**调用时机**：方案确认后

**触发条件**：
- 谋略脑完成，用户确认方案
- 用户说"直接做"（跳过前面所有步骤）

**工作流程**：
1. 调用 task_decomposer.py 拆解任务
2. 调用 skill_scheduler.py 调度Skill
3. 每完成一个任务，调用 progress_monitor.py 更新进度
4. 阶段性成果调用慧眼脑检查

**结束条件**：
- 所有任务完成
- 用户说"先到这里"
- 遇到无法解决的问题

**输出格式**：
```json
{
  "state": "executing",
  "tasks": [...],
  "completed": [...],
  "in_progress": [...],
  "blocked": [...],
  "progress": "60%"
}
```

### 慧眼脑（QualityBrain）

**调用时机**：阶段性成果产出，或项目完成

**触发条件**：
- 巧手脑完成一个阶段
- 项目最终交付前
- 用户要求"检查一下"

**工作流程**：
1. 调用 checklist_generator.py 生成检查清单
2. 调用 test_case_generator.py 生成测试用例（如有代码）
3. 调用 review_helper.py 辅助审查
4. 输出质量报告

**结束条件**：
- 质量通过
- 记录问题，返回巧手脑修复

**输出格式**：
```json
{
  "state": "reviewing",
  "checklist": [...],
  "issues": [...],
  "passed": true|false,
  "score": 85
}
```

### 进化脑（EvolutionBrain）

**调用时机**：项目交付后，或用户反馈

**触发条件**：
- 慧眼脑完成，项目交付
- 用户主动反馈
- 项目结束一段时间后

**工作流程**：
1. 调用 feedback_collector.py 收集反馈
2. 调用 iteration_planner.py 规划迭代
3. 调用 pattern_learner.py 学习模式
4. 调用 user_insight.py 深度洞察

**结束条件**：
- 数据记录完成
- 更新用户画像和偏好

**输出格式**：
```json
{
  "state": "evolving",
  "feedback": [...],
  "insights": [...],
  "next_version_plan": {...},
  "user_profile_updated": true
}
```

## 异常处理

### 用户放弃

**信号**："算了""不做了""放弃"

**处理**：
1. 记录放弃原因（behavior_observer）
2. 询问是否需要保存当前进度
3. 更新项目状态为"暂停"
4. 进入 EVOLVING 收集反馈

### 用户改变方向

**信号**："等等""换个方向""我想做别的"

**处理**：
1. 不追问为什么改变
2. 保存当前项目状态
3. 询问是否开始新项目
4. 如果是，回到 IDLE 重新进入流程

### 用户表达不满

**信号**："太麻烦了""太慢了""不满意"

**处理**：
1. 立即道歉并询问具体问题
2. 调用 adaptation_engine 调整策略
3. 提供简化方案或加速方案
4. 记录到 preferences

## 快速模式

对于明确知道自己要什么的用户，提供快速模式：

```
用户：直接帮我做个记账小程序，用React，越快越好

Octopus：
（主脑：检测到"直接""越快越好"，进入快速模式）
明白，快速模式启动。跳过追问和调研，直接出原型。

（直接跳到 EXECUTING，调用巧手脑）
```

快速模式跳过：EXPLORING、RESEARCHING、PLANNING
直接进入：EXECUTING（使用默认最佳实践）

## 数据持久化

每个状态转换时，自动保存：
- 当前状态
- 上下文信息
- 用户输入和章鱼回复
- 行为信号（用于进化）

保存位置：data/sessions/{session_id}/
