import React, { useEffect, useState } from 'react'
import { Card, Statistic, Row, Col, message } from 'antd'
import {
  FileOutlined,
  BulbOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import Split from 'react-split'
import AIChatPanel from '@/components/AIChatPanel'
import { useChatStore } from '@/store/chatStore'

import { apiClient } from '@/services/api'

interface DashboardStats {
  total_files: number
  learned_rules: number
  generation_tasks: number
  success_rate: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(false)
  const { isOpen: isChatOpen } = useChatStore()

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true)
        const res = await apiClient.get<DashboardStats>('/metrics/dashboard')
        setStats(res.data)
      } catch (error) {
        console.error('获取仪表盘统计失败', error)
        message.error('获取首页统计数据失败，将显示示例数据')
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  const totalFiles = stats?.total_files ?? 156
  const learnedRules = stats?.learned_rules ?? 342
  const generationTasks = stats?.generation_tasks ?? 89
  const successRate = stats?.success_rate ?? 96.5

  return (
    <Split
      className="flex h-full overflow-hidden"
      sizes={isChatOpen ? [70, 30] : [100, 0]}
      minSize={isChatOpen ? [300, 280] : [100, 0]}
      maxSize={isChatOpen ? [Infinity, 600] : [Infinity, 0]}
      gutterSize={isChatOpen ? 8 : 0}
      snapOffset={30}
      dragInterval={1}
      direction="horizontal"
      cursor="col-resize"
    >
      <div className="space-y-6 overflow-auto pr-4">
      <div>
        <h1 className="text-3xl font-bold text-grok-text mb-2">欢迎使用投标智能系统</h1>
        <p className="text-grok-textMuted">
          智能化投标文件生成与学习平台
        </p>
      </div>

      {/* Statistics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="grok-card">
            <Statistic
              title={<span className="text-grok-textMuted">总文件数</span>}
              loading={loading}
              value={totalFiles}
              prefix={<FileOutlined className="text-grok-accent" />}
              valueStyle={{ color: '#00D9FF' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="grok-card">
            <Statistic
              title={<span className="text-grok-textMuted">逻辑规则数</span>}
              loading={loading}
              value={learnedRules}
              prefix={<BulbOutlined className="text-grok-success" />}
              valueStyle={{ color: '#00E676' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="grok-card">
            <Statistic
              title={<span className="text-grok-textMuted">生成任务数</span>}
              loading={loading}
              value={generationTasks}
              prefix={<RocketOutlined className="text-grok-warning" />}
              valueStyle={{ color: '#FFD600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="grok-card">
            <Statistic
              title={<span className="text-grok-textMuted">成功率</span>}
              loading={loading}
              value={successRate}
              suffix="%"
              prefix={<CheckCircleOutlined className="text-grok-success" />}
              valueStyle={{ color: '#00E676' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Card className="grok-card" title="快速开始">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="grok-card p-4 hover:border-grok-accent cursor-pointer transition-all">
            <FileOutlined className="text-3xl text-grok-accent mb-2" />
            <h3 className="text-grok-text font-semibold">上传文件</h3>
            <p className="text-grok-textMuted text-sm">上传招标和投标文件</p>
          </div>
          <div className="grok-card p-4 hover:border-grok-accent cursor-pointer transition-all">
            <BulbOutlined className="text-3xl text-grok-success mb-2" />
            <h3 className="text-grok-text font-semibold">逻辑学习</h3>
            <p className="text-grok-textMuted text-sm">从历史文件学习逻辑</p>
          </div>
          <div className="grok-card p-4 hover:border-grok-accent cursor-pointer transition-all">
            <FileTextOutlined className="text-3xl text-grok-warning mb-2" />
            <h3 className="text-grok-text font-semibold">文件总结</h3>
            <p className="text-grok-textMuted text-sm">总结招标公告和文件</p>
          </div>
          <div className="grok-card p-4 hover:border-grok-accent cursor-pointer transition-all">
            <RocketOutlined className="text-3xl text-blue-500 mb-2" />
            <h3 className="text-grok-text font-semibold">生成标书</h3>
            <p className="text-grok-textMuted text-sm">智能生成投标文件</p>
          </div>
        </div>
      </Card>

      {/* Recent Activity */}
      <Card className="grok-card" title="最近活动">
        <div className="space-y-3">
          {[
            { action: '完成逻辑学习', time: '5分钟前', status: 'success' },
            { action: '生成投标文件', time: '1小时前', status: 'success' },
            { action: '上传文件', time: '2小时前', status: 'success' },
          ].map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-grok-bg rounded"
            >
              <div className="flex items-center gap-3">
                <CheckCircleOutlined className="text-grok-success" />
                <span className="text-grok-text">{item.action}</span>
              </div>
              <span className="text-grok-textMuted text-sm">{item.time}</span>
            </div>
          ))}
        </div>
      </Card>
      </div>

      {isChatOpen && (
        <div className="h-full overflow-hidden">
          <AIChatPanel />
        </div>
      )}
    </Split>
  )
}

export default Dashboard
