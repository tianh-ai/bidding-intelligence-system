import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Space, Statistic, Row, Col, Tag, Alert, InputNumber } from 'antd'
import { FolderOutlined, SaveOutlined, ReloadOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons'
import { settingsAPI } from '@/services/api'

interface UploadSettings {
  upload_dir: string
  max_file_size: number
  allowed_extensions: string[]
}

interface PathInfo {
  configured_path: string
  absolute_path: string
  exists: boolean
  is_absolute: boolean
  permissions: {
    readable: boolean
    writable: boolean
  }
  disk_space?: {
    total: number
    free: number
    used_percent: number
  }
  uploaded_files?: {
    count: number
    total_size: number
  }
}

const Settings: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [pathInfo, setPathInfo] = useState<PathInfo | null>(null)
  const [testResult, setTestResult] = useState<any>(null)

  // 加载当前设置
  const loadSettings = async () => {
    try {
      const response = await settingsAPI.getUploadSettings()
      const settings = response.data
      form.setFieldsValue({
        upload_dir: settings.upload_dir,
        max_file_size: settings.max_file_size,
        allowed_extensions: settings.allowed_extensions.join(', ')
      })
    } catch (error: any) {
      console.error('Load settings error:', error)
      message.error('加载设置失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 加载路径信息
  const loadPathInfo = async () => {
    try {
      const response = await settingsAPI.getUploadPathInfo()
      const info = response.data
      setPathInfo(info)
    } catch (error: any) {
      console.error('Failed to load path info:', error)
      message.error('加载路径信息失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  useEffect(() => {
    loadSettings()
    loadPathInfo()
  }, [])

  // 测试路径
  const handleTestPath = async () => {
    const path = form.getFieldValue('upload_dir')
    if (!path) {
      message.warning('请输入路径')
      return
    }

    setLoading(true)
    try {
      const result = await settingsAPI.testUploadPath(path)
      setTestResult(result)
      
      if (result.valid) {
        message.success('路径可用')
      } else {
        message.error('路径不可用，请查看错误信息')
      }
    } catch (error) {
      message.error('测试失败')
    } finally {
      setLoading(false)
    }
  }

  // 保存设置
  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      
      setLoading(true)
      const extensions = values.allowed_extensions
        .split(',')
        .map((ext: string) => ext.trim())
        .filter((ext: string) => ext.length > 0)

      const result = await settingsAPI.updateUploadSettings({
        upload_dir: values.upload_dir,
        max_file_size: values.max_file_size,
        allowed_extensions: extensions
      })

      if (result.restart_required) {
        message.warning({
          content: '设置已保存，但需要重启后端服务才能生效',
          duration: 5
        })
      } else {
        message.success('设置保存成功')
      }

      await loadPathInfo()
    } catch (error) {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ marginBottom: '24px' }}>系统设置</h1>

      {/* 当前路径信息 */}
      {pathInfo && (
        <Card 
          title={<><FolderOutlined /> 当前上传路径信息</>}
          style={{ marginBottom: '24px' }}
          className="grok-card"
        >
          <Row gutter={16}>
            <Col span={8}>
              <Statistic 
                title="配置路径" 
                value={pathInfo.configured_path}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
            <Col span={16}>
              <Statistic 
                title="实际路径" 
                value={pathInfo.absolute_path}
                valueStyle={{ fontSize: '14px' }}
              />
            </Col>
          </Row>

          <Row gutter={16} style={{ marginTop: '16px' }}>
            <Col span={6}>
              <div>
                <span style={{ marginRight: '8px' }}>状态:</span>
                {pathInfo.exists ? (
                  <Tag color="success" icon={<CheckCircleOutlined />}>目录存在</Tag>
                ) : (
                  <Tag color="warning" icon={<WarningOutlined />}>目录不存在</Tag>
                )}
              </div>
            </Col>
            <Col span={6}>
              <div>
                <span style={{ marginRight: '8px' }}>可读:</span>
                {pathInfo.permissions.readable ? (
                  <Tag color="success">是</Tag>
                ) : (
                  <Tag color="error">否</Tag>
                )}
              </div>
            </Col>
            <Col span={6}>
              <div>
                <span style={{ marginRight: '8px' }}>可写:</span>
                {pathInfo.permissions.writable ? (
                  <Tag color="success">是</Tag>
                ) : (
                  <Tag color="error">否</Tag>
                )}
              </div>
            </Col>
            <Col span={6}>
              <div>
                <span style={{ marginRight: '8px' }}>路径类型:</span>
                <Tag>{pathInfo.is_absolute ? '绝对路径' : '相对路径'}</Tag>
              </div>
            </Col>
          </Row>

          {pathInfo.disk_space && (
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={8}>
                <Statistic 
                  title="磁盘总空间" 
                  value={formatBytes(pathInfo.disk_space.total)}
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="可用空间" 
                  value={formatBytes(pathInfo.disk_space.free)}
                />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="已使用" 
                  value={pathInfo.disk_space.used_percent}
                  suffix="%"
                />
              </Col>
            </Row>
          )}

          {pathInfo.uploaded_files && (
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={12}>
                <Statistic 
                  title="已上传文件数" 
                  value={pathInfo.uploaded_files.count}
                />
              </Col>
              <Col span={12}>
                <Statistic 
                  title="文件总大小" 
                  value={formatBytes(pathInfo.uploaded_files.total_size)}
                />
              </Col>
            </Row>
          )}
        </Card>
      )}

      {/* 设置表单 */}
      <Card 
        title="文件上传设置"
        className="grok-card"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="上传目录"
            name="upload_dir"
            rules={[{ required: true, message: '请输入上传目录' }]}
            extra="支持相对路径（如 ./uploads）或绝对路径（如 /data/bidding-uploads）"
          >
            <Input 
              placeholder="./uploads" 
              suffix={
                <Button 
                  type="link" 
                  size="small"
                  onClick={handleTestPath}
                  loading={loading}
                >
                  测试路径
                </Button>
              }
            />
          </Form.Item>

          {testResult && (
            <Alert
              type={testResult.valid ? 'success' : 'error'}
              message={testResult.valid ? '路径可用' : '路径不可用'}
              description={
                <div>
                  {testResult.errors?.map((err: string, i: number) => (
                    <div key={i} style={{ color: '#ff4d4f' }}>❌ {err}</div>
                  ))}
                  {testResult.warnings?.map((warn: string, i: number) => (
                    <div key={i} style={{ color: '#faad14' }}>⚠️ {warn}</div>
                  ))}
                  {testResult.absolute_path && (
                    <div style={{ marginTop: '8px' }}>
                      实际路径: <code>{testResult.absolute_path}</code>
                    </div>
                  )}
                </div>
              }
              style={{ marginBottom: '16px' }}
              closable
            />
          )}

          <Form.Item
            label="最大文件大小"
            name="max_file_size"
            rules={[{ required: true, message: '请输入最大文件大小' }]}
            extra="单位：字节（默认 52428800 = 50MB）"
          >
            <InputNumber 
              style={{ width: '100%' }}
              min={1024}
              max={1024 * 1024 * 1024}
              formatter={value => `${formatBytes(Number(value))}`}
              parser={value => {
                const match = value?.match(/[\d.]+/)
                return match ? Number(match[0]) : 0
              }}
            />
          </Form.Item>

          <Form.Item
            label="允许的文件扩展名"
            name="allowed_extensions"
            rules={[{ required: true, message: '请输入允许的扩展名' }]}
            extra="多个扩展名用逗号分隔，如: .pdf, .docx, .doc, .xlsx"
          >
            <Input placeholder=".pdf, .docx, .doc" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                icon={<SaveOutlined />}
                onClick={handleSave}
                loading={loading}
              >
                保存设置
              </Button>
              <Button 
                icon={<ReloadOutlined />}
                onClick={() => {
                  loadSettings()
                  loadPathInfo()
                  setTestResult(null)
                }}
              >
                重置
              </Button>
            </Space>
          </Form.Item>
        </Form>

        <Alert
          type="info"
          message="重要提示"
          description="修改设置后需要重启后端服务才能生效。在 Docker 环境下，请运行: docker restart bidding_backend"
          showIcon
        />
      </Card>
    </div>
  )
}

export default Settings
