'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

interface WebSocketMessage {
  type: string
  data?: any
  timestamp?: string
  download_id?: string
  message?: string
  user?: any
}

interface UseWebSocketSingletonOptions {
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

// Singleton para gerenciar uma única conexão WebSocket
class WebSocketSingleton {
  private static instance: WebSocketSingleton
  private ws: WebSocket | null = null
  private listeners: Set<(message: WebSocketMessage) => void> = new Set()
  private onOpenCallbacks: Set<() => void> = new Set()
  private onCloseCallbacks: Set<() => void> = new Set()
  private onErrorCallbacks: Set<(error: Event) => void> = new Set()
  private onAuthSuccessCallbacks: Set<(user: any) => void> = new Set()
  private reconnectTimeout: NodeJS.Timeout | null = null
  private isAuthenticated = false
  private currentToken: string | null = null
  private url: string | null = null
  private enabled = true
  private autoReconnect = true
  private reconnectInterval = 3000

  private constructor() {}

  static getInstance(): WebSocketSingleton {
    if (!WebSocketSingleton.instance) {
      WebSocketSingleton.instance = new WebSocketSingleton()
    }
    return WebSocketSingleton.instance
  }

  static disconnectAll(): void {
    if (WebSocketSingleton.instance) {
      WebSocketSingleton.instance.disconnectAll()
    }
  }

  configure(options: UseWebSocketSingletonOptions) {
    this.url = options.url
    this.currentToken = options.token || null
    this.enabled = options.enabled ?? true
    this.autoReconnect = options.autoReconnect ?? true
    this.reconnectInterval = options.reconnectInterval || 3000

    if (options.onMessage) this.listeners.add(options.onMessage)
    if (options.onOpen) this.onOpenCallbacks.add(options.onOpen)
    if (options.onClose) this.onCloseCallbacks.add(options.onClose)
    if (options.onError) this.onErrorCallbacks.add(options.onError)
    if (options.onAuthSuccess) this.onAuthSuccessCallbacks.add(options.onAuthSuccess)

    this.connect()
  }

  private connect() {
    if (!this.enabled || !this.url) return

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("🔗 [WebSocketSingleton] WebSocket já está aberto")
      return
    }

    try {
      console.log("🔗 [WebSocketSingleton] Iniciando conexão WebSocket")
      this.ws = new WebSocket(this.url)
      
      this.ws.onopen = () => {
        console.log("🔗 [WebSocketSingleton] WebSocket conectado com sucesso")
        this.onOpenCallbacks.forEach(callback => callback())
        
        // Se há token, enviar autenticação
        if (this.currentToken && !this.isAuthenticated) {
          console.log("🔗 [WebSocketSingleton] Enviando autenticação WebSocket")
          this.ws?.send(JSON.stringify({
            type: 'auth',
            token: this.currentToken
          }))
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log("🔗 [WebSocketSingleton] Mensagem recebida", { messageType: data.type })
          
          // Verificar se é mensagem de autenticação
          if (data.type === 'auth_success') {
            this.isAuthenticated = true
            console.log("🔗 [WebSocketSingleton] Autenticação WebSocket bem-sucedida", { user: data.user })
            this.onAuthSuccessCallbacks.forEach(callback => callback(data.user))
          } else {
            // Enviar para todos os listeners
            this.listeners.forEach(listener => listener(data))
          }
        } catch (error) {
          console.error("🔗 [WebSocketSingleton] Erro ao processar mensagem", error)
        }
      }

      this.ws.onclose = (event) => {
        console.log("🔗 [WebSocketSingleton] WebSocket desconectado", { code: event.code, reason: event.reason })
        this.isAuthenticated = false
        this.onCloseCallbacks.forEach(callback => callback())
        
        // Reconectar se habilitado
        if (this.autoReconnect && this.enabled) {
          console.log("🔗 [WebSocketSingleton] Agendando reconexão")
          this.reconnectTimeout = setTimeout(() => {
            this.connect()
          }, this.reconnectInterval)
        }
      }

      this.ws.onerror = (error) => {
        console.error("🔗 [WebSocketSingleton] Erro no WebSocket", error)
        this.onErrorCallbacks.forEach(callback => callback(error))
      }

    } catch (error) {
      console.error("🔗 [WebSocketSingleton] Erro ao conectar WebSocket", error)
    }
  }

  disconnect() {
    console.log("🔗 [WebSocketSingleton] Desconectando WebSocket")
    this.enabled = false
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    
    this.isAuthenticated = false
  }

  // Método para desconexão global (logout)
  disconnectAll() {
    console.log("🔗 [WebSocketSingleton] Desconectando TODAS as conexões WebSocket (logout)")
    this.enabled = false
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    
    this.isAuthenticated = false
    this.currentToken = null
    
    // Limpar todos os listeners e callbacks
    this.listeners.clear()
    this.onOpenCallbacks.clear()
    this.onCloseCallbacks.clear()
    this.onErrorCallbacks.clear()
    this.onAuthSuccessCallbacks.clear()
    
    console.log("🔗 [WebSocketSingleton] Todas as conexões e listeners foram limpos")
  }

  removeListeners(options: UseWebSocketSingletonOptions) {
    if (options.onMessage) this.listeners.delete(options.onMessage)
    if (options.onOpen) this.onOpenCallbacks.delete(options.onOpen)
    if (options.onClose) this.onCloseCallbacks.delete(options.onClose)
    if (options.onError) this.onErrorCallbacks.delete(options.onError)
    if (options.onAuthSuccess) this.onAuthSuccessCallbacks.delete(options.onAuthSuccess)
  }

  getStatus() {
    return {
      isConnected: this.ws?.readyState === WebSocket.OPEN,
      isAuthenticated: this.isAuthenticated,
      readyState: this.ws?.readyState
    }
  }
}

export { WebSocketSingleton }
export function useWebSocketSingleton(options: UseWebSocketSingletonOptions) {
  const [status, setStatus] = useState(() => WebSocketSingleton.getInstance().getStatus())
  const singleton = useRef(WebSocketSingleton.getInstance())

  const updateStatus = useCallback(() => {
    setStatus(singleton.current.getStatus())
  }, [])

  useEffect(() => {
    const onOpen = () => {
      updateStatus()
      options.onOpen?.()
    }

    const onClose = () => {
      updateStatus()
      options.onClose?.()
    }

    const onError = (error: Event) => {
      updateStatus()
      options.onError?.(error)
    }

    const onAuthSuccess = (user: any) => {
      updateStatus()
      options.onAuthSuccess?.(user)
    }

    // Configurar o singleton com os callbacks
    singleton.current.configure({
      ...options,
      onOpen,
      onClose,
      onError,
      onAuthSuccess
    })

    // Atualizar status inicial
    updateStatus()

    // Cleanup
    return () => {
      singleton.current.removeListeners({
        ...options,
        onOpen,
        onClose,
        onError,
        onAuthSuccess
      })
    }
  }, [options.url, options.token, options.enabled, updateStatus])

  // Cleanup global quando o componente é desmontado
  useEffect(() => {
    return () => {
      // Não desconectar aqui, apenas remover listeners
      // A conexão será mantida para outros componentes
    }
  }, [])

  return {
    isConnected: status.isConnected,
    isAuthenticated: status.isAuthenticated,
    readyState: status.readyState
  }
} 