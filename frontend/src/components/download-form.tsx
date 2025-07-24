'use client'

import { useState } from 'react'
import { useDownloadForm } from '@/hooks/use-downloads'
import { useDownloads } from '@/hooks/use-downloads'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/hooks/use-toast'
import { Download, Link, AlertCircle, CheckCircle, Plus, X } from 'lucide-react'

export function DownloadForm() {
  const { url, setUrl, quality, setQuality, storageType, setStorageType, canSubmit, resetForm } = useDownloadForm()
  const { createBatchDownloads, isCreating, createError, isWebSocketConnected } = useDownloads()
  const { isAuthenticated } = useAuth()
  const { toast } = useToast()
  
  // Estado para múltiplos URLs
  const [urls, setUrls] = useState<string[]>([''])

  const log = (message: string, data?: any) => {
    const timestamp = new Date().toISOString()
    const logData = {
      timestamp,
      message,
      data,
      isAuthenticated,
      isWebSocketConnected
    }
    console.log(`📝 [DownloadForm] ${message}`, logData)
  }

  // Funções para gerenciar múltiplos URLs
  const addUrl = () => {
    setUrls([...urls, ''])
  }

  const removeUrl = (index: number) => {
    if (urls.length > 1) {
      setUrls(urls.filter((_, i) => i !== index))
    }
  }

  const updateUrl = (index: number, value: string) => {
    const newUrls = [...urls]
    newUrls[index] = value
    setUrls(newUrls)
  }

  const getValidUrls = () => {
    return urls.filter(url => url.trim() !== '' && isValidUrl(url.trim()))
  }

  const canSubmitMultiple = () => {
    return getValidUrls().length > 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const validUrls = getValidUrls()
    if (validUrls.length === 0) {
      log("Tentativa de envio sem URLs válidas", { urls, validUrls })
      return
    }

    log("Iniciando criação de downloads", { 
      urls: validUrls, 
      quality, 
      storageType,
      isWebSocketConnected
    })

    try {
      const downloadData = {
        urls: validUrls,
        quality,
        storage_type: storageType,
        upload_to_drive: false
      }

      log("Dados do download preparados", { downloadData })

      await createBatchDownloads(downloadData)
      
      log("Downloads criados com sucesso")
      
      toast({
        title: "Downloads iniciados!",
        description: `${validUrls.length} download(s) adicionado(s) à fila e será(ão) processado(s) em breve.`,
      })

      resetForm()
      setUrls([''])
      log("Formulário resetado após sucesso")
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Erro desconhecido"
      log("Erro ao criar downloads", { error: errorMessage })
      
      toast({
        title: "Erro ao iniciar downloads",
        description: errorMessage || "Ocorreu um erro ao processar seus downloads.",
        variant: "destructive",
      })
    }
  }

  const isValidUrl = (url: string) => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname.includes('youtube.com') || urlObj.hostname.includes('youtu.be')
    } catch {
      return false
    }
  }

  log("Renderizando DownloadForm", { 
    urls, 
    quality, 
    storageType, 
    canSubmitMultiple: canSubmitMultiple(),
    isCreating,
    hasError: !!createError
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="w-5 h-5" />
          Novo Download
        </CardTitle>
        <CardDescription>
          Adicione um novo vídeo do YouTube para download
          {!isWebSocketConnected && (
            <span className="text-yellow-600 ml-2">
              (Atualizações em tempo real indisponíveis)
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* URLs Inputs */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>URLs do YouTube</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addUrl}
                className="flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Adicionar mais
              </Button>
            </div>
            
            {urls.map((url, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Link className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input
                      type="url"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={url}
                      onChange={(e) => {
                        const newUrl = e.target.value
                        log("URL alterada", { index, newUrl, isValid: isValidUrl(newUrl) })
                        updateUrl(index, newUrl)
                      }}
                      className="pl-10"
                    />
                  </div>
                  {urls.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeUrl(index)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
                
                {url && !isValidUrl(url) && (
                  <div className="flex items-center gap-2 text-sm text-red-600">
                    <AlertCircle className="w-4 h-4" />
                    URL inválida. Use uma URL do YouTube.
                  </div>
                )}
                {url && isValidUrl(url) && (
                  <div className="flex items-center gap-2 text-sm text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    URL válida do YouTube.
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Quality and Storage Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="quality">Qualidade</Label>
              <select
                id="quality"
                value={quality}
                onChange={(e) => {
                  const newQuality = e.target.value
                  log("Qualidade alterada", { newQuality })
                  setQuality(e.target.value)
                }}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="best">Melhor qualidade</option>
                <option value="worst">Pior qualidade</option>
                <option value="720p">720p</option>
                <option value="480p">480p</option>
                <option value="360p">360p</option>
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="storage">Tipo de Armazenamento</Label>
              <select
                id="storage"
                value={storageType}
                onChange={(e) => {
                  const newStorageType = e.target.value as 'temporary' | 'permanent'
                  log("Tipo de armazenamento alterado", { newStorageType })
                  setStorageType(newStorageType)
                }}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="temporary">Temporário (24h)</option>
                <option value="permanent">Permanente</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={!canSubmitMultiple() || isCreating}
            className="w-full"
          >
            {isCreating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processando...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Iniciar {getValidUrls().length > 1 ? 'Downloads' : 'Download'} ({getValidUrls().length})
              </>
            )}
          </Button>

          {/* Error Display */}
          {createError && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded">
              <AlertCircle className="w-4 h-4" />
              Erro: {createError.message}
            </div>
          )}

          {/* WebSocket Status */}
          <div className="text-xs text-gray-500 text-center">
            {isWebSocketConnected ? (
              <span className="text-green-600">✓ Conectado para atualizações em tempo real</span>
            ) : (
              <span className="text-yellow-600">⚠ Atualizações em tempo real indisponíveis</span>
            )}
            
          </div>
        </form>
      </CardContent>
    </Card>
  )
} 