import React from 'react'
import { Layout } from 'antd'
import { Outlet, Navigate } from 'react-router-dom'
import AppHeader from '@/components/AppHeader'
import AppSidebar from '@/components/AppSidebar'
import AIChatPanel from '@/components/AIChatPanel'
import { useAuthStore } from '@/store/authStore'
import { useChatStore } from '@/store/chatStore'
import Split from 'react-split'

const { Content } = Layout

const MainLayout: React.FC = () => {
  const { isAuthenticated } = useAuthStore()
  const { isOpen: isChatOpen } = useChatStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return (
    <Layout className="min-h-screen">
      {/* 第一层Split: 侧边栏 | [主内容区+AI助手] */}
      <Split
        className="flex h-screen"
        sizes={[15, 85]}
        minSize={[200, 600]}
        gutterSize={4}
        direction="horizontal"
      >
        {/* 侧边栏 - 可调整宽度 */}
        <div className="h-full overflow-hidden">
          <AppSidebar />
        </div>

        {/* 右侧区域: Header + [主内容 | AI助手] */}
        <Layout className="h-full overflow-hidden">
          <AppHeader />

          {/* 主内容区 - 始终占满 */}
          <Split
            className="flex flex-1 overflow-hidden"
            sizes={isChatOpen ? [65, 35] : [100, 0]}
            minSize={[400, 350]}
            gutterSize={isChatOpen ? 4 : 0}
            direction="horizontal"
          >
            <Content className="overflow-auto bg-grok-bg p-6">
              <Outlet />
            </Content>

            {isChatOpen && (
              <div className="h-full overflow-hidden">
                <AIChatPanel />
              </div>
            )}
          </Split>
        </Layout>
      </Split>
    </Layout>
  )
}

export default MainLayout
