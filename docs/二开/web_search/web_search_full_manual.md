# Primintel WebSearch (联网搜索) 深度定制手册

本手册涵盖了经过 V2 优化及 Plan A 架构简化后的联网搜索技能全配置与使用指南。

---

## 🌟 1. 核心架构：统一聚合 (Plan A)
在最新版本中，Primintel 的搜索技能已进化为 **“统一代理”架构**：
- **API 优先**：对于高质量、高稳定性的需求，优先调用专业搜索 API（如博查、Serper）。
- **统一兜底**：所有免费搜索需求统一由 **SearXNG** 驱动。
- **配置即生效**：如需增减搜索引擎，只需修改 SearXNG 的 `settings.yml`，无需改动 Primintel 代码。

---

## 🚀 2. 智能路由与地域优化
系统通过内置的地理位置探测逻辑，实现国内外差异化路由：

### 🇨🇳 国内环境 (CN Mode)
- **优先级**：博查 API (Bocha) > LinkAI > 私有化 SearXNG (百度/搜狗/360)。
- **优化点**：自动屏蔽 DuckDuckGo 等国内无法访问的引擎。

### 🌍 海外环境 (Global Mode)
- **优先级**：博查 API > Serper (Google) > LinkAI > 私有化 SearXNG (Google/DDG)。
- **优化点**：利用海外服务器直连优势，获取全球最新的实时资讯。

---

## ⚙️ 3. 配置参数详解 (`config.json`)

| 参数名 | 默认值 | 推荐设置 | 说明 |
| :--- | :--- | :--- | :--- |
| `search_region` | `auto` | `CN` (国内) | 强制地域覆盖。若自动探测不准，请手动设为 `CN`。 |
| `bocha_api_key` | 空 | 填写 Key | **国内首选**。支持微信、知乎、小红书等信源。 |
| `serper_api_key` | 空 | 填写 Key | **海外首选**。Google 搜索的最佳落地 API。 |
| `searxng_url` | 空 | 您的 URL | 指向您在阿里云/海外自建的 SearXNG 地址。 |

---

## 🐳 4. 自建 SearXNG 部署指引
为了极致的隐私和稳定性，强烈建议自建实例。

### 核心步骤 (阿里云/国内服务器)：
1. **获取配置**：参考项目下 [searxng_deploy_guide.md](file:///d:/project/AIproject/mcn/Primintel/二开/web_search/searxng_deploy_guide.md)。
2. **启用 JSON 格式 (重要)**：在 `settings.yml` 中务必确保 `formats` 包含 `json`。
   ```yaml
   search:
     formats: [html, json]
   ```
3. **关闭访问限制**：将 `limiter` 设为 `false`，确保护理器内部调用不被拦截。

---

## 📝 5. 使用技巧与最佳实践
- **如何触发**：在对话中询问“今天苏州新闻”、“查询宁德时代股价”等需要实时信息的指令。
- **质量提升**：免费 SearXNG 节点可能包含较多网页广告摘要，配置 **博查 API** 后，机器人会自动整合高质量摘要，大幅减少“幻觉”。
- **海外切换**：未来部署至海外服务器时，仅需将 `search_region` 设为 `Global`，并确保 SearXNG 端的 Google 引擎已开启。

---

## 🛠️ 6. 常见故障排查 (FAQ)

### Q1: 技能显示绿色勾选，但机器人说“查不到”？
- **原因**：可能是 SearXNG 返回的结果为空。
- **解决**：检查 SearXNG 的 `settings.yml` 是否正确开启了百度/搜狗引擎，并确认服务器网络是否能访问这些引擎。

### Q2: 报错 HTTP 403 (JSON missing)？
- **原因**：SearXNG 未开启 JSON API 格式。
- **解决**：在 `settings.yml` 中添加 `- json` 到 `formats` 列表并重启容器。

### Q3: 为什么不直接用 DuckDuckGo 库了？
- **原因**：独立库依赖多、易失效，且国内不稳定。
- **优势**：Plan A 架构下，所有的维护都在 SearXNG 服务端完成，Primintel 代码保持零依赖、零漏洞。

---
*Primintel 联网搜索 V2.1 - 2026-04-21*
