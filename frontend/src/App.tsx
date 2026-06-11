import React, { useState, useCallback } from 'react'
import { TopicForm } from './components/TopicForm'
import { ProgressStream } from './components/ProgressStream'
import { DeckViewer } from './components/DeckViewer'
import { useWebSocket, WebSocketMessage } from './hooks/useWebSocket'
import { Button } from './components/ui/button'
import { Leaf, Github, Sparkles } from 'lucide-react'

interface Deck {
  title: string
  audience: string
  style: string
  theme: Record<string, string>
  slides: Array<{
    index: number
    kind: string
    intent: string
    title: string
    bullets: string[]
    speaker_notes: string
    visual: string
    layout?: string
  }>
  review_notes: string[]
}

type AppState = 'form' | 'generating' | 'preview' | 'completed'

function App() {
  const [state, setState] = useState<AppState>('form')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [deck, setDeck] = useState<Deck | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // WebSocket连接
  const {
    isConnected,
    messages,
    clearMessages,
  } = useWebSocket({
    url: sessionId ? `ws://localhost:8000/ws/${sessionId}` : '',
    onMessage: useCallback((message: WebSocketMessage) => {
      if (message.type === 'deck_ready' && message.deck) {
        setDeck(message.deck)
        setState('preview')
      }
      if (message.type === 'error') {
        setError(message.message || '生成失败')
      }
    }, []),
  })

  // 提交表单
  const handleSubmit = async (formData: any) => {
    setError(null)
    setState('generating')

    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: formData.topic,
          audience: formData.audience,
          slides: formData.slides,
          style: formData.style,
          visual_style: formData.visualStyle,
          mode: formData.mode,
          source_text: formData.sourceText,
        }),
      })

      if (!response.ok) {
        throw new Error('创建会话失败')
      }

      const data = await response.json()
      setSessionId(data.session_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : '请求失败')
      setState('form')
    }
  }

  // 确认生成PPTX
  const handleConfirm = async () => {
    if (!sessionId) return

    setIsConfirming(true)
    try {
      const response = await fetch(`/api/sessions/${sessionId}/confirm`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error('生成PPTX失败')
      }

      const data = await response.json()
      setState('completed')

      // 触发下载
      window.open(`/api/sessions/${sessionId}/download`, '_blank')
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成PPTX失败')
    } finally {
      setIsConfirming(false)
    }
  }

  // 查看预览
  const handlePreview = () => {
    if (sessionId) {
      window.open(`/api/sessions/${sessionId}/preview`, '_blank')
    }
  }

  // 重置
  const handleReset = () => {
    setState('form')
    setSessionId(null)
    setDeck(null)
    setError(null)
    clearMessages()
  }

  return (
    <div className="min-h-screen nature-gradient leaf-pattern">
      {/* 头部 */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-bark-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-moss-100 to-sand-100">
                <Leaf className="w-6 h-6 text-moss-600" />
              </div>
              <div>
                <h1 className="text-xl font-display font-bold text-bark-800">
                  PPT Agent
                </h1>
                <p className="text-xs text-bark-500">智能演示文稿生成工具</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {state !== 'form' && (
                <Button variant="ghost" onClick={handleReset}>
                  新建PPT
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700">
            {error}
          </div>
        )}

        {/* 表单页面 */}
        {state === 'form' && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-moss-100 text-moss-700 mb-4">
                <Sparkles className="w-4 h-4" />
                <span className="text-sm font-medium">AI驱动的PPT生成</span>
              </div>
              <h2 className="text-3xl font-display font-bold text-bark-800 mb-3">
                创建你的演示文稿
              </h2>
              <p className="text-bark-500 max-w-md mx-auto">
                输入主题和需求，AI将帮你生成专业的PPT内容，支持多种视觉风格和生成模式
              </p>
            </div>
            <TopicForm onSubmit={handleSubmit} />
          </div>
        )}

        {/* 生成进度页面 */}
        {state === 'generating' && sessionId && (
          <div className="max-w-3xl mx-auto">
            <ProgressStream
              messages={messages}
              isConnected={isConnected}
              onConfirm={handleConfirm}
              onPreview={handlePreview}
              onReset={handleReset}
              isLoading={isConfirming}
            />
          </div>
        )}

        {/* 预览页面 */}
        {state === 'preview' && deck && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-display font-bold text-bark-800">
                PPT内容预览
              </h2>
              <div className="flex gap-3">
                <Button variant="outline" onClick={handlePreview}>
                  查看HTML预览
                </Button>
                <Button onClick={handleConfirm} disabled={isConfirming}>
                  {isConfirming ? '渲染中...' : '下载PPTX'}
                </Button>
              </div>
            </div>
            <DeckViewer deck={deck} />
          </div>
        )}

        {/* 完成页面 */}
        {state === 'completed' && (
          <div className="max-w-2xl mx-auto text-center">
            <div className="organic-card p-12">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-moss-100 flex items-center justify-center">
                <Sparkles className="w-10 h-10 text-moss-600" />
              </div>
              <h2 className="text-3xl font-display font-bold text-bark-800 mb-3">
                PPT生成完成！
              </h2>
              <p className="text-bark-500 mb-8">
                你的演示文稿已经准备好了，点击下方按钮下载
              </p>
              <div className="flex justify-center gap-4">
                <Button variant="outline" onClick={handlePreview}>
                  查看HTML预览
                </Button>
                <Button
                  onClick={() => {
                    if (sessionId) {
                      window.open(`/api/sessions/${sessionId}/download`, '_blank')
                    }
                  }}
                >
                  下载PPTX文件
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* 底部 */}
      <footer className="mt-auto py-6 border-t border-bark-100 bg-white/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between text-sm text-bark-500">
            <span>PPT Agent - 智能演示文稿生成工具</span>
            <span>Powered by DeepAgents</span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
