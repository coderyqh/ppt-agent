import React from 'react'
import { Card, CardContent } from './ui/card'
import { cn } from '@/lib/utils'
import { MessageSquare, Eye } from 'lucide-react'

interface SlideCardProps {
  slide: {
    index: number
    kind: string
    intent: string
    title: string
    bullets: string[]
    speaker_notes: string
    visual: string
    layout?: string
  }
  theme?: {
    accent?: string
    background?: string
    text?: string
  }
}

const kindLabels: Record<string, string> = {
  title: '封面',
  context: '背景',
  problem: '问题',
  insight: '洞察',
  framework: '框架',
  evidence: '证据',
  roadmap: '路线图',
  deep_dive: '深入',
  closing: '结尾',
}

const kindColors: Record<string, string> = {
  title: 'bg-bark-500',
  context: 'bg-moss-400',
  problem: 'bg-clay-400',
  insight: 'bg-bark-400',
  framework: 'bg-moss-500',
  evidence: 'bg-clay-500',
  roadmap: 'bg-bark-400',
  deep_dive: 'bg-moss-300',
  closing: 'bg-bark-500',
}

export function SlideCard({ slide, theme }: SlideCardProps) {
  const kindLabel = kindLabels[slide.kind] || slide.kind
  const kindColor = kindColors[slide.kind] || 'bg-bark-400'

  return (
    <Card className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
      {/* 顶部装饰条 */}
      <div className={`h-1.5 ${kindColor} rounded-t-2xl`} />

      <CardContent className="p-5">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-bark-100 text-bark-700 font-bold text-sm">
              {slide.index}
            </span>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium text-white ${kindColor}`}>
              {kindLabel}
            </span>
          </div>
        </div>

        {/* 标题 */}
        <h3 className="font-display text-lg font-semibold text-bark-800 mb-2 line-clamp-2">
          {slide.title}
        </h3>

        {/* 意图 */}
        <p className="text-sm text-bark-500 mb-4 italic">
          {slide.intent}
        </p>

        {/* 要点 */}
        <div className="space-y-2 mb-4">
          {slide.bullets.map((bullet, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 text-sm text-bark-700"
            >
              <span className="text-moss-400 mt-1 flex-shrink-0">▸</span>
              <span>{bullet}</span>
            </div>
          ))}
        </div>

        {/* 视觉建议 */}
        <div className="flex items-center gap-2 p-3 rounded-lg bg-sand-100 mb-3">
          <Eye className="w-4 h-4 text-clay-500 flex-shrink-0" />
          <span className="text-xs text-bark-600">{slide.visual}</span>
        </div>

        {/* 演讲备注 */}
        <div className="p-3 rounded-lg bg-bark-50 border border-bark-100">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare className="w-4 h-4 text-bark-400" />
            <span className="text-xs font-semibold text-bark-500">演讲备注</span>
          </div>
          <p className="text-xs text-bark-600 leading-relaxed">
            {slide.speaker_notes}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
