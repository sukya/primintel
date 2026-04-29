# Primintel 阿里云 Docker Compose 部署指导手册

这是一份专门针对阿里云环境的纯净部署指南。我们已经为您生成了移除了所有本地测试数据、运行日志和临时缓存的纯净包 `primintel-deploy.zip`。

## 1. 准备工作

请确保您的阿里云服务器已安装必要的环境：
* **Docker**: 容器引擎
* **Docker Compose**: 容器编排工具
* **Unzip**: 解压工具 (`apt install unzip` 或 `yum install unzip`)

## 2. 上传解压部署包

将项目根目录下的 `primintel-deploy.zip` 上传到阿里云服务器（可通过 Xftp、WinSCP 或 `scp` 命令）。

```bash
# 在服务器根目录下创建项目目录并解压
mkdir -p /root/primintel
unzip primintel-deploy.zip -d /root/primintel
cd /root/primintel

# 非常重要：权限设置
# 因为 Docker 容器内部使用的是非 root 用户 (agent)，
# 您需要给 workspace 目录赋予写入权限，否则日志和生成的视频无法保存。
chmod -R 777 workspace
```

## 3. 初始化配置

为了安全起见，纯净部署包中不包含含有您私钥的 `config.json` 文件。请使用模板初始化配置：

```bash
# 复制配置模板
cp config-template.json config.json

# 使用 vim 或 nano 编辑您的 API Key 等私有配置
vim config.json

# 赋予读写权限
chmod 666 config.json
```

## 4. 启动容器服务

项目自带了针对生产环境优化的部署配置（内部已集成阿里云镜像源加速）。

```bash
# 执行一键构建并后台启动
docker compose -f docker/docker-compose.deploy.yml up -d --build
``` 

**常用运维命令：**
* 查看实时运行日志：`docker logs -f primintel-modified`
* 重启服务：`docker restart primintel-modified`
* 停止并移除服务：`docker-compose -f docker/docker-compose.deploy.yml down`

## 5. 阿里云网络安全组设置 (非常重要)

根据 `docker-compose.deploy.yml` 中的配置，Web 交互通道映射到了宿主机的 **`9899`** 端口。

要在公网访问您的 Agent 前端，您必须：
1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 找到您的 ECS 实例 -> 点击 **安全组** -> **配置规则**
3. **入方向** 手动添加一条规则：
   - 协议类型：`TCP`
   - 端口范围：`9899/9899`
   - 授权对象：`0.0.0.0/0` (允许所有公网访问，如需内网限制可指定IP)
4. 保存后即可通过浏览器访问：`http://<您的服务器公网IP>:9899`
