'use client'

import { DownloadForm } from './download-form'
import { DownloadList } from './download-list'

export function DownloadPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            YouTube Download API
          </h1>
          <p className="text-lg text-gray-600">
            Baixe vídeos do YouTube de forma rápida e segura
          </p>
        </div>

        {/* Download Form */}
        <div className="mb-8">
          <DownloadForm />
        </div>

        {/* Downloads List */}
        <DownloadList />
      </div>
    </div>
  )
} 