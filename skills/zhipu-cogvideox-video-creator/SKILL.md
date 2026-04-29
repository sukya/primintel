---
name: zhipu-cogvideox-video-creator
description: 智谱 CogVideoX 高级文生视频驱动内核。支持基于文本描述生成高质量短视频，适用于创意视频、动画及视觉演示。
metadata:
  emoji: 🎬
  homepage: https://open.bigmodel.cn/
  env_vars:
    - name: api_key
      description: "智谱 API Key (留空默认使用系统统一配置)"
      required: false
    - name: model_name
      description: "模型名称 (默认: cogvideox-flash, 可选: cogvideox)"
      required: false
    - name: size
      description: "分辨率 (默认: 1280x720, 可选 720x1280 等)"
      required: false
---

# 智谱 CogVideoX 视频驱动 (Zhipu CogVideoX Video Creator)

本技能调用智谱 AI 的 CogVideoX 系列模型，支持以下专业级能力：
- **CogVideoX-Flash**: 永久免费，极速生成。
- **CogVideoX-2/3**: 高画质、长时长（最长 10 秒），支持最高 4K 分辨率。
- **多比例支持**: 横屏 (16:9)、竖屏 (9:16) 及正方形 (1:1) 等多种主流比例。

## 提示词优化 (Prompt Engineering)
为了生成高质量视频，建议将用户的简单描述扩充为包含动态过程的详细场景：
1. **动作描述 (Action):** 描述主体的动作，如 `奔跑`, `缓缓绽放`, `在风中摇曳`。
2. **镜头语言 (Cinematography):** 如 `推拉镜头 (Zoom)`, `环绕拍摄 (Orbit)`, `特写 (Close-up)`。
3. **环境细节 (Environment):** 描述背景、光影和材质。

## 调度执行 (Execution)
在确定视频提示词后，执行以下指令：

```bash
python skills/zhipu-cogvideox-video-creator/scripts/video_handler.py "<你优化的最终提示词>"
```

*注意：生成视频通常需要 30-100 秒，请耐心等待。*

## 交互与展示 (I/O & UX)
- **展示视频 (非常重要)：** 当视频生成成功后，你**必须**在回复的最后，严格使用 Markdown 语法展示视频！格式为：`![video](这里替换为工具返回的 videos 列表中的路径)`。**绝对不能**只说“生成成功”而不附带视频链接！
- **配置管理：** 点击技能侧边的“齿轮”图标可切换模型（Flash/Pro）或修改 API Key。
