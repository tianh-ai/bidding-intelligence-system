import React, { useState } from 'react'
import { Card, Input, Button, Select, Tabs, message, Spin } from 'antd'
import { FileTextOutlined, LinkOutlined, FolderOutlined } from '@ant-design/icons'
import { summaryAPI } from '@/services/api'
import ReactMarkdown from 'react-markdown'

const FileSummary: React.FC = () => {
  const [activeTab, setActiveTab] = useState('link')
  const [linkInput, setLinkInput] = useState('')
  const [fileId, setFileId] = useState('')
  const [folderPath, setFolderPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState('')

  const handleSummarizeLink = async () => {
    if (!linkInput) {
      message.warning('请输入链接')
      return
    }

    setLoading(true)
    try {
      const response = await summaryAPI.summarizeLink(linkInput)
      setSummary(response.data.summary)
      message.success('总结完成！')
    } catch (error: any) {
      message.error(error.response?.data?.message || '总结失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSummarizeFile = async () => {
    if (!fileId) {
      message.warning('请选择文件')
      return
    }

    setLoading(true)
    try {
      const response = await summaryAPI.summarizeFile(fileId)
      setSummary(response.data.summary)
      message.success('总结完成！')
    } catch (error: any) {
      message.error(error.response?.data?.message || '总结失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSummarizeFolder = async () => {
    if (!folderPath) {
      message.warning('请输入文件夹路径')
      return
    }

    setLoading(true)
    try {
      const response = await summaryAPI.summarizeFolder(folderPath)
      setSummary(response.data.summary)
      message.success('总结完成！')
    } catch (error: any) {
      message.error(error.response?.data?.message || '总结失败')
    } finally {
      setLoading(false)
    }
  }

  const tabItems = [
    {
      key: 'link',
      label: (
        <span>
          <LinkOutlined /> 链接总结
        </span>
      ),
      children: (
        <div className="space-y-4">
          <Input
            placeholder="输入招标公告链接..."
            value={linkInput}
            onChange={(e) => setLinkInput(e.target.value)}
            className="grok-input"
            size="large"
          />
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleSummarizeLink}
            loading={loading}
            className="grok-btn-primary"
          >
            开始总结
          </Button>
        </div>
      ),
    },
    {
      key: 'file',
      label: (
        <span>
          <FileTextOutlined /> 文件总结
        </span>
      ),
      children: (
        <div className="space-y-4">
          <Select
            placeholder="选择文件..."
            value={fileId}
            onChange={setFileId}
            className="w-full"
            size="large"
          />
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleSummarizeFile}
            loading={loading}
            className="grok-btn-primary"
          >
            开始总结
          </Button>
        </div>
      ),
    },
    {
      key: 'folder',
      label: (
        <span>
          <FolderOutlined /> 文件夹总结
        </span>
      ),
      children: (
        <div className="space-y-4">
          <Input
            placeholder="输入文件夹路径..."
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            className="grok-input"
            size="large"
          />
          <Button
            type="primary"
            icon={<FileTextOutlined />}
            onClick={handleSummarizeFolder}
            loading={loading}
            className="grok-btn-primary"
          >
            开始总结
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-grok-text">文件总结</h1>

      <Card className="grok-card">
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      {(loading || summary) && (
        <Card className="grok-card" title="总结结果">
          {loading ? (
            <div className="flex justify-center py-12">
              <Spin size="large" />
              <span className="ml-4 text-grok-textMuted">正在生成总结...</span>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}

export default FileSummary
