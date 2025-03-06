#!/bin/bash

# 设置变量
IMAGE_NAME="yamleditor"
VERSION="1.1"
DOCKER_HUB_USERNAME="econome"

echo "开始构建Docker镜像..."

# 构建前端
cd frontend
echo "安装前端依赖..."
npm install --no-fund --no-audit
echo "构建前端..."
npm run build
cd ..

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t "$DOCKER_HUB_USERNAME/$IMAGE_NAME:latest" -t "$DOCKER_HUB_USERNAME/$IMAGE_NAME:v$VERSION" .

# 检查构建是否成功
if [ $? -ne 0 ]; then
    echo "构建失败！"
    exit 1
fi

echo "构建成功！"

# 询问是否要推送到Docker Hub
read -p "是否要推送到Docker Hub？(y/n): " PUSH_CONFIRM
if [ "${PUSH_CONFIRM,,}" = "y" ]; then
    echo "登录到Docker Hub..."
    docker login
    
    if [ $? -ne 0 ]; then
        echo "Docker Hub登录失败！"
        exit 1
    fi
    
    echo "推送latest标签..."
    docker push "$DOCKER_HUB_USERNAME/$IMAGE_NAME:latest"
    
    echo "推送版本标签..."
    docker push "$DOCKER_HUB_USERNAME/$IMAGE_NAME:v$VERSION"
    
    echo "镜像已成功推送到Docker Hub！"
else
    echo "已取消推送到Docker Hub。"
fi

echo
echo "镜像信息："
echo "- $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest"
echo "- $DOCKER_HUB_USERNAME/$IMAGE_NAME:v$VERSION"
echo
echo "本地测试命令："
echo "docker run -d --name $IMAGE_NAME -p 8000:8000 -v \$(pwd)/workspace:/app/workspace -e APP_PASSWORD=admin123 $DOCKER_HUB_USERNAME/$IMAGE_NAME:latest"
echo 