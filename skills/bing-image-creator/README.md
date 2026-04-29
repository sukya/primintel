# Bing Image Creator 技能插件指南

## 简介
`bing-image-creator` 是一个处于工业级标准的高阶 AI 绘画技能插件。它通过封装底层的 `bingart` 库，并引入严苛的反风控指纹伪装（`curl_cffi` + `fake-useragent`）机制，实现了极其稳定的、通过 Bing 服务间接调用 OpenAI DALL-E 3 模型的文生图能力。

不仅如此，本插件自带“多账号洗牌轮询”与“安全冻结降级”算法。当某个账号遭遇频率限制 (Quota Exhausted) 或 Cookie 失效时，它会自动切换至备用账号，并在 24 小时后尝试解冻恢复，从而支持全天候挂机输出极高规格的美术素材。

## 环境依赖
使用前，必须确保宿主环境（运行该 Python 脚本的系统环境）安装了以下关键第三方库：

```bash
pip install --upgrade bingart

pip install fake-useragent curl_cffi bingart

```

## 配置指南 (获取身份认证)
由于本插件高度模拟真实浏览器运作，您需要提取个人浏览器中的身份 Token 放入插件的凭证池中。

1. 使用 Edge 或 Chrome 浏览器打开并登录 [Bing Image Creator](https://www.bing.com/images/create)。
2. 按 `F12` 打开开发者工具，进入 **Application（应用）** 面板 -> **Cookies** 树 -> `https://www.bing.com`。
3. 找到名称为 `_U` 的 Cookie，复制其极其冗长的 Value 值。
4. 打开项目目录下的 `resources/config.json` 文件，将刚刚提取的值填入对应账号的 `cookie_U` 字段中。

**提示**：您可以往 `auth_cookies` 数组中添加多个包含不同 `_U` 值的账号字典，脚本会智能计算时间戳，自动轮流调度，极大降低单账号的封控概率。

## 平台接入与使用
1. **安装**：如在 Primintel 等框架中使用，将整个 `bing-image-creator` 文件夹拷贝至宿主的 `plugins/` (或 skills) 目录下。如果有安装前置指令（如 `#scanp`, `#installp`），请依宿主框架常规逻辑装载。
2. **触发**：直接以日常语言下达绘图指令，例如：“帮我画一张写实风格的赛博朋克猫咪”。
3. **工作流**：Agent 中的调度脑（`SKILL.md`）会先拦截您的短句，将其发散为包含镜头、光影、渲染器维度的导演级专业英文提示词，随后投递给底层 Python 脚本请求成图。最后，Agent 会为您直接在界面呈现精美的图片合集。
