# 使用多阶段构建

# 第一阶段：安装依赖
FROM python:3.9-slim AS builder

# 设置工作目录
WORKDIR /app

# 设置pip镜像源
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

# 只复制requirements.txt
COPY backend/requirements.txt .

# 安装依赖到指定目录
RUN pip install --no-cache-dir -r requirements.txt --target=/app/packages

# 第二阶段：构建最终镜像
FROM python:3.9-slim-bullseye AS final

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    PYTHONPATH=/app/packages

# 从builder阶段复制依赖
COPY --from=builder /app/packages /app/packages

# 复制应用代码
COPY backend/ ./backend/
COPY frontend/dist ./frontend/dist

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    # 创建并设置目录权限
    mkdir -p /workspace && \
    chown -R appuser:appuser /app /workspace && \
    # 清理不必要的文件
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    # 删除不必要的Python文件
    find /app/packages -type d -name "__pycache__" -exec rm -r {} + && \
    find /app/packages -type f -name "*.pyc" -delete && \
    find /app/packages -type f -name "*.pyo" -delete && \
    find /app/packages -type f -name "*.pyd" -delete

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 