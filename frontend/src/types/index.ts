export interface User {
  id: string
  username: string
  email: string
  role?: 'admin' | 'user' | 'guest'  // 使角色可选，兼容后端返回
  permissions?: string[]  // 可选权限列表
  createdAt?: string  // 可选创建时间
}

export interface AuthResponse {
  token: string
  user: User
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface FileInfo {
  id: string
  name: string
  type: 'tender' | 'proposal' | 'summary' | 'other'
  size: number
  path: string
  uploadedAt: string
  uploadedBy: string
  metadata?: Record<string, any>
}

export interface LogicRule {
  id: string
  type: 'generation' | 'validation'
  category: string
  rule: string
  confidence: number
  source: string
  createdAt: string
  isActive: boolean
}

export interface LogicDatabase {
  generationRules: LogicRule[]
  validationRules: LogicRule[]
  totalRules: number
  lastUpdated: string
}

export interface LearningTask {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  filesCount: number
  rulesLearned: number
  progress: number
  startedAt: string
  completedAt?: string
  error?: string
}

export interface GenerationTask {
  id: string
  tenderFile: string
  status: 'idle' | 'generating' | 'validating' | 'completed' | 'failed'
  progress: number
  currentChapter?: string
  generatedProposal?: string
  validationResult?: ValidationResult
  iterations: number
  startedAt: string
  completedAt?: string
}

export interface ValidationResult {
  score: number
  passed: boolean
  issues: ValidationIssue[]
  suggestions: string[]
}

export interface ValidationIssue {
  chapter: string
  severity: 'high' | 'medium' | 'low'
  message: string
  suggestion: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface LLMModel {
  id: string
  name: string
  provider: 'openai' | 'deepseek' | 'qwen' | 'ollama' | 'other'
  apiKey?: string
  endpoint?: string
  modelName?: string
  temperature: number
  maxTokens: number
  isActive: boolean
}

export interface PromptTemplate {
  id: string
  name: string
  category: string
  template: string
  variables: string[]
  createdBy: string
  createdAt: string
}
