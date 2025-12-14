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
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [collapsedDocs, setCollapsedDocs] = useState<Set<string>>(new Set()) // 折叠状态
  const [expandedKeys, setExpandedKeys] = useState<Record<string, string[]>>({}) // 每个文档的展开keys
  const [allExpanded, setAllExpanded] = useState<Record<string, boolean>>({}) // 每个文档是否全部展开
  const [currentUploadIds, setCurrentUploadIds] = useState<string[]>([]) // 保存本次上传的文件ID，用于自动刷新完成后只加载这些文件
  const [allDisplayFileIds, setAllDisplayFileIds] = useState<string[]>([]) // 保存所有要显示的文件ID（新上传+重复）
  const [duplicateFilesList, setDuplicateFilesList] = useState<any[]>([]) // 保存重复文件的显示信息

  // 初始加载数据 - 每次打开页面重置所有状态（不自动加载已上传文件）
  useEffect(() => {
    // 1. 清空本地UI状态
    setFileList([])
    setSelectedDoc(null)
    setProcessingFiles(new Set())
    setAutoRefresh(false)
    setUploadProgress(0)
    setUploading(false)
    setCollapsedDocs(new Set())
    setExpandedKeys({})
    setAllExpanded({})
    
    // 2. 清空数据列表（不显示之前的文件）
    setUploadedFilesList([])
    setKnowledgeEntries([])
    setDocumentIndexes([])
    setDatabaseStats(null)
    
    // 3. 不自动加载服务器数据，等待用户手动上传或刷新
    // loadUploadedFiles()
    // loadDatabaseStats()
    // loadKnowledgeEntries()
    // loadDocumentIndexes()
  }, [])

  // 自动刷新机制：当有文件处理中时，每5秒刷新一次
  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(async () => {
      console.log('自动刷新文件状态...')
      
      // 如果只有重复文件（没有新上传），直接停止刷新
      if (currentUploadIds.length === 0) {
        console.log('只有重复文件，无需自动刷新')
        setAutoRefresh(false)
        return
      }
      
      // 查询新上传文件的状态，同时保留重复文件
      const response = await fileAPI.getFiles()
      const allFiles = response.data?.files || []
      // 只保留本次上传的文件
      const currentFiles = allFiles.filter((f: any) => currentUploadIds.includes(f.id))
      
      // 合并新上传文件和重复文件
      const combinedFiles = [...currentFiles, ...duplicateFilesList]
      setUploadedFilesList(combinedFiles)
      
      // 检查是否还有处理中的文件
      const hasProcessing = currentFiles.some((f: any) => 
        ['parsing', 'archiving', 'indexing'].includes(f.status)
      )
      
      if (!hasProcessing) {
        console.log('所有文件处理完成，停止自动刷新')
        setAutoRefresh(false)
        // 最后刷新一次数据 - 加载所有文件（新上传+重复）的数据
        await loadDatabaseStats()
        if (allDisplayFileIds.length > 0) {
          await loadSpecificDocumentIndexes(allDisplayFileIds)
          await loadKnowledgeEntriesForFiles(allDisplayFileIds)
        }
      }
    }, 5000) // 每5秒刷新一次
    
    return () => clearInterval(interval)
  }, [autoRefresh, currentUploadIds, allDisplayFileIds, duplicateFilesList]) // 依赖所有相关状态


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
      console.log('获取知识库条目:', response.data)
      setKnowledgeEntries(response.data || [])
    } catch (error) {
      console.error('获取知识库条目失败:', error)
    }
  }

  const loadDocumentIndexes = async () => {
    try {
      const response = await fileAPI.getDocumentIndexes()
      console.log('获取文档索引:', response.data)
      if (Array.isArray(response.data)) {
        // 后端已经返回分组后的数据，直接使用
        setDocumentIndexes(response.data)
        // 默认折叠所有文档
        const allDocIds = new Set(response.data.map((doc: any) => doc.id))
        setCollapsedDocs(allDocIds)
      }
    } catch (error) {
      console.error('获取文档索引失败:', error)
    }
  }

  // 只加载特定文件的目录索引
  const loadSpecificDocumentIndexes = async (fileIds: string[]) => {
    try {
      const indexes = []
      for (const fileId of fileIds) {
        const response = await fileAPI.getDocumentIndexes(fileId)
        console.log(`获取文件 ${fileId} 的目录索引:`, response.data)
        if (Array.isArray(response.data) && response.data.length > 0) {
          indexes.push(...response.data)
        }
      }
      setDocumentIndexes(indexes)
      // 默认折叠所有文档
      const allDocIds = new Set(indexes.map((doc: any) => doc.id))
      setCollapsedDocs(allDocIds)
    } catch (error) {
      console.error('获取特定文档索引失败:', error)
    }
  }

  // 只加载特定文件的知识库条目
  const loadKnowledgeEntriesForFiles = async (fileIds: string[]) => {
    try {
      const response = await fileAPI.getKnowledgeBaseEntries()
      console.log('获取知识库条目:', response.data)
      if (Array.isArray(response.data)) {
        // 过滤出只属于本次上传文件的知识库条目
        // 注意：需要根据实际数据结构调整过滤逻辑
        const filtered = response.data.filter((entry: any) => 
          fileIds.some(id => entry.id?.includes(id) || entry.fileName?.includes(id))
        )
        setKnowledgeEntries(filtered)
      }
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
      const fileObj = file.originFileObj || (file as any)
      
      if (fileObj instanceof File || (fileObj && fileObj.size !== undefined)) {
        console.log('添加文件:', fileObj.name || file.name, '大小:', fileObj.size)
        formData.append('files', fileObj as Blob)
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
        message.success(`成功上传 ${result.uploaded.length} 个文件，正在后台处理...`)
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
      
      // 清空文件列表，防止重复上传
      setFileList([])
      setUploadProgress(0)

      // 后端已通过 background_tasks 自动处理文件解析、归档和向量化
      // 无需前端再次调用 processFiles
      
      // 收集所有需要显示的文件ID：新上传的 + 重复的历史文件
      const allFileIds: string[] = []
      const displayFiles: any[] = []
      const duplicates: any[] = []
      
      // 1. 处理新上传的文件
      if (result.uploaded && result.uploaded.length > 0) {
        const uploadedIds = result.uploaded.map((f: any) => f.id)
        allFileIds.push(...uploadedIds)
        displayFiles.push(...result.uploaded)
        setCurrentUploadIds(uploadedIds)
      }
      
      // 2. 处理重复文件：显示历史文件并标记为重复
      if (result.duplicates && result.duplicates.length > 0) {
        result.duplicates.forEach((dup: any) => {
          allFileIds.push(dup.existing_id)
          // 添加重复文件到显示列表，使用历史文件的ID
          const duplicateFile = {
            id: dup.existing_id,
            name: dup.existing_name || dup.name,
            status: 'completed',
            isDuplicate: true,  // 标记为重复
            message: dup.message
          }
          displayFiles.push(duplicateFile)
          duplicates.push(duplicateFile)
        })
      }
      
      // 保存所有文件ID和重复文件信息，供自动刷新使用
      setAllDisplayFileIds(allFileIds)
      setDuplicateFilesList(duplicates)
      
      // 显示所有文件（新上传 + 重复）
      setUploadedFilesList(displayFiles)
      
      // 加载数据库统计
      await loadDatabaseStats()
      
      // 加载所有文件的目录索引和知识库条目（包括重复文件）
      if (allFileIds.length > 0) {
        await loadSpecificDocumentIndexes(allFileIds)
        await loadKnowledgeEntriesForFiles(allFileIds)
      }
      
      // 启动自动刷新，监控处理状态
      setAutoRefresh(true)
      
      console.log('数据刷新完成，已启动自动刷新')
      
      console.log('数据刷新完成，已启动自动刷新')
      
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
      render: (text: string, record: FileInfo) => {
        const status = (record as any).status || 'uploaded'
        const isDuplicate = (record as any).isDuplicate || false
        const statusMap: Record<string, { text: string, color: string }> = {
          'uploaded': { text: '已上传', color: 'default' },
          'parsing': { text: '解析中', color: 'processing' },
          'parsed': { text: '已解析', color: 'success' },
          'archiving': { text: '归档中', color: 'processing' },
          'archived': { text: '已归档', color: 'success' },
          'indexing': { text: '索引中', color: 'processing' },
          'indexed': { text: '已完成', color: 'success' },
          'completed': { text: '已完成', color: 'success' },
          'parse_failed': { text: '处理失败', color: 'error' },
        }
        const statusInfo = statusMap[status] || { text: status, color: 'default' }
        
        return (
          <Space>
            <FileTextOutlined />
            <span>{text}</span>
            {isDuplicate && <Tag color="warning">重复文件</Tag>}
            {processingFiles.has(record.id) && <Tag color="processing">处理中</Tag>}
            {!processingFiles.has(record.id) && status && !isDuplicate && (
              <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
            )}
          </Space>
        )
      },
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
  const renderDocumentTree = (chapters: any[], docId: string) => {
    if (!chapters || chapters.length === 0) {
      return <div className="text-grok-textMuted text-sm">暂无章节数据</div>
    }

    // 将扁平的章节列表转换为树形结构
    const buildTree = (items: any[]): any[] => {
      const tree: any[] = []
      const levelStacks: any[][] = [[], [], [], [], []] // 支持5层
      const allKeys: string[] = []

      items.forEach((item, index) => {
        // 兼容旧字段: level/number/title 和 chapter_level/chapter_number/chapter_title
        const level = item.level ?? item.chapter_level ?? 1
        const number = item.number ?? item.chapter_number ?? ''
        const title = item.title ?? item.chapter_title ?? '未命名'
        const key = `${docId}-${index}`
        allKeys.push(key)
        
        const node = {
          title: number ? `${number} ${title}` : title,
          key,
          children: []
        }

        if (level === 1) {
          tree.push(node)
          levelStacks[1] = [node]
        } else {
          // 找到父节点
          const parentLevel = level - 1
          if (levelStacks[parentLevel] && levelStacks[parentLevel].length > 0) {
            const parent = levelStacks[parentLevel][levelStacks[parentLevel].length - 1]
            parent.children.push(node)
          } else {
            // 没有找到父节点，加到根节点
            tree.push(node)
          }
          levelStacks[level] = levelStacks[level] || []
          levelStacks[level].push(node)
        }
      })

      return tree
    }

    const treeData = buildTree(chapters)
    const currentExpandedKeys = expandedKeys[docId] || []
    
    return (
      <Tree 
        treeData={treeData} 
        expandedKeys={currentExpandedKeys}
        onExpand={(keys) => {
          setExpandedKeys(prev => ({ ...prev, [docId]: keys as string[] }))
        }}
        className="text-sm" 
      />
    )
  }

  // 全部展开/折叠函数
  const handleToggleAll = (docId: string, chapters: any[]) => {
    const isExpanded = allExpanded[docId]
    
    if (isExpanded) {
      // 折叠全部
      setExpandedKeys(prev => ({ ...prev, [docId]: [] }))
      setAllExpanded(prev => ({ ...prev, [docId]: false }))
    } else {
      // 展开全部 - 生成所有keys
      const allKeys = chapters.map((_, index) => `${docId}-${index}`)
      setExpandedKeys(prev => ({ ...prev, [docId]: allKeys }))
      setAllExpanded(prev => ({ ...prev, [docId]: true }))
    }
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
                beforeUpload={() => {
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
                        documentIndexes.map((doc) => {
                          const isCollapsed = collapsedDocs.has(doc.id)
                          return (
                            <Card
                              key={doc.id}
                              size="small"
                              title={doc.fileName}
                              extra={
                                <Space>
                                  <Button
                                    type="link"
                                    size="small"
                                    onClick={() => {
                                      const newCollapsed = new Set(collapsedDocs)
                                      if (isCollapsed) {
                                        newCollapsed.delete(doc.id)
                                      } else {
                                        newCollapsed.add(doc.id)
                                      }
                                      setCollapsedDocs(newCollapsed)
                                    }}
                                  >
                                    {isCollapsed ? '展开' : '折叠'}
                                  </Button>
                                  {!isCollapsed && (
                                    <Button
                                      type="link"
                                      size="small"
                                      onClick={() => handleToggleAll(doc.id, doc.chapters)}
                                    >
                                      {allExpanded[doc.id] ? '全部折叠' : '全部展开'}
                                    </Button>
                                  )}
                                  <Button
                                    type="link"
                                    size="small"
                                    icon={<EyeOutlined />}
                                    onClick={() => setSelectedDoc(doc)}
                                  >
                                    查看
                                  </Button>
                                  <Popconfirm
                                    title="确定删除此文件？"
                                    onConfirm={async () => {
                                      try {
                                        await fileAPI.deleteFile(doc.id)
                                        message.success('文件删除成功')
                                        loadDocumentIndexes()
                                        loadUploadedFiles()
                                      } catch (error) {
                                        message.error('删除文件失败')
                                      }
                                    }}
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
                              }
                            >
                              {!isCollapsed && renderDocumentTree(doc.chapters, doc.id)}
                            </Card>
                          )
                        })
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
            {renderDocumentTree(selectedDoc.chapters, selectedDoc.id)}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default FileUpload
