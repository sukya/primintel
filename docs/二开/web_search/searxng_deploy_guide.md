# SearXNG 国内优化部署手册 (Aliyun/Docker)

本手册专为阿里云 2C2G 环境设计，旨在通过 Docker 容器化部署一个针对中国网络优化的 SearXNG 实例，并实现配置文件的宿主机持久化挂载。

---

## 🛠️ 1. 准备目录结构
在宿主机（阿里云服务器）上，建议创建一个独立的目录来存放 SearXNG 的配置：

```bash
mkdir -p /searxng
cd /searxng
```

---

## 📄 2. 创建 `settings.yml` (核心配置)
在 `/searxng` 目录下创建 `settings.yml` 文件。此配置已根据您的需求：
- **开启**：百度、必应中国、搜狗、360 搜索。
- **禁用**：Google、YouTube、维基百科（避免国内请求超时导致整体变慢）。

```yaml
# SearXNG 基础配置
use_default_settings: true

server:
  port: 8080
  bind_address: "0.0.0.0"
  secret_key: "3f5901447c7f4e0f964693b6807635b1"
  limiter: false  # 关闭访问限制，避免API调用失败

search:
  safe_search: 0
  autocomplete: "bing"
  formats:
    - html

# 只启用国内引擎，全部用 disabled: false
engines:
  - name: baidu
    engine: baidu
    shortcut: bd
    disabled: false
  - name: bing
    engine: bing
    shortcut: bi
    disabled: false
    locale: zh-CN
  - name: sogou
    engine: sogou
    shortcut: sg
    disabled: false
  - name: qh360
    engine: qh360
    shortcut: 360
    disabled: false

  # 强制禁用所有境外引擎（兜底）
  - name: google
    engine: google
    disabled: true
  - name: wikipedia
    engine: wikipedia
    disabled: true
  - name: youtube
    engine: youtube
    disabled: true
  - name: duckduckgo
    engine: duckduckgo
    disabled: true
  - name: brave
    engine: brave
    disabled: true
  - name: startpage
    engine: startpage
    disabled: true
  - name: karmasearch
    engine: karmasearch
    disabled: true
```

---

## 🐳 3. 创建 `docker-compose.yml`
在同一目录下创建 `docker-compose.yml`，将配置文件挂载到容器内部：

```yaml
version: '3.7'

services:
  searxng:
    container_name: searxng
    image: searxng/searxng:latest
    restart: always
    networks:
      - searxng_net
    ports:
      - "8080:8080"
    volumes:
      - ./settings.yml:/etc/searxng/settings.yml:ro # 挂载宿主机配置，只读模式
    environment:
      - SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  searxng_net:
```

---

## 🚀 4. 启动与验证
1.  **启动容器**：
    ```bash
    docker-compose up -d
    ```
2.  **验证访问**：
    打开浏览器访问 `http://你的服务器IP:8080`，测试搜索“苏州”检查是否走的是百度/搜狗的结果。

---

## 🔗 5. 在 Primintel 中配置
部署完成后，请修改 Primintel 的 `config.json`：

```json
{
  "searxng_url": "http://localhost:8080/",
  "search_region": "CN"
}
```

---

## 🌍 6. 海外部署与架构简化 (Plan A)
在 Primintel 的最新版本中，我们已经移除了对本地 DuckDuckGo 库的直接依赖，转而采用 **统一的 SearXNG 接口** 进行所有免费搜索。

### 为什么这样做？
- **架构解耦**：Primintel 不再需要处理复杂的反爬逻辑，全部交给专业的 SearXNG 处理。
- **跨环境统一**：
    - **国内部署**：配置 `search_region: CN`，SearXNG 开启百度/搜狗。
    - **海外部署**：配置 `search_region: Global`，SearXNG 开启 Google/DDG。
- **配置即效果**：只需修改 SearXNG 的 `settings.yml` 即可增减引擎，无需修改 Primintel 代码。

### 海外部署建议
如果您在海外服务器部署 SearXNG，请在 `settings.yml` 中：
1. **启用**：`google` (建议首选), `duckduckgo`, `wikipedia`, `bing`。
2. **禁用**：国内专用的 `baidu`, `sogou` (海外环境访问这些可能受限)。
