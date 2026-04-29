# Primintel 阿里云部署操作手册 (Docker版)

本手册将引导您将本地改进后的 Primintel 项目“打包”并部署到阿里云 Ubuntu 服务器，替换原有的 9899 端口版本。

## 📋 部署概览
- **交付方式**：代码压缩包 (ZIP) + WinSCP 上传。
- **运行环境**：Docker + Docker Compose。
- **目标端口**：服务器 9899 -> 容器 9900。
- **状态维护**：Cookie 需要在部署后通过 Web UI 重新录入。

---

## 第一步：本地打包处理 (Local Packing)

在您的 Windows 开发机器上，执行以下操作：

1. **生成依赖文档**：确认 `requirements.txt` 已包含 `curl_cffi` 等新依赖（我已帮您更新）。
2. **清理冗余文件**：删除 `__pycache__`、`.git`、`run.log` 等不必要的文件，减小体积。
3. **压缩项目**：
   使用常用的压缩工具（如 WinRAR, 7-Zip）将 `Primintel` 文件夹整体压缩为 `Primintel.zip`。
   > [!TIP]
   > 确保 `Dockerfile.deploy` 和 `docker/docker-compose.deploy.yml` 包含在内。

---

## 第二步：文件上传 (Transfer)

1. 打开 **WinSCP**，连接到您的阿里云服务器。
2. 建议在服务器上创建一个新目录（或备份旧目录）：
   ```bash
   # 在服务器终端执行
   mkdir -p /root/primintel_new
   ```
3. 将 `Primintel.zip` 上传至 `/root/Cowagent`。

---

## 第三步：云端部署 (Server Deployment)

连接到您的阿里云 Ubuntu 终端，依次执行以下命令：

### 1. 解压并进入目录
```bash
cd /root/Cowagent
apt-get install unzip -y  # 如果没安装 unzip
unzip Primintel.zip
cd Primintel
```

### 2. 停止并移除旧容器 (如果冲突)
由于您要彻底替换 9899 端口的版本，请先停掉老容器：
```bash
# 查看正在运行的容器
docker ps
# 停止旧的 Primintel 容器 (替换 <container_id>)
docker stop <old_container_id>
docker rm <old_container_id>
```

### 3. 构建并启动新版本
使用我为您准备的专用部署文件进行构建：
```bash
# 使用指定的 compose 文件启动
docker compose -f docker/docker-compose.deploy.yml up -d --build
```

---

## 第四步：配置与验证 (Verify)

1. **防火墙检查**：确保阿里云安全组已放行 `9899` 端口。
2. **访问 UI**：在浏览器访问 `http://您的服务器IP:9899`。
3. **重新配置 Cookie**：
   - 进入 **管理 > 技能** (Skills)。
   - 找到 `bing-image-creator`，点击右侧的**齿轮图标**。
   - 录入您的必应 `_U` Cookie 并保存。
4. **功能测试**：在对话框输入“画一张赛博朋克风格的猫”，观察是否能正常调用新技能绘图。

---

## ⚠️ 常见问题排查 (Troubleshooting)

- **构建慢**：如果阿里云拉取 Python 镜像慢，可以修改 `Dockerfile.deploy` 第一行，使用阿里源镜像：`FROM registry.cn-hangzhou.aliyuncs.com/aliyun_google/python:3.10-slim-bullseye`。
- **权限问题**：如果容器日志报 `Permission Denied`，请在服务器执行 `chmod -R 777 workspace skills` (仅限调试使用)。
- **查看日志**：`docker logs -f primintel`。

---
> [!IMPORTANT]
> **备份建议**：在执行 `rm` 操作前，建议将旧版本的 `config.json` 复制出来备份，以防模型 API 密钥丢失：`cp /旧路径/config.json /root/config_backup.json`。
