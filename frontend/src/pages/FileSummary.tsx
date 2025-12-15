import React, { useEffect, useMemo, useState } from 'react'
import { Card, Input, Button, Select, Tabs, message, Spin, Table, Tag, Empty, Descriptions } from 'antd'
import { FileTextOutlined, LinkOutlined, FolderOutlined, DatabaseOutlined } from '@ant-design/icons'
import { apiClient, fileAPI, summaryAPI, knowledgeAPI } from '@/services/api'
import ReactMarkdown from 'react-markdown'

const FileSummary: React.FC = () => {
  const [activeTab, setActiveTab] = useState('link')
  const [linkInput, setLinkInput] = useState('')
  const [fileId, setFileId] = useState('')
  const [folderPath, setFolderPath] = useState('')
  const [loading, setLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [fileOptions, setFileOptions] = useState<{ label: string; value: string }[]>([])
  const [knowledgeEntries, setKnowledgeEntries] = useState<any[]>([])
  const [knowledgeLoading, setKnowledgeLoading] = useState(false)
  const [selectedFileForKB, setSelectedFileForKB] = useState('')
  const [kbTotal, setKbTotal] = useState(0)
  const [kbPage, setKbPage] = useState(1)
  const [kbPageSize, setKbPageSize] = useState(10)
  const [kbDetailById, setKbDetailById] = useState<Record<string, any>>({})
  const [kbDetailLoadingIds, setKbDetailLoadingIds] = useState<Set<string>>(new Set())
  const [kbExpandedRowKeys, setKbExpandedRowKeys] = useState<React.Key[]>([])

  useEffect(() => {
    // 清除上次会话状态
    setLinkInput('')
    setFileId('')
    setFolderPath('')
    setSummary('')
    setActiveTab('link')
    
    // 加载文件列表
    loadFiles()
  }, [])

  const loadFiles = async () => {
    try {
      const res = await fileAPI.getFiles({ limit: 100 })
      const options = (res.data?.files || []).map((f: any) => ({
        label: f.name || f.filename || f.semanticName || '未命名文件',
        value: f.id,
      }))
      setFileOptions(options)
    } catch (error) {
      message.error('加载文件列表失败')
    }
  }

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
    } catch (error: unknown) {
      if (typeof error === 'object' && error !== null && 'response' in error) {
        // @ts-ignore
        message.error(error.response?.data?.message || '总结失败')
      } else {
        message.error('总结失败')
      }
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

  const fetchKnowledgeEntries = async (page: number, pageSize: number) => {
    setKnowledgeLoading(true)
    try {
      const offset = (page - 1) * pageSize
      const response = await knowledgeAPI.listEntries({
        file_id: selectedFileForKB || undefined,
        limit: pageSize,
        offset,
      })

      const entries = response.data.entries || []
      const total = typeof response.data.total === 'number' ? response.data.total : entries.length

      setKnowledgeEntries(entries)
      setKbTotal(total)

      if (total > 0) {
        message.success(`✓ 通过 MCP 加载了 ${entries.length} / ${total} 条知识条目`)
      } else if (selectedFileForKB) {
        message.info('该文件没有知识条目。提示：上传文件后需要等待后台处理完成')
      } else {
        message.info('知识库暂无条目')
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '加载知识条目失败'
      message.error(`加载失败: ${errorMsg}`)
      setKnowledgeEntries([])
      setKbTotal(0)
    } finally {
      setKnowledgeLoading(false)
    }
  }

  const loadKnowledgeEntries = async () => {
    setKbPage(1)
    setKbExpandedRowKeys([])
    await fetchKnowledgeEntries(1, kbPageSize)
  }

  const kbPagination = useMemo(
    () => ({
      current: kbPage,
      pageSize: kbPageSize,
      total: kbTotal,
      showSizeChanger: true,
      showTotal: (t: number) => `共 ${t} 条`,
      onChange: (page: number, pageSize: number) => {
        setKbPage(page)
        setKbPageSize(pageSize)
        fetchKnowledgeEntries(page, pageSize)
      },
    }),
    [kbPage, kbPageSize, kbTotal, selectedFileForKB]
  )

  const ensureKbDetailLoaded = async (entryId: string) => {
    if (!entryId) return
    if (kbDetailById[entryId]) return
    if (kbDetailLoadingIds.has(entryId)) return

    setKbDetailLoadingIds((prev) => new Set(prev).add(entryId))
    try {
      const res = await apiClient.get(`/api/knowledge/entries/${entryId}`)
      const entry = res.data?.entry
      if (entry) {
        setKbDetailById((prev) => ({ ...prev, [entryId]: entry }))
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '加载条目详情失败'
      message.error(`详情加载失败: ${errorMsg}`)
    } finally {
      setKbDetailLoadingIds((prev) => {
        const next = new Set(prev)
        next.delete(entryId)
        return next
      })
    }
  }

  const toggleKbRowExpand = (record: any) => {
    const key = record?.id
    if (!key) return

    setKbExpandedRowKeys((prev) => {
      const exists = prev.includes(key)
      const next = exists ? prev.filter((k) => k !== key) : [...prev, key]
      return next
    })

    // 展开时预取详情
    const willExpand = !kbExpandedRowKeys.includes(key)
    if (willExpand) {
      ensureKbDetailLoaded(String(key))
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
            options={fileOptions}
            showSearch
            optionFilterProp="label"
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
    {
      key: 'knowledge',
      label: (
        <span>
          <DatabaseOutlined /> 知识库条目
        </span>
      ),
      children: (
        <div className="space-y-4">
          <div className="flex gap-4">
            <Select
              placeholder="可选：选择文件过滤知识条目（不选则查看全库）..."
              value={selectedFileForKB}
              onChange={(v) => {
                setSelectedFileForKB(v)
                setKbPage(1)
              }}
              className="flex-1"
              size="large"
              options={fileOptions}
              showSearch
              optionFilterProp="label"
              allowClear
            />
            <Button
              type="primary"
              icon={<DatabaseOutlined />}
              onClick={loadKnowledgeEntries}
              loading={knowledgeLoading}
              className="grok-btn-primary"
            >
              查看知识条目
            </Button>
          </div>

          {knowledgeLoading ? (
            <div className="flex justify-center py-12">
              <Spin size="large" />
              <span className="ml-4 text-grok-textMuted">正在通过 MCP 加载知识条目...</span>
            </div>
          ) : knowledgeEntries.length > 0 ? (
            <Table
              dataSource={knowledgeEntries}
              rowKey="id"
              pagination={kbPagination}
              className="grok-table"
              onRow={(record) => ({
                onClick: () => toggleKbRowExpand(record),
              })}
              expandable={{
                expandRowByClick: true,
                showExpandColumn: true,
                expandIconColumnIndex: 0,
                rowExpandable: (record: any) => Boolean(record?.id),
                expandedRowKeys: kbExpandedRowKeys,
                onExpandedRowsChange: (keys) => setKbExpandedRowKeys(keys as React.Key[]),
                expandedRowRender: (record: any) => {
                  const entryId = record?.id
                  const detail = entryId ? kbDetailById[entryId] : undefined
                  const isDetailLoading = entryId ? kbDetailLoadingIds.has(entryId) : false
                  const fullContent = detail?.content || record?.content
                  const preview = record?.content_preview || record?.content_preview || record?.contentPreview || record?.content || ''

                  return (
                    <div className="space-y-3">
                      <Descriptions
                        size="small"
                        column={2}
                        items={[
                          { label: '条目ID', children: record?.id || '-' },
                          { label: '文件ID', children: record?.file_id || '-' },
                          { label: '类别', children: record?.category || '未分类' },
                          { label: '创建时间', children: record?.created_at || '-' },
                        ]}
                      />

                      <div>
                        <div className="text-sm text-grok-textMuted mb-2">完整内容</div>
                        {isDetailLoading ? (
                          <div className="flex items-center gap-2 text-grok-textMuted">
                            <Spin size="small" /> 正在加载详情...
                          </div>
                        ) : fullContent ? (
                          <div className="prose prose-invert max-w-none">
                            <ReactMarkdown>{String(fullContent)}</ReactMarkdown>
                          </div>
                        ) : (
                          <div className="text-grok-textMuted whitespace-pre-wrap">{String(preview || '-')}</div>
                        )}
                      </div>

                      {detail?.metadata && Object.keys(detail.metadata || {}).length > 0 ? (
                        <div>
                          <div className="text-sm text-grok-textMuted mb-2">元数据</div>
                          <pre className="text-xs whitespace-pre-wrap text-grok-textMuted">
                            {JSON.stringify(detail.metadata, null, 2)}
                          </pre>
                        </div>
                      ) : null}
                    </div>
                  )
                },
                onExpand: (expanded: boolean, record: any) => {
                  if (expanded && record?.id) {
                    ensureKbDetailLoaded(record.id)
                  }
                },
              }}
              columns={[
                {
                  title: '类别',
                  dataIndex: 'category',
                  key: 'category',
                  width: 100,
                  render: (cat: string) => (
                    <Tag color="blue">{cat || '未分类'}</Tag>
                  ),
                },
                {
                  title: '标题',
                  dataIndex: 'title',
                  key: 'title',
                  ellipsis: true,
                },
                {
                  title: '内容摘要',
                  dataIndex: 'content_preview',
                  key: 'content_preview',
                  ellipsis: true,
                  render: (_: any, record: any) => {
                    const preview = record?.content_preview || record?.contentPreview || record?.content || ''
                    if (!preview) return <span className="text-grok-textMuted">-</span>
                    const s = String(preview)
                    return <div className="text-grok-textMuted">{s.length > 120 ? `${s.slice(0, 120)}...` : s}</div>
                  },
                },
                {
                  title: '关键词',
                  dataIndex: 'keywords',
                  key: 'keywords',
                  width: 200,
                  render: (keywords: string[]) =>
                    keywords?.slice(0, 3).map((k: string, i: number) => (
                      <Tag key={i} color="green">
                        {k}
                      </Tag>
                    )),
                },
                {
                  title: '重要性',
                  dataIndex: 'importance_score',
                  key: 'importance_score',
                  width: 90,
                  render: (score: number) => (
                    <span className={score > 70 ? 'text-red-400' : 'text-grok-textMuted'}>
                      {score?.toFixed(0)}
                    </span>
                  ),
                },
                {
                  title: '创建时间',
                  dataIndex: 'created_at',
                  key: 'created_at',
                  width: 170,
                  render: (t: string) => <span className="text-grok-textMuted">{t || '-'}</span>,
                },
                {
                  title: '操作',
                  key: 'actions',
                  width: 90,
                  render: (_: any, record: any) => {
                    const id = record?.id
                    const expanded = id ? kbExpandedRowKeys.includes(id) : false
                    return (
                      <Button
                        type="link"
                        className="p-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleKbRowExpand(record)
                        }}
                      >
                        {expanded ? '收起' : '展开'}
                      </Button>
                    )
                  },
                },
              ]}
            />
          ) : selectedFileForKB ? (
            <Empty
              description={
                <div>
                  <p>该文件暂无知识条目</p>
                  <p className="text-sm text-grok-textMuted mt-2">
                    提示：文件上传后需要等待后台处理才会生成知识条目
                  </p>
                </div>
              }
              className="py-12"
            />
          ) : (
            <Empty
              description="可直接点击'查看知识条目'查看全库，或先选择文件进行过滤"
              className="py-12"
            />
          )}
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
