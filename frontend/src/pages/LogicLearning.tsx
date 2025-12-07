import React, { useState, useEffect } from 'react'
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
  Drawer,
  Input,
  Divider,
} from 'antd'
import {
  PlayCircleOutlined,
  SaveOutlined,
  FileTextOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { learningAPI, generationAPI, fileAPI } from '@/services/api'
import type { LogicRule, LearningTask, GenerationTask, ValidationIssue } from '@/types'

const { TextArea } = Input

const LogicLearning: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [availableFiles, setAvailableFiles] = useState<any[]>([])
  const [learningTask, setLearningTask] = useState<LearningTask | null>(null)
  const [generationTask, setGenerationTask] = useState<GenerationTask | null>(null)
  const [logicRules, setLogicRules] = useState<LogicRule[]>([])
  const [tempLogicRules, setTempLogicRules] = useState<LogicRule[]>([])
  const [validationDrawer, setValidationDrawer] = useState(false)
  const [humanFeedback, setHumanFeedback] = useState('')

  useEffect(() => {
    loadFiles()
    loadLogicDatabase()
  }, [])

  const loadFiles = async () => {
    try {
      const response = await fileAPI.getFiles()
      setAvailableFiles(response.data.files)
    } catch (error) {
      console.error('Failed to load files:', error)
    }
  }

  const loadLogicDatabase = async () => {
    try {
      const response = await learningAPI.getLogicDatabase()
      setLogicRules([
        ...response.data.generationRules,
        ...response.data.validationRules,
      ])
    } catch (error) {
      console.error('Failed to load logic database:', error)
    }
  }

  const handleStartLearning = async () => {
    if (selectedFiles.length === 0) {
      message.warning('请先选择文件')
      return
    }

    try {
      const response = await learningAPI.startLearning({ fileIds: selectedFiles })
      setLearningTask(response.data)
      message.success('学习任务已启动')
      
      // 轮询任务状态
      pollLearningStatus(response.data.id)
    } catch (error: any) {
      message.error(error.response?.data?.message || '启动失败')
    }
  }

  const pollLearningStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await learningAPI.getLearningStatus(taskId)
        setLearningTask(response.data)
        
        if (response.data.status === 'completed') {
          clearInterval(interval)
          message.success('学习完成！')
          setTempLogicRules(response.data.learnedRules || [])
        } else if (response.data.status === 'failed') {
          clearInterval(interval)
          message.error('学习失败：' + response.data.error)
        }
      } catch (error) {
        clearInterval(interval)
      }
    }, 2000)
  }

  const handleGenerateProposal = async () => {
    if (!selectedFiles[0]) {
      message.warning('请选择招标文件')
      return
    }

    try {
      const response = await generationAPI.generateProposal({
        tenderFileId: selectedFiles[0],
        useTemporaryLogic: tempLogicRules.length > 0,
        taskId: learningTask?.id,
      })
      
      setGenerationTask(response.data)
      message.success('开始生成投标文件')
      
      // 轮询生成状态
      pollGenerationStatus(response.data.id)
    } catch (error: any) {
      message.error(error.response?.data?.message || '生成失败')
    }
  }

  const pollGenerationStatus = async (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await generationAPI.getGenerationStatus(taskId)
        setGenerationTask(response.data)
        
        if (response.data.status === 'completed') {
          clearInterval(interval)
          message.success('生成完成！正在自动检查...')
          handleValidateProposal(taskId)
        } else if (response.data.status === 'failed') {
          clearInterval(interval)
          message.error('生成失败')
        }
      } catch (error) {
        clearInterval(interval)
      }
    }, 2000)
  }

  const handleValidateProposal = async (taskId: string) => {
    try {
      const response = await generationAPI.validateProposal(taskId)
      setGenerationTask((prev) => prev ? {
        ...prev,
        validationResult: response.data,
      } : null)
      setValidationDrawer(true)
    } catch (error: any) {
      message.error('检查失败')
    }
  }

  const handleRegenerateWithFeedback = async () => {
    if (!generationTask?.id) return
    
    try {
      await generationAPI.regenerate(generationTask.id, humanFeedback)
      message.success('开始重新生成...')
      setHumanFeedback('')
      pollGenerationStatus(generationTask.id)
    } catch (error: any) {
      message.error('重新生成失败')
    }
  }

  const handleSaveLogic = async () => {
    if (!learningTask?.id) {
      message.warning('没有可保存的学习任务')
      return
    }

    Modal.confirm({
      title: '确认保存逻辑',
      content: '保存后，本次学习的逻辑将加入逻辑库，影响后续生成。确定继续吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await learningAPI.saveLogic(learningTask.id)
          message.success('逻辑已保存到逻辑库')
          setTempLogicRules([])
          loadLogicDatabase()
        } catch (error: any) {
          message.error(error.response?.data?.message || '保存失败')
        }
      },
    })
  }

  const logicColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'generation' ? 'blue' : 'green'}>
          {type === 'generation' ? '生成逻辑' : '检查逻辑'}
        </Tag>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: '规则',
      dataIndex: 'rule',
      key: 'rule',
      ellipsis: true,
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => (
        <Progress
          percent={Math.round(confidence * 100)}
          size="small"
          strokeColor="#00D9FF"
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: LogicRule) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteRule(record.id)}
        >
          删除
        </Button>
      ),
    },
  ]

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await learningAPI.deleteLogicRule(ruleId)
      message.success('删除成功')
      loadLogicDatabase()
    } catch (error: any) {
      message.error('删除失败')
    }
  }

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
            保存逻辑到逻辑库
          </Button>
        </Space>
      </div>

      {/* File Selection */}
      <Card className="grok-card" title="选择学习文件">
        <Select
          mode="multiple"
          style={{ width: '100%' }}
          placeholder="选择文件或文件夹"
          value={selectedFiles}
          onChange={setSelectedFiles}
          options={availableFiles.map(f => ({
            label: f.name,
            value: f.id,
          }))}
          className="grok-input"
        />
        
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleStartLearning}
          disabled={selectedFiles.length === 0 || learningTask?.status === 'processing'}
          loading={learningTask?.status === 'processing'}
          className="grok-btn-primary mt-4"
        >
          开始学习
        </Button>
      </Card>

      {/* Learning Progress */}
      {learningTask && (
        <Card className="grok-card" title="学习进度">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-grok-text">处理进度</span>
                <span className="text-grok-accent">{learningTask.progress}%</span>
              </div>
              <Progress
                percent={learningTask.progress}
                status={learningTask.status === 'failed' ? 'exception' : 'active'}
                strokeColor="#00D9FF"
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="grok-card">
                <p className="text-grok-textMuted text-sm">文件数量</p>
                <p className="text-2xl text-grok-accent">{learningTask.filesCount}</p>
              </div>
              <div className="grok-card">
                <p className="text-grok-textMuted text-sm">学习的规则</p>
                <p className="text-2xl text-grok-accent">{learningTask.rulesLearned}</p>
              </div>
              <div className="grok-card">
                <p className="text-grok-textMuted text-sm">状态</p>
                <p className="text-lg">
                  {learningTask.status === 'completed' && (
                    <Tag color="success">已完成</Tag>
                  )}
                  {learningTask.status === 'processing' && (
                    <Tag color="processing">进行中</Tag>
                  )}
                  {learningTask.status === 'failed' && (
                    <Tag color="error">失败</Tag>
                  )}
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Generate Proposal */}
      {learningTask?.status === 'completed' && (
        <Card className="grok-card" title="生成投标文件">
          <Space>
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              onClick={handleGenerateProposal}
              loading={generationTask?.status === 'generating'}
              className="grok-btn-primary"
            >
              生成投标文件
            </Button>
            
            {generationTask && (
              <Button
                icon={<EyeOutlined />}
                onClick={() => setValidationDrawer(true)}
                className="grok-btn-secondary"
              >
                查看检查结果
              </Button>
            )}
          </Space>

          {generationTask && (
            <div className="mt-4">
              <Progress
                percent={generationTask.progress}
                status={generationTask.status === 'failed' ? 'exception' : 'active'}
                strokeColor="#00D9FF"
              />
              <p className="text-grok-textMuted text-sm mt-2">
                当前章节：{generationTask.currentChapter || '准备中...'}
              </p>
              <p className="text-grok-textMuted text-sm">
                迭代次数：{generationTask.iterations}
              </p>
            </div>
          )}
        </Card>
      )}

      {/* Logic Database */}
      <Card className="grok-card" title="逻辑库">
        <Tabs
          items={[
            {
              key: 'permanent',
              label: '永久逻辑库',
              children: (
                <Table
                  dataSource={logicRules}
                  columns={logicColumns}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              ),
            },
            {
              key: 'temporary',
              label: `临时逻辑 (${tempLogicRules.length})`,
              children: (
                <Table
                  dataSource={tempLogicRules}
                  columns={logicColumns.filter(col => col.key !== 'action')}
                  rowKey="id"
                  pagination={{ pageSize: 10 }}
                />
              ),
            },
          ]}
        />
      </Card>

      {/* Validation Drawer */}
      <Drawer
        title="检查结果"
        placement="right"
        width={600}
        open={validationDrawer}
        onClose={() => setValidationDrawer(false)}
        className="grok-card"
      >
        {generationTask?.validationResult && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold mb-2 text-grok-text">总体评分</h3>
              <Progress
                percent={Math.round(generationTask.validationResult.score * 100)}
                strokeColor={
                  generationTask.validationResult.passed ? '#00E676' : '#FF1744'
                }
              />
              <Tag
                color={generationTask.validationResult.passed ? 'success' : 'error'}
                className="mt-2"
              >
                {generationTask.validationResult.passed ? '通过' : '未通过'}
              </Tag>
            </div>

            <Divider />

            <div>
              <h3 className="text-lg font-semibold mb-2 text-grok-text">发现的问题</h3>
              <div className="space-y-2">
                {generationTask.validationResult.issues.map((issue: ValidationIssue, index: number) => (
                  <div key={index} className="grok-card p-3">
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
                      <div className="flex-1">
                        <p className="font-medium text-grok-text">{issue.chapter}</p>
                        <p className="text-sm text-grok-textMuted">{issue.message}</p>
                        <p className="text-sm text-grok-accent mt-1">
                          建议：{issue.suggestion}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Divider />

            <div>
              <h3 className="text-lg font-semibold mb-2 text-grok-text">人工反馈</h3>
              <TextArea
                value={humanFeedback}
                onChange={(e) => setHumanFeedback(e.target.value)}
                placeholder="输入额外的修改意见..."
                rows={4}
                className="grok-input"
              />
              <Button
                type="primary"
                onClick={handleRegenerateWithFeedback}
                disabled={!humanFeedback}
                className="grok-btn-primary mt-2"
              >
                应用反馈并重新生成
              </Button>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default LogicLearning
