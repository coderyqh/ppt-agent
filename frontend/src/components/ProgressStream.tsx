import React, { useMemo } from 'react'
import { StepCard } from './StepCard'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { WebSocketMessage } from '@/hooks/useWebSocket'
import { Activity, Download, Eye, RefreshCw } from 'lucide-react'

interface ProgressStreamProps {
  messages: WebSocketMessage[]
  isConnected: boolean
  onConfirm?: () => void
  onPreview?: () => void
  onReset?: () => void
  isLoading?: boolean
}

const allSteps = ['brief', 'insights', 'outline', 'slides', 'design', 'review', 'preview']

export function ProgressStream({
  messages,
  isConnected,
  onConfirm,
  onPreview,
  onReset,
  isLoading,
}: ProgressStreamProps) {
  // 解析消息，获取每个步骤的状态
  const stepStates = useMemo(() => {
    const states: Record<string, {
      status: 'pending' | 'active' | 'completed' | 'failed'
      message: string
      progress?: number
      result?: any
    }> = {}

    // 初始化所有步骤
    allSteps.forEach((step) => {
      states[step] = {
        status: 'pending',
        message: '等待中...',
      }
    })

    // 处理消息
    messages.forEach((msg) => {
      if (msg.step) {
        if (msg.type === 'step_start') {
          states[msg.step] = {
            status: 'active',
            message: msg.message || '处理中...',
            progress: 0,
          }
        } else if (msg.type === 'step_done') {
          states[msg.step] = {
            status: 'completed',
            message: '完成',
            progress: 100,
            result: msg.result,
          }
        }
      }

      // 更新进度
      if (msg.progress && msg.step) {
        if (states[msg.step]) {
          states[msg.step].progress = msg.progress
        }
      }

      // 错误处理
      if (msg.type === 'error') {
        // 找到最后一个active的步骤，标记为failed
        for (const step of allSteps) {
          if (states[step].status === 'active') {
            states[step] = {
              status: 'failed',
              message: msg.message || '失败',
            }
            break
          }
        }
      }
    })

    return states
  }, [messages])

  // 计算总体进度
  const totalProgress = useMemo(() => {
    const completedSteps = allSteps.filter(
      (step) => stepStates[step].status === 'completed'
    ).length
    return (completedSteps / allSteps.length) * 100
  }, [stepStates])

  // 检查是否完成
  const isCompleted = messages.some((msg) => msg.type === 'deck_ready')
  const isFailed = messages.some((msg) => msg.type === 'error')

  return (
    <Card className="relative overflow-hidden">
      {/* 装饰 */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-moss-400 via-clay-400 to-bark-400" />

      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-moss-100">
              <Activity className="w-5 h-5 text-moss-500" />
            </div>
            <CardTitle>生成进度</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-moss-400 animate-pulse' : 'bg-bark-300'
              }`}
            />
            <span className="text-xs text-bark-500">
              {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>

        {/* 总体进度条 */}
        <div className="mt-4">
          <div className="flex justify-between text-sm text-bark-600 mb-2">
            <span>总体进度</span>
            <span className="font-semibold">{Math.round(totalProgress)}%</span>
          </div>
          <div className="h-3 bg-bark-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-moss-400 to-moss-500 rounded-full transition-all duration-700 ease-out"
              style={{ width: `${totalProgress}%` }}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* 步骤列表 */}
        {allSteps.map((step) => (
          <StepCard
            key={step}
            step={step}
            message={stepStates[step].message}
            status={stepStates[step].status}
            progress={stepStates[step].progress}
            result={stepStates[step].result}
          />
        ))}

        {/* 操作按钮 */}
        <div className="pt-4 space-y-3">
          {isCompleted && (
            <>
              <Button
                onClick={onPreview}
                variant="outline"
                className="w-full"
                size="lg"
              >
                <Eye className="w-5 h-5 mr-2" />
                查看HTML预览
              </Button>
              <Button
                onClick={onConfirm}
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                    渲染中...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5 mr-2" />
                    确认并下载PPTX
                  </>
                )}
              </Button>
            </>
          )}

          {isFailed && (
            <Button
              onClick={onReset}
              variant="secondary"
              className="w-full"
            >
              <RefreshCw className="w-5 h-5 mr-2" />
              重新开始
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
