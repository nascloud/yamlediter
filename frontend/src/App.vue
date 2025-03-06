<template>
  <div class="app-container" :class="{ 'dark-mode': isDarkMode }">
    <!-- 登录对话框 -->
    <el-dialog
      v-model="loginDialogVisible"
      title="登录"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
      class="login-dialog"
    >
      <div v-if="loginError" class="login-error-message">
        <el-alert
          :title="loginError"
          type="error"
          show-icon
          :closable="false"
        />
      </div>
      <el-form :model="loginForm" @submit.prevent="login">
        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            @keyup.enter="login"
            :disabled="isLoggingIn"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="login" :loading="isLoggingIn">
            {{ isLoggingIn ? '登录中...' : '登录' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 顶部标题栏 -->
    <header class="header">
      <div class="header-left">
        <h1>YAML配置文件编辑器</h1>
      </div>
      <div class="header-right">
        <el-tooltip content="设置工作目录" placement="bottom">
          <el-button @click="openWorkspaceDialog" circle>
            <el-icon><Folder /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip :content="isDarkMode ? '切换到浅色模式' : '切换到深色模式'" placement="bottom">
          <el-button @click="toggleDarkMode" circle>
            <el-icon><component :is="isDarkMode ? 'Sunny' : 'Moon'" /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </header>

    <div class="main-content">
      <!-- 左侧面板 -->
      <aside class="sidebar">
        <!-- 工作目录信息 -->
        <div class="workspace-info">
          <div class="workspace-title">
            <el-icon><FolderOpened /></el-icon>
            <span>工作目录</span>
          </div>
          <div class="workspace-path">{{ workspacePath }}</div>
        </div>

        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button-group>
            <el-button type="primary" @click="createNewFile" size="small">
              <el-icon><DocumentAdd /></el-icon> 新建文件
            </el-button>
            <el-button type="primary" @click="createNewDirectory" size="small">
              <el-icon><FolderAdd /></el-icon> 新建目录
            </el-button>
          </el-button-group>
          <el-button type="danger" @click="deleteCurrentFile" size="small">
            <el-icon><Delete /></el-icon> 删除
          </el-button>
        </div>

        <!-- 搜索框 -->
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索文件..."
            clearable
            @input="refreshFileList"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 文件树 -->
        <div class="file-tree">
          <el-tree
            ref="fileTreeRef"
            :data="fileList"
            :props="defaultProps"
            @node-click="handleFileSelect"
            expand-on-click-node="false"
            node-key="path"
            :default-expanded-keys="expandedKeys"
            highlight-current="true"
            indent="12"
            draggable
            @node-drag-start="handleDragStart"
            @node-drag-enter="handleDragEnter"
            @node-drag-leave="handleDragLeave"
            @node-drag-over="handleDragOver"
            @node-drag-end="handleDragEnd"
            @node-drop="handleDrop"
            :allow-drop="allowDrop"
            :allow-drag="allowDrag"
          >
            <template #default="{ node, data }">
              <div 
                class="custom-tree-node"
                @contextmenu.prevent="showContextMenu($event, node, data)"
              >
                <span class="node-icon">
                  <el-icon v-if="data.isDirectory && isExpanded(node)"><FolderOpened /></el-icon>
                  <el-icon v-else-if="data.isDirectory"><Folder /></el-icon>
                  <el-icon v-else><Document /></el-icon>
                </span>
                <span class="node-label">{{ node.label }}</span>
              </div>
            </template>
          </el-tree>
          
          <!-- 右键菜单 -->
          <div 
            v-show="contextMenuVisible" 
            class="context-menu"
            :style="{ top: contextMenuTop + 'px', left: contextMenuLeft + 'px' }"
          >
            <div v-if="contextMenuNode && contextMenuNode.isDirectory" class="context-menu-item" @click="createFileInDirectory(contextMenuNode)">
              <el-icon><DocumentAdd /></el-icon>
              <span>新建文件</span>
            </div>
            <div v-if="contextMenuNode && contextMenuNode.isDirectory" class="context-menu-item" @click="createDirectoryInDirectory(contextMenuNode)">
              <el-icon><FolderAdd /></el-icon>
              <span>新建文件夹</span>
            </div>
            <div class="context-menu-item" @click="deleteContextMenuNode">
              <el-icon><Delete /></el-icon>
              <span>删除</span>
            </div>
          </div>
        </div>

        <!-- 历史记录 -->
        <div class="history">
          <div class="history-title">
            <el-icon><Timer /></el-icon>
            <span>最近文件</span>
          </div>
          <el-scrollbar height="150px">
            <div class="history-list">
              <div 
                v-for="file in recentFiles" 
                :key="file.path" 
                @click="handleRecentFileClick(file)"
                class="history-item"
              >
                <div class="history-item-content">
                  <el-icon><Document /></el-icon>
                  <span class="history-name">{{ file.name }}</span>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>

        <!-- 历史文件 -->
        <div class="history">
          <div class="history-title">
            <el-icon><Clock /></el-icon>
            <span>历史版本</span>
          </div>
          <el-scrollbar height="150px">
            <div class="history-list">
              <div 
                v-for="file in historyFiles" 
                :key="file.history_path" 
                @click="handleHistoryFileClick(file)"
                class="history-item"
              >
                <div class="history-item-content">
                  <el-icon><DocumentCopy /></el-icon>
                  <span class="history-name">{{ formatHistoryFileName(file.name) }}</span>
                </div>
                <span class="history-time">{{ formatTimestamp(file.timestamp) }}</span>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </aside>

      <!-- 右侧编辑区 -->
      <main class="editor-area">
        <!-- 编辑器工具栏 -->
        <div class="editor-toolbar">
          <div class="current-file">
            <el-icon v-if="currentFile"><Document /></el-icon>
            <span>{{ currentFile?.name || '无文件' }}</span>
          </div>
          <div class="toolbar-actions">
            <el-button-group>
              <el-button type="primary" @click="saveFile" :disabled="!currentFile">
                <el-icon><Check /></el-icon> 保存
              </el-button>
              <el-button @click="exportFile" :disabled="!currentFile">
                <el-icon><Download /></el-icon> 导出
              </el-button>
            </el-button-group>
          </div>
        </div>

        <!-- YAML编辑器 -->
        <div class="monaco-container" ref="editorContainer"></div>

        <!-- 状态栏 -->
        <div class="status-bar">
          <div class="status-item">
            <el-icon><InfoFilled /></el-icon>
            <span>YAML</span>
          </div>
          <div class="status-item" v-if="currentFile">
            <el-icon><Edit /></el-icon>
            <span>{{ lastSaved }}</span>
          </div>
          <div class="status-item" v-if="currentFile">
            <el-icon><Clock /></el-icon>
            <span>{{ historyFiles.length }}个历史版本</span>
          </div>
        </div>
      </main>
    </div>

    <!-- 设置工作目录对话框 -->
    <el-dialog
      v-model="workspaceDialogVisible"
      title="设置工作目录"
      width="500px"
    >
      <el-form :model="workspaceForm" label-width="100px">
        <el-form-item label="目录路径">
          <el-input v-model="workspaceForm.path" placeholder="请输入本地目录的完整路径"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="workspaceDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="setWorkspaceDir">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新建目录对话框 -->
    <el-dialog
      v-model="newDirDialogVisible"
      title="新建目录"
      width="500px"
    >
      <el-form :model="newDirForm" label-width="100px">
        <el-form-item label="目录名称">
          <el-input v-model="newDirForm.name" placeholder="请输入目录名称"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="newDirDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmCreateDirectory">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 原有内容，添加v-if控制显示 -->
    <template v-if="isAuthenticated">
      <!-- 原有的应用内容 -->
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as monaco from 'monaco-editor'
import { useElementSize } from '@vueuse/core'

// 类型定义
interface HistoryFileInfo {
  original_path: string
  history_path: string
  name: string
  timestamp: string
  content?: string
}

interface FileInfo {
  path: string
  name: string
  isDirectory: boolean
  children?: FileInfo[]
}

// 状态定义
const searchQuery = ref('')
const fileList = ref<FileInfo[]>([])
const currentFile = ref<FileInfo | null>(null)
const editorContent = ref('')
const recentFiles = ref<FileInfo[]>([])
const expandedKeys = ref<string[]>([])
const workspacePath = ref('')
const lastSaved = ref('未保存')
const isDarkMode = ref(true)

// 文件树引用
const fileTreeRef = ref(null)

// 右键菜单状态
const contextMenuVisible = ref(false)
const contextMenuTop = ref(0)
const contextMenuLeft = ref(0)
const contextMenuNode = ref<FileInfo | null>(null)

// 对话框状态
const workspaceDialogVisible = ref(false)
const workspaceForm = ref({ path: '' })
const newDirDialogVisible = ref(false)
const newDirForm = ref({ name: '', parentPath: '' })
const newFileDialogVisible = ref(false)
const newFileForm = ref({ name: '', parentPath: '' })

// 历史文件
const historyFiles = ref<HistoryFileInfo[]>([])

const defaultProps = {
  children: 'children',
  label: 'name'
}

// 编辑器引用
const editorContainer = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

// API调用
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

// 统一路径分隔符
const normalizePath = (path: string) => {
  return path.replace(/\\/g, '/')
}

const isAuthenticated = ref(false)
const loginDialogVisible = ref(true)
const loginForm = ref({
  password: ''
})
const isLoggingIn = ref(false)
const loginError = ref('')

// 登录方法
const login = async () => {
  if (!loginForm.value.password.trim()) {
    loginError.value = '请输入密码'
    return
  }
  
  isLoggingIn.value = true
  loginError.value = ''
  
  try {
    const response = await fetch(`${apiBaseUrl}/api/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ password: loginForm.value.password })
    })
    
    if (!response.ok) {
      throw new Error('登录失败')
    }
    
    const data = await response.json()
    localStorage.setItem('token', data.access_token)
    isAuthenticated.value = true
    loginDialogVisible.value = false
    
    // 登录成功后初始化应用
    await initializeApp()
  } catch (error) {
    console.error('登录失败:', error)
    loginError.value = '密码错误，请重试'
    loginForm.value.password = '' // 清空密码输入框
  } finally {
    isLoggingIn.value = false
  }
}

// 初始化应用
const initializeApp = async () => {
  try {
    // 初始化编辑器
    nextTick(() => {
      initEditor()
    })
    
    // 加载工作目录信息
    await loadWorkspaceInfo()
    
    // 刷新文件列表
    await refreshFileList()
    
    // 加载历史文件列表
    await loadHistoryFiles()
    
    ElMessage.success('初始化完成')
  } catch (error) {
    console.error('初始化失败:', error)
    ElMessage.error('应用初始化失败')
  }
}

// 修改api对象中的所有方法，添加认证头
const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
}

// 处理API响应的通用函数
const handleApiResponse = async (response: Response, errorMessage: string) => {
  if (response.status === 401) {
    // 认证失败，显示登录对话框
    ElMessage.error('认证已过期，请重新登录')
    isAuthenticated.value = false
    loginDialogVisible.value = true
    loginError.value = '认证已过期，请重新登录'
    localStorage.removeItem('token') // 清除无效的token
    throw { status: 401, message: '认证已过期，请重新登录' }
  }
  
  if (!response.ok) {
    throw { status: response.status, message: `${errorMessage}: ${response.status}` }
  }
  
  return await response.json()
}

const api = {
  async listFiles(search = '') {
    const response = await fetch(`${apiBaseUrl}/api/files?search=${search}`, {
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '获取文件列表失败')
  },

  async readFile(path: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/file/${path}`, {
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '读取文件失败')
  },

  async saveFile(path: string, content: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/file/${path}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ content })
    })
    return handleApiResponse(response, '保存文件失败')
  },

  async deleteFile(path: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/file/${path}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '删除失败')
  },

  async getWorkspaceDir() {
    const response = await fetch(`${apiBaseUrl}/api/config/workspace`, {
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '获取工作目录失败')
  },

  async setWorkspaceDir(path: string) {
    const response = await fetch(`${apiBaseUrl}/api/config/workspace`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ path })
    })
    return handleApiResponse(response, '设置工作目录失败')
  },

  async createDirectory(path: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/directory`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ path })
    })
    return handleApiResponse(response, '创建目录失败')
  },
  
  async moveFile(sourcePath: string, targetPath: string) {
    sourcePath = normalizePath(sourcePath)
    targetPath = normalizePath(targetPath)
    const response = await fetch(`${apiBaseUrl}/api/file/move`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ source_path: sourcePath, target_path: targetPath })
    })
    return handleApiResponse(response, '移动文件失败')
  },

  async fileExists(path: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/file/${path}`, {
      headers: getAuthHeaders()
    })
    return response.ok
  },

  async getHistoryFiles() {
    const response = await fetch(`${apiBaseUrl}/api/history`, {
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '获取历史文件失败')
  },

  async readHistoryFile(path: string) {
    path = normalizePath(path)
    const response = await fetch(`${apiBaseUrl}/api/history/${path}`, {
      headers: getAuthHeaders()
    })
    return handleApiResponse(response, '读取历史文件失败')
  },
}

// 初始化编辑器
const initEditor = () => {
  if (editorContainer.value) {
    // 定义YAML语言
    monaco.languages.register({ id: 'yaml' })
    
    // 创建编辑器
    editor = monaco.editor.create(editorContainer.value, {
      value: '# 请选择或创建YAML文件',
      language: 'yaml',
      theme: isDarkMode.value ? 'vs-dark' : 'vs',
      automaticLayout: true,
      minimap: { enabled: false },
      fontSize: 14,
      lineHeight: 21,
      scrollBeyondLastLine: false,
      renderLineHighlight: 'all',
      cursorBlinking: 'smooth',
      cursorSmoothCaretAnimation: 'on',
      smoothScrolling: true,
      roundedSelection: true,
      padding: { top: 10 }
    })
    
    // 监听编辑器内容变化
    editor.onDidChangeModelContent(() => {
      if (editor) {
        editorContent.value = editor.getValue()
      }
    })
  }
}

// 更新编辑器主题
const updateEditorTheme = () => {
  if (editor) {
    editor.updateOptions({
      theme: isDarkMode.value ? 'vs-dark' : 'vs'
    })
  }
}

// 更新编辑器内容
const updateEditorContent = (content: string) => {
  if (editor) {
    editor.setValue(content)
  }
}

// 切换深色/浅色模式
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  updateEditorTheme()
}

// 跟踪当前选中的节点（文件或目录）
const currentSelectedNode = ref<FileInfo | null>(null)

const refreshFileList = async () => {
  try {
    fileList.value = await api.listFiles(searchQuery.value)
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  }
}

const loadWorkspaceInfo = async () => {
  try {
    const result = await api.getWorkspaceDir()
    workspacePath.value = result.path
  } catch (error) {
    console.error('获取工作目录失败:', error)
    ElMessage.error('获取工作目录失败')
  }
}

const handleFileSelect = async (file: FileInfo) => {
  // 更新当前选中的节点
  currentSelectedNode.value = file
  
  if (file.isDirectory) {
    // 如果是目录，展开/折叠
    const key = file.path
    if (expandedKeys.value.includes(key)) {
      expandedKeys.value = expandedKeys.value.filter(k => k !== key)
    } else {
      expandedKeys.value.push(key)
    }
    return
  }
  
  try {
    currentFile.value = file
    const { content } = await api.readFile(file.path)
    editorContent.value = content
    updateEditorContent(content)
    updateRecentFiles(file)
    lastSaved.value = '刚刚加载'
  } catch (error) {
    console.error('读取文件失败:', error)
    ElMessage.error('读取文件失败')
  }
}

const handleRecentFileClick = async (file: FileInfo) => {
  try {
    currentFile.value = file
    const { content } = await api.readFile(file.path)
    editorContent.value = content
    updateEditorContent(content)
    lastSaved.value = '刚刚加载'
  } catch (error) {
    console.error('读取文件失败:', error)
    ElMessage.error('读取文件失败')
  }
}

const updateRecentFiles = (file: FileInfo) => {
  // 移除已存在的相同文件
  recentFiles.value = recentFiles.value.filter(f => f.path !== file.path)
  
  // 添加到最前面
  recentFiles.value.unshift(file)
  
  // 只保留最近的5个文件
  if (recentFiles.value.length > 5) {
    recentFiles.value = recentFiles.value.slice(0, 5)
  }
}

const saveFile = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先选择一个文件')
    return
  }
  
  // 如果是历史文件，提示用户另存为
  if (currentFile.value.isHistoryFile) {
    ElMessage.warning('历史文件不能直接保存，请另存为新文件')
    return
  }
  
  try {
    const result = await api.saveFile(currentFile.value.path, editorContent.value)
    ElMessage.success('保存成功')
    lastSaved.value = '刚刚保存'
    
    // 刷新文件列表，确保历史文件夹显示
    await refreshFileList()
    
    // 刷新历史文件列表
    await loadHistoryFiles()
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(`保存失败: ${error.message}`)
  }
}

const createNewFile = async () => {
  try {
    // 确定文件应该创建在哪个目录
    let parentPath = ''
    let dialogTitle = '新建文件'
    
    // 如果当前选中了一个目录，则在该目录下创建文件
    if (currentSelectedNode.value && currentSelectedNode.value.isDirectory) {
      parentPath = normalizePath(currentSelectedNode.value.path + '/')
      dialogTitle = `在 ${currentSelectedNode.value.name} 中新建文件`
    }
    
    const fileName = await ElMessageBox.prompt('请输入文件名', dialogTitle, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^[a-zA-Z0-9_\-\.]+\.ya?ml$/,
      inputErrorMessage: '文件名必须以.yml或.yaml结尾'
    })
    
    const filePath = normalizePath(parentPath + fileName.value)
    
    // 检查文件是否已存在
    const fileExists = await checkFileExists(filePath)
    if (fileExists) {
      try {
        await ElMessageBox.confirm(
          `路径 "${filePath}" 已存在文件，是否覆盖？`,
          '文件已存在',
          {
            confirmButtonText: '覆盖',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        // 用户点击了覆盖，继续执行
      } catch (error) {
        // 用户取消了覆盖操作
        return
      }
    }
    
    const newFile = {
      path: filePath,
      name: fileName.value,
      isDirectory: false
    }
    
    currentFile.value = newFile
    editorContent.value = '# 新建YAML文件\n'
    updateEditorContent(editorContent.value)
    await saveFile()
    await refreshFileList()
    updateRecentFiles(newFile)
    
    // 如果在目录中创建，确保该目录展开
    if (parentPath && !expandedKeys.value.includes(parentPath.slice(0, -1))) {
      expandedKeys.value.push(parentPath.slice(0, -1))
    }
  } catch (error) {
    // 用户取消操作
    console.log('用户取消新建文件')
  }
}

const openWorkspaceDialog = () => {
  workspaceForm.value.path = workspacePath.value
  workspaceDialogVisible.value = true
}

const setWorkspaceDir = async () => {
  try {
    await api.setWorkspaceDir(workspaceForm.value.path)
    ElMessage.success('工作目录设置成功')
    workspaceDialogVisible.value = false
    await loadWorkspaceInfo()
    await refreshFileList()
  } catch (error: any) {
    console.error('设置工作目录失败:', error)
    ElMessage.error(`设置工作目录失败: ${error.message}`)
  }
}

const createNewDirectory = () => {
  // 根据当前选中的节点确定父目录
  if (currentSelectedNode.value && currentSelectedNode.value.isDirectory) {
    newDirForm.value.parentPath = currentSelectedNode.value.path
  } else {
    newDirForm.value.parentPath = ''
  }
  
  newDirForm.value.name = ''
  newDirDialogVisible.value = true
}

const confirmCreateDirectory = async () => {
  try {
    let dirPath = newDirForm.value.name
    
    // 如果有父路径，拼接完整路径
    if (newDirForm.value.parentPath) {
      dirPath = normalizePath(newDirForm.value.parentPath + '/' + dirPath)
    }
    
    await api.createDirectory(dirPath)
    ElMessage.success('目录创建成功')
    newDirDialogVisible.value = false
    await refreshFileList()
    
    // 确保父目录展开
    if (newDirForm.value.parentPath && !expandedKeys.value.includes(newDirForm.value.parentPath)) {
      expandedKeys.value.push(newDirForm.value.parentPath)
    }
  } catch (error: any) {
    console.error('创建目录失败:', error)
    ElMessage.error(`创建目录失败: ${error.message}`)
  }
}

const deleteCurrentFile = async () => {
  // 使用当前选中的节点，而不是当前文件
  const nodeToDelete = currentSelectedNode.value
  
  if (!nodeToDelete) {
    ElMessage.warning('请先选择一个文件或目录')
    return
  }
  
  try {
    const isDir = nodeToDelete.isDirectory
    await ElMessageBox.confirm(
      `确定要删除${isDir ? '目录' : '文件'} ${nodeToDelete.name} 吗？`,
      `删除${isDir ? '目录' : '文件'}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.deleteFile(nodeToDelete.path)
    ElMessage.success('删除成功')
    
    // 从最近文件中移除
    if (!isDir) {
      recentFiles.value = recentFiles.value.filter(f => f.path !== nodeToDelete.path)
    }
    
    // 如果删除的是当前打开的文件，清空编辑器
    if (currentFile.value && currentFile.value.path === nodeToDelete.path) {
      currentFile.value = null
      editorContent.value = ''
      updateEditorContent('# 请选择或创建YAML文件')
    }
    
    // 清空当前选中节点
    currentSelectedNode.value = null
    
    // 刷新文件列表
    await refreshFileList()
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消操作
      return
    }
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

const exportFile = () => {
  if (!currentFile.value) {
    ElMessage.warning('请先选择一个文件')
    return
  }
  
  const blob = new Blob([editorContent.value], { type: 'text/yaml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = currentFile.value.name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('导出成功')
}

// 判断节点是否展开
const isExpanded = (node: FileInfo) => {
  return expandedKeys.value.includes(node.path)
}

// 显示右键菜单
const showContextMenu = (event: MouseEvent, node: FileInfo, data: FileInfo) => {
  event.preventDefault()
  contextMenuVisible.value = true
  contextMenuTop.value = event.clientY
  contextMenuLeft.value = event.clientX
  contextMenuNode.value = data
  
  // 点击其他区域关闭菜单
  document.addEventListener('click', closeContextMenu)
}

// 关闭右键菜单
const closeContextMenu = () => {
  contextMenuVisible.value = false
  document.removeEventListener('click', closeContextMenu)
}

// 在指定目录中创建文件
const createFileInDirectory = async (directory: FileInfo) => {
  closeContextMenu()
  
  try {
    const result = await ElMessageBox.prompt(
      '请输入文件名',
      '在 ' + directory.name + ' 中新建文件',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^[a-zA-Z0-9_\-\.]+\.ya?ml$/,
        inputErrorMessage: '文件名必须以.yml或.yaml结尾'
      }
    )
    
    const fileName = result.value
    const filePath = normalizePath(directory.path + '/' + fileName)
    
    // 检查文件是否已存在
    const fileExists = await checkFileExists(filePath)
    if (fileExists) {
      try {
        await ElMessageBox.confirm(
          `路径 "${filePath}" 已存在文件，是否覆盖？`,
          '文件已存在',
          {
            confirmButtonText: '覆盖',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        // 用户点击了覆盖，继续执行
      } catch (error) {
        // 用户取消了覆盖操作
        return
      }
    }
    
    const newFile = {
      path: filePath,
      name: fileName,
      isDirectory: false
    }
    
    currentFile.value = newFile
    editorContent.value = '# 新建YAML文件\n'
    updateEditorContent(editorContent.value)
    await saveFile()
    await refreshFileList()
    updateRecentFiles(newFile)
    
    // 确保父目录展开
    if (!expandedKeys.value.includes(directory.path)) {
      expandedKeys.value.push(directory.path)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('创建文件失败:', error)
      ElMessage.error('创建文件失败')
    }
  }
}

// 在指定目录中创建子目录
const createDirectoryInDirectory = (directory: FileInfo) => {
  closeContextMenu()
  newDirForm.value.name = ''
  newDirForm.value.parentPath = directory.path
  newDirDialogVisible.value = true
}

// 删除右键菜单选中的节点
const deleteContextMenuNode = async () => {
  closeContextMenu()
  if (!contextMenuNode.value) return
  
  try {
    const isDir = contextMenuNode.value.isDirectory
    await ElMessageBox.confirm(
      `确定要删除${isDir ? '目录' : '文件'} ${contextMenuNode.value.name} 吗？`,
      `删除${isDir ? '目录' : '文件'}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await api.deleteFile(contextMenuNode.value.path)
    ElMessage.success('删除成功')
    
    // 从最近文件中移除
    if (!isDir) {
      recentFiles.value = recentFiles.value.filter(f => f.path !== contextMenuNode.value.path)
    }
    
    // 如果删除的是当前文件，清空编辑器
    if (currentFile.value && currentFile.value.path === contextMenuNode.value.path) {
      currentFile.value = null
      editorContent.value = ''
      updateEditorContent('# 请选择或创建YAML文件')
    }
    
    // 刷新文件列表
    await refreshFileList()
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消操作
      return
    }
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

// 修正使用改进后的api
const checkFileExists = async (path: string) => {
  return await api.fileExists(path)
}

// 监听搜索条件变化
watch(searchQuery, () => {
  refreshFileList()
})

// 文件拖拽相关方法
const dragState = ref({
  isDragging: false,
  dragNode: null as FileInfo | null,
  dropNode: null as FileInfo | null
})

const allowDrag = (node: FileInfo) => {
  // 允许拖拽所有节点
  return true
}

const allowDrop = (draggingNode: FileInfo, dropNode: FileInfo, type: string) => {
  // 只允许拖到文件夹上
  if (!dropNode.isDirectory) {
    return false
  }
  
  // 不允许拖到自己或自己的子文件夹
  if (draggingNode.path === dropNode.path) {
    return false
  }
  
  // 检查是否是子文件夹
  if (draggingNode.isDirectory) {
    if (dropNode.path.startsWith(draggingNode.path + '/')) {
      return false
    }
  }
  
  return true
}

const handleDragStart = (node: FileInfo) => {
  dragState.value.isDragging = true
  dragState.value.dragNode = node
}

const handleDragEnter = (draggingNode: FileInfo, dropNode: FileInfo) => {
  dragState.value.dropNode = dropNode
}

const handleDragLeave = () => {
  // 可以在这里添加样式处理
}

const handleDragOver = () => {
  // 拖动过程中的处理
}

const handleDragEnd = () => {
  dragState.value.isDragging = false
}

const handleDrop = async (draggingNode: FileInfo, dropNode: FileInfo, type: 'before' | 'after' | 'inner') => {
  // 只处理拖放到文件夹内的情况
  if (type !== 'inner' || !dropNode.isDirectory) {
    return
  }
  
  try {
    const sourcePath = normalizePath(draggingNode.path)
    const fileName = draggingNode.name
    const targetPath = normalizePath(`${dropNode.path}/${fileName}`)
    
    // 如果源路径和目标路径相同，不进行操作
    if (sourcePath === targetPath) {
      ElMessage.info('文件已经在此目录中')
      return
    }
    
    // 检查目标路径是否已存在文件/目录
    const fileExists = await checkFileExists(targetPath)
    if (fileExists) {
      try {
        await ElMessageBox.confirm(
          `目标路径 "${targetPath}" 已存在${draggingNode.isDirectory ? '目录' : '文件'}，是否覆盖？`,
          `${draggingNode.isDirectory ? '目录' : '文件'}已存在`,
          {
            confirmButtonText: '覆盖',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        // 用户点击了覆盖，继续执行
      } catch (error) {
        // 用户取消了覆盖操作
        return
      }
    }
    
    // 调用移动文件的API
    await api.moveFile(sourcePath, targetPath)
    
    // 更新当前文件的路径（如果正在编辑被移动的文件）
    if (currentFile.value && currentFile.value.path === sourcePath) {
      currentFile.value = {
        ...currentFile.value,
        path: targetPath,
        name: fileName
      }
    }
    
    // 如果当前选中的是被移动的节点，更新选中节点
    if (currentSelectedNode.value && currentSelectedNode.value.path === sourcePath) {
      currentSelectedNode.value = {
        ...currentSelectedNode.value,
        path: targetPath
      }
    }
    
    // 更新最近文件列表中的路径
    recentFiles.value = recentFiles.value.map(file => {
      if (file.path === sourcePath) {
        return {
          ...file,
          path: targetPath,
          name: fileName
        }
      }
      return file
    })
    
    // 刷新文件树
    await refreshFileList()
    
    // 确保目标文件夹展开
    if (!expandedKeys.value.includes(dropNode.path)) {
      expandedKeys.value.push(dropNode.path)
    }
    
    ElMessage.success('文件移动成功')
  } catch (error) {
    console.error('移动文件失败:', error)
    ElMessage.error('移动文件失败')
  }
}

// 格式化历史文件名
const formatHistoryFileName = (fileName: string) => {
  // 从文件名中提取原始文件名（去掉时间戳部分）
  const parts = fileName.split('_')
  if (parts.length >= 3) {
    // 假设格式是 filename_YYYYMMDD_HHMMSS.ext
    const dateIndex = parts.length - 2
    const timeIndex = parts.length - 1
    
    // 检查倒数第二部分是否是日期格式
    const datePattern = /^\d{8}$/
    const timePattern = /^\d{6}\.ya?ml$/
    
    if (datePattern.test(parts[dateIndex]) && 
        (timePattern.test(parts[timeIndex]) || /^\d{6}$/.test(parts[timeIndex]))) {
      // 移除日期和时间部分
      return parts.slice(0, dateIndex).join('_') + parts[timeIndex].replace(/^\d{6}/, '')
    }
  }
  return fileName
}

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  if (!timestamp) return ''
  
  // 假设时间戳格式是 YYYYMMDD_HHMMSS
  const parts = timestamp.split('_')
  if (parts.length !== 2) return timestamp
  
  const dateStr = parts[0]
  const timeStr = parts[1]
  
  if (dateStr.length !== 8 || timeStr.length !== 6) return timestamp
  
  const year = dateStr.substring(0, 4)
  const month = dateStr.substring(4, 6)
  const day = dateStr.substring(6, 8)
  
  const hour = timeStr.substring(0, 2)
  const minute = timeStr.substring(2, 4)
  const second = timeStr.substring(4, 6)
  
  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

// 加载历史文件列表
const loadHistoryFiles = async () => {
  try {
    historyFiles.value = await api.getHistoryFiles()
    
    // 确保历史文件夹在文件树中展开
    const historyFolderPath = 'history'
    if (!expandedKeys.value.includes(historyFolderPath)) {
      // 检查历史文件夹是否存在于文件列表中
      const historyFolderExists = fileList.value.some(item => 
        item.path === historyFolderPath && item.isDirectory
      )
      
      // 如果存在且未展开，则添加到展开列表
      if (historyFolderExists) {
        expandedKeys.value.push(historyFolderPath)
      }
    }
  } catch (error: any) {
    console.error('加载历史文件失败:', error)
    ElMessage.error(`加载历史文件失败: ${error.message}`)
  }
}

// 处理历史文件点击
const handleHistoryFileClick = async (file: HistoryFileInfo) => {
  try {
    const result = await api.readHistoryFile(file.history_path)
    
    // 创建一个临时文件对象用于显示
    const tempFile = {
      path: file.history_path,
      name: `${formatHistoryFileName(file.name)} (历史版本 ${formatTimestamp(file.timestamp)})`,
      isDirectory: false,
      isHistoryFile: true
    }
    
    // 设置当前文件和编辑器内容
    currentFile.value = tempFile
    editorContent.value = result.content
    
    // 更新编辑器
    if (editor) {
      editor.setValue(result.content)
    }
    
    // 显示提示
    ElMessage.info(`已打开历史版本: ${formatTimestamp(file.timestamp)}`)
  } catch (error: any) {
    console.error('打开历史文件失败:', error)
    ElMessage.error(`打开历史文件失败: ${error.message}`)
  }
}

// 生命周期钩子
onMounted(async () => {
  // 检查是否已经登录
  const token = localStorage.getItem('token')
  if (token) {
    isAuthenticated.value = true
    loginDialogVisible.value = false
    try {
      await initializeApp()
    } catch (error: any) {
      // 如果初始化过程中出现401错误，会在handleApiResponse中处理
      console.error('应用初始化失败:', error)
    }
  } else {
    loginDialogVisible.value = true
  }
  
  // 点击外部关闭右键菜单
  document.addEventListener('click', (e) => {
    if (contextMenuVisible.value) {
      closeContextMenu()
    }
  })
})

// 组件销毁前清理编辑器
onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
  }
  document.removeEventListener('click', closeContextMenu)
})
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  --primary-color: #3498db;
  --primary-dark: #2980b9;
  --danger-color: #e74c3c;
  --success-color: #2ecc71;
  --text-color: #333;
  --text-light: #666;
  --bg-color: #f5f7fa;
  --bg-dark: #e4e7ed;
  --sidebar-bg: #f0f2f5;
  --header-bg: #ffffff;
  --card-bg: #ffffff;
  --border-color: #dcdfe6;
  --shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  --transition: all 0.3s ease;
  color: var(--text-color);
  background-color: var(--bg-color);
}

.app-container.dark-mode {
  --primary-color: #3498db;
  --primary-dark: #2980b9;
  --danger-color: #e74c3c;
  --success-color: #2ecc71;
  --text-color: #c9d1d9;
  --text-light: #8b949e;
  --bg-color: #0d1117;
  --bg-dark: #161b22;
  --sidebar-bg: #161b22;
  --header-bg: #21262d;
  --card-bg: #21262d;
  --border-color: #30363d;
  --shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
}

.header {
  background-color: var(--header-bg);
  color: var(--text-color);
  padding: 0.75rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow);
  z-index: 10;
}

.header h1 {
  font-size: 1.5rem;
  margin: 0;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 0.5rem;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 1rem;
  overflow-y: auto;
}

.workspace-info {
  background-color: var(--card-bg);
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border-color);
}

.workspace-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.workspace-path {
  font-size: 0.85rem;
  color: var(--text-light);
  word-break: break-all;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.search-box {
  margin-bottom: 1rem;
}

.file-tree {
  flex: 1;
  overflow-y: auto;
  background-color: var(--card-bg);
  border-radius: 6px;
  padding: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid var(--border-color);
  position: relative; /* 为右键菜单定位 */
}

.custom-tree-node {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  cursor: pointer;
  width: 100%;
  height: 24px;
  line-height: 24px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: var(--transition);
}

.node-icon {
  display: flex;
  align-items: center;
  color: var(--text-light);
}

.node-label {
  font-size: 0.9rem;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  box-shadow: var(--shadow);
  z-index: 1000;
  min-width: 160px;
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: var(--transition);
}

.context-menu-item:hover {
  background-color: var(--bg-dark);
}

/* 修改Element Plus树组件样式，更接近VSCode */
:deep(.el-tree) {
  background-color: transparent;
  color: var(--text-color);
}

:deep(.el-tree-node__content) {
  height: 24px;
  border-radius: 3px;
}

:deep(.el-tree-node__content:hover) {
  background-color: var(--bg-dark);
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: var(--primary-color);
  color: white;
}

:deep(.el-tree-node__expand-icon) {
  font-size: 0.8rem;
}

/* 新建目录对话框 */
.el-dialog {
  border-radius: 6px;
}

.history {
  background-color: var(--card-bg);
  border-radius: 6px;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
}

.history-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 2px;
}

.history-item-content {
  display: flex;
  align-items: center;
  max-width: 60%;
  overflow: hidden;
}

.history-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 6px;
}

.history-item:hover {
  background-color: var(--el-fill-color-light);
}

.history-item .el-icon {
  color: var(--el-color-primary);
  flex-shrink: 0;
}

.history-time {
  font-size: 0.8em;
  color: var(--el-text-color-secondary);
  flex-shrink: 0;
}

.editor-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color);
}

.editor-toolbar {
  background-color: var(--card-bg);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.current-file {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: var(--text-color);
}

.monaco-container {
  flex: 1;
  overflow: hidden;
}

.status-bar {
  background-color: var(--card-bg);
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--border-color);
  font-size: 0.85rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-light);
}

/* 动画效果 */
.el-button {
  transition: var(--transition);
}

.el-tree-node__content {
  transition: var(--transition);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .sidebar {
    width: 240px;
  }
}

/* 拖拽相关样式 */
:deep(.is-drop-inner) {
  background-color: var(--primary-color) !important;
  color: white !important;
}

/* 添加登录对话框样式 */
.login-dialog {
  .el-dialog__body {
    padding: 20px 40px;
  }
  
  .el-input {
    margin: 20px 0;
  }
  
  .login-error-message {
    margin-bottom: 15px;
  }
}
</style> 