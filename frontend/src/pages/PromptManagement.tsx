import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  message,
  Popconfirm,
  Tag,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { promptAPI } from '@/services/api'
import type { ColumnsType } from 'antd/es/table'

const { TextArea } = Input

interface Prompt {
  id: string
  title: string
  content: string
  category: string
  is_system: boolean
  created_at: string
  updated_at: string
}

const PromptManagement: React.FC = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null)
  const [form] = Form.useForm()

  // 提示词分类
  const categories = [
    { label: '文档分析', value: 'document_analysis' },
    { label: '需求提取', value: 'requirement_extraction' },
    { label: '合规检查', value: 'compliance_check' },
    { label: '评估辅助', value: 'evaluation_support' },
    { label: '其他', value: 'other' },
  ]

  // 加载提示词列表
  const loadPrompts = async () => {
    setLoading(true)
    try {
      const response = await promptAPI.getTemplates()
      setPrompts(response.data)
    } catch (error: any) {
      message.error(error.message || '加载提示词失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPrompts()
  }, [])

  // 打开新建/编辑弹窗
  const handleOpenModal = (prompt?: Prompt) => {
    if (prompt) {
      setEditingPrompt(prompt)
      form.setFieldsValue(prompt)
    } else {
      setEditingPrompt(null)
      form.resetFields()
    }
    setModalVisible(true)
  }

  // 关闭弹窗
  const handleCloseModal = () => {
    setModalVisible(false)
    setEditingPrompt(null)
    form.resetFields()
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingPrompt) {
        // 编辑
        await promptAPI.updateTemplate(editingPrompt.id, values)
        message.success('提示词更新成功')
      } else {
        // 新建
        await promptAPI.createTemplate(values)
        message.success('提示词创建成功')
      }
      
      handleCloseModal()
      loadPrompts()
    } catch (error: any) {
      message.error(error.message || '操作失败')
    }
  }

  // 删除提示词
  const handleDelete = async (id: string) => {
    try {
      await promptAPI.deleteTemplate(id)
      message.success('删除成功')
      loadPrompts()
    } catch (error: any) {
      message.error(error.message || '删除失败')
    }
  }

  // 表格列定义
  const columns: ColumnsType<Prompt> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      render: (text, record) => (
        <Space>
          <ThunderboltOutlined className="text-grok-accent" />
          <span>{text}</span>
          {record.is_system && (
            <Tag color="blue" className="text-xs">
              系统
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (text) => (
        <div className="text-grok-textMuted max-w-md truncate">{text}</div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 150,
      render: (category) => {
        const cat = categories.find((c) => c.value === category)
        return <Tag color="green">{cat?.label || category}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
            disabled={record.is_system}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个提示词吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
            disabled={record.is_system}
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              disabled={record.is_system}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <Card className="grok-card">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-semibold text-grok-text">提示词管理</h2>
            <p className="text-sm text-grok-textMuted mt-1">
              管理AI助手的快捷提示词，提高工作效率
            </p>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
            className="grok-btn-primary"
          >
            新建提示词
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={prompts}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: true,
          }}
          className="grok-table"
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingPrompt ? '编辑提示词' : '新建提示词'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={600}
        okText="保存"
        cancelText="取消"
        className="grok-modal"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            category: 'other',
          }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="例如：分析投标文档结构" />
          </Form.Item>

          <Form.Item
            name="category"
            label="分类"
            rules={[{ required: true, message: '请选择分类' }]}
          >
            <Select options={categories} placeholder="选择分类" />
          </Form.Item>

          <Form.Item
            name="content"
            label="提示词内容"
            rules={[{ required: true, message: '请输入提示词内容' }]}
          >
            <TextArea
              rows={6}
              placeholder="请输入提示词内容，例如：请分析这份投标文件，提取关键信息..."
              maxLength={2000}
              showCount
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PromptManagement
