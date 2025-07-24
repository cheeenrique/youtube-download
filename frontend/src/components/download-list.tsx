'use client'

import { useDownloads } from '@/hooks/use-downloads'
import { useAuth } from '@/contexts/auth-context'
import { formatDate, formatDateWithExpiration, getStatusColor, getStatusText } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { Badge } from '@/components/ui/badge'
import { 
  Play, 
  Download, 
  Clock, 
  CheckCircle,
  XCircle,
  Trash2,
  ExternalLink,
  AlertCircle,
  Wifi,
  WifiOff
} from 'lucide-react'

export function DownloadList() {
  const { downloads, isLoading, deleteDownload, isDeleting, isWebSocketConnected } = useDownloads()
  const { isAuthenticated } = useAuth()
  const { toast } = useToast()

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'downloading':
        return <Play className="h-5 w-5 text-blue-500 animate-pulse" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const handleDelete = (id: string) => {
    if (confirm('Tem certeza que deseja excluir este download?')) {
      deleteDownload(id)
      toast({
        title: "Download excluído",
        description: "O download foi removido com sucesso",
      })
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Meus Downloads
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando downloads...</p>
        </CardContent>
      </Card>
    )
  }

  if (downloads.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            Meus Downloads
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">Nenhum download encontrado</p>
          <p className="text-sm text-gray-500">Faça seu primeiro download acima</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            <CardTitle>Meus Downloads</CardTitle>
          </div>
          <Badge variant={isWebSocketConnected ? "default" : "secondary"} className="flex items-center gap-1">
            {isWebSocketConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                Tempo Real
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                {isAuthenticated ? 'Conectando...' : 'Offline'}
              </>
            )}
          </Badge>
        </div>
        <CardDescription>
          Gerencie todos os seus downloads do YouTube
          {!isWebSocketConnected && (
            <span className="text-yellow-600 ml-2">
              (Atualizações em tempo real indisponíveis)
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {downloads.map((download) => (
            <div key={download.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start space-x-3 mb-2">
                    {download.thumbnail && (
                      <img 
                        src={download.thumbnail} 
                        alt={download.title || 'Thumbnail'} 
                        className="w-16 h-12 object-cover rounded flex-shrink-0"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none'
                        }}
                      />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        {getStatusIcon(download.status)}
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {download.title || download.url}
                        </p>
                      </div>
                      {download.title && (
                        <p className="text-xs text-gray-500 truncate mb-1">
                          {download.url}
                        </p>
                      )}
                      {download.description && (
                        <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                          {download.description}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {/* Barra de progresso */}
                  {download.status === 'downloading' && (
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Progresso</span>
                        <span>{Math.round(download.progress)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${download.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500 mb-3">
                    <div>
                      <span className="font-medium">Qualidade:</span> {download.quality}
                    </div>
                    <div>
                      <span className="font-medium">Armazenamento:</span> {download.storage_type === 'temporary' ? 'Temporário' : 'Permanente'}
                    </div>
                    <div>
                      <span className="font-medium">Criado:</span> {formatDate(download.created_at)}
                      {download.storage_type === 'temporary' && (
                        <div className="text-xs text-orange-600">
                          Expira: {formatDateWithExpiration(download.created_at).expires}
                        </div>
                      )}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>
                      <span className={`ml-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(download.status)}`}>
                        {getStatusText(download.status)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Informações do Google Drive */}
                  {download.uploaded_to_drive && (
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-2 rounded mb-3">
                      <CheckCircle className="w-4 h-4" />
                      Enviado para o Google Drive
                      {download.drive_file_id && (
                        <span className="text-xs text-gray-500">
                          (ID: {download.drive_file_id})
                        </span>
                      )}
                    </div>
                  )}
                  
                  {download.error_message && (
                    <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded mb-3">
                      <AlertCircle className="w-4 h-4" />
                      Erro: {download.error_message}
                    </div>
                  )}

                  {/* Botões de ação */}
                  <div className="flex items-center gap-2 mb-3">
                    {/* Botão de download do arquivo */}
                    {download.file_path && download.status === 'completed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        asChild
                      >
                        <a
                          href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/videos/${download.file_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2"
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </a>
                      </Button>
                    )}
                    
                    {/* Botão de link do vídeo original */}
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                    >
                      <a
                        href={download.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Link do Vídeo
                      </a>
                    </Button>
                    
                    {/* Informações do arquivo */}
                    {download.file_path && download.status === 'completed' && (
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {download.file_size && (
                          <span>
                            ({(download.file_size / 1024 / 1024).toFixed(1)} MB)
                          </span>
                        )}
                        {download.format && (
                          <span>
                            {download.format}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(download.id)}
                  disabled={isDeleting}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
} 