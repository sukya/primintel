# 🚀 Primintel: 轻量化全能多通道 AI Agent 助理

<p align="center">
  <strong>融合 OpenClaw、CowAgent 与 HermersAgent 优势的高性价比智能体网关</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python: 3.10+">
  <img src="https://img.shields.io/badge/Docker-Supported-brightgreen.svg" alt="Docker">
</p>

---

## 🌟 项目简介

**Primintel** 是一款面向未来的、架构轻量化且高度可扩展的超级 AI 助理系统。它不只是一个聊天机器人，而是一个能够主动思考、规划任务、操作计算机并不断自我进化的“数字大脑”。

本项目致力于在保持架构极致轻量的同时，提供商业级的稳定性。无论你是追求极致性价比的个人用户，还是希望快速构建原型并推向市场的商业开发者，Primintel 都能通过其灵活的模型路由和多通道接入能力，为你提供最平衡的解决方案。

> 💡 **致敬开源**：Primintel 深度进化自优秀的开源项目 [CowAgent](https://github.com/zhayujie/CowAgent)，并融合了 OpenClaw 与 HermersAgent 的设计理念，针对云端部署环境、长链推理稳定性及多通道富媒体渲染进行了深度重构。

---

## 🛠 核心优势

- ⚖️ **高性价比架构**：延续了 OpenClaw 的轻量级基因，支持在低配服务器上流畅运行，完美适配各类主流及高性价比 API（如 Gemini, GLM-4, DeepSeek 等）。
- 🔗 **多通道原生接入**：原生支持微信（扫码即用）、飞书、钉钉、网页等平台，具备工业级的文本、语音、图片、文件全模态消息处理能力。
- 🧠 **深度记忆与自进化**：集成 SQLite 长期记忆索引系统，支持会话自动蒸馏与知识库交叉引用，构建 Agent 的持续成长能力。
- 🛡 **沙盒化技能引擎**：引入严格的 Skills 运行规范与路径隔离机制，彻底杜绝大模型在工具调用时的路径幻觉与权限溢出。
- ☁️ **云原生自动化部署**：内置 GitHub Actions 自动化构建工作流，支持一键推送镜像至 GHCR，阿里云等云端环境可秒级拉取更新。

---

## 🚀 快速开始

### 1. 极速部署 (推荐)
如果您已有 Docker 环境，只需两步即可完成生产级部署：

```bash
# 1. 下载部署配置文件
wget https://raw.githubusercontent.com/sukya/primintel/main/docker/docker-compose.deploy.yml -O docker-compose.yml

# 2. 启动容器
docker-compose up -d
```
> **注意**：启动前请确保本地目录下已有 `config.json` 配置文件。

### 2. 源码构建部署
如果您需要进行二次开发，请使用以下方式：
cp config-template.json config.json
# 编辑 config.json 填入你的 API Key

# 3. 启动服务
docker-compose -f docker/docker-compose.deploy.yml up -d
```

### 2. 源码本地运行
如果你需要进行技能开发或二次开发：
```bash
# 安装依赖
pip3 install -r requirements.txt
pip3 install -r requirements-optional.txt

# 启动程序
python3 app.py
```
启动后访问 `http://localhost:9900/chat` 即可进入 Web 控制台。

---

## 📅 产品路线图 (Roadmap)

- [x] **架构解耦**：完成核心逻辑与技能插件的深度解耦。
- [x] **自动化运维**：实现基于 GitHub Actions 的多环境镜像自动构建。
- [x] **渲染优化**：修复微信端图像生成无法原生显示的链路问题。
- [x] **路径加固**：实现工作空间沙盒指令集，防止工具调用路径幻觉。
- [ ] **多智能体协作**：引入基于任务编排的多 Agent 协同工作流。
- [ ] **可视化流建模**：支持通过 Web UI 拖拽构建 Agent 技能流。

---

## ⚖️ 声明与协议

1. **开源协议**：本项目遵循 [MIT 协议](/LICENSE)。
2. **免责声明**：本项目主要用于技术研究和学习，使用本项目时需遵守所在地法律法规。任何个人或企业使用该项目所产生的后果，本项目均不承担责任。
3. **关联说明**：Primintel 是一个独立的社区优化分支，旨在为开发者提供更轻量、更易于云端化和商业化扩展的选择。

---

感谢所有为开源 AI 生态做出贡献的先驱项目。

---

## 📬 联系与反馈

- **技术支持**：如有 Bug 反馈、功能建议或技术交流，请提交 [Issues](https://github.com/sukya/primintel/issues)。
- **商业合作**：如果您在寻找企业级部署方案、定制化智能体开发或有商业合作意向，欢迎联系：
  - **Email**: [847879808@qq.com](mailto:847879808@qq.com)

- **开发者社区**：如果您对本项目感兴趣，欢迎关注并给予项目一个 ⭐ **Star**，您的支持是我们持续迭代的最大动力。


