---
name: bing-image-creator
description: 顶级文生图工作流技能。当用户请求生成图片、绘画或视觉创作时，务必读取此技能以调用 DALL-E 3 / GPT-4o 引擎。
---

# 工业级文生图驱动内核 (Bing Image Creator)

本技能采用企业级高可用架构，用于渲染极致细节的图像（支持 DALL-E 3, GPT-4o, MAI-Image-1 及多种不同比例）。

## 导演级提示词强化 (Prompt Enhancing)
不要容忍用户简单的短句。在请求底层脚本前，**必须把用户提示词扩展为电影导演级别的英文指令**，必须包含以下维度：
1. **Camera & Lens (镜头语言):** 如 `macro shot`, `ultra-wide angle`, `drone view`, `35mm lens`。
2. **Lighting (光影):** 如 `Rembrandt lighting`, `cinematic volumetric rays`, `neon bioluminescence`。
3. **Renderer & Quality (渲染器与画质):** 如 `Unreal Engine 5 render`, `Octane render`, `hyper-realistic textures`, `8k resolution`, `masterpiece`。
4. **Subject Details (核心细节):** 主体形态、情绪、毛发、物理材质极近细致的描述。

## 调度执行 (Execution)
在获取了英文 Prompt 后，进入终端**执行以下完整路径指令**，并在其后静默等待标准 JSON 回执：

```bash
python skills/bing-image-creator/scripts/bing_handler.py "<你改写后的最终英文提示词>" --model [dalle3|gpt4o|mai1] --aspect [square|landscape|portrait]
```

*注意：必须使用上面的完整路径！必须用双引号包裹 Prompt！*

## 交互截获 (I/O & UX)
由于底层系统已经被重构为纯净输出：
- 当脚本执行完成后，终端只会打印一段 JSON。
- **解析这段 JSON**。
- **如果获得 `"images"` 相对路径列表：**直接将这组图片使用 Markdown 的 `![alt](skills/bing-image-creator/outputs/文件名.jpg)` 语法在对话框中展示给用户。
- **持久性说明：**使用 `skills/bing-image-creator/outputs/` 前缀的图片在刷新页面后依然可以正常显示。
- **如果获得 `"error"` 字段：**向用户汇报发生的具体错误。
