# Primintel：智能进化版 验证操作手册

本手册旨在指导用户如何验证 Primintel 的“Hermes 风格深度进化”（自动化技能提炼）功能。

---

## 1. 环境准备与配置

在开始验证前，请确保功能已开启：

1. **修改配置文件**：
   在 `config.json` 中添加或更新以下配置：
   ```json
   {
     "enable_skill_distillation": true,
     "distillation_min_tools": 2,
     "agent": true
   }
   ```
   - `enable_skill_distillation`: 核心开关，必须为 `true`。
   - `distillation_min_tools`: 自动触发的最小工具调用数。建议测试时设为 `2`。

2. **启动服务**：
   运行 `python app.py`。

---

## 2. 验证场景一：自动静默学习 (Background Learning)

### 步骤：
1. **下达复合任务**：
   访问 Web 控制台 (`localhost:9900`)，向 Agent 发送一个需要调用多个工具的任务。
   *示例提示词*：
   > “帮我搜索一下今天北京的天气，然后创建一个名为 weather.txt 的文件记录这些信息，最后告诉我文件保存的完整路径。”

2. **观察执行过程**：
   确认 Agent 依次执行了 `web_search` 和 `write_file`（或类似工具）。

3. **结果验证**：
   任务完成后，检查项目根目录下的 `workspace/skills/` 文件夹。
   - **预期结果**：出现一个以 `auto-` 开头的新文件夹（例如 `auto-weather-recorder`）。
   - **文件检查**：文件夹内应包含一个 `SKILL.md`，内容包含该任务的步骤总结。

---

## 3. 验证场景二：手动触发进化 (/evolve)

### 步骤：
1. **建立上下文**：
   在聊天窗口中先进行一段复杂的对话（确保包含工具调用，但不需要达到自动触发的阈值，或者即使达到了也可以手动再次触发）。

2. **发送指令**：
   输入指令：
   ```text
   /evolve
   ```

3. **观察回复**：
   - **预期结果**：Agent 回复类似“✅ 技能进化完成！新技能: auto-xxx”的信息。
   - **异常处理**：若工具调用不足，Agent 会提示“⚠️ 当前对话的工具调用数低于提炼阈值”。

---

## 4. 验证场景三：技能持久化与重用

### 步骤：
1. **刷新技能**：
   查看 `/skill list`，确认刚生成的 `auto-` 技能已在列表中且显示为 `✅ on`。

2. **验证重用**：
   开启一个**新会话**（清除上下文 `/context clear`）。
   发送一个类似的简短请求，观察 Agent 是否开始引用之前学到的流程。
   *例如*：如果之前学了记录天气，现在问“帮我记一下上海的天气”，观察它是否比之前更熟练。

---

## 5. 调试与日志

若未生成技能，请检查控制台/日志输出：
- 搜索 `[Distill]` 关键字。
- `[Distill] Skipping`: 说明未达到工具调用阈值。
- `[Distill] LLM determined workflow is not reusable`: 说明模型认为这个任务太琐碎，不值得存为技能。
- `[Distill] ✅ New skill saved`: 提炼成功。

> [!TIP]
> 建议在验证时使用 `Claude-3.5-Sonnet` 或 `Gemini-1.5-Pro` 等逻辑能力较强的模型，以获得更高质量的技能建模。
