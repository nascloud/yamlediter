# Docker自动化构建指南

本项目使用GitHub Actions实现Docker镜像的自动化构建和推送。

## GitHub Actions Workflow

### 触发条件

- 当推送到`main`分支时
- 当创建新的Git标签（以`v`开头）时
- 当创建Pull Request到`main`分支时

### 构建流程

1. 检出代码
2. 设置Node.js环境
3. 安装前端依赖并构建前端应用
4. 设置Docker Buildx
5. 登录DockerHub（仅在非PR时）
6. 提取Docker镜像元数据（标签、标签等）
7. 构建并推送Docker镜像

### 支持的平台

- linux/amd64
- linux/arm64

## 配置说明

### 1. GitHub Secrets配置

在GitHub仓库的Settings > Secrets and variables > Actions中添加以下Secrets：

| Secret名称 | 说明 | 获取方式 |
|------------|------|----------|
| DOCKER_HUB_USERNAME | DockerHub用户名 | 在DockerHub账户设置中查看 |
| DOCKER_HUB_ACCESS_TOKEN | DockerHub访问令牌 | 在DockerHub账户安全设置中创建 |

### 2. 创建DockerHub访问令牌

1. 登录DockerHub
2. 进入账户设置（Account Settings）
3. 选择"Security"选项卡
4. 点击"New Access Token"
5. 输入令牌描述（如：GitHub Actions）
6. 选择适当的权限（推荐选择"Read & Write"）
7. 复制生成的令牌并添加到GitHub Secrets中

## 镜像标签策略

根据不同的触发条件，镜像会自动打上相应的标签：

- **分支推送**：`branch-<分支名>`
- **Pull Request**：`pr-<PR号>`
- **版本标签**：遵循语义化版本规则
  - Git标签`v1.2.3`会生成标签`1.2.3`、`1.2`、`1`
- **最新版本**：`latest` 和版本标签（在推送到main分支或创建Git标签时）

## 本地测试

要本地测试GitHub Actions workflow，可以使用[act](https://github.com/nektos/act)工具：

```bash
# 安装act
# 详细安装说明请参考：https://github.com/nektos/act#installation

# 运行workflow
act push -j build-and-push

# 运行特定事件的workflow
act pull_request -j build-and-push
```

## 故障排除

### 构建失败

1. 检查前端构建是否成功
2. 确认Dockerfile语法是否正确
3. 验证GitHub Secrets是否正确配置

### 推送失败

1. 检查DOCKER_HUB_USERNAME和DOCKER_HUB_ACCESS_TOKEN是否正确
2. 确认DockerHub令牌是否有推送权限
3. 验证DockerHub仓库是否存在

### 权限问题

1. 确保GitHub Actions有足够权限访问仓库
2. 检查DockerHub账户权限设置

## 最佳实践

1. **安全**：定期轮换DockerHub访问令牌
2. **版本管理**：使用语义化版本控制
3. **标签策略**：合理使用标签以便于镜像管理
4. **构建缓存**：利用GitHub Actions缓存加速构建过程