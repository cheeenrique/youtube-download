'use client'

import { useAuth } from '@/contexts/auth-context'
import { DownloadPage } from '@/components/download-page'
import { ProtectedRoute } from '@/components/protected-route'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { LogOut, User, Settings, Download, BarChart3 } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { useRouter } from 'next/navigation'
import { useDownloadStats } from '@/hooks/use-downloads'

function DashboardContent() {
  const { user, logout, isAuthenticated } = useAuth()
  const { toast } = useToast()
  const router = useRouter()
  const { stats, isLoading: statsLoading } = useDownloadStats()

  const handleLogout = async () => {
    try {
      // Mostrar toast de "fazendo logout"
      toast({
        title: "Fazendo logout...",
        description: "Desconectando WebSocket e limpando sessão",
      })
      
      // Aguardar o logout (que inclui desconexão do WebSocket)
      await logout()
      
      // Mostrar toast de sucesso
      toast({
        title: "Logout realizado",
        description: "Você foi desconectado com sucesso",
      })
      
      // Redirecionar para login
      router.push('/login')
    } catch (error) {
      console.error('Erro durante logout:', error)
      toast({
        title: "Erro no logout",
        description: "Ocorreu um erro durante o logout",
        variant: "destructive",
      })
    }
  }

  // Verificação adicional de segurança
  if (!isAuthenticated || !user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Download className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">
                YouTube Download API
              </h1>
            </div>

            {/* User menu */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Avatar className="w-8 h-8">
                  <AvatarImage src="" />
                  <AvatarFallback className="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm">
                    {user.username.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-900">{user.username}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
              </div>
              
              <Separator orientation="vertical" className="h-6" />
              
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="text-gray-600 hover:text-gray-900"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Sair
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Welcome section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Bem-vindo, {user.username}! 👋
          </h2>
          <p className="text-gray-600">
            Gerencie seus downloads do YouTube de forma rápida e segura
          </p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Download className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Downloads</p>
                <p className="text-2xl font-bold text-gray-900">
                  {statsLoading ? '...' : stats?.total_downloads || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <BarChart3 className="w-6 h-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Concluídos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {statsLoading ? '...' : stats?.completed_downloads || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Settings className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Em Processo</p>
                <p className="text-2xl font-bold text-gray-900">
                  {statsLoading ? '...' : stats?.pending_downloads || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Download section */}
        <DownloadPage />
      </main>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
} 