'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { WebSocketSingleton } from '@/hooks/use-websocket-singleton'

interface User {
  id: string
  username: string
  email: string
  full_name?: string
  role: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (usernameOrEmail: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, full_name?: string) => Promise<void>
  logout: () => void
  isLoading: boolean
  isAuthenticated: boolean
  disconnectWebSocket: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const log = (message: string, data?: any) => {
    const timestamp = new Date().toISOString()
    const logData = {
      timestamp,
      message,
      data,
      hasUser: !!user,
      hasToken: !!token,
      isAuthenticated: !!user && !!token
    }
    console.log(`🔐 [AuthContext] ${message}`, logData)
  }

  // Função para validar token no backend
  const validateToken = async (token: string): Promise<boolean> => {
    try {
      log("Validando token no backend", { tokenLength: token.length })
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      const isValid = response.ok
      log("Token validado", { isValid })
      return isValid
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      log("Erro ao validar token", { error: errorMessage })
      console.error('Erro ao validar token:', error)
      return false
    }
  }

  // Função para desconectar WebSocket no backend
  const disconnectWebSocketFromServer = async (token: string) => {
    try {
      log("Desconectando WebSocket do servidor", { tokenLength: token.length })
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/ws/connections/disconnect-me`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        log("WebSocket desconectado do servidor com sucesso", { result })
      } else {
        log("Erro ao desconectar WebSocket do servidor", { 
          status: response.status, 
          statusText: response.statusText 
        })
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      log("Erro ao desconectar WebSocket do servidor", { error: errorMessage })
      console.error('Erro ao desconectar WebSocket do servidor:', error)
    }
  }

  // Função para desconectar WebSocket
  const disconnectWebSocket = () => {
    log("Disparando evento de logout para desconectar WebSocket", { hasToken: !!token })
    // Disparar evento customizado para que os hooks de WebSocket possam se desconectar
    window.dispatchEvent(new CustomEvent('logout', { detail: { token } }))
  }

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        log("Inicializando autenticação")
        // Verificar se há um token salvo no localStorage
        const savedToken = localStorage.getItem('token')
        const savedUser = localStorage.getItem('user')
        
        log("Dados salvos encontrados", { 
          hasSavedToken: !!savedToken, 
          hasSavedUser: !!savedUser 
        })
        
        if (savedToken && savedUser) {
          // Validar token no backend
          const isValid = await validateToken(savedToken)
          
          if (isValid) {
            // Token válido, fazer login automático
            setToken(savedToken)
            setUser(JSON.parse(savedUser))
            log("Login automático realizado com sucesso")
          } else {
            // Token inválido, limpar localStorage
            log("Token inválido, limpando localStorage")
            localStorage.removeItem('token')
            localStorage.removeItem('user')
          }
        } else {
          log("Nenhum dado salvo encontrado")
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        log("Erro durante inicialização da autenticação", { error: errorMessage })
        console.error('Erro durante inicialização da autenticação:', error)
        // Em caso de erro, limpar localStorage
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      } finally {
        setIsLoading(false)
        log("Inicialização da autenticação concluída")
      }
    }

    initializeAuth()
  }, [])

  const login = async (usernameOrEmail: string, password: string) => {
    log("Iniciando processo de login", { usernameOrEmail })
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username_or_email: usernameOrEmail,
        password: password,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      log("Erro no login", { error: errorData.detail })
      throw new Error(errorData.detail || 'Erro no login')
    }

    const data = await response.json()
    log("Login bem-sucedido", { user: data.user?.username })
    
    // Salvar token e dados do usuário
    setToken(data.access_token)
    setUser(data.user)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
  }

  const register = async (username: string, email: string, password: string, full_name?: string) => {
    log("Iniciando processo de registro", { username, email })
    
    const payload: any = {
      username,
      email,
      password,
    }
    
    if (full_name && full_name.trim()) {
      payload.full_name = full_name.trim()
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorData = await response.json()
      log("Erro no registro", { error: errorData.detail })
      throw new Error(errorData.detail || 'Erro no registro')
    }

    const result = await response.json()
    log("Registro bem-sucedido", { result })
    return result
  }

  const logout = async () => {
    log("Iniciando processo de logout")
    
    // Desconectar WebSocket do servidor antes de limpar o estado
    if (token) {
      try {
        log("Desconectando WebSocket do servidor")
        await disconnectWebSocketFromServer(token)
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        log("Erro ao desconectar WebSocket", { error: errorMessage })
        console.error('Erro ao desconectar WebSocket:', error)
      }
    } else {
      log("Nenhum token disponível para desconectar WebSocket")
    }

    // Desconectar TODAS as conexões WebSocket no frontend (incluindo todas as abas)
    log("Desconectando TODAS as conexões WebSocket no frontend")
    WebSocketSingleton.disconnectAll()

    // Disparar evento para desconectar WebSocket no frontend (para compatibilidade)
    log("Disparando evento de logout no frontend")
    disconnectWebSocket()

    // Limpar estado e localStorage
    log("Limpando estado e localStorage")
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    log("Logout concluído com sucesso")
  }

  const isAuthenticated = !!user && !!token

  log("Renderizando AuthProvider", { 
    isAuthenticated, 
    hasUser: !!user, 
    hasToken: !!token,
    isLoading 
  })

  return (
    <AuthContext.Provider value={{ 
      user, 
      token, 
      login, 
      register, 
      logout, 
      isLoading,
      isAuthenticated,
      disconnectWebSocket
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 