import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string) {
  const date = new Date(dateString)
  // Aplicar offset -03 manualmente
  const localDate = new Date(date.getTime() - (3 * 60 * 60 * 1000))
  
  return localDate.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatDateWithExpiration(dateString: string, hoursToExpire: number = 1) {
  const date = new Date(dateString)
  // Aplicar offset -03 manualmente
  const localDate = new Date(date.getTime() - (3 * 60 * 60 * 1000))
  const expirationDate = new Date(localDate.getTime() + (hoursToExpire * 60 * 60 * 1000))
  
  const createdFormatted = localDate.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
  
  const expiresFormatted = expirationDate.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
  
  return {
    created: createdFormatted,
    expires: expiresFormatted
  }
}

export function getStatusColor(status: string) {
  switch (status) {
    case 'completed':
      return 'text-green-600 bg-green-50 border-green-200'
    case 'failed':
      return 'text-red-600 bg-red-50 border-red-200'
    case 'downloading':
      return 'text-blue-600 bg-blue-50 border-blue-200'
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200'
  }
}

export function getStatusText(status: string) {
  switch (status) {
    case 'completed':
      return 'Concluído'
    case 'failed':
      return 'Falhou'
    case 'downloading':
      return 'Baixando'
    case 'pending':
      return 'Pendente'
    default:
      return status
  }
}
