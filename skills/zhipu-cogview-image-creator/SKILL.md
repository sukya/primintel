---
name: zhipu-cogview-image-creator
description: Generate or edit images from text prompts. Use when the user asks to create, draw, design, or edit an image, illustration, photo, icon, poster, or any visual content.
metadata:
  emoji: 🎨
  homepage: https://open.bigmodel.cn/
  env_vars:
    - name: api_key
      description: "智谱 API Key (留空默认使用系统统一配置)"
      required: false
    - name: model_name
      description: "模型名称 (默认: cogview-3-flash, 可选: cogview-3-plus)"
      required: false
    - name: size
      description: "分辨率 (默认: 1024x1024, 可选 1024x768 等)"
      required: false
---

# Zhipu CogView Image Generation

Generate images using Zhipu AI CogView model.

## Usage

Run `scripts/cogview_handler.py` with the user's prompt. You MUST execute this exact script. Do NOT attempt to write your own Python script, and do NOT use `requests` or external APIs directly. The script handles API keys and configurations automatically.

```bash
python <base_dir>/scripts/cogview_handler.py "<prompt>"
```

### Output

Prints JSON to stdout:

```json
{
  "status": "success",
  "images": [
    "/skills/zhipu-cogview-image-creator/outputs/zhipu_xxx.jpg"
  ]
}
```

After success, display the image to the user. You MUST embed it in markdown using the EXACT path returned by the script: `![description](/skills/zhipu-cogview-image-creator/outputs/zhipu_xxx.jpg)`.

On error:

```json
{
  "error": "error message"
}
```

### Important rules
1. Do NOT hallucinate URLs or external CDNs. You MUST use the exact path returned in the `images` list.
2. Embed the image in markdown: `![image](/skills/zhipu-cogview-image-creator/outputs/zhipu_xxx.jpg)`.
3. Do NOT use the `send` tool.
