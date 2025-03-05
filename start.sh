#!/bin/bash

echo "==================================="
echo "    YAML配置文件编辑器启动脚本"
echo "==================================="
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python，请安装Python 3.8或更高版本。"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到Node.js，请安装Node.js 14或更高版本。"
    exit 1
fi

echo "[信息] 正在启动后端服务..."
cd backend || exit

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[信息] 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
echo "[信息] 安装后端依赖..."
pip install -r requirements.txt

# 启动后端服务（后台运行）
echo "[信息] 启动后端服务..."
gnome-terminal --title="YAML编辑器 - 后端服务" -- bash -c "source venv/bin/activate && uvicorn main:app --reload" &
# 如果gnome-terminal不可用，尝试其他终端
if [ $? -ne 0 ]; then
    xterm -title "YAML编辑器 - 后端服务" -e "source venv/bin/activate && uvicorn main:app --reload" &
    # 如果xterm也不可用，尝试直接在后台运行
    if [ $? -ne 0 ]; then
        echo "[警告] 无法打开新终端窗口，在后台启动后端服务..."
        source venv/bin/activate && uvicorn main:app --reload > backend.log 2>&1 &
    fi
fi

echo "[信息] 等待后端服务启动..."
sleep 3

echo "[信息] 正在启动前端服务..."
cd ../frontend || exit

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "[信息] 安装前端依赖..."
    npm install
fi

# 启动前端服务（后台运行）
echo "[信息] 启动前端服务..."
gnome-terminal --title="YAML编辑器 - 前端服务" -- bash -c "npm run dev" &
# 如果gnome-terminal不可用，尝试其他终端
if [ $? -ne 0 ]; then
    xterm -title "YAML编辑器 - 前端服务" -e "npm run dev" &
    # 如果xterm也不可用，尝试直接在后台运行
    if [ $? -ne 0 ]; then
        echo "[警告] 无法打开新终端窗口，在后台启动前端服务..."
        npm run dev > frontend.log 2>&1 &
    fi
fi

echo ""
echo "==================================="
echo "    YAML配置文件编辑器已启动！"
echo "==================================="
echo ""
echo "后端API: http://localhost:8000"
echo "前端界面: http://localhost:5173"
echo ""
echo "按Enter键打开浏览器访问应用..."
read -r

# 尝试使用不同的浏览器打开应用
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5173
elif command -v google-chrome &> /dev/null; then
    google-chrome http://localhost:5173
elif command -v firefox &> /dev/null; then
    firefox http://localhost:5173
else
    echo "[警告] 无法自动打开浏览器，请手动访问 http://localhost:5173"
fi

echo ""
echo "服务正在后台运行。要停止服务，请关闭终端窗口或使用 kill 命令。"
echo "按Ctrl+C退出此脚本..." 