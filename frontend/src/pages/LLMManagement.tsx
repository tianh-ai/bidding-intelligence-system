import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Space,
  message,
  Tag,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'
import Split from 'react-split'
import AIChatPanel from '@/components/AIChatPanel'
import { useChatStore } from '@/store/chatStore'
import { llmAPI } from '@/services/api'
import type { LLMModel } from '@/types'

const LLMManagement: React.FC = () => {
  const [models, setModels] = useState<any[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingModel, setEditingModel] = useState<any | null>(null)
  const [testingModel, setTestingModel] = useState<string | null>(null)
  const [form] = Form.useForm()
  const { isOpen: isChatOpen } = useChatStore()

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      const response = await llmAPI.getModels()
      setModels(response.data || [])
    } catch (error) {
      console.error('Failed to load models:', error)
      message.error('加载模型列表失败')
    }
  }

  const handleAdd = () => {
    setEditingModel(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (model: LLMModel) => {
    setEditingModel(model)
    form.setFieldsValue(model)
    setModalVisible(true)
  }

  const handleDelete = (modelId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个模型吗？',
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await llmAPI.deleteModel(modelId)
          message.success('删除成功')
          loadModels()
        } catch (error: any) {
          message.error(error.response?.data?.message || '删除失败')
        }
      },
    })
  }

  const handleTest = async (modelId: string) => {
    setTestingModel(modelId)
    try {
      await llmAPI.testModel(modelId)
      message.success('模型测试成功！')
    } catch (error: any) {
      message.error(error.response?.data?.message || '测试失败')
    } finally {
      setTestingModel(null)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingModel) {
        await llmAPI.updateModel(editingModel.id, values)
        message.success('更新成功')
      } else {
        await llmAPI.addModel(values)
        message.success('添加成功')
      }
      setModalVisible(false)
      loadModels()
    } catch (error: any) {
      message.error(error.response?.data?.message || '操作失败')
    }
  }

  const columns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => {
        const colorMap: Record<string, string> = {
          openai: 'blue',
          deepseek: 'purple',
          qwen: 'orange',
          other: 'default',
        }
        return <Tag color={colorMap[provider] || 'default'}>{provider.toUpperCase()}</Tag>
      },
    },
    {
      title: 'API 端点',
      dataIndex: 'endpoint',
      key: 'endpoint',
      ellipsis: true,
    },
    {
      title: 'Temperature',
      dataIndex: 'temperature',
      key: 'temperature',
    },
    {
      title: 'Max Tokens',
      dataIndex: 'maxTokens',
      key: 'maxTokens',
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      key: 'isActive',
      render: (isActive: boolean) =>
        isActive ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>
            已激活
          </Tag>
        ) : (
          <Tag color="warning">未激活</Tag>
        ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: LLMModel) => (
        <Space>
          <Button
            type="link"
            icon={<ExperimentOutlined />}
            onClick={() => handleTest(record.id)}
            loading={testingModel === record.id}
          >
            测试
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
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
    <Split
      className="flex h-full overflow-hidden"
      sizes={isChatOpen ? [60, 40] : [100, 0]}
      minSize={isChatOpen ? [400, 320] : [100, 0]}
      maxSize={isChatOpen ? [Infinity, 700] : [Infinity, 0]}
      gutterSize={isChatOpen ? 8 : 0}
      snapOffset={30}
      dragInterval={1}
      direction="horizontal"
      cursor="col-resize"
    >
      <div className="space-y-6 overflow-auto pr-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-grok-text">大模型管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleAdd}
          className="grok-btn-primary"
        >
          添加模型
        </Button>
      </div>

      <Card className="grok-card">
        <Table
          dataSource={models}
          columns={columns}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingModel ? '编辑模型' : '添加模型'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className="mt-4"
        >
          <Form.Item
            label="模型名称"
            name="name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="例如：GPT-4" className="grok-input" />
          </Form.Item>

          <Form.Item
            label="提供商"
            name="provider"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select
              options={[
                { label: 'OpenAI', value: 'openai' },
                { label: 'DeepSeek', value: 'deepseek' },
                { label: 'Qwen (通义千问)', value: 'qwen' },
                { label: '其他', value: 'other' },
              ]}
            />
          </Form.Item>

          <Form.Item
            label="API Key"
            name="apiKey"
            rules={[{ required: true, message: '请输入 API Key' }]}
          >
            <Input.Password placeholder="sk-..." className="grok-input" />
          </Form.Item>

          <Form.Item label="API 端点" name="endpoint">
            <Input
              placeholder="https://api.openai.com/v1"
              className="grok-input"
            />
          </Form.Item>

          <Form.Item
            label="Temperature"
            name="temperature"
            initialValue={0.7}
            rules={[{ required: true }]}
          >
            <InputNumber min={0} max={2} step={0.1} className="w-full" />
          </Form.Item>

          <Form.Item
            label="Max Tokens"
            name="maxTokens"
            initialValue={2000}
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={100000} className="w-full" />
          </Form.Item>

          <Form.Item
            label="激活状态"
            name="isActive"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Space className="w-full justify-end">
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" className="grok-btn-primary">
                {editingModel ? '更新' : '添加'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
      </div>

      {isChatOpen && (
        <div className="h-full overflow-hidden">
          <AIChatPanel />
        </div>
      )}
    </Split>
  )
}

export default LLMManagement
