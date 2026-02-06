/**
 * API Client for ExportSathi Backend
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const api = {
  // Reports
  generateReport: (data: FormData) => 
    apiClient.post('/api/reports/generate', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  getReport: (reportId: string) => 
    apiClient.get(`/api/reports/${reportId}`),
  getReportStatus: (reportId: string) => 
    apiClient.get(`/api/reports/${reportId}/status`),
  
  // Certifications
  getCertifications: () => 
    apiClient.get('/api/certifications'),
  getCertificationGuidance: (certId: string, data: any) => 
    apiClient.post(`/api/certifications/${certId}/guidance`, data),
  
  // Documents
  generateDocument: (data: any) => 
    apiClient.post('/api/documents/generate', data),
  validateDocument: (docId: string) => 
    apiClient.post('/api/documents/validate', { document_id: docId }),
  
  // Finance
  getFinanceAnalysis: (reportId: string) => 
    apiClient.get(`/api/finance/analysis/${reportId}`),
  calculateRoDTEP: (data: any) => 
    apiClient.post('/api/finance/rodtep-calculator', data),
  
  // Logistics
  analyzeLogistics: (data: any) => 
    apiClient.post('/api/logistics/risk-analysis', data),
  
  // Chat
  submitQuestion: (data: any) => 
    apiClient.post('/api/chat', data),
  getChatHistory: (sessionId: string) => 
    apiClient.get(`/api/chat/${sessionId}/history`),
  
  // Users
  register: (data: any) => 
    apiClient.post('/api/users/register', data),
  login: (data: any) => 
    apiClient.post('/api/users/login', data),
  getProfile: (userId: string) => 
    apiClient.get(`/api/users/profile?user_id=${userId}`),
}
