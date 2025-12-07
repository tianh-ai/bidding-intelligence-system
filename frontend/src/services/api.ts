import axiosInstance from '@/utils/axios'
import type { AxiosRequestConfig } from 'axios'
import type { 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse,
  User
} from '@/types'

// 导出 axios 实例供直接使用
export const apiClient = axiosInstance

export const authAPI = {
  // 登录
  login: (data: LoginRequest) => 
    axiosInstance.post<AuthResponse>('/api/auth/login', data),

  // 注册
  register: (data: RegisterRequest) => 
    axiosInstance.post<AuthResponse>('/api/auth/register', data),

  // 获取当前用户信息
  getCurrentUser: () => 
    axiosInstance.get<User>('/api/auth/me'),

  // 登出
  logout: () => 
    axiosInstance.post('/api/auth/logout'),

  // 刷新 token
  refreshToken: () => 
    axiosInstance.post<{ token: string }>('/api/auth/refresh'),
}

export const fileAPI = {
  // 上传文件
  uploadFiles: (files: FormData, onProgress?: (progress: number) => void) =>
    axiosInstance.post('/api/files/upload', files, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    }),

  // 获取文件列表
  getFiles: (params?: { type?: string; page?: number; limit?: number }) =>
    axiosInstance.get('/api/files', { params }),

  // 删除文件（使用uploaded_files表）
  deleteFile: (id: string) =>
    axiosInstance.delete(`/api/files/uploaded/${id}`),

  // 下载文件（使用uploaded_files表）
  downloadFile: (id: string) =>
    axiosInstance.get(`/api/files/uploaded/${id}/download`, { responseType: 'blob' }),

  // 获取数据库详情
  getDatabaseDetails: () =>
    axiosInstance.get('/api/files/database-details'),

  // 获取知识库条目
  getKnowledgeBaseEntries: () =>
    axiosInstance.get('/api/files/knowledge-base-entries'),

  // 处理上传的文件（生成知识库和文档索引）
  processFiles: (fileIds: string[]) =>
    axiosInstance.post('/api/files/process', { fileIds }),

  // 获取文档索引
  getDocumentIndexes: (fileId?: string) =>
    axiosInstance.get('/api/files/document-indexes', { params: { fileId } }),
}

export const learningAPI = {
  // 开始学习任务
  startLearning: (data: { fileIds?: string[]; folderPath?: string }) =>
    axiosInstance.post('/api/learning/start', data),

  // 获取学习任务状态
  getLearningStatus: (taskId: string) =>
    axiosInstance.get(`/api/learning/status/${taskId}`),

  // 获取逻辑库
  getLogicDatabase: () =>
    axiosInstance.get('/api/learning/logic-db'),

  // 保存临时逻辑到逻辑库
  saveLogic: (taskId: string) =>
    axiosInstance.post(`/api/learning/save/${taskId}`),

  // 删除逻辑规则
  deleteLogicRule: (ruleId: string) =>
    axiosInstance.delete(`/api/learning/rules/${ruleId}`),
}

export const generationAPI = {
  // 生成投标文件
  generateProposal: (data: { 
    tenderFileId: string
    useTemporaryLogic?: boolean
    taskId?: string
  }) =>
    axiosInstance.post('/api/generation/generate', data),

  // 获取生成任务状态
  getGenerationStatus: (taskId: string) =>
    axiosInstance.get(`/api/generation/status/${taskId}`),

  // 验证生成的文件
  validateProposal: (taskId: string) =>
    axiosInstance.post(`/api/generation/validate/${taskId}`),

  // 重新生成（基于反馈）
  regenerate: (taskId: string, feedback: string) =>
    axiosInstance.post(`/api/generation/regenerate/${taskId}`, { feedback }),

  // 保存修改的逻辑
  saveModifications: (taskId: string, modifications: any) =>
    axiosInstance.post(`/api/generation/save-modifications/${taskId}`, modifications),
}

export const summaryAPI = {
  // 总结招标公告（链接）
  summarizeLink: (url: string) =>
    axiosInstance.post('/api/summary/link', { url }),

  // 总结文件
  summarizeFile: (fileId: string) =>
    axiosInstance.post('/api/summary/file', { fileId }),

  // 总结文件夹
  summarizeFolder: (folderPath: string) =>
    axiosInstance.post('/api/summary/folder', { folderPath }),

  // 获取总结历史
  getSummaries: (params?: { page?: number; limit?: number }) =>
    axiosInstance.get('/api/summary/history', { params }),
}

export const llmAPI = {
  // 获取模型列表
  getModels: () =>
    axiosInstance.get('/api/llm/models'),

  // 添加模型
  addModel: (data: any) =>
    axiosInstance.post('/api/llm/models', data),

  // 更新模型
  updateModel: (id: string, data: any) =>
    axiosInstance.put(`/api/llm/models/${id}`, data),

  // 删除模型
  deleteModel: (id: string) =>
    axiosInstance.delete(`/api/llm/models/${id}`),

  // 测试模型
  testModel: (id: string) =>
    axiosInstance.post(`/api/llm/models/${id}/test`),

  // 聊天
  chat: (
    data: {
      message: string
      modelId?: string
      conversationId?: string
    },
    config: AxiosRequestConfig = {}
  ) => axiosInstance.post('/api/llm/chat', data, config),
}

export const promptAPI = {
  // 获取提示词模板
  getTemplates: (category?: string) =>
    axiosInstance.get('/api/prompts/templates', { params: { category } }),

  // 创建模板
  createTemplate: (data: any) =>
    axiosInstance.post('/api/prompts/templates', data),

  // 更新模板
  updateTemplate: (id: string, data: any) =>
    axiosInstance.put(`/api/prompts/templates/${id}`, data),

  // 删除模板
  deleteTemplate: (id: string) =>
    axiosInstance.delete(`/api/prompts/templates/${id}`),
}

export const userAPI = {
  // 获取用户列表（管理员）
  getUsers: (params?: { page?: number; limit?: number }) =>
    axiosInstance.get('/api/users', { params }),

  // 创建用户
  createUser: (data: any) =>
    axiosInstance.post('/api/users', data),

  // 更新用户
  updateUser: (id: string, data: any) =>
    axiosInstance.put(`/api/users/${id}`, data),

  // 删除用户
  deleteUser: (id: string) =>
    axiosInstance.delete(`/api/users/${id}`),

  // 更新用户权限
  updatePermissions: (id: string, permissions: string[]) =>
    axiosInstance.put(`/api/users/${id}/permissions`, { permissions }),
}

export const settingsAPI = {
  // 获取上传设置
  getUploadSettings: () =>
    axiosInstance.get('/api/settings/upload'),

  // 获取上传路径详细信息
  getUploadPathInfo: () =>
    axiosInstance.get('/api/settings/upload/path-info'),

  // 更新上传设置
  updateUploadSettings: (data: {
    upload_dir?: string
    max_file_size?: number
    allowed_extensions?: string[]
  }) =>
    axiosInstance.put('/api/settings/upload', data),

  // 测试上传路径
  testUploadPath: (path: string) =>
    axiosInstance.post('/api/settings/upload/test-path', null, { params: { path } }),
}
