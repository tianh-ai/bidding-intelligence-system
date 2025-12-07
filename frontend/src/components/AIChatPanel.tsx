import React, { useState, useRef, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Input, Button, Select, Avatar, Tooltip, message as antdMessage, Upload, Dropdown } from 'antd'
import { SendOutlined, ClearOutlined, UserOutlined, RobotOutlined, StopOutlined, LikeOutlined, DislikeOutlined, CheckCircleOutlined, PaperClipOutlined, ThunderboltOutlined, CloseOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { useChatStore } from '@/store/chatStore'
import { useAuthStore } from '@/store/authStore'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage } from '@/types'
import { llmAPI, promptAPI } from '@/services/api'

// 1. 提取 MessageItem 子组件
interface MessageItemProps {
  message: ChatMessage
  usernameInitial?: string
  onFeedback: (messageId: string, rating: 'good' | 'bad') => void
}

const MessageItem: React.FC<MessageItemProps> = React.memo(({ message, usernameInitial, onFeedback }) => {
  const isUser = message.role === 'user'
  const [feedbackSent, setFeedbackSent] = useState(false)

  // 2. 优化 MessageItem 内部的元素创建
  const avatar = useMemo(() => {
    return isUser ? (
      <Avatar icon={<UserOutlined />} className="bg-gray-600 flex-shrink-0">
        {usernameInitial}
      </Avatar>
    ) : (
      <Avatar icon={<RobotOutlined />} className="bg-grok-accent flex-shrink-0" />
    )
  }, [isUser, usernameInitial])

  const handleFeedbackClick = (rating: 'good' | 'bad') => {
    onFeedback(message.id, rating)
    setFeedbackSent(true)
  }

  return (
    <div className={`group relative flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && avatar}
      <div
        className={`relative max-w-[80%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-grok-accent text-grok-bg'
            : 'bg-grok-bg border border-grok-border text-grok-text'
        }`}
      >
        <ReactMarkdown className="prose prose-invert prose-sm max-w-none">
          {message.content}
        </ReactMarkdown>
        <div className="text-xs mt-2 opacity-60">{new Date(message.timestamp).toLocaleTimeString()}</div>
        {!isUser && message.content && !feedbackSent && (
          <div className="absolute -bottom-4 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
            <Tooltip title="回答得很好">
              <Button size="small" type="text" icon={<LikeOutlined />} onClick={() => handleFeedbackClick('good')} />
            </Tooltip>
            <Tooltip title="回答不满意">
              <Button
                size="small"
                type="text"
                icon={<DislikeOutlined />}
                onClick={() => handleFeedbackClick('bad')} />
            </Tooltip>
          </div>
        )}
        {feedbackSent && (
          <div className="absolute -bottom-4 right-0 flex items-center gap-1 text-green-500">
            <CheckCircleOutlined />
            <span className="text-xs">感谢反馈</span>
          </div>
        )}
      </div>
      {isUser && avatar}
    </div>
  )
})

MessageItem.displayName = 'MessageItem'

const AIChatPanel: React.FC = () => {
  const [input, setInput] = useState('')
  const [models, setModels] = useState<{ id: string; name: string }[]>([])
  const [attachments, setAttachments] = useState<UploadFile[]>([])
  const [prompts, setPrompts] = useState<any[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const {
    messages,
    clearMessages,
    isLoading,
    conversationId,
    addMessage,
    updateMessage,
    setConversationId,
    setLoading,
    setAbortController,
    stopGeneration,
    currentModel,
    setCurrentModel,
  } = useChatStore()
  const { user } = useAuthStore()

  // 1. 使用 useMemo 稳定化 usernameInitial prop
  const usernameInitial = useMemo(() => user?.username?.[0]?.toUpperCase(), [user])

  useEffect(() => {
    const fetchModels = async () => {
      try {
        console.log('[AIChatPanel] 开始获取模型列表...')
        const res = await llmAPI.getModels()
        console.log('[AIChatPanel] API响应:', res.data)
        
        // API直接返回数组格式
        const data = (res.data || []) as { id: string; name: string; is_default?: boolean }[]
        
        console.log('[AIChatPanel] 解析后的模型列表:', data)
        setModels(data)
        
          if (!currentModel && data.length > 0) {
          const defaultModel = data.find((m) => m.is_default) || data[0]
          console.log('[AIChatPanel] 设置默认模型:', defaultModel)
          setCurrentModel(defaultModel)
        }
      } catch (error) {
        console.error('[AIChatPanel] 获取模型列表失败:', error)
        if (axios.isAxiosError(error)) {
          console.error('- 错误详情:', error.response?.data || error.message)
          console.error('- 请求URL:', error.config?.url)
          console.error('- 状态码:', error.response?.status)
        }
        antdMessage.error('获取模型列表失败，请检查网络连接')
      }
    }

      fetchModels()
    }, [currentModel, setCurrentModel])

  // 加载提示词模板
  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        console.log('[AIChatPanel] 开始获取提示词列表...')
        const res = await promptAPI.getTemplates()
        console.log('[AIChatPanel] 提示词API响应:', res.data)
        setPrompts(res.data.templates || [])
      } catch (error) {
        console.error('[AIChatPanel] 获取提示词失败:', error)
      }
    }
    fetchPrompts()
  }, [])

  const handleFeedback = async (messageId: string, rating: 'good' | 'bad') => {
    const messageIndex = messages.findIndex((m) => m.id === messageId)

    // 确保找到了消息，并且它前面有一条用户消息
    if (messageIndex > 0 && messages[messageIndex - 1].role === 'user') {
      const aiMessage = messages[messageIndex]
      const userMessage = messages[messageIndex - 1]

      const payload = {
        question: userMessage.content,
        answer: aiMessage.content,
        rating: rating,
        conversation_id: conversationId,
        message_id: messageId,
        metadata: aiMessage.metadata || {},
      }

      try {
        // 假设你有一个 API 服务来发送请求
        // await feedbackAPI.submit(payload);
        // 这里我们用 fetch 模拟
        await fetch('/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
      } catch (error) {
        console.error('Failed to submit feedback:', error)
        antdMessage.error('提交反馈失败，请稍后再试。')
      }
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const messageContent = input
    setInput('')

    const userMessageId = `user-${Date.now()}`
    const assistantMessageId = `assistant-${Date.now()}`

    const timestamp = new Date().toISOString()

    addMessage({
      id: userMessageId,
      role: 'user',
      content: messageContent,
      timestamp,
    })

    addMessage({
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp,
    })

    setLoading(true)

    const controller = new AbortController()
    setAbortController(controller)

    try {
      const response = await llmAPI.chat(
        {
          message: messageContent,
          conversationId: conversationId ?? undefined,
          modelId: currentModel?.id,
        },
        { signal: controller.signal }
      )

      const data = response.data ?? {}
      const nextConversationId = data.conversationId || data.conversation_id
      if (nextConversationId) {
        setConversationId(nextConversationId)
      }

      // 后端返回的字段是 content，不是 answer 或 response
      const aiContent = data.content || data.answer || data.response || data.message || '⚠️ AI返回内容为空'
      updateMessage(assistantMessageId, {
        content: aiContent,
        metadata: data.metadata,
        timestamp: new Date().toISOString(),
      })
    } catch (error) {
      if (axios.isCancel(error)) {
        updateMessage(assistantMessageId, {
          content: '⏹️ 已停止生成。',
        })
      } else {
        console.error('发送消息失败:', error)
        updateMessage(assistantMessageId, {
          content: '⚠️ AI 响应失败，请稍后重试。',
        })
      }
    } finally {
      setLoading(false)
      setAbortController(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-grok-surface border-l border-grok-border overflow-hidden">
      {/* Header - 固定高度 */}
      <div className="px-4 py-3 border-b border-grok-border flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <RobotOutlined className="text-grok-accent text-xl" />
          <span className="font-semibold text-grok-text">AI 助手</span>
        </div>
        <div className="flex items-center gap-2">
          <Select
            size="small"
            className="min-w-[140px] text-grok-text"
            placeholder={models.length === 0 ? "加载中..." : "选择模型"}
            value={currentModel?.id}
            onChange={(id) => {
              const model = models.find((m) => m.id === id) || null
              console.log('[AIChatPanel] 切换模型:', model)
              setCurrentModel(model)
            }}
            options={models.map((m) => ({ label: m.name, value: m.id }))}
            loading={models.length === 0}
            dropdownStyle={{ 
              zIndex: 9999,
              backgroundColor: '#1a1a2e',
              border: '1px solid #2d3748'
            }}
            style={{
              color: '#e5e7eb',
            }}
          />
          <Button
            type="text"
            icon={<ClearOutlined />}
            onClick={clearMessages}
            className="text-grok-textMuted hover:text-grok-text"
          >
            清空
          </Button>
        </div>
      </div>

      {/* Messages - 可滚动区域 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-grok-textMuted">
            <div className="text-center">
              <RobotOutlined className="text-6xl mb-4 text-grok-accent" />
              <p>你好！我是 AI 助手</p>
              <p className="text-sm mt-2">有什么可以帮助你的吗？</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageItem
            key={message.id} message={message} usernameInitial={usernameInitial} onFeedback={handleFeedback} />
        ))}

        {isLoading && (
          // When streaming, the AI message placeholder is already rendered.
          // We can show a subtle loading indicator or rely on the disabled input.
          // For a better UX, we can show a blinking cursor at the end of the streaming message.
          // The current implementation will just show the input as disabled, which is clean.
          // If the last message is an empty assistant message, we can show the spinner.
          messages[messages.length - 1]?.role === 'assistant' &&
          messages[messages.length - 1]?.content === '' && (
            <div className="flex gap-3 justify-start"></div>
          )
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input - 固定在底部 */}
      <div className="px-4 py-3 border-t border-grok-border flex-shrink-0">
        {/* 附件列表 - 限制高度，避免把输入框推出屏幕 */}
        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2 max-h-[100px] overflow-y-auto">
            {attachments.map((file) => (
              <div
                key={file.uid}
                className="flex items-center gap-1 px-2 py-1 bg-grok-bg border border-grok-border rounded text-xs"
              >
                <PaperClipOutlined className="text-grok-accent" />
                <span className="text-grok-text max-w-[120px] truncate">{file.name}</span>
                <CloseOutlined
                  className="text-grok-textMuted hover:text-red-500 cursor-pointer"
                  onClick={() => setAttachments(attachments.filter((f) => f.uid !== file.uid))}
                />
              </div>
            ))}
          </div>
        )}
        {isLoading ? (
          <div className="flex justify-center">
            <Button type="default" icon={<StopOutlined />} onClick={stopGeneration}>
              停止生成
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex gap-2 items-center">
              {/* 附件上传按钮 */}
              <Upload
                beforeUpload={(file) => {
                  if (attachments.length >= 5) {
                    antdMessage.warning('最多只能上传5个附件')
                    return false
                  }
                  setAttachments([...attachments, file])
                  return false
                }}
                fileList={[]}
                showUploadList={false}
                accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
              >
                <Tooltip title="添加附件 (最多5个)">
                  <Button
                    size="small"
                    icon={<PaperClipOutlined />}
                    className="text-grok-textMuted hover:text-grok-accent"
                  />
                </Tooltip>
              </Upload>

              {/* 提示词快捷选择 */}
              <Dropdown
                menu={{
                  items: prompts.map((p) => ({
                    key: p.id,
                    label: p.title,
                    onClick: () => setInput(p.content),
                  })),
                }}
                placement="topLeft"
                disabled={prompts.length === 0}
              >
                <Tooltip title="快捷提示词">
                  <Button
                    size="small"
                    icon={<ThunderboltOutlined />}
                    className="text-grok-textMuted hover:text-grok-accent"
                  >
                    提示词 ({prompts.length})
                  </Button>
                </Tooltip>
              </Dropdown>
            </div>

            <div className="flex gap-2">
              <Input.TextArea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleSend()
                  }
                }}
                placeholder="输入消息... (Shift+Enter 换行)"
                autoSize={{ minRows: 3, maxRows: 10 }}
                className="grok-input"
                style={{ minHeight: '80px' }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSend}
                disabled={!input.trim()}
                className="grok-btn-primary"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

AIChatPanel.displayName = 'AIChatPanel'

export default AIChatPanel
