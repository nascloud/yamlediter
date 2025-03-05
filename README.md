# YAML编辑器

一个基于Web的YAML文件在线编辑器，支持语法高亮、格式检查、版本历史等功能。

## 功能特点

- 🚀 在线编辑YAML文件
- ✨ 实时语法检查和错误提示
- 📝 自动格式化
- 🔍 文件搜索功能
- 📂 文件树浏览
- 📜 版本历史管理（保留最近5个版本）
- 🔒 基于JWT的身份验证
- 🎨 美观的界面设计

## 快速开始

### 使用 docker run

```bash
# 创建工作目录
mkdir workspace

# 创建配置文件
cat > docker.env << EOF
APP_PASSWORD=your_password
JWT_SECRET=your_secret_key
WORKSPACE_DIR=/workspace
ALLOW_ORIGINS=*
TZ=Asia/Shanghai
EOF

# 运行容器
docker run -d \
  --name yamleditor \
  -p 8000:8000 \
  --env-file docker.env \
  -v $(pwd)/workspace:/workspace \
  econome/yamleditor:latest
```

### 使用 docker-compose

1. 创建 `docker-compose.yml`：

```yaml
version: '3'

services:
  yamleditor:
    image: econome/yamleditor:latest
    ports:
      - "8000:8000"
    env_file:
      - docker.env
    volumes:
      - ./workspace:/workspace
    restart: unless-stopped
```

2. 创建 `docker.env`：

```env
APP_PASSWORD=your_password
JWT_SECRET=your_secret_key
WORKSPACE_DIR=/workspace
ALLOW_ORIGINS=*
TZ=Asia/Shanghai
```

3. 启动服务：

```bash
docker-compose up -d
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| APP_PASSWORD | 登录密码 | admin123 |
| JWT_SECRET | JWT密钥 | your_jwt_secret_key |
| WORKSPACE_DIR | 工作目录路径 | /workspace |
| ALLOW_ORIGINS | CORS允许的源 | * |
| TZ | 时区设置 | Asia/Shanghai |

## 版本说明

- latest: 最新版本
- v1.1: 优化版本（减小镜像体积，增加安全性）
- v1.0: 初始版本

## 安全说明

- 使用非root用户运行
- 支持JWT身份验证
- 文件操作限制在工作目录内
- 定期清理历史文件

## 目录结构

```
/workspace/          # 工作目录（需要挂载）
  ├── your_files/   # 您的YAML文件
  └── history/      # 历史版本文件
```

## 使用建议

1. 生产环境使用建议：
   - 修改默认密码
   - 设置强密钥
   - 限制CORS源
   - 使用安全的网络配置

2. 数据管理：
   - 定期备份workspace目录
   - 监控磁盘使用情况
   - 及时清理不需要的历史文件

## 技术栈

- 后端：Python FastAPI
- 前端：Vue.js
- 编辑器：Monaco Editor
- 容器：Docker

## 问题反馈

如有问题或建议，请访问项目GitHub仓库提交issue。

## 许可证

MIT License 