import React from 'react'
import { Layout, Menu } from 'antd'
import {
  HomeOutlined,
  FileOutlined,
  BulbOutlined,
  FileTextOutlined,
  RocketOutlined,
  RobotOutlined,
  FolderOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  ThunderboltOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useLayoutStore } from '@/store/layoutStore'

const { Sider } = Layout

const AppSidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { isSidebarCollapsed, toggleSidebar } = useLayoutStore()

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/files',
      icon: <FileOutlined />,
      label: '文件上传及存档',
    },
    {
      key: '/learning',
      icon: <BulbOutlined />,
      label: '逻辑学习',
    },
    {
      key: '/summary',
      icon: <FileTextOutlined />,
      label: '文件总结',
    },
    {
      key: '/generation',
      icon: <RocketOutlined />,
      label: '标书生成',
    },
    {
      key: '/llm',
      icon: <RobotOutlined />,
      label: '大模型',
    },
    {
      key: '/prompts',
      icon: <ThunderboltOutlined />,
      label: '提示词管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
    {
      key: '/management',
      icon: <FolderOutlined />,
      label: '文件管理',
    },
  ]

  return (
    <Sider
      collapsible
      collapsed={isSidebarCollapsed}
      onCollapse={toggleSidebar}
      trigger={null}
      width={240}
      className="bg-grok-surface border-r border-grok-border"
      theme="dark"
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-center border-b border-grok-border">
        {!isSidebarCollapsed ? (
          <span className="text-xl font-bold text-grok-accent">投标智能系统</span>
        ) : (
          <span className="text-2xl font-bold text-grok-accent">投</span>
        )}
      </div>

      {/* Menu */}
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        className="border-0"
        theme="dark"
      />

      {/* Collapse Trigger */}
      <div
        className="absolute bottom-4 left-0 right-0 flex justify-center cursor-pointer text-grok-textMuted hover:text-grok-accent"
        onClick={toggleSidebar}
      >
        {isSidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
      </div>
    </Sider>
  )
}

export default AppSidebar
