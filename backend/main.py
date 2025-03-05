from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yaml
import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 加载环境变量
load_dotenv()

app = FastAPI(title="YAML编辑器API")

# 配置CORS
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,  # 从环境变量读取允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 安全配置
security = HTTPBearer()
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24  # token有效期（小时）

# 工作目录配置
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/workspace")
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "app_config.json")

def init_workspace():
    """初始化工作目录和配置"""
    try:
        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # 确保工作目录存在
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        
        # 确保历史目录存在
        history_dir = os.path.join(WORKSPACE_DIR, "history")
        os.makedirs(history_dir, exist_ok=True)
        
        # 设置目录权限（如果不是root用户）
        if os.getuid() != 0:
            os.chmod(WORKSPACE_DIR, 0o755)
            os.chmod(history_dir, 0o755)
            
        return True
    except Exception as e:
        print(f"初始化工作目录失败: {e}")
        return False

# 初始化工作目录
init_workspace()

# 挂载前端静态文件
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# 生成JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# 验证JWT token
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="登录已过期或无效，请重新登录"
        )

# 路径规范化函数
def normalize_path(path):
    """
    统一路径分隔符为斜杠(/)，方便前后端交互和跨平台兼容
    """
    return path.replace('\\', '/')

# 还原路径分隔符为系统分隔符，用于实际文件操作
def system_path(path):
    """
    将规范化的路径转换为系统路径，用于实际文件操作
    """
    return os.path.normpath(path)

# 数据模型
class FileInfo(BaseModel):
    path: str
    name: str
    isDirectory: bool
    children: Optional[List['FileInfo']] = None

class HistoryFileInfo(BaseModel):
    original_path: str
    history_path: str
    name: str
    timestamp: str
    content: Optional[str] = None

class YAMLContent(BaseModel):
    content: str

class DirectoryConfig(BaseModel):
    path: str

class FileMove(BaseModel):
    source_path: str
    target_path: str

# 读取配置
def get_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"读取配置文件错误: {e}")
    
    # 默认配置
    config = {
        "workspace_dir": normalize_path(WORKSPACE_DIR)  # 使用规范化的路径
    }
    
    # 保存默认配置
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置文件错误: {e}")
    
    return config

# 获取工作目录
def get_workspace_dir():
    return WORKSPACE_DIR  # 直接返回环境变量中的工作目录

# 获取历史文件目录
def get_history_dir():
    workspace_dir = get_workspace_dir()
    history_dir = os.path.join(workspace_dir, "history")
    
    # 确保历史目录存在
    sys_history_dir = system_path(history_dir)
    os.makedirs(sys_history_dir, exist_ok=True)
    
    # 返回规范化的路径
    return normalize_path(history_dir)

# 清理历史文件
def clean_history_files(original_file_name, limit=5):
    """
    清理指定原始文件的历史版本，只保留最近的limit个版本
    """
    try:
        history_dir = get_history_dir()
        sys_history_dir = system_path(history_dir)
        
        # 获取所有历史文件
        all_files = os.listdir(sys_history_dir)
        
        # 筛选出属于该原始文件的历史版本
        file_name_without_ext, file_ext = os.path.splitext(original_file_name)
        history_files = [f for f in all_files if f.startswith(file_name_without_ext + "_")]
        
        # 按时间戳排序（新的在前）
        history_files.sort(key=lambda x: os.path.getmtime(os.path.join(sys_history_dir, x)), reverse=True)
        
        # 删除多余的历史文件
        if len(history_files) > limit:
            for old_file in history_files[limit:]:
                try:
                    os.remove(os.path.join(sys_history_dir, old_file))
                except Exception as e:
                    print(f"删除旧历史文件失败: {old_file}, 错误: {e}")
    except Exception as e:
        print(f"清理历史文件失败: {e}")

# 保存历史文件
def save_history_file(file_path, content):
    try:
        # 获取文件名和扩展名
        file_name = os.path.basename(file_path)
        file_name_without_ext, file_ext = os.path.splitext(file_name)
        
        # 创建带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file_name = f"{file_name_without_ext}_{timestamp}{file_ext}"
        
        # 获取历史目录
        history_dir = get_history_dir()
        history_file_path = os.path.join(history_dir, history_file_name)
        
        # 保存历史文件
        with open(system_path(history_file_path), 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 清理旧的历史文件
        clean_history_files(file_name)
        
        # 返回历史文件信息
        return {
            "original_path": file_path,
            "history_path": normalize_path(os.path.join("history", history_file_name)),
            "name": history_file_name,
            "timestamp": timestamp
        }
    except Exception as e:
        print(f"保存历史文件失败: {e}")
        return None

# 获取历史文件列表
def get_history_files(file_path=None):
    """
    获取历史文件列表
    如果指定了file_path，则只返回该文件的历史版本
    否则返回所有文件的最新历史版本
    """
    history_dir = get_history_dir()
    history_files = []
    
    try:
        # 获取所有历史文件
        files = os.listdir(system_path(history_dir))
        
        if file_path:
            # 如果指定了文件路径，只获取该文件的历史版本
            file_name = os.path.basename(file_path)
            file_name_without_ext = os.path.splitext(file_name)[0]
            files = [f for f in files if f.startswith(file_name_without_ext + "_")]
        
        # 按修改时间排序
        files.sort(key=lambda x: os.path.getmtime(os.path.join(system_path(history_dir), x)), reverse=True)
        
        # 如果没有指定文件路径，对每个原始文件只保留最新的一个版本
        if not file_path:
            seen_files = set()
            filtered_files = []
            for file in files:
                original_name = "_".join(os.path.splitext(file)[0].split("_")[:-2])
                if original_name not in seen_files:
                    seen_files.add(original_name)
                    filtered_files.append(file)
            files = filtered_files
        
        for file in files:
            file_path = os.path.join(history_dir, file)
            # 解析文件名获取原始文件名和时间戳
            parts = os.path.splitext(file)[0].split('_')
            timestamp_str = parts[-2] + "_" + parts[-1] if len(parts) >= 2 else ""
            original_name = "_".join(parts[:-2]) if len(parts) >= 2 else file
            
            history_files.append(HistoryFileInfo(
                original_path=original_name,
                history_path=normalize_path(os.path.join("history", file)),
                name=file,
                timestamp=timestamp_str
            ))
        
        return history_files
    except Exception as e:
        print(f"获取历史文件列表失败: {e}")
        return []

# 设置工作目录
@app.post("/api/config/workspace")
async def set_workspace_dir(config: DirectoryConfig):
    """设置工作目录"""
    try:
        # 规范化路径
        workspace_dir = normalize_path(config.path)
        
        # 验证目录是否存在
        if not os.path.isdir(system_path(workspace_dir)):
            raise HTTPException(status_code=400, detail=f"目录不存在: {workspace_dir}")
        
        # 更新配置
        current_config = get_config()
        current_config["workspace_dir"] = workspace_dir
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_config, f, ensure_ascii=False, indent=2)
        
        return {"message": "工作目录设置成功", "path": workspace_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 获取当前工作目录
@app.get("/api/config/workspace")
async def get_current_workspace():
    """获取当前工作目录"""
    workspace_dir = get_workspace_dir()
    return {"path": workspace_dir}

# 递归获取目录结构
def get_directory_structure(dir_path, base_path):
    result = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        rel_path = os.path.relpath(item_path, base_path)
        # 规范化相对路径
        rel_path = normalize_path(rel_path)
        
        if os.path.isdir(item_path):
            # 目录
            children = get_directory_structure(item_path, base_path)
            result.append(FileInfo(
                path=rel_path,
                name=item,
                isDirectory=True,
                children=children
            ))
        elif item.endswith(('.yaml', '.yml')):
            # YAML文件
            result.append(FileInfo(
                path=rel_path,
                name=item,
                isDirectory=False
            ))
    
    # 排序：目录在前，文件在后，按名称排序
    result.sort(key=lambda x: (not x.isDirectory, x.name.lower()))
    
    return result

@app.get("/api/files")
async def list_files(search: str = "", token: dict = Depends(verify_token)):
    """获取文件列表"""
    workspace_dir = get_workspace_dir()
    sys_workspace_dir = system_path(workspace_dir)
    
    try:
        if not search:
            # 获取完整目录结构
            files = get_directory_structure(sys_workspace_dir, sys_workspace_dir)
            return files
        else:
            # 搜索文件
            files = []
            search_lower = search.lower()
            
            for root, dirs, filenames in os.walk(sys_workspace_dir):
                for filename in filenames:
                    if filename.endswith(('.yaml', '.yml')) and search_lower in filename.lower():
                        rel_path = os.path.relpath(os.path.join(root, filename), sys_workspace_dir)
                        # 规范化相对路径
                        rel_path = normalize_path(rel_path)
                        files.append(FileInfo(
                            path=rel_path,
                            name=filename,
                            isDirectory=False
                        ))
            
            return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/file/{file_path:path}")
async def read_file(file_path: str, token: dict = Depends(verify_token)):
    """读取文件内容"""
    try:
        # 规范化输入路径
        file_path = normalize_path(file_path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_file_path = system_path(os.path.join(sys_workspace_dir, file_path))
        
        # 验证文件是否在工作目录内
        if not os.path.abspath(sys_file_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=403, detail="出于安全考虑，不允许访问工作目录之外的文件")
        
        if not os.path.exists(sys_file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在：{file_path}")
        
        try:
            with open(sys_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except PermissionError:
            raise HTTPException(status_code=403, detail="没有权限读取文件，请检查文件权限设置")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码错误，请确保文件为UTF-8编码")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取文件失败：{str(e)}")
            
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")

@app.post("/api/file/{file_path:path}")
async def save_file(file_path: str, content: YAMLContent, token: dict = Depends(verify_token)):
    """保存文件内容"""
    try:
        # 验证YAML格式
        try:
            yaml.safe_load(content.content)
        except yaml.YAMLError as e:
            error_msg = str(e)
            if "found character '\\t'" in error_msg:
                error_msg = "YAML文件中不能使用制表符(Tab)，请使用空格进行缩进"
            elif "found unknown escape character" in error_msg:
                error_msg = "YAML文件中包含无效的转义字符"
            elif "could not find expected ':'" in error_msg:
                error_msg = "YAML格式错误：缺少冒号(:)，请检查键值对格式"
            elif "mapping values are not allowed here" in error_msg:
                error_msg = "YAML格式错误：缩进不正确或在不允许的位置使用了冒号"
            else:
                error_msg = f"YAML格式错误：{error_msg}"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 规范化输入路径
        file_path = normalize_path(file_path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_file_path = system_path(os.path.join(sys_workspace_dir, file_path))
        
        # 验证文件是否在工作目录内
        if not os.path.abspath(sys_file_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=403, detail="出于安全考虑，不允许访问工作目录之外的文件")
        
        # 确保目录存在
        try:
            os.makedirs(os.path.dirname(sys_file_path), exist_ok=True)
        except PermissionError:
            raise HTTPException(status_code=403, detail="没有权限创建目录，请检查文件权限设置")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"创建目录失败：{str(e)}")
        
        # 保存历史文件
        history_file = save_history_file(file_path, content.content)
        if not history_file:
            print("警告：历史文件保存失败")
        
        # 保存当前文件
        try:
            with open(sys_file_path, 'w', encoding='utf-8') as f:
                f.write(content.content)
        except PermissionError:
            raise HTTPException(status_code=403, detail="没有权限保存文件，请检查文件权限设置")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"保存文件失败：{str(e)}")
        
        return {
            "message": "文件保存成功",
            "history_file": history_file
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")

@app.get("/api/history")
async def get_history(file_path: str = None, token: dict = Depends(verify_token)):
    """获取历史文件列表"""
    try:
        history_files = get_history_files(file_path)
        return history_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{file_path:path}")
async def read_history_file(file_path: str, token: dict = Depends(verify_token)):
    """读取历史文件内容"""
    try:
        # 规范化输入路径
        file_path = normalize_path(file_path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_file_path = system_path(os.path.join(sys_workspace_dir, file_path))
        
        # 验证文件是否在工作目录内
        if not os.path.abspath(sys_file_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=400, detail="文件路径必须在工作目录内")
        
        with open(sys_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析文件名获取原始文件名和时间戳
        file_name = os.path.basename(file_path)
        parts = os.path.splitext(file_name)[0].split('_')
        timestamp_str = parts[-2] + "_" + parts[-1] if len(parts) >= 2 else ""
        
        return {
            "content": content,
            "name": file_name,
            "timestamp": timestamp_str
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/api/file/{file_path:path}")
async def delete_file(file_path: str, token: dict = Depends(verify_token)):
    """删除文件"""
    try:
        # 规范化输入路径
        file_path = normalize_path(file_path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_file_path = system_path(os.path.join(sys_workspace_dir, file_path))
        
        # 验证文件是否在工作目录内
        if not os.path.abspath(sys_file_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=403, detail="出于安全考虑，不允许访问工作目录之外的文件")
        
        if not os.path.exists(sys_file_path):
            raise HTTPException(status_code=404, detail=f"要删除的文件或目录不存在：{file_path}")
        
        try:
            if os.path.isdir(sys_file_path):
                if os.listdir(sys_file_path):
                    shutil.rmtree(sys_file_path)
                else:
                    os.rmdir(sys_file_path)
            else:
                os.remove(sys_file_path)
        except PermissionError:
            raise HTTPException(status_code=403, detail="没有权限删除文件或目录，请检查权限设置")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")
        
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")

@app.post("/api/directory")
async def create_directory(path: DirectoryConfig, token: dict = Depends(verify_token)):
    """创建目录"""
    try:
        # 规范化输入路径
        dir_path = normalize_path(path.path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_dir_path = system_path(os.path.join(sys_workspace_dir, dir_path))
        
        # 验证路径是否在工作目录内
        if not os.path.abspath(sys_dir_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=400, detail="目录路径必须在工作目录内")
        
        os.makedirs(sys_dir_path, exist_ok=True)
        return {"message": "目录创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/file/move")
async def move_file(file_move: FileMove, token: dict = Depends(verify_token)):
    """移动文件"""
    try:
        # 规范化输入路径
        source_path = normalize_path(file_move.source_path)
        target_path = normalize_path(file_move.target_path)
        workspace_dir = get_workspace_dir()
        
        # 构建系统路径用于文件操作
        sys_workspace_dir = system_path(workspace_dir)
        sys_source_path = system_path(os.path.join(sys_workspace_dir, source_path))
        sys_target_path = system_path(os.path.join(sys_workspace_dir, target_path))
        
        # 验证源路径是否在工作目录内
        if not os.path.abspath(sys_source_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=400, detail="源文件路径必须在工作目录内")
        
        # 验证目标路径是否在工作目录内
        if not os.path.abspath(sys_target_path).startswith(os.path.abspath(sys_workspace_dir)):
            raise HTTPException(status_code=400, detail="目标文件路径必须在工作目录内")
        
        # 检查源文件是否存在
        if not os.path.exists(sys_source_path):
            raise HTTPException(status_code=404, detail="源文件不存在")
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(sys_target_path), exist_ok=True)
        
        # 移动文件
        shutil.move(sys_source_path, sys_target_path)
        
        return {"message": "文件移动成功", "source": source_path, "target": target_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 认证相关模型
class LoginRequest(BaseModel):
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# 登录端点
@app.post("/api/login", response_model=Token)
async def login(request: LoginRequest):
    if request.password != APP_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="密码错误，请重试"
        )
    
    try:
        access_token = create_access_token(
            data={"sub": "user"}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="登录失败，请稍后重试"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 