// API 基础配置
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:18888'

// 权限级别
export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest',
}

// 权限映射
export const ROLE_PERMISSIONS = {
  [UserRole.ADMIN]: {
    canUploadFiles: true,
    canLearnLogic: true,
    canGenerateProposal: true,
    canManageModels: true,
    canManagePrompts: true,
    canManageUsers: true,
  },
  [UserRole.USER]: {
    canUploadFiles: true,
    canLearnLogic: true,
    canGenerateProposal: true,
    canManageModels: false,
    canManagePrompts: false,
    canManageUsers: false,
  },
  [UserRole.GUEST]: {
    canUploadFiles: false,
    canLearnLogic: false,
    canGenerateProposal: false,
    canManageModels: false,
    canManagePrompts: false,
    canManageUsers: false,
  },
}

// 本地存储键
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  SIDEBAR_WIDTH: 'sidebar_width',
  AI_CHAT_WIDTH: 'ai_chat_width',
}

// 文件类型
export enum FileType {
  TENDER = 'tender',
  PROPOSAL = 'proposal',
  SUMMARY = 'summary',
  OTHER = 'other',
}

// 学习状态
export enum LearningStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

// 生成状态
export enum GenerationStatus {
  IDLE = 'idle',
  GENERATING = 'generating',
  VALIDATING = 'validating',
  COMPLETED = 'completed',
  FAILED = 'failed',
}
