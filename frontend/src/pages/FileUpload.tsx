import React, { useState, useEffect } from 'react'
import {
  Card,
  Upload,
  Button,
  Table,
  Tag,
  Space,
  Modal,
  Progress,
  List,
  Tree,
  Descriptions,
  Statistic,
  Row,
  Col,
  Popconfirm,
  Tabs,
  App,
} from 'antd'
import {
  UploadOutlined,
  FolderOpenOutlined,
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  DatabaseOutlined,
  FolderOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd'
import Split from 'react-split'
import { fileAPI } from '@/services/api'
import type { FileInfo } from '@/types'
import { useAuthStore } from '@/store/authStore'

interface DocumentIndex {
  id: string
  fileName: string
  chapters: {
    title: string
    level: number
    pageNum: number
    children?: any[]
  }[]
}

interface KnowledgeEntry {
  id: string
  title: string
  content: string
  category: string
  fileName: string
  createdAt: string
}

interface DatabaseStats {
  totalFiles: number
  totalSize: number
  storageUsed: number
  knowledgeEntries: number
  lastUpdate: string
}

const FileUpload: React.FC = () => {
  const { message } = App.useApp() // 使用Ant Design 5.x hooks
  const { user } = useAuthStore() // 获取当前登录用户
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFilesList, setUploadedFilesList] = useState<FileInfo[]>([])
  const [databaseStats, setDatabaseStats] = useState<DatabaseStats | null>(null)
  const [knowledgeEntries, setKnowledgeEntries] = useState<KnowledgeEntry[]>([])
  const [documentIndexes, setDocumentIndexes] = useState<DocumentIndex[]>([])
  const [selectedDoc, setSelectedDoc] = useState<DocumentIndex | null>(null)
  const [processingFiles, setProcessingFiles] = useState<Set<string>>(new Set())

  // 初始加载数据
  useEffect(() => {
    loadUploadedFiles()
    loadDatabaseStats()
    loadKnowledgeEntries()
  }, [])

  const loadUploadedFiles = async () => {
    try {
      const response = await fileAPI.getFiles()
      setUploadedFilesList(response.data?.files || [])
    } catch (error) {
      console.error('加载文件列表失败:', error)
    }
  }

  const loadDatabaseStats = async () => {
    try {
      const response = await fileAPI.getDatabaseDetails()
      setDatabaseStats(response.data)
    } catch (error) {
      console.error('获取数据库统计失败:', error)
    }
  }

  const loadKnowledgeEntries = async () => {
    try {
      const response = await fileAPI.getKnowledgeBaseEntries()
      setKnowledgeEntries(response.data || [])
    } catch (error) {
      console.error('获取知识库条目失败:', error)
    }
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    if (!user || !user.username) {
      message.error('无法获取当前用户信息，请重新登录')
      return
    }

    const formData = new FormData()
    let hasValidFile = false
    
    // 关键修复：正确获取File对象
    fileList.forEach((file) => {
      // Ant Design Upload的file有三种可能：
      // 1. file.originFileObj - 新上传的文件
      // 2. file本身就是File对象
      const fileObj = file.originFileObj || file
      
      if (fileObj instanceof File || (fileObj && fileObj.size !== undefined)) {
        console.log('添加文件:', fileObj.name || file.name, '大小:', fileObj.size)
        formData.append('files', fileObj)
        hasValidFile = true
      } else {
        console.error('无效的文件对象:', file)
      }
    })
    
    if (!hasValidFile) {
      message.error('没有有效的文件可以上传')
      return
    }

    // 添加上传人参数（必需）
    formData.append('uploader', user.username)
    // 添加重复文件处理策略（默认跳过）
    formData.append('duplicate_action', 'skip')

    setUploading(true)
    console.log('开始上传文件，数量:', fileList.length, '上传人:', user.username)
    
    try {
      const response = await fileAPI.uploadFiles(formData, setUploadProgress)
      console.log('上传成功响应:', response.data)
      
      const result = response.data
      
      // 显示上传结果
      if (result.uploaded && result.uploaded.length > 0) {
        message.success(`成功上传 ${result.uploaded.length} 个文件`)
      }
      
      // 显示重复文件信息
      if (result.duplicates && result.duplicates.length > 0) {
        result.duplicates.forEach((f: any) => {
          message.warning(`${f.name}: ${f.message || '文件已存在，已跳过'}`)
        })
      }
      
      if (result.failed && result.failed.length > 0) {
        result.failed.forEach((f: any) => {
          message.error(`${f.name}: ${f.error}`)
        })
      }
      
      if (result.duplicates && result.duplicates.length > 0) {
        result.duplicates.forEach((f: any) => {
          message.warning(`${f.name}: 文件已存在`)
        })
      }
      
      // 清空文件列表
      setFileList([])
      setUploadProgress(0)

      // 启动文件处理流程
      const uploadedFiles = result.uploaded || []
      console.log('已上传文件列表:', uploadedFiles)
      
      if (uploadedFiles.length > 0) {
        // 处理文件生成知识库
        await processUploadedFiles(uploadedFiles)
      }

      // 刷新所有数据
      console.log('刷新页面数据...')
      await Promise.all([
        loadUploadedFiles(),
        loadDatabaseStats(),
        loadKnowledgeEntries(),
      ])
      console.log('数据刷新完成')
      
    } catch (error: any) {
      console.error('上传错误:', error)
      console.error('错误详情:', error.response?.data)
      
      // 处理422错误（FastAPI validation error）
      let errorMsg = '上传失败'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        
        // 如果detail是数组（FastAPI validation errors）
        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => {
            if (typeof err === 'string') return err
            if (err.msg) return `${err.loc?.join('.')}: ${err.msg}`
            return JSON.stringify(err)
          }).join('; ')
        } 
        // 如果detail是字符串
        else if (typeof detail === 'string') {
          errorMsg = detail
        }
        // 其他情况
        else {
          errorMsg = JSON.stringify(detail)
        }
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message
      } else if (error.message) {
        errorMsg = error.message
      }
      
      message.error(errorMsg)
    } finally {
      setUploading(false)
    }
  }

  // 处理上传的文件：生成知识库和文档索引
  const processUploadedFiles = async (files: FileInfo[]) => {
    const fileIds = files.map(f => f.id)
    console.log('准备处理文件IDs:', fileIds)
    setProcessingFiles(new Set(fileIds))

    try {
      // 调用后端API启动文件处理
      console.log('调用processFiles API...')
      const response = await fileAPI.processFiles(fileIds)
      console.log('处理响应:', response.data)
      
      if (response.data?.documentIndexes) {
        setDocumentIndexes(response.data.documentIndexes)
        console.log('已设置文档索引:', response.data.documentIndexes.length)
      }

      message.success('文件处理完成，已生成文档索引和知识库')
    } catch (error: any) {
      console.error('文件处理错误:', error)
      const errorMsg = error.response?.data?.detail || error.message || '文件处理失败'
      message.error(errorMsg)
    } finally {
      setProcessingFiles(new Set())
    }
  }

  // 删除已上传的文件
  const handleDeleteFile = async (fileId: string) => {
    try {
      await fileAPI.deleteFile(fileId)
      message.success('文件删除成功')
      await loadUploadedFiles()
      await loadDatabaseStats()
    } catch (error) {
      message.error('删除文件失败')
    }
  }

  // 下载文件
  const handleDownloadFile = async (fileId: string, fileName: string) => {
    try {
      const response = await fileAPI.downloadFile(fileId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载文件失败')
    }
  }


  // 上传文件列表的列定义
  const uploadedFilesColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (text: string, record: FileInfo) => (
        <Space>
          <FileTextOutlined />
          <span>{text}</span>
          {processingFiles.has(record.id) && <Tag color="processing">处理中</Tag>}
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
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
      width: 180,
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: any, record: FileInfo) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadFile(record.id, record.name)}
          >
            下载
          </Button>
          <Popconfirm
            title="确定删除此文件？"
            onConfirm={() => handleDeleteFile(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // 渲染文档目录树
  const renderDocumentTree = (chapters: any[]) => {
    const treeData = chapters.map((chapter, index) => ({
      title: `${chapter.title} (第${chapter.pageNum}页)`,
      key: `${index}`,
      children: chapter.children?.map((child: any, childIndex: number) => ({
        title: `${child.title} (第${child.pageNum}页)`,
        key: `${index}-${childIndex}`,
      })),
    }))

    return <Tree treeData={treeData} defaultExpandAll />
  }

  return (
    <div className="h-full w-full overflow-hidden">
      <div className="px-6 py-4">
        <h1 className="text-2xl font-bold text-grok-text">文件上传及存档</h1>
      </div>

      <Split
        className="flex h-[calc(100%-80px)]"
        sizes={[60, 40]}
        minSize={[400, 300]}
        maxSize={[Infinity, 700]}
        gutterSize={8}
        snapOffset={30}
        dragInterval={1}
        direction="horizontal"
        cursor="col-resize"
      >
        {/* 左侧：上传区域和上传文件列表 */}
        <div className="h-full overflow-y-auto px-6 space-y-6">
          {/* 文件上传卡片 */}
          <Card className="grok-card">
            <div className="space-y-4">
              <Upload.Dragger
                multiple
                fileList={fileList}
                onChange={({ fileList }) => setFileList(fileList)}
                beforeUpload={(file) => {
                  // 返回 false 阻止自动上传，但保留文件对象
                  return false
                }}
                customRequest={() => {
                  // 不使用默认上传，我们手动控制
                }}
                className="grok-input"
                style={{ minHeight: 180 }}
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

              <div className="flex flex-wrap gap-2">
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

          {/* 已上传文件列表 */}
          <Card 
            className="grok-card" 
            title={
              <Space>
                <FileTextOutlined />
                <span>已上传文件 ({uploadedFilesList.length})</span>
              </Space>
            }
          >
            <Table
              dataSource={uploadedFilesList}
              columns={uploadedFilesColumns}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `共 ${total} 个文件`,
              }}
              size="small"
            />
          </Card>
        </div>

        {/* 右侧：文件存档和知识库预览 */}
        <div className="h-full overflow-y-auto px-6 space-y-6">
          {/* 数据库统计 */}
          <Card 
            className="grok-card"
            title={
              <Space>
                <DatabaseOutlined />
                <span>存档统计</span>
              </Space>
            }
          >
            {databaseStats ? (
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="文件总数"
                    value={databaseStats.totalFiles}
                    suffix="个"
                    valueStyle={{ color: '#00D9FF' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="存储占用"
                    value={databaseStats.storageUsed}
                    suffix="MB"
                    precision={2}
                    valueStyle={{ color: '#00D9FF' }}
                  />
                </Col>
                <Col span={12} className="mt-4">
                  <Statistic
                    title="知识条目"
                    value={databaseStats.knowledgeEntries}
                    suffix="条"
                    valueStyle={{ color: '#00D9FF' }}
                  />
                </Col>
                <Col span={12} className="mt-4">
                  <Statistic
                    title="最后更新"
                    value={databaseStats.lastUpdate}
                    valueStyle={{ fontSize: '14px', color: '#00D9FF' }}
                  />
                </Col>
              </Row>
            ) : (
              <div className="text-center text-grok-textMuted py-8">
                暂无统计数据
              </div>
            )}
          </Card>

          {/* 文档索引和知识库 */}
          <Card className="grok-card">
            <Tabs
              items={[
                {
                  key: 'indexes',
                  label: (
                    <span>
                      <FolderOutlined /> 文档目录索引
                    </span>
                  ),
                  children: (
                    <div className="space-y-4">
                      {documentIndexes.length > 0 ? (
                        documentIndexes.map((doc) => (
                          <Card
                            key={doc.id}
                            size="small"
                            title={doc.fileName}
                            extra={
                              <Button
                                type="link"
                                size="small"
                                icon={<EyeOutlined />}
                                onClick={() => setSelectedDoc(doc)}
                              >
                                查看
                              </Button>
                            }
                          >
                            {renderDocumentTree(doc.chapters)}
                          </Card>
                        ))
                      ) : (
                        <div className="text-center text-grok-textMuted py-8">
                          暂无文档索引，请上传文件后自动生成
                        </div>
                      )}
                    </div>
                  ),
                },
                {
                  key: 'knowledge',
                  label: (
                    <span>
                      <DatabaseOutlined /> 知识库条目
                    </span>
                  ),
                  children: (
                    <List
                      dataSource={knowledgeEntries}
                      locale={{ emptyText: '暂无知识库条目' }}
                      renderItem={(item) => (
                        <List.Item
                          actions={[
                            <Button type="link" size="small" icon={<EyeOutlined />}>
                              查看
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta
                            title={item.title}
                            description={
                              <Space direction="vertical" size="small">
                                <Tag color="blue">{item.category}</Tag>
                                <span className="text-xs text-grok-textMuted">
                                  来源: {item.fileName}
                                </span>
                                <span className="text-xs text-grok-textMuted">
                                  创建时间: {new Date(item.createdAt).toLocaleString('zh-CN')}
                                </span>
                              </Space>
                            }
                          />
                        </List.Item>
                      )}
                      pagination={{
                        pageSize: 5,
                        size: 'small',
                      }}
                    />
                  ),
                },
              ]}
            />
          </Card>
        </div>
      </Split>

      {/* 文档查看模态框 */}
      <Modal
        title={selectedDoc?.fileName}
        open={!!selectedDoc}
        onCancel={() => setSelectedDoc(null)}
        footer={null}
        width={800}
      >
        {selectedDoc && (
          <div className="space-y-4">
            <Descriptions title="文档信息" column={1} size="small">
              <Descriptions.Item label="文件名">{selectedDoc.fileName}</Descriptions.Item>
              <Descriptions.Item label="章节数">{selectedDoc.chapters.length}</Descriptions.Item>
            </Descriptions>
            {renderDocumentTree(selectedDoc.chapters)}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default FileUpload
