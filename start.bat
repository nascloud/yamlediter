@echo off
chcp 65001 > nul
title YAML配置文件编辑器

REM 设置工作目录为脚本所在目录
cd /d "%~dp0"

echo 检查项目结构...

REM 检查后端目录
if not exist "backend" (
    echo 错误: 后端目录不存在
    pause
    exit /b 1
)

REM 检查前端目录
if not exist "frontend" (
    echo 错误: 前端目录不存在
    pause
    exit /b 1
)

REM 检查关键文件
if not exist "backend\main.py" (
    echo 错误: 后端主程序不存在
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo 错误: 前端配置文件不存在
    pause
    exit /b 1
)

echo 启动后端服务...

REM 启动后端（使用已有的启动脚本）
if exist "start_backend.bat" (
    start "YAML编辑器-后端" cmd /c start_backend.bat
) else (
    REM 创建后端启动脚本
    echo @echo off > start_backend.bat
    echo cd /d "%~dp0backend" >> start_backend.bat
    echo if not exist "venv" python -m venv venv >> start_backend.bat
    echo call venv\Scripts\activate.bat >> start_backend.bat
    echo pip install -r requirements.txt >> start_backend.bat
    echo python -m uvicorn main:app --reload --port=8000 >> start_backend.bat
    start "YAML编辑器-后端" cmd /c start_backend.bat
)

echo 启动前端服务...

REM 启动前端（使用已有的启动脚本）
if exist "start_frontend.bat" (
    start "YAML编辑器-前端" cmd /c start_frontend.bat
) else (
    REM 创建前端启动脚本
    echo @echo off > start_frontend.bat
    echo cd /d "%~dp0frontend" >> start_frontend.bat
    echo if not exist "node_modules" npm install --no-fund --no-audit >> start_frontend.bat
    echo npm run dev >> start_frontend.bat
    start "YAML编辑器-前端" cmd /c start_frontend.bat
)

echo.
echo 服务已启动：
echo - 后端: http://localhost:8000
echo - 前端: http://localhost:5173
echo.
echo 按任意键打开前端页面...
pause > nul
start http://localhost:5173

exit /b 0