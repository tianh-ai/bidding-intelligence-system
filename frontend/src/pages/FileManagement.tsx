import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Space, message, Modal, Tag, Input } from 'antd'
import { DeleteOutlined, DownloadOutlined, ReloadOutlined, SearchOutlined, FolderOutlined } from '@ant-design/icons'
import { fileAPI } from '@/services/api'

interface FileRecord {
  id: string
  filename: string
  filetype: string
  doc_type: string
  file_size: number
  created_at: string
}

const FileManagement: React.FC = () => {
  const [files, setFiles] = useState<FileRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')

  const loadFiles = async () => {
    setLoading(true)
    try {
      const response = await fileAPI.getFiles()
      setFiles(response.data.files || [])
    } catch (error) {
      message.error('加载文件列表失败')
      console.error('Load files error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFiles()
  }, [])

  const handleDelete = async (fileId: string, filename: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除文件 "${filename}" 吗？此操作不可恢复。`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        try {
          await fileAPI.deleteFile(fileId)
          message.success('删除成功')
          loadFiles()
        } catch (error: any) {
          message.error(error.response?.data?.detail || '删除失败')
        }
      },
    })
  }

  const handleDownload = async (fileId: string, filename: string) => {
    try {
      const response = await fileAPI.downloadFile(fileId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error: any) {
      message.error('下载失败')
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const filteredFiles = files.filter(file =>
    file.filename.toLowerCase().includes(searchText.toLowerCase())
  )

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
      width: '30%',
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: '12%',
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          tender: 'blue',
          proposal: 'green',
          reference: 'orange',
          other: 'default',
        }
        const labelMap: Record<string, string> = {
          tender: '招标文件',
          proposal: '投标文件',
          reference: '参考文件',
          other: '其他',
        }
        return <Tag color={colorMap[type] || 'default'}>{labelMap[type] || type}</Tag>
      },
    },
    {
      title: '格式',
      dataIndex: 'filetype',
      key: 'filetype',
      width: '10%',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: '12%',
      render: (size: number) => formatBytes(size),
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: '18%',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: '18%',
      render: (_: any, record: FileRecord) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.id, record.filename)}
          >
            下载
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id, record.filename)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-grok-text">
          <FolderOutlined className="mr-2" />
          文件管理
        </h1>
        <Button
          icon={<ReloadOutlined />}
          onClick={loadFiles}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      <Card className="grok-card">
        <div className="mb-4">
          <Input
            placeholder="搜索文件名..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
          />
        </div>

        <Table
          dataSource={filteredFiles}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个文件`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />
      </Card>
    </div>
  )
}

export default FileManagement
