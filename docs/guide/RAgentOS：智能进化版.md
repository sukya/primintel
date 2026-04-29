# 实施计划：为 Primintel 实现 Hermes 风格的深度进化

## 目标

将“自我进化”响应循环集成到 Primintel 中，使代理（Agent）能够自动提取成功的任务执行路径，并将其提炼为可重用的技能（Skills），从而模仿 Hermes Agent 的能力。

## 原理与架构

目前，Primintel 高度依赖手动创建的技能（广泛连接/规则）。为了实现“深度进化”，我们需要一种元编程机制。在代理成功完成一项复杂任务（例如执行了超过 3 次工具调用）后，任务后处理流程会将上下文历史记录与反思提示词（reflection prompt）一起发送给 LLM，以确定是否发现了一个全新的、可重用的系统化流程。如果是这样，它将动态生成一个技能文件（Markdown 格式）。

## 拟议变更

### 1. 提炼模块

#### [新增] `agent/skills/distill.py`
创建一个处理技能提炼逻辑的新模块。
- **功能**：
  - `evaluate_trajectory(messages: list) -> bool`：检查最近的对话是否值得进行技能提炼（例如，成功的结果、非琐碎的工具使用）。
  - `distill_skill(messages: list, model: LLMModel)`：使用元提示词（metaprompt）将用户意图和所采取的步骤总结为有效的技能（Skill）Markdown 格式。
  - `save_distilled_skill(skill_content: str, workspace_dir: str)`：验证生成的技能并将其保存到 `workspace/skills/` 目录，同时调用 `SkillManager.refresh_skills()`。

### 2. 核心代理循环集成

#### [修改] `agent/protocol/agent.py`
- 导入新的提炼服务。
- 在 `run_stream` 执行结束时添加一个异步或后处理步骤。
- 如果大量使用了 `agent.max_steps` 且最终状态为成功，则在后台线程中异步触发 `distill_skill()`，以防止阻塞用户的聊天响应。

#### [修改] `config.py` & `config-template.json`
- 添加配置开关：`"enable_skill_distillation": true`
- 添加配置属性：`"distillation_model"`（可选择使用更便宜/更快的模型进行反思填充，或默认使用主模型）。

## 需要用户确认

> [!WARNING]
> **性能影响：** 在对话结束时触发完整的上下文反思可能会消耗大量 token。我建议**仅**当代理在单回合对话中使用了超过 2 个工具，或者通过 `/distill` CLI 命令明确请求时才运行此功能。为了节省成本，您同意这个条件吗？

> [!IMPORTANT]
> **异步执行：** 技能提炼将在用户获得答案后于后台进行。您希望代理在“学到新技能”时在聊天中主动通知用户，还是应该静默学习？

## 验证计划

### 自动化测试
- 创建单元测试以模拟包含工具使用的对话历史记录，验证 `distill_skill` 是否正确生成了符合 Primintel 技能格式的 Markdown 输出。

### 手动验证
- 重启代理，测试 `SkillManager` 是否正确加载了自动生成的技能。

---

## 维护与同步原则

> [!IMPORTANT]
> **代码同步冲突处理：**
> Primintel 基于 `zhayujie/CowAgent` 开发，但在进化路线上具有独立性。
>
> 1. **设计优先权**：后续拉取同步原作者代码时，必须先判定原作者的新改动是否与 Primintel 的“智能进化/Hermes 风格”设计原则有冲突。
> 2. **冲突解决**：若发生冲突，**必须以当前 Primintel 的进化版设计为准**。不得为了追随上游更新而牺牲自主学习、自动提炼技能等核心能力。
   3. **核心保活**：必须确保 `agent/skills/distill.py` 和相关的 `Agent` 钩子在同步后依然生效。
