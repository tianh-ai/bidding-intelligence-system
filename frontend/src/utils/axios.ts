import axios from 'axios'
import { API_BASE_URL, STORAGE_KEYS } from '@/config/constants'

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

// 请求拦截器 - 添加 token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 确保表单上传时让浏览器自行设置 multipart 边界
    if (config.data instanceof FormData) {
      const headers = config.headers as any
      if (headers?.has?.('Content-Type')) {
        headers.delete('Content-Type')
      } else if (headers && headers['Content-Type']) {
        delete headers['Content-Type']
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期或无效，清除本地存储并跳转登录
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
      localStorage.removeItem(STORAGE_KEYS.USER_INFO)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default axiosInstance
