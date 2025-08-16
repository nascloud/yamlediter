# GitHub Actions Workflow测试指南

本指南说明如何测试Docker自动化构建的GitHub Actions workflow。

## 测试前准备

1. 确保已完成DockerHub认证配置
2. 确保代码已推送到GitHub仓库

## 测试方法

### 1. 手动触发测试workflow

项目中包含一个测试workflow文件 `.github/workflows/test-docker-build.yml`，可以通过以下步骤手动触发：

1. 进入GitHub仓库页面
2. 点击"Actions"选项卡
3. 在左侧workflow列表中选择"Test Docker Build"
4. 点击"Run workflow"按钮
5. 选择要运行的分支（通常是main分支）
6. 点击"Run workflow"确认

### 2. 通过推送代码触发

#### 测试分支推送
1. 创建新的分支：
   ```bash
   git checkout -b test-build
   ```
2. 进行一些小的修改并提交：
   ```bash
   git commit -am "Test build"
   ```
3. 推送到GitHub：
   ```bash
   git push origin test-build
   ```

#### 测试标签推送
1. 创建轻量级标签：
   ```bash
   git tag v1.0.0-test
   ```
2. 推送标签到GitHub：
   ```bash
   git push origin v1.0.0-test
   ```

### 3. 创建Pull Request

1. 创建新分支并进行修改：
   ```bash
   git checkout -b feature/test
   # 进行一些修改
   git commit -am "Test PR"
   git push origin feature/test
   ```
2. 在GitHub上创建Pull Request

## 验证结果

### 1. 检查GitHub Actions运行状态

1. 进入GitHub仓库的"Actions"选项卡
2. 查看相关workflow的运行状态
3. 点击具体的运行记录查看详细日志

### 2. 检查DockerHub镜像

1. 登录到DockerHub
2. 进入你的仓库页面
3. 查看是否有新构建的镜像标签

### 3. 本地测试镜像

如果workflow成功构建并推送了镜像，可以在本地测试：

```bash
# 拉取镜像
docker pull econome/yamleditor:test

# 运行容器
docker run -d --name test-yamleditor -p 8000:8000 econome/yamleditor:test
```

## 常见问题排查

### Workflow失败

1. 检查日志中的错误信息
2. 确认前端构建是否成功
3. 验证Dockerfile语法是否正确
4. 检查GitHub Secrets配置是否正确

### 镜像未推送

1. 确认是否是Pull Request触发（PR不会推送镜像）
2. 检查DockerHub认证配置
3. 验证DockerHub仓库是否存在

## 清理测试资源

测试完成后，记得清理相关资源：

1. 删除测试标签：
   ```bash
   git tag -d v1.0.0-test
   git push origin :v1.0.0-test
   ```

2. 删除测试分支：
   ```bash
   git branch -d test-build
   git push origin --delete test-build
   ```

3. 在DockerHub中删除测试镜像标签