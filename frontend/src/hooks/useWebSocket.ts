import { useState, useEffect, useRef, useCallback } from 'react'

export interface WebSocketMessage {
  type: string
  step?: string
  message?: string
  result?: any
  progress?: number
  deck?: any
  url?: string
  session_id?: string
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
  autoReconnect?: boolean
  reconnectInterval?: number
  enabled?: boolean
}

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    enabled = true,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  const connect = useCallback(() => {
    // 如果没有url或未启用，不连接
    if (!url || !enabled) {
      return
    }

    try {
      console.log('正在连接WebSocket:', url)
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket连接成功')
        setIsConnected(true)
        setError(null)
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          console.log('收到WebSocket消息:', message)
          setMessages((prev) => [...prev, message])
          onMessage?.(message)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket连接关闭')
        setIsConnected(false)
        onDisconnect?.()

        if (autoReconnect && enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('尝试重新连接...')
            connect()
          }, reconnectInterval)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket错误:', event)
        setError('WebSocket连接错误')
        onError?.(event)
      }
    } catch (e) {
      console.error('无法创建WebSocket连接:', e)
      setError('无法创建WebSocket连接')
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, autoReconnect, reconnectInterval, enabled])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((data: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  useEffect(() => {
    if (enabled && url) {
      connect()
    }
    return () => {
      disconnect()
    }
  }, [connect, disconnect, enabled, url])

  return {
    isConnected,
    messages,
    error,
    send,
    disconnect,
    clearMessages,
  }
}
