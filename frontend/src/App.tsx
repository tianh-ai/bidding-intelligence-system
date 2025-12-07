import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import FileUpload from './pages/FileUpload'
import LogicLearning from './pages/LogicLearning'
import FileSummary from './pages/FileSummary'
import LLMManagement from './pages/LLMManagement'
import PromptManagement from './pages/PromptManagement'
import Settings from './pages/Settings'
import FileManagement from './pages/FileManagement'

function App() {

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00D9FF',
          colorBgBase: '#0A0A0A',
          colorBgContainer: '#111111',
          colorBorder: '#2A2A2A',
          colorText: '#E5E5E5',
          colorTextSecondary: '#A0A0A0',
          borderRadius: 8,
          fontFamily: 'Inter, system-ui, sans-serif',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="files" element={<FileUpload />} />
            <Route path="learning" element={<LogicLearning />} />
            <Route path="summary" element={<FileSummary />} />
            <Route path="llm" element={<LLMManagement />} />
            <Route path="prompts" element={<PromptManagement />} />
            <Route path="settings" element={<Settings />} />
            <Route path="management" element={<FileManagement />} />
            
            {/* Placeholder routes for other pages */}
            <Route path="generation" element={<div className="text-grok-text">标书生成（开发中）</div>} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
