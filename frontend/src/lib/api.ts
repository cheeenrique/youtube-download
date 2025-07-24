import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptors para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptors para tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    
    // Se o token expirou, redirecionar para login
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

export interface Download {
  id: string
  url: string
  title?: string
  description?: string
  thumbnail?: string
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  quality: string
  storage_type: 'temporary' | 'permanent'
  created_at: string
  file_path?: string
  file_size?: number
  format?: string
  error_message?: string
  progress: number
  uploaded_to_drive: boolean
  drive_file_id?: string
}

export interface CreateDownloadRequest {
  url: string
  quality: string
  storage_type: 'temporary' | 'permanent'
}

export interface CreateBatchDownloadRequest {
  urls: string[]
  quality: string
  storage_type: 'temporary' | 'permanent'
  upload_to_drive: boolean
}

export interface CreateDownloadResponse {
  download: Download
  message: string
}

export interface CreateBatchDownloadResponse {
  downloads: Download[]
  message: string
}

export interface DownloadsResponse {
  downloads: Download[]
  total: number
}

export interface DownloadStats {
  total_downloads: number
  completed_downloads: number
  failed_downloads: number
  pending_downloads: number
  downloads_today: number
  downloads_this_week: number
  downloads_this_month: number
  total_storage_used: number
  average_download_time: number
}

export const downloadService = {
  // Buscar todos os downloads
  getDownloads: async (): Promise<DownloadsResponse> => {
    const response = await api.get('/api/v1/downloads/')
    return response.data
  },

  // Criar novo download
  createDownload: async (data: CreateDownloadRequest): Promise<CreateDownloadResponse> => {
    const response = await api.post('/api/v1/downloads/sync', data)
    return response.data
  },

  // Criar múltiplos downloads
  createBatchDownloads: async (data: CreateBatchDownloadRequest): Promise<CreateBatchDownloadResponse> => {
    const response = await api.post('/api/v1/downloads/batch', data)
    return response.data
  },

  // Buscar download por ID
  getDownload: async (id: string): Promise<Download> => {
    const response = await api.get(`/api/v1/downloads/${id}`)
    return response.data
  },

  // Deletar download
  deleteDownload: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/downloads/${id}`)
  },

  // Buscar estatísticas dos downloads
  getStats: async (): Promise<DownloadStats> => {
    const response = await api.get('/api/v1/downloads/stats/summary')
    return response.data
  },
} 