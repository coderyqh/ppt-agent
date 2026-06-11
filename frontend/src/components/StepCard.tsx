import React from 'react'
import { cn } from '@/lib/utils'
import { Check, Loader2, AlertCircle, Clock } from 'lucide-react'

interface StepCardProps {
  step: string
  message: string
  status: 'pending' | 'active' | 'completed' | 'failed'
  progress?: number
  result?: any
}

const stepLabels: Record<string, string> = {
  brief: '解析需求',
  insights: '提取洞察',
  outline: '构建大纲',
  slides: '生成内容',
  design: '应用设计',
  review: '质量检查',
  preview: '生成预览',
}

const stepIcons: Record<string, string> = {
  brief: '📋',
  insights: '💡',
  outline: '📝',
  slides: '📊',
  design: '🎨',
  review: '✅',
  preview: '👁️',
}

export function StepCard({ step, message, status, progress, result }: StepCardProps) {
  const label = stepLabels[step] || step
  const icon = stepIcons[step] || '📌'

  return (
    <div
      className={cn(
        'flex items-start gap-4 p-4 rounded-xl transition-all duration-300',
        status === 'active' && 'bg-moss-50 border-2 border-moss-200 shadow-md',
        status === 'completed' && 'bg-white border border-bark-100',
        status === 'failed' && 'bg-red-50 border border-red-200',
        status === 'pending' && 'bg-bark-50/50 border border-bark-100 opacity-60'
      )}
    >
      {/* 图标 */}
      <div
        className={cn(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg',
          status === 'active' && 'bg-moss-100 animate-pulse',
          status === 'completed' && 'bg-moss-100',
          status === 'failed' && 'bg-red-100',
          status === 'pending' && 'bg-bark-100'
        )}
      >
        {status === 'completed' ? (
          <Check className="w-5 h-5 text-moss-600" />
        ) : status === 'active' ? (
          <Loader2 className="w-5 h-5 text-moss-600 animate-spin" />
        ) : status === 'failed' ? (
          <AlertCircle className="w-5 h-5 text-red-600" />
        ) : (
          <span>{icon}</span>
        )}
      </div>

      {/* 内容 */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="font-semibold text-bark-800">{label}</h4>
          {status === 'active' && (
            <span className="text-xs text-moss-600 bg-moss-100 px-2 py-0.5 rounded-full">
              进行中
            </span>
          )}
          {status === 'completed' && (
            <span className="text-xs text-moss-600 bg-moss-100 px-2 py-0.5 rounded-full">
              完成
            </span>
          )}
        </div>
        <p className="text-sm text-bark-500 mt-1">{message}</p>

        {/* 进度条 */}
        {status === 'active' && progress !== undefined && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-bark-500 mb-1">
              <span>进度</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-2 bg-bark-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-moss-400 to-moss-500 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* 结果预览 */}
        {status === 'completed' && result && (
          <div className="mt-2 text-xs text-bark-400">
            {Array.isArray(result) ? (
              <span>已生成 {result.length} 项</span>
            ) : typeof result === 'object' ? (
              <span>数据已就绪</span>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
