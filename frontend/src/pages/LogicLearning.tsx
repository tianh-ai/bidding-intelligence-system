import React, { useEffect, useMemo, useState } from 'react'
import {
  Card,
  Button,
  Select,
  Table,
  Progress,
  Space,
  message,
  Modal,
  Tag,
  Tabs,
  Upload,
  List,
  Input,
  Divider,
  InputNumber,
  Drawer,
} from 'antd'
import {
  PlayCircleOutlined,
  SaveOutlined,
  FileTextOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  EyeOutlined,
  UploadOutlined,
  SyncOutlined,
  AuditOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { learningAPI, generationAPI, fileAPI } from '@/services/api'
import type { LogicRule, LearningTask, GenerationTask, ValidationIssue } from '@/types'
import { useAuthStore } from '@/store/authStore'
import type { UploadFile } from 'antd'

const { TextArea } = Input
const { Dragger } = Upload
const LOGIC_BACKUP_KEY = 'logic-learning-backups'

type WorkspaceRole = 'system' | 'user' | 'ai'

interface WorkspaceMessage {
  id: string
  role: WorkspaceRole
  content: string
  timestamp: string
}

interface LogicSnapshot {
  id: string
  name: string
  createdAt: string
  permanent: LogicRule[]
  temporary: LogicRule[]
}

interface LearningFile {
  id: string
  name: string
  status?: string
  size?: number
  uploadedAt?: string
}

interface LogicEditorState {
  type: LogicRule['type']
  category: string
  rule: string
  confidence: number
}

const initialEditorState: LogicEditorState = {
  type: 'generation',
  category: '',
  rule: '',
  confidence: 0.8,
}

const LogicLearning: React.FC = () => {
  const { user } = useAuthStore()

  const [availableFiles, setAvailableFiles] = useState<LearningFile[]>([])
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [learningTask, setLearningTask] = useState<LearningTask | null>(null)
  const [generationTask, setGenerationTask] = useState<GenerationTask | null>(null)
  const [learningLoading, setLearningLoading] = useState(false)
  const [uploadQueue, setUploadQueue] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [_uploadProgress, setUploadProgress] = useState(0)
  const [logicRules, setLogicRules] = useState<LogicRule[]>([])
  const [tempLogicRules, setTempLogicRules] = useState<LogicRule[]>([])
  const [selectedLogic, setSelectedLogic] = useState<LogicRule | null>(null)
  const [selectedBucket, setSelectedBucket] = useState<'permanent' | 'temporary' | null>(null)
  const [logicEditor, setLogicEditor] = useState<LogicEditorState>(initialEditorState)
  const [workspaceMessages, setWorkspaceMessages] = useState<WorkspaceMessage[]>([])
  const [backups, setBackups] = useState<LogicSnapshot[]>([])
  const [validationDrawer, setValidationDrawer] = useState(false)
  const [humanFeedback, setHumanFeedback] = useState('')

  useEffect(() => {
    // 清除上次会话的临时状态
    setSelectedFiles([])
    setLearningTask(null)
    setGenerationTask(null)
    setUploadQueue([])
    setUploadProgress(0)
    setSelectedLogic(null)
    setSelectedBucket(null)
    setLogicEditor(initialEditorState)
    setWorkspaceMessages([])
    setHumanFeedback('')
    
    // 加载持久化数据
    loadAvailableFiles()
    loadLogicDatabase()
    loadBackups()
  }, [])

  const appendWorkspaceMessage = (role: WorkspaceRole, content: string) => {
    setWorkspaceMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role,
        content,
        timestamp: new Date().toLocaleTimeString(),
      },
    ])
  }

  const loadAvailableFiles = async () => {
    try {
      // 使用 /api/files/list 获取所有文件（不过滤状态）
      const response = await fileAPI.getFiles({ limit: 100 })
      const files = response.data?.files || []
      setAvailableFiles(files.map((file: any) => ({
        id: file.id,
        name: file.name,
        status: file.status || 'uploaded',
        size: file.size || 0,
        uploadedAt: file.uploadedAt || new Date().toISOString(),
      })))
      console.log(`加载了 ${files.length} 个文件（包含所有状态）`)
    } catch (error) {
      message.error('获取文件失败')
      console.error('Load files error:', error)
    }
  }

  const loadLogicDatabase = async () => {
    try {
      const response = await learningAPI.getLogicDatabase()
      setLogicRules(response.data?.chapterRules || [])
      setTempLogicRules(response.data?.globalRules || [])
    } catch (error) {
      message.error('加载逻辑库失败')
    }
  }

  const loadBackups = () => {
    const stored = localStorage.getItem(LOGIC_BACKUP_KEY)
    if (stored) {
      try {
        setBackups(JSON.parse(stored))
      } catch (error) {
        console.error('备份解析失败', error)
      }
    }
  }

  const persistBackups = (snapshots: LogicSnapshot[]) => {
    localStorage.setItem(LOGIC_BACKUP_KEY, JSON.stringify(snapshots))
    setBackups(snapshots)
  }

  const createBackup = () => {
    const snapshot: LogicSnapshot = {
      id: crypto.randomUUID(),
      name: `备份-${new Date().toLocaleString()}`,
      createdAt: new Date().toISOString(),
      permanent: logicRules,
      temporary: tempLogicRules,
    }
    persistBackups([snapshot, ...backups].slice(0, 10))
    message.success('逻辑备份已保存')
  }

  const handleRestoreBackup = (snapshot: LogicSnapshot) => {
    setLogicRules(snapshot.permanent)
    setTempLogicRules(snapshot.temporary)
    message.success('已恢复逻辑备份')
  }

  const handleDeleteBackup = (backupId: string) => {
    persistBackups(backups.filter((snapshot) => snapshot.id !== backupId))
    message.success('已删除备份')
  }

  const handleStartLearning = async () => {
    if (selectedFiles.length === 0) {
      message.warning('请选择至少一个文件')
      return
    }
    
    // 检查选中文件的状态
    const selectedFileObjects = availableFiles.filter(f => selectedFiles.includes(f.id))
    const unarchivedFiles = selectedFileObjects.filter(f => 
      !f.status || !['archived', 'indexed'].includes(f.status)
    )
    
    // 如果有未存档文件，先触发处理
    if (unarchivedFiles.length > 0) {
      appendWorkspaceMessage('system', `检测到 ${unarchivedFiles.length} 个未存档文件，正在自动处理...`)
      
      try {
        message.loading({ content: `正在处理 ${unarchivedFiles.length} 个未存档文件...`, key: 'process', duration: 0 })
        
        // 调用后端处理接口
        const unarchivedIds = unarchivedFiles.map(f => f.id)
        await fileAPI.processFiles(unarchivedIds)
        
        message.success({ content: `${unarchivedFiles.length} 个文件已提交处理，请等待处理完成`, key: 'process' })
        appendWorkspaceMessage('ai', `文件处理已启动，包括解析、归档和索引`)
        
        // 刷新文件列表
        await loadAvailableFiles()
        
        // 等待一段时间让处理进行
        message.info('建议等待 10-30 秒后再开始学习，以确保文件处理完成')
        return
      } catch (error: any) {
        const errorDetail = error?.response?.data?.detail || error?.message || '未知错误'
        message.error({ content: `文件处理失败：${errorDetail}`, key: 'process' })
        appendWorkspaceMessage('system', `❌ 文件处理失败：${errorDetail}`)
        console.error('Process files error:', error)
        return
      }
    }
    
    // 用户明确反馈
    appendWorkspaceMessage('user', `选择了 ${selectedFiles.length} 个文件，开始学习...`)
    
    try {
      setLearningLoading(true)
      message.loading({ content: '正在创建学习任务...', key: 'learning', duration: 0 })
      
      // 调用新的 MCP 架构 API
      const response = await learningAPI.startLearning({ 
        fileIds: selectedFiles,
        learningType: 'global',  // 默认全局学习
        chapterIds: []  // 可扩展为章节级学习
      })
      const taskId = response.data?.taskId || response.data?.id
      
      if (!taskId) {
        message.error({ content: '任务创建失败：返回数据缺少taskId', key: 'learning' })
        appendWorkspaceMessage('system', '❌ 任务创建失败：返回数据格式错误')
        return
      }
      
      message.success({ content: `学习任务已创建 (ID: ${taskId.substring(0, 8)}...)`, key: 'learning' })
      
      setLearningTask({
        id: taskId,
        status: response.data?.status || 'processing',
        filesCount: selectedFiles.length,
        rulesLearned: response.data?.rulesLearned || 0,
        progress: response.data?.progress || 0,
        startedAt: new Date().toISOString(),
      })
      appendWorkspaceMessage('system', `✅ 学习任务已创建（MCP架构），开始解析 ${selectedFiles.length} 个文件`)
      appendWorkspaceMessage('ai', '正在分析文档结构和逻辑规则（通过MCP服务）...')
      pollLearningStatus(taskId)
    } catch (error: any) {
      const errorDetail = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '未知错误'
      message.error({ content: `学习任务创建失败：${errorDetail}`, key: 'learning' })
      appendWorkspaceMessage('system', `❌ 学习失败：${errorDetail}`)
      console.error('Start learning error:', error)
    } finally {
      setLearningLoading(false)
    }
  }

  const pollLearningStatus = (taskId: string) => {
    const interval = window.setInterval(async () => {
      try {
        const response = await learningAPI.getLearningStatus(taskId)
        setLearningTask({
          id: response.data?.taskId || taskId,
          status: response.data?.status,
          filesCount: (response.data?.fileIds || []).length,
          rulesLearned: response.data?.result?.rulesLearned || 0,
          progress: response.data?.progress || 0,
          startedAt: response.data?.createdAt || new Date().toISOString(),
          completedAt: response.data?.completedAt,
          error: response.data?.error,
        })
        if (response.data.status === 'completed') {
          clearInterval(interval)
          appendWorkspaceMessage('ai', '学习完成，逻辑已更新')
          loadLogicDatabase()
        } else if (response.data.status === 'failed') {
          clearInterval(interval)
          message.error('学习失败')
          appendWorkspaceMessage('system', '学习失败，请重传文件')
        }
      } catch (error) {
        clearInterval(interval)
      }
    }, 2000)
  }

  const handleGenerateProposal = async () => {
    if (!learningTask || learningTask.status !== 'completed') {
      message.warning('请先完成学习后再生成')
      return
    }
    if (selectedFiles.length === 0) {
      message.warning('请先选择一个投标文件')
      return
    }
    try {
      const response = await generationAPI.generateProposal({
        tenderFileId: selectedFiles[0],
        taskId: learningTask.id,
      })
      setGenerationTask(response.data)
      appendWorkspaceMessage('system', '提交生成任务，正在推进投标材料')
      pollGenerationStatus(response.data.id)
    } catch (error) {
      message.error('生成请求失败')
    }
  }

  const pollGenerationStatus = (taskId: string) => {
    const interval = window.setInterval(async () => {
      try {
        const response = await generationAPI.getGenerationStatus(taskId)
        setGenerationTask(response.data)
        if (response.data.status === 'completed') {
          clearInterval(interval)
          message.success('生成完成，正在检查')
          appendWorkspaceMessage('ai', '生成完成，触发合规检查')
          handleValidateProposal(taskId)
        } else if (response.data.status === 'failed') {
          clearInterval(interval)
          message.error('生成失败')
          appendWorkspaceMessage('system', '生成失败，请调整逻辑')
        }
      } catch (error) {
        clearInterval(interval)
      }
    }, 2000)
  }

  const handleValidateProposal = async (taskId: string) => {
    try {
      const response = await generationAPI.validateProposal(taskId)
      setGenerationTask((prev) => (prev ? { ...prev, validationResult: response.data } : null))
      setValidationDrawer(true)
    } catch (error) {
      message.error('检查失败')
    }
  }

  const handleRegenerateWithFeedback = async () => {
    if (!generationTask?.id) return
    if (!humanFeedback) {
      message.warning('请填写反馈内容')
      return
    }
    try {
      await generationAPI.regenerate(generationTask.id, humanFeedback)
      message.success('重新生成已提交')
      setHumanFeedback('')
      pollGenerationStatus(generationTask.id)
    } catch (error) {
      message.error('重新生成失败')
    }
  }

  const handleUploadFiles = async () => {
    if (uploadQueue.length === 0) {
      message.warning('请先添加上传文件')
      return
    }
    const formData = new FormData()
    let hasValid = false
    uploadQueue.forEach((file) => {
      const fileObj = (file as any).originFileObj || (file as any)
      if (fileObj && fileObj.size !== undefined) {
        formData.append('files', fileObj as Blob)
        hasValid = true
      }
    })
    if (!hasValid) {
      message.error('没有有效的文件可上传')
      return
    }
    // 添加必需的 uploader 参数
    formData.append('uploader', user?.username || 'admin')
    formData.append('duplicate_action', 'skip')
    
    try {
      setUploading(true)
      await fileAPI.uploadFiles(formData, setUploadProgress)
      message.success('文件上传成功')
      setUploadQueue([])
      setUploadProgress(0)
      loadAvailableFiles()
    } catch (error) {
      // @ts-ignore
      const detail = error?.response?.data?.detail || error?.message || '上传失败'
      message.error(detail)
    } finally {
      setUploading(false)
    }
  }

  const handleSelectLogic = (rule: LogicRule, bucket: 'permanent' | 'temporary') => {
    setSelectedLogic(rule)
    setSelectedBucket(bucket)
    setLogicEditor({
      type: rule.type,
      category: rule.category,
      rule: rule.rule,
      confidence: rule.confidence,
    })
    appendWorkspaceMessage('ai', `${bucket === 'permanent' ? '永久' : '临时'}逻辑已加载到编辑区`)
  }

  const handleSaveEditor = (target: 'permanent' | 'temporary') => {
    if (!selectedLogic || selectedBucket !== target) {
      message.warning('请在目标逻辑分组中选择一个规则')
      return
    }
    const updater = (rule: LogicRule): LogicRule => ({
      ...rule,
      type: logicEditor.type,
      category: logicEditor.category,
      rule: logicEditor.rule,
      confidence: logicEditor.confidence,
      source: `${rule.source || '系统'}（手动编辑）`,
    })
    if (target === 'permanent') {
      setLogicRules((prev) => prev.map((rule) => (rule.id === selectedLogic.id ? updater(rule) : rule)))
    } else {
      setTempLogicRules((prev) => prev.map((rule) => (rule.id === selectedLogic.id ? updater(rule) : rule)))
    }
    message.success(`${target === 'permanent' ? '永久' : '临时'}逻辑已更新`)
    appendWorkspaceMessage('system', `${target === 'permanent' ? '永久' : '临时'}逻辑已保存`)
  }

  const handlePromoteLogic = () => {
    if (!selectedLogic) {
      message.warning('请先选择一个逻辑')
      return
    }
    if (user?.role !== 'admin') {
      message.warning('需要管理员权限才能提升为永久逻辑')
      appendWorkspaceMessage('user', '请求管理员提升当前逻辑为永久')
      return
    }
    setLogicRules((prev) =>
      prev.map((rule) =>
        rule.id === selectedLogic.id
          ? {
              ...rule,
              rule: logicEditor.rule,
              confidence: logicEditor.confidence,
              category: logicEditor.category,
            }
          : rule
      )
    )
    message.success('管理员更新了永久逻辑')
    appendWorkspaceMessage('ai', '管理员更新了永久逻辑')
  }

  const handleSaveLogic = () => {
    if (!learningTask) {
      message.warning('没有活跃的学习任务可保存')
      return
    }
    Modal.confirm({
      title: '确认保存逻辑',
      content: '保存后本次学习生成的逻辑将加入逻辑库',
      onOk: async () => {
        try {
          await learningAPI.saveLogic(learningTask.id)
          message.success('逻辑已写入逻辑库')
          setTempLogicRules([])
          loadLogicDatabase()
        } catch (error: any) {
          message.error(error?.response?.data?.message || '保存失败')
        }
      },
    })
  }

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await learningAPI.deleteLogicRule(ruleId)
      message.success('逻辑已删除')
      loadLogicDatabase()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const logicColumns = useMemo(
    () => [
      {
        title: '类型',
        dataIndex: 'type',
        key: 'type',
        render: (type: string) => (
          <Tag color={type === 'generation' ? 'blue' : 'green'}>
            {type === 'generation' ? '生成逻辑' : '验证逻辑'}
          </Tag>
        ),
      },
      { title: '分类', dataIndex: 'category', key: 'category' },
      { title: '规则', dataIndex: 'rule', key: 'rule', ellipsis: true },
      {
        title: '置信度',
        dataIndex: 'confidence',
        key: 'confidence',
        render: (confidence: number) => (
          <Progress percent={Math.round(confidence * 100)} size="small" strokeColor="#00D9FF" />
        ),
      },
      {
        title: '操作',
        key: 'action',
        render: (_: any, record: LogicRule) => (
          <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDeleteRule(record.id)}>
            删除
          </Button>
        ),
      },
    ],
    [handleDeleteRule]
  )

  const validationContent = generationTask?.validationResult

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-grok-text">逻辑学习</h1>
        <Space>
          <Button
            icon={<SaveOutlined />}
            onClick={handleSaveLogic}
            disabled={!learningTask || learningTask.status !== 'completed'}
            className="grok-btn-primary"
          >
            保存逻辑
          </Button>
          <Button icon={<PlayCircleOutlined />} onClick={createBackup} className="grok-btn-secondary">
            备份逻辑
          </Button>
        </Space>
      </div>

      <Card className="grok-card" title="选择学习文件">
        <Select
          mode="multiple"
          className="grok-input"
          style={{ width: '100%' }}
          placeholder="选择已有文件（可搜索）"
          showSearch
          filterOption={(input, option) =>
            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
          }
          maxTagCount="responsive"
          value={selectedFiles}
          onChange={setSelectedFiles}
          options={availableFiles.map((file) => {
            const statusMap: Record<string, { text: string; color: string }> = {
              'uploaded': { text: '已上传', color: 'default' },
              'parsing': { text: '解析中', color: 'processing' },
              'parsed': { text: '已解析', color: 'success' },
              'archiving': { text: '归档中', color: 'processing' },
              'archived': { text: '已归档', color: 'success' },
              'indexing': { text: '索引中', color: 'processing' },
              'indexed': { text: '已完成', color: 'success' },
            }
            const status = file.status || 'uploaded'
            const statusInfo = statusMap[status] || { text: status, color: 'default' }
            return {
              label: `${file.name} [${statusInfo.text}]`,
              value: file.id,
            }
          })}
          dropdownStyle={{ maxHeight: 400 }}
          listHeight={320}
        />
        <Dragger
          accept=".pdf,.docx,.xlsx"
          multiple
          beforeUpload={(file) => {
            setUploadQueue((prev) => [...prev, file])
            return false
          }}
          fileList={uploadQueue}
          onRemove={(file) => setUploadQueue((prev) => prev.filter((item) => item.uid !== file.uid))}
          className="mt-3 grok-dragger"
          showUploadList={{ showDownloadIcon: false }}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined className="text-4xl text-grok-accent" />
          </p>
          <p className="text-grok-textMuted">拖拽或点击上传文件，上传后自动可选</p>
        </Dragger>
        <Space className="mt-4">
          <Button icon={<UploadOutlined />} loading={uploading} onClick={handleUploadFiles} className="grok-btn-primary">
            上传文件
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleStartLearning}
            disabled={selectedFiles.length === 0 || learningLoading}
            loading={learningLoading}
            className="grok-btn-secondary"
          >
            开始学习
          </Button>
        </Space>
        {learningTask && (
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="grok-card">
              <p className="text-grok-textMuted text-sm">进度</p>
              <Progress
                percent={learningTask.progress}
                status={learningTask.status === 'failed' ? 'exception' : 'active'}
                strokeColor="#00D9FF"
              />
            </div>
            <div className="grok-card">
              <p className="text-grok-textMuted text-sm">规则数</p>
              <p className="text-2xl text-grok-accent">{learningTask.rulesLearned || 0}</p>
            </div>
            <div className="grok-card">
              <p className="text-grok-textMuted text-sm">状态</p>
              <Tag
                color={
                  learningTask.status === 'completed'
                    ? 'success'
                    : learningTask.status === 'failed'
                    ? 'error'
                    : 'processing'
                }
              >
                {learningTask.status}
              </Tag>
            </div>
          </div>
        )}
      </Card>

      <Card className="grok-card" title="逻辑互动工作区">
        <div className="space-y-3 max-h-[240px] overflow-auto">
          {workspaceMessages.map((msg) => (
            <div
              key={msg.id}
              className={`p-3 rounded-lg border ${
                msg.role === 'user'
                  ? 'border-grok-accent/40 bg-grok-accent/10'
                  : msg.role === 'ai'
                  ? 'border-grok-border bg-grok-surface'
                  : 'border-dashed border-grok-border'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-grok-textMuted">
                <span>{msg.role === 'user' ? '你' : msg.role === 'ai' ? '逻辑AI' : '系统'}</span>
                <span>{msg.timestamp}</span>
              </div>
              <p className="text-sm text-grok-text mt-1">{msg.content}</p>
            </div>
          ))}
        </div>
        <Space className="mt-3" wrap>
          <Button onClick={() => appendWorkspaceMessage('user', '请求澄清当前逻辑')} className="grok-btn-secondary">
            请求澄清
          </Button>
          <Button
            icon={<SyncOutlined />}
            onClick={() => {
              appendWorkspaceMessage('user', '再次发起学习')
              handleStartLearning()
            }}
            className="grok-btn-secondary"
          >
            再次学习
          </Button>
          <Button icon={<MessageOutlined />} onClick={() => appendWorkspaceMessage('ai', '需要细化规则')} className="grok-btn-secondary">
            细化逻辑
          </Button>
          <Button icon={<AuditOutlined />} onClick={() => appendWorkspaceMessage('user', '申请复审当前逻辑')} className="grok-btn-secondary">
            申请复审
          </Button>
          <Button icon={<FileTextOutlined />} onClick={() => appendWorkspaceMessage('ai', '临时逻辑部署成功')} className="grok-btn-primary">
            部署临时逻辑
          </Button>
        </Space>
      </Card>

      <Card className="grok-card" title="逻辑编辑与权限">
        <Space direction="vertical" className="w-full">
          <Select
            value={logicEditor.type}
            onChange={(value) => setLogicEditor((prev) => ({ ...prev, type: value }))}
            options={[
              { label: '生成逻辑', value: 'generation' },
              { label: '验证逻辑', value: 'validation' },
            ]}
            className="grok-input"
          />
          <Input
            placeholder="逻辑分类（如：履约/成本/技术）"
            value={logicEditor.category}
            onChange={(event) => setLogicEditor((prev) => ({ ...prev, category: event.target.value }))}
            className="grok-input"
          />
          <TextArea
            value={logicEditor.rule}
            onChange={(event) => setLogicEditor((prev) => ({ ...prev, rule: event.target.value }))}
            rows={4}
            className="grok-input"
            placeholder="在此描述你的逻辑要点"
          />
          <InputNumber
            min={0}
            max={1}
            step={0.05}
            value={logicEditor.confidence}
            onChange={(value) => setLogicEditor((prev) => ({ ...prev, confidence: Number(value) }))}
            className="w-full grok-input"
            stringMode
          />
        </Space>
        <Space className="mt-3">
          <Button onClick={() => handleSaveEditor('temporary')} className="grok-btn-secondary">
            保存临时逻辑
          </Button>
          <Button onClick={() => handleSaveEditor('permanent')} className="grok-btn-secondary">
            保存永久逻辑
          </Button>
          <Button onClick={handlePromoteLogic} type="primary" className="grok-btn-primary">
            {user?.role === 'admin' ? '管理员发布永久逻辑' : '申请管理员复审'}
          </Button>
        </Space>
        <p className="text-xs text-grok-textMuted mt-2">
          {user?.role !== 'admin'
            ? '非管理员的修改将进入管理员审批流程'
            : '管理员修改将直接生效'}
        </p>
      </Card>

      <Card className="grok-card" title="逻辑备份与恢复">
        <List
          dataSource={backups}
          locale={{ emptyText: '暂无备份' }}
          renderItem={(snapshot) => (
            <List.Item
              actions={[
                <Button key="restore" type="link" onClick={() => handleRestoreBackup(snapshot)}>
                  恢复
                </Button>,
                <Button key="delete" type="text" danger onClick={() => handleDeleteBackup(snapshot.id)}>
                  删除
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={snapshot.name}
                description={`创建于 ${new Date(snapshot.createdAt).toLocaleString()}`}
              />
            </List.Item>
          )}
        />
      </Card>

      <Card className="grok-card" title="逻辑库">
        <Tabs
          items={[
            {
              key: 'permanent',
              label: '永久逻辑',
              children: (
                <Table
                  dataSource={logicRules}
                  columns={logicColumns}
                  rowKey="id"
                  pagination={{ pageSize: 6 }}
                  onRow={(record) => ({
                    onClick: () => handleSelectLogic(record, 'permanent'),
                    className:
                      record.id === selectedLogic?.id && selectedBucket === 'permanent' ? 'bg-grok-accent/10' : undefined,
                  })}
                />
              ),
            },
            {
              key: 'temporary',
              label: `临时逻辑 (${tempLogicRules.length})`,
              children: (
                <Table
                  dataSource={tempLogicRules}
                  columns={logicColumns}
                  rowKey="id"
                  pagination={{ pageSize: 6 }}
                  onRow={(record) => ({
                    onClick: () => handleSelectLogic(record, 'temporary'),
                    className:
                      record.id === selectedLogic?.id && selectedBucket === 'temporary' ? 'bg-grok-accent/10' : undefined,
                  })}
                />
              ),
            },
          ]}
        />
      </Card>

      <Card className="grok-card" title="生成投标材料">
        <Space>
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleGenerateProposal}
            disabled={!learningTask || learningTask.status !== 'completed'}
            className="grok-btn-primary"
          >
            生成投标文件
          </Button>
          {generationTask && (
            <Button icon={<EyeOutlined />} onClick={() => setValidationDrawer(true)} className="grok-btn-secondary">
              查看检查结果
            </Button>
          )}
        </Space>
        {generationTask && (
          <div className="mt-4 space-y-2">
            <Progress
              percent={generationTask.progress}
              status={generationTask.status === 'failed' ? 'exception' : 'active'}
              strokeColor="#00D9FF"
            />
            <p className="text-sm text-grok-textMuted">
              当前章节：{generationTask.currentChapter || '准备中'} · 迭代：{generationTask.iterations}
            </p>
          </div>
        )}
      </Card>

      <Divider />

      <Card className="grok-card" type="inner" title="检查结果">
        {validationContent ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-grok-text">总体评分</h3>
              <Progress
                percent={Math.round(validationContent.score * 100)}
                strokeColor={validationContent.passed ? '#00E676' : '#FF1744'}
              />
              <Tag color={validationContent.passed ? 'success' : 'error'} className="mt-2">
                {validationContent.passed ? '通过' : '未通过'}
              </Tag>
            </div>
            <Divider />
            <div>
              <h3 className="text-lg font-semibold text-grok-text">发现的问题</h3>
              <div className="space-y-2">
                {validationContent.issues.map((issue: ValidationIssue, index: number) => (
                  <div key={`${issue.chapter}-${index}`} className="grok-card p-3">
                    <div className="flex items-start gap-2">
                      <ExclamationCircleOutlined
                        className={
                          issue.severity === 'high'
                            ? 'text-red-500'
                            : issue.severity === 'medium'
                            ? 'text-yellow-500'
                            : 'text-blue-500'
                        }
                      />
                      <div>
                        <p className="font-medium text-grok-text">{issue.chapter}</p>
                        <p className="text-sm text-grok-textMuted">{issue.message}</p>
                        <p className="text-sm text-grok-accent mt-1">建议：{issue.suggestion}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <Divider />
            <div>
              <h3 className="text-lg font-semibold text-grok-text">人工反馈</h3>
              <TextArea
                value={humanFeedback}
                onChange={(event) => setHumanFeedback(event.target.value)}
                rows={3}
                placeholder="输入复审意见，辅助重新生成"
                className="grok-input"
              />
              <Button
                type="primary"
                className="grok-btn-primary mt-2"
                onClick={handleRegenerateWithFeedback}
                disabled={!humanFeedback}
              >
                应用反馈并重跑
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-grok-textMuted">等待生成检查结果</p>
        )}
      </Card>

      <Drawer
        title="检查结果详情"
        open={validationDrawer}
        placement="right"
        width={520}
        onClose={() => setValidationDrawer(false)}
      >
        {validationContent ? (
          <div className="space-y-3">
            <p className="text-sm text-grok-textMuted">当前得分：{Math.round(validationContent.score * 100)}%</p>
            <List
              dataSource={validationContent.issues}
              renderItem={(issue: ValidationIssue) => (
                <List.Item>
                  <List.Item.Meta title={issue.chapter} description={issue.message} />
                  <Tag
                    color={
                      issue.severity === 'high'
                        ? 'error'
                        : issue.severity === 'medium'
                        ? 'warning'
                        : 'default'
                    }
                  >
                    {issue.severity}
                  </Tag>
                </List.Item>
              )}
            />
          </div>
        ) : (
          <p className="text-sm text-grok-textMuted">暂无检查结果</p>
        )}
      </Drawer>
    </div>
  )
}

export default LogicLearning
