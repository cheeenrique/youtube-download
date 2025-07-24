'use client'

import { useEffect, useRef, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  data?: any
  timestamp?: string
  download_id?: string
  message?: string
  user?: any
}

interface UseWebSocketOptions {
  url: string
  token?: string
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  onAuthSuccess?: (user: any) => void
  reconnectInterval?: number
  autoReconnect?: boolean
  enabled?: boolean
}

export function useWebSocket({
  url,
  token,
  onMessage,
  onOpen,
  onClose,
  onError,
  onAuthSuccess,
  reconnectInterval = 3000,
  autoReconnect = true,
  enabled = true
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isAuthenticatedRef = useRef(false)
  const connectionIdRef = useRef<string>(`ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

  const log = useCallback((message: string, data?: any) => {
    const timestamp = new Date().toISOString()
    const logData = {
      timestamp,
      connectionId: connectionIdRef.current,
      message,
      data,
      url,
      hasToken: !!token,
      isAuthenticated: isAuthenticatedRef.current,
      readyState: wsRef.current?.readyState
    }
    console.log(`🔗 [WebSocket ${connectionIdRef.current}] ${message}`, logData)
  }, [url, token])

  const connect = useCallback(() => {
    if (!enabled) {
      log("Conexão desabilitada, não conectando")
      return
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      log("WebSocket já está aberto, não conectando novamente")
      return
    }

    try {
      log("Iniciando conexão WebSocket")
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        log("WebSocket conectado com sucesso")
        onOpen?.()
        
        // Se há token, enviar autenticação
        if (token && !isAuthenticatedRef.current) {
          log("Enviando autenticação WebSocket", { tokenLength: token.length })
          ws.send(JSON.stringify({
            type: 'auth',
            token: token
          }))
        } else if (!token) {
          log("Nenhum token disponível para autenticação")
        } else {
          log("Já autenticado, não enviando autenticação novamente")
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          log("Mensagem recebida", { messageType: data.type, data })
          
          // Verificar se é mensagem de autenticação
          if (data.type === 'auth_success') {
            isAuthenticatedRef.current = true
            log("Autenticação WebSocket bem-sucedida", { user: data.user })
            onAuthSuccess?.(data.user)
          } else if (data.type === 'error') {
            log("Erro no WebSocket recebido", { error: data.message })
            console.error('Erro no WebSocket:', data.message)
            onError?.(new Event(data.message))
          } else {
            // Mensagem normal
            log("Processando mensagem normal", { messageType: data.type })
            onMessage?.(data)
          }
        } catch (error) {
          log("Erro ao processar mensagem WebSocket", { error: error instanceof Error ? error.message : String(error) })
          console.error('Erro ao processar mensagem WebSocket:', error)
        }
      }

      ws.onclose = (event) => {
        log("WebSocket desconectado", { 
          code: event.code, 
          reason: event.reason, 
          wasClean: event.wasClean 
        })
        isAuthenticatedRef.current = false
        onClose?.()
        
        // Se foi fechado por erro de autenticação, não tentar reconectar
        if (event.code === 1008 || event.code === 1000) {
          log("WebSocket fechado por erro de autenticação, não reconectando")
          return
        }
        
        if (autoReconnect && enabled) {
          log("Agendando reconexão", { interval: reconnectInterval })
          reconnectTimeoutRef.current = setTimeout(() => {
            log("Tentando reconectar WebSocket")
            connect()
          }, reconnectInterval)
        } else {
          log("Reconexão automática desabilitada")
        }
      }

      ws.onerror = (error) => {
        log("Erro no WebSocket", { error: error.type })
        console.error('Erro no WebSocket:', error)
        onError?.(error)
      }

      wsRef.current = ws
    } catch (error) {
      log("Erro ao conectar WebSocket", { error: error instanceof Error ? error.message : String(error) })
      console.error('Erro ao conectar WebSocket:', error)
      onError?.(new Event('Erro ao conectar WebSocket'))
    }
  }, [url, token, onMessage, onOpen, onClose, onError, onAuthSuccess, reconnectInterval, autoReconnect, enabled, log])

  const disconnect = useCallback(() => {
    log("Desconectando WebSocket")
    
    if (reconnectTimeoutRef.current) {
      log("Cancelando timeout de reconexão")
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      log("Fechando conexão WebSocket")
      wsRef.current.close()
      wsRef.current = null
    }
    
    isAuthenticatedRef.current = false
    log("WebSocket desconectado completamente")
  }, [log])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN && isAuthenticatedRef.current) {
      log("Enviando mensagem", { message })
      wsRef.current.send(JSON.stringify(message))
    } else {
      log("Não é possível enviar mensagem", { 
        readyState: wsRef.current?.readyState, 
        isAuthenticated: isAuthenticatedRef.current 
      })
      console.warn('WebSocket não está conectado ou autenticado')
    }
  }, [log])

  useEffect(() => {
    log("useEffect executado", { enabled, hasToken: !!token })
    
    if (enabled) {
      log("Habilitando conexão WebSocket")
      connect()
    } else {
      log("Desabilitando conexão WebSocket")
      disconnect()
    }

    return () => {
      log("Cleanup do useEffect - desconectando")
      disconnect()
    }
  }, [connect, disconnect, enabled, log])

  // Listener para evento de logout
  useEffect(() => {
    const handleLogout = (event: CustomEvent) => {
      log("Evento de logout detectado, desconectando WebSocket", { eventDetail: event.detail })
      disconnect()
    }

    log("Registrando listener de logout")
    window.addEventListener('logout', handleLogout as EventListener)

    return () => {
      log("Removendo listener de logout")
      window.removeEventListener('logout', handleLogout as EventListener)
    }
  }, [disconnect, log])

  const connectionStatus = {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    isAuthenticated: isAuthenticatedRef.current,
    readyState: wsRef.current?.readyState,
    connectionId: connectionIdRef.current
  }

  log("Retornando status da conexão", connectionStatus)

  return {
    sendMessage,
    disconnect,
    ...connectionStatus
  }
} 