import React, { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authAPI } from '@/services/api'
import type { LoginRequest } from '@/types'

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const onFinish = async (values: LoginRequest) => {
    setLoading(true)
    try {
      const response = await authAPI.login(values)
      console.log('[Login] 登录响应:', response.data)
      const { token, user } = response.data
      
      // 确保 user 对象包含 role 字段
      if (!user.role) {
        console.warn('[Login] user.role 为空，使用默认值')
        user.role = 'user'
      }
      console.log('[Login] 用户信息:', user)
      
      login(token, user)
      message.success(`登录成功！欢迎 ${user.role === 'admin' ? '管理员' : '用户'} ${user.username}`)
      navigate('/')
    } catch (error: any) {
      message.error(error.response?.data?.message || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-grok-bg">
      <div className="w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-grok-accent mb-2">投标智能系统</h1>
          <p className="text-grok-textMuted">智能化投标文件生成与学习平台</p>
        </div>

        {/* Login Card */}
        <Card className="grok-card">
          <Form
            name="login"
            onFinish={onFinish}
            autoComplete="new-password"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined className="text-grok-textMuted" />}
                placeholder="用户名"
                className="grok-input"
                autoComplete="off"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined className="text-grok-textMuted" />}
                placeholder="密码"
                className="grok-input"
                autoComplete="new-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                className="grok-btn-primary h-12"
              >
                登录
              </Button>
            </Form.Item>

            <div className="text-center text-grok-textMuted text-sm">
              <p>默认管理员账号：admin / bidding2024</p>
            </div>
          </Form>
        </Card>

        <div className="mt-6 text-center text-grok-textMuted text-sm">
          <p>© 2024 投标智能系统. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}

export default Login
