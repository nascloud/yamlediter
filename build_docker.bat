@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM 设置变量
set IMAGE_NAME=yamleditor
set VERSION=1.2
set DOCKER_HUB_USERNAME=econome

echo 开始构建Docker镜像...

REM 构建前端
cd frontend
echo 安装前端依赖...
call npm install --no-fund --no-audit
echo 构建前端...
call npm run build
cd ..

REM 构建Docker镜像
echo 构建Docker镜像...
docker build -t %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:latest -t %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:v%VERSION% .

REM 检查构建是否成功
if %errorlevel% neq 0 (
    echo 构建失败！
    exit /b 1
)

echo 构建成功！

REM 询问是否要推送到Docker Hub
set /p PUSH_CONFIRM=是否要推送到Docker Hub？(y/n): 
if /i "%PUSH_CONFIRM%"=="y" (
    echo 登录到Docker Hub...
    docker login
    
    if %errorlevel% neq 0 (
        echo Docker Hub登录失败！
        exit /b 1
    )
    
    echo 推送latest标签...
    docker push %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:latest
    
    echo 推送版本标签...
    docker push %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:v%VERSION%
    
    echo 镜像已成功推送到Docker Hub！
) else (
    echo 已取消推送到Docker Hub。
)

echo.
echo 镜像信息：
echo - %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:latest
echo - %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:v%VERSION%
echo.
echo 本地测试命令：
echo docker run -d --name %IMAGE_NAME% -p 8000:8000 -v %cd%/workspace:/app/workspace -e APP_PASSWORD=admin123 %DOCKER_HUB_USERNAME%/%IMAGE_NAME%:latest
echo.

endlocal 