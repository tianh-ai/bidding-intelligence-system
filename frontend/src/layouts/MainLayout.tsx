import React from 'react'
import { Layout } from 'antd'
import { Outlet, Navigate } from 'react-router-dom'
import AppHeader from '@/components/AppHeader'
import AppSidebar from '@/components/AppSidebar'
import { useAuthStore } from '@/store/authStore'
import Split from 'react-split'

const { Content } = Layout

const MainLayout: React.FC = () => {
  const { isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Layout className="min-h-screen">
      {/* Split: 侧边栏 | 主内容区 - 支持响应式调整 */}
      <Split
        className="flex h-screen"
        sizes={[15, 85]}
        minSize={[180, 400]}
        maxSize={[400, Infinity]}
        gutterSize={8}
        snapOffset={30}
        dragInterval={1}
        direction="horizontal"
        cursor="col-resize"
      >
        {/* 侧边栏 - 可调整宽度 */}
        <div className="h-full overflow-hidden">
          <AppSidebar />
        </div>

        {/* 右侧区域: Header + 主内容 */}
        <Layout className="h-full overflow-hidden">
          <AppHeader />
          <Content className="overflow-auto bg-grok-bg p-6">
            <Outlet />
          </Content>
        </Layout>
      </Split>
    </Layout>
  )
}

export default MainLayout
