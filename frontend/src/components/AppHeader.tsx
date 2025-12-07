import React from 'react'
import { Layout, Dropdown, Avatar, Space, Button } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  BellOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import { useNavigate } from 'react-router-dom'
import type { MenuProps } from 'antd'

const { Header } = Layout

const AppHeader: React.FC = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Header className="bg-grok-surface border-b border-grok-border px-6 flex items-center justify-between h-16">
      <div className="flex items-center gap-4">
        <span className="text-grok-text text-lg">
          欢迎回来，{user?.username || '用户'}
        </span>
        <span className="px-2 py-1 bg-grok-accent/20 text-grok-accent rounded text-xs">
          {user?.role === 'admin' ? '管理员' : user?.role === 'user' ? '用户' : '访客'}
        </span>
      </div>

      <Space size="middle">
        <Button
          type="text"
          icon={<BellOutlined />}
          className="text-grok-textMuted hover:text-grok-text"
        />

        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <div className="cursor-pointer">
            <Avatar
              icon={<UserOutlined />}
              className="bg-grok-accent"
            >
              {user?.username?.[0]?.toUpperCase()}
            </Avatar>
          </div>
        </Dropdown>
      </Space>
    </Header>
  )
}

export default AppHeader
