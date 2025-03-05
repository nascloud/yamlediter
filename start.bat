@echo off
echo ===================================
echo    YAML配置文件编辑器启动脚本
echo ===================================
echo.

REM 检查Python是否安装
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到Python，请安装Python 3.8或更高版本。
    goto :end
)

REM 检查Node.js是否安装
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到Node.js，请安装Node.js 14或更高版本。
    goto :end
)

echo [信息] 正在启动后端服务...
cd backend

REM 检查虚拟环境是否存在
if not exist venv (
    echo [信息] 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境并安装依赖
call venv\Scripts\activate
echo [信息] 安装后端依赖...
pip install -r requirements.txt

REM 启动后端服务
start cmd /k "title YAML编辑器 - 后端服务 && color 0A && call venv\Scripts\activate && uvicorn main:app --reload"

echo [信息] 等待后端服务启动...
timeout /t 3 > nul

echo [信息] 正在启动前端服务...
cd ..\frontend

REM 检查node_modules是否存在
if not exist node_modules (
    echo [信息] 安装前端依赖...
    call npm install
)

REM 启动前端服务
start cmd /k "title YAML编辑器 - 前端服务 && color 0B && npm run dev"

echo.
echo ===================================
echo    YAML配置文件编辑器已启动！
echo ===================================
echo.
echo 后端API: http://localhost:8000
echo 前端界面: http://localhost:5173
echo.
echo 按任意键打开浏览器访问应用...
pause > nul

start http://localhost:5173

:end
echo.
echo 按任意键退出...
pause > nul 