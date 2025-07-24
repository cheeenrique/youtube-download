'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { downloadService, type CreateDownloadRequest, type CreateBatchDownloadRequest, type Download, type DownloadStats } from '@/lib/api'
import { useState } from 'react'
import { useWebSocketSingleton } from './use-websocket-singleton'
import { useAuth } from '@/contexts/auth-context'

export function useDownloads() {
  const queryClient = useQueryClient()
  const { isAuthenticated, token } = useAuth()

  // Query para buscar downloads (sem polling)
  const {
    data: downloadsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['downloads'],
    queryFn: downloadService.getDownloads,
    // Removido refetchInterval - não fazer polling
    enabled: isAuthenticated, // Só buscar quando autenticado
  })


  // WebSocket para atualizações em tempo real (só quando autenticado)
  const { isConnected, isAuthenticated: wsAuthenticated } = useWebSocketSingleton({
    url: `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/dashboard`,
    token: token || undefined,
    onMessage: (message) => {


      if (message.type === 'download_update') {
        // Atualizar um download específico
        const downloadId = message.download_id
        const downloadData = message.data
        

        
        queryClient.setQueryData(['downloads'], (oldData: any) => {
          if (!oldData) {
            console.log("Nenhum dado antigo encontrado, não é possível atualizar")
            return oldData
          }

          
          const updatedDownloads = oldData.downloads.map((download: any) => {
            if (download.id === downloadId) {
              
              return {
                ...download,
                ...downloadData,
                // Garantir que os campos obrigatórios estejam presentes
                id: download.id,
                url: download.url,
                created_at: download.created_at,
                storage_type: download.storage_type,
                quality: download.quality
              }
            }
            return download
          })

          
          return {
            ...oldData,
            downloads: updatedDownloads
          }
        })
      } else if (message.type === 'queue_update' || message.type === 'dashboard_update') {
        // Atualizar a lista completa quando houver mudanças na fila
        console.log("Invalidando query de downloads devido a mudança na fila", { messageType: message.type })
        queryClient.invalidateQueries({ queryKey: ['downloads'] })
      } else {
        console.log("Tipo de mensagem não tratado", { messageType: message.type })
      }
    },
    onOpen: () => {
      console.log("WebSocket conectado para dashboard")
    },
    onClose: () => {
      console.log("WebSocket desconectado do dashboard")
    },
    onError: (error) => {
      console.log("Erro no WebSocket do dashboard", { error: error.type })
      console.error('Erro no WebSocket do dashboard:', error)
    },
    onAuthSuccess: (user) => {
      console.log("WebSocket autenticado para usuário", { user: user?.username })
    },
    autoReconnect: isAuthenticated, // Só reconectar se autenticado
    enabled: isAuthenticated, // Só conectar se autenticado
  })

  // Mutation para criar download
  const createDownloadMutation = useMutation({
    mutationFn: downloadService.createDownload,
    onSuccess: (data) => {
      console.log("Download criado com sucesso", { downloadId: data?.download?.id || 'unknown' })
      queryClient.invalidateQueries({ queryKey: ['downloads'] })
    },
    onError: (error) => {
      console.log("Erro ao criar download", { error: error.message })
    }
  })

  // Mutation para criar downloads em lote
  const createBatchDownloadsMutation = useMutation({
    mutationFn: downloadService.createBatchDownloads,
    onSuccess: (data) => {
      console.log("Downloads em lote criados com sucesso", { 
        downloadsCount: data.downloads?.length || 0,
        downloadIds: data.downloads?.map((d: any) => d.id) 
      })
      queryClient.invalidateQueries({ queryKey: ['downloads'] })
    },
    onError: (error) => {
      console.log("Erro ao criar downloads em lote", { error: error.message })
    }
  })

  // Mutation para deletar download
  const deleteDownloadMutation = useMutation({
    mutationFn: downloadService.deleteDownload,
    onSuccess: (data, downloadId) => {
      console.log("Download deletado com sucesso", { downloadId })
      queryClient.invalidateQueries({ queryKey: ['downloads'] })
    },
    onError: (error, downloadId) => {
      console.log("Erro ao deletar download", { downloadId, error: error.message })
    }
  })

  const downloads = downloadsData?.downloads || []

  const result = {
    downloads,
    isLoading,
    error,
    refetch,
    createDownload: createDownloadMutation.mutate,
    createDownloadAsync: createDownloadMutation.mutateAsync,
    createBatchDownloads: createBatchDownloadsMutation.mutate,
    createBatchDownloadsAsync: createBatchDownloadsMutation.mutateAsync,
    isCreating: createDownloadMutation.isPending || createBatchDownloadsMutation.isPending,
    createError: createDownloadMutation.error || createBatchDownloadsMutation.error,
    deleteDownload: deleteDownloadMutation.mutate,
    isDeleting: deleteDownloadMutation.isPending,
    isWebSocketConnected: isConnected && wsAuthenticated
  }

  return result
}

export function useDownloadForm() {
  const [url, setUrl] = useState('')
  const [quality, setQuality] = useState('best')
  const [storageType, setStorageType] = useState<'temporary' | 'permanent'>('temporary')

  const resetForm = () => {
    setUrl('')
    setQuality('best')
    setStorageType('temporary')
  }

  const isValidUrl = (url: string) => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.includes('youtube.com') || urlObj.hostname.includes('youtu.be')
    } catch {
      return false
    }
  }

  const canSubmit = url.trim() !== '' && isValidUrl(url.trim())

  return {
    url,
    setUrl,
    quality,
    setQuality,
    storageType,
    setStorageType,
    resetForm,
    canSubmit,
    isValidUrl,
  }
} 

export function useDownloadStats() {
  const { isAuthenticated } = useAuth()

  const {
    data: stats,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['download-stats'],
    queryFn: downloadService.getStats,
    enabled: isAuthenticated,
    refetchInterval: 3600, // Atualizar a cada 1 minuto
    staleTime: 3600, // Dados ficam "frescos" por 1 minuto
  })

  return {
    stats,
    isLoading,
    error,
    refetch,
  }
} 