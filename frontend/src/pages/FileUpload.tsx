import React, { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  Table,
  message,
  Tag,
  Space,
  Modal,
  Progress,
} from 'antd'
import {
  UploadOutlined,
  FolderOpenOutlined,
  DeleteOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { fileAPI } from '@/services/api'
import type { FileInfo } from '@/types'

const FileUpload: React.FC = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [matchingResult, setMatchingResult] = useState<any>(null)
  const [duplicates, setDuplicates] = useState<any[]>([])
  const [showDuplicateModal, setShowDuplicateModal] = useState(false)

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    const formData = new FormData()
    fileList.forEach((file) => {
      // UploadFile对象的originFileObj才是真正的File对象
      if (file.originFileObj) {
        formData.append('files', file.originFileObj)
      }
    })

    setUploading(true)
    try {
      const response = await fileAPI.uploadFiles(formData, setUploadProgress)
      
      // 如果返回重复文件信息，提示用户选择覆盖
      if (response?.data?.duplicates && response.data.duplicates.length > 0) {
        setDuplicates(response.data.duplicates)
        setShowDuplicateModal(true)
      }

      message.success('文件上传成功（解析已安排）')
      setFileList([])
      setUploadProgress(0)

      // 显示匹配结果（可能包含 duplicates）
      setMatchingResult(response.data)
    } catch (error: any) {
      console.error('Upload error:', error)
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '上传失败'
      message.error(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  const handleConfirmOverwrite = async () => {
    // 重新上传所有当前选择文件并携带 overwrite=true
    if (fileList.length === 0) {
      setShowDuplicateModal(false)
      return
    }

    const formData = new FormData()
    fileList.forEach((file) => {
      if (file.originFileObj) formData.append('files', file.originFileObj)
    })
    formData.append('overwrite', 'true')

    try {
      setUploading(true)
      const response = await fileAPI.uploadFiles(formData, setUploadProgress)
      message.success('覆盖上传已提交，解析已安排')
      setMatchingResult(response.data)
      setDuplicates([])
      setShowDuplicateModal(false)
      setFileList([])
    } catch (err: any) {
      message.error('覆盖上传失败')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDelete = async (fileId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个文件吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await fileAPI.deleteFile(fileId)
          message.success('删除成功')
          // 从当前结果中移除已删除的文件
          if (matchingResult?.files) {
            setMatchingResult({
              ...matchingResult,
              files: matchingResult.files.filter((f: any) => f.id !== fileId)
            })
          }
        } catch (error: any) {
          message.error(error.response?.data?.detail || error.response?.data?.message || '删除失败')
        }
      },
    })
  }

  const handleDownload = async (fileId: string, fileName: string) => {
    try {
      const response = await fileAPI.downloadFile(fileId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error: any) {
      message.error('下载失败')
    }
  }

  // 不再自动加载历史文件，仅显示当次上传结果

  const columns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          tender: 'blue',
          proposal: 'green',
          summary: 'orange',
          other: 'default',
        }
        const labelMap: Record<string, string> = {
          tender: '招标文件',
          proposal: '投标文件',
          summary: '总结文件',
          other: '其他',
        }
        return <Tag color={colorMap[type]}>{labelMap[type]}</Tag>
      },
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => {
        if (size < 1024) return `${size} B`
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
        return `${(size / (1024 * 1024)).toFixed(2)} MB`
      },
    },
    {
      title: '上传时间',
      dataIndex: 'uploadedAt',
      key: 'uploadedAt',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: FileInfo) => (
        <Space>
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record.id, record.name)}
          >
            下载
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-grok-text">文件上传及存档</h1>
      </div>

      {/* Upload Card */}
      <Card className="grok-card">
        <div className="space-y-4">
          <Upload.Dragger
            multiple
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false}
            className="grok-input"
          >
            <p className="ant-upload-drag-icon">
              <FolderOpenOutlined className="text-grok-accent text-5xl" />
            </p>
            <p className="ant-upload-text text-grok-text">
              点击或拖拽文件到此区域上传
            </p>
            <p className="ant-upload-hint text-grok-textMuted">
              支持单个或批量上传。支持 PDF、Word、Excel 等格式
            </p>
          </Upload.Dragger>

          {uploading && (
            <Progress
              percent={uploadProgress}
              status="active"
              strokeColor="#00D9FF"
            />
          )}

          <div className="flex gap-2">
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={handleUpload}
              disabled={fileList.length === 0}
              loading={uploading}
              className="grok-btn-primary"
            >
              开始上传
            </Button>
            <Button
              onClick={() => setFileList([])}
              disabled={fileList.length === 0 || uploading}
              className="grok-btn-secondary"
            >
              清空列表
            </Button>
          </div>
        </div>
      </Card>

      {/* Matching Result */}
      {matchingResult && (
        <Card
          className="grok-card"
          title={
            <div className="flex items-center gap-2">
              <CheckCircleOutlined className="text-grok-success" />
              <span>匹配结果</span>
            </div>
          }
        >
          <div className="space-y-2">
            <p className="text-grok-text">
              共上传 <span className="text-grok-accent">{matchingResult.totalFiles}</span> 个文件
            </p>
            <p className="text-grok-text">
              成功匹配 <span className="text-grok-accent">{matchingResult.matchedPairs}</span> 对
            </p>
            {matchingResult.unmatchedFiles && matchingResult.unmatchedFiles.length > 0 && (
              <p className="text-grok-warning">
                未匹配文件：{matchingResult.unmatchedFiles.join(', ')}
              </p>
            )}
          </div>
        </Card>
      )}

      {/* File List - 仅显示当次上传 */}
      {matchingResult?.files && matchingResult.files.length > 0 && (
        <Card className="grok-card" title="已上传清单">
          <Table
            dataSource={matchingResult.files}
            columns={columns}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `本次上传 ${total} 个文件`,
            }}
          />
        </Card>
      )}

      {/* Duplicate Modal */}
      <Modal
        title="发现重复文件"
        open={showDuplicateModal}
        onOk={handleConfirmOverwrite}
        onCancel={() => setShowDuplicateModal(false)}
        okText="覆盖并上传"
        cancelText="取消"
      >
        <div>
          <p>检测到以下重复文件，是否要覆盖已有文件并重新解析？</p>
          <ul>
            {duplicates.map((d) => (
              <li key={d.existing_id}>{d.name} （已存在 ID: {d.existing_id}）</li>
            ))}
          </ul>
        </div>
      </Modal>
    </div>
  )
}

export default FileUpload
