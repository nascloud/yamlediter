# YAML编辑器 Docker指南

## 功能特点

这是一个基于Web的YAML文件在线编辑器，具有以下特点：

- 🚀 在线编辑YAML文件，实时语法检查
- 📝 自动格式化和错误提示
- 🔍 文件搜索和树形浏览
- 📜 版本历史管理（保留最近5个版本）
- 🔒 JWT身份验证
- 🎯 轻量级（镜像仅277MB）
- ⚡ 支持热重载和自动恢复

## 快速开始

### 1. 准备工作目录

```bash
# 创建工作目录
mkdir workspace
```

### 2. 启动服务

#### 使用 docker-compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3'

services:
  yamleditor:
    image: econome/yamleditor:latest
    ports:
      - "8000:8000"
    environment:
      - APP_PASSWORD=your_secure_password    # 修改为安全密码
      - JWT_SECRET=your_jwt_secret          # 修改为随机密钥
      - WORKSPACE_DIR=/app/workspace
      - ALLOW_ORIGINS=*                     # 生产环境建议限制
      - TZ=Asia/Shanghai
    volumes:
      - ./workspace:/app/workspace
    user: "${UID}:${GID}"                   # 使用当前用户权限
    restart: unless-stopped
```

启动服务：

```bash
docker-compose up -d
```

#### 使用 docker run

```bash
docker run -d \
  --name yamleditor \
  -p 8000:8000 \
  -e APP_PASSWORD=your_secure_password \
  -e JWT_SECRET=your_jwt_secret \
  -e WORKSPACE_DIR=/app/workspace \
  -e ALLOW_ORIGINS=* \
  -e TZ=Asia/Shanghai \
  -v $(pwd)/workspace:/app/workspace \
  -u $(id -u):$(id -g) \
  econome/yamleditor:latest
```

## 配置说明

### 环境变量

| 变量名           | 说明     | 默认值                 | 建议       |
| ------------- | ------ | ------------------- | -------- |
| APP_PASSWORD  | 登录密码   | admin123            | 生产环境必须修改 |
| JWT_SECRET    | JWT密钥  | your_jwt_secret_key | 使用随机字符串  |
| WORKSPACE_DIR | 工作目录   | /app/workspace      | 建议保持默认   |
| ALLOW_ORIGINS | CORS配置 | *                   | 生产环境应限制  |
| TZ            | 时区设置   | Asia/Shanghai       | 按需修改     |

### 用户权限配置

支持两种权限配置方式：

1. **动态用户权限**（推荐）：
   
   ```yaml
   # docker-compose.yml
   user: "${UID}:${GID}"
   ```

2. **固定用户权限**：
   
   ```yaml
   # docker-compose.yml
   user: "1000:1000"
   ```

### 权限问题处理

如果遇到权限问题，请按以下步骤排查：

1. 检查权限：
   
   ```bash
   # 查看容器用户
   docker exec yamleditor id
   ```

# 查看目录权限

ls -la workspace/

```
2. 修复权限：
```bash
# 使用当前用户
sudo chown -R $(id -u):$(id -g) workspace/

# 或使用固定用户
sudo chown -R 1000:1000 workspace/
```

## 生产环境建议

1. **安全配置**：
   
   - 使用强密码和随机JWT密钥
   - 限制CORS来源
   - 使用固定的非root用户
   - 配置安全的网络环境

2. **数据管理**：
   
   - 定期备份workspace目录
   - 监控磁盘使用情况
   - 设置日志轮转策略

3. **性能优化**：
   
   - 适当调整容器资源限制
   - 监控容器状态
   - 根据需求调整历史版本保留数量

## 版本信息

- latest: 最新版本
- v1.1: 优化版本（减小体积，增加安全性）
- v1.0: 初始版本

## 问题反馈

如有问题或建议，请访问项目GitHub仓库提交issue。 