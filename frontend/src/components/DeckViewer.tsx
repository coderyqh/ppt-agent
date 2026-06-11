import React from 'react'
import { SlideCard } from './SlideCard'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Badge } from './ui/badge'
import { Layers, Users, Palette, FileText } from 'lucide-react'

interface DeckViewerProps {
  deck: {
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
}

export function DeckViewer({ deck }: DeckViewerProps) {
  return (
    <div className="space-y-6">
      {/* Deck信息卡片 */}
      <Card className="relative overflow-hidden">
        {/* 装饰 */}
        <div className="absolute top-0 right-0 w-40 h-40 organic-blob bg-moss-100/30 -z-10" />
        <div className="absolute bottom-0 left-0 w-32 h-32 organic-blob bg-sand-200/30 -z-10" />

        <CardHeader>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-moss-100 to-sand-100">
              <Layers className="w-8 h-8 text-moss-600" />
            </div>
            <div>
              <CardTitle className="text-2xl">{deck.title}</CardTitle>
              <p className="text-bark-500 mt-1">共 {deck.slides.length} 页</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bark-50 border border-bark-100">
              <Users className="w-4 h-4 text-bark-500" />
              <span className="text-sm text-bark-700">{deck.audience}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bark-50 border border-bark-100">
              <FileText className="w-4 h-4 text-bark-500" />
              <span className="text-sm text-bark-700">{deck.style}</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-bark-50 border border-bark-100">
              <Palette className="w-4 h-4 text-bark-500" />
              <span className="text-sm text-bark-700">{deck.theme?.deerStyle || 'dark-premium'}</span>
            </div>
          </div>
        </CardHeader>

        {/* 审查意见 */}
        {deck.review_notes && deck.review_notes.length > 0 && (
          <CardContent>
            <div className="p-4 rounded-xl bg-sand-50 border border-sand-200">
              <h4 className="font-semibold text-bark-700 mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                审查意见
              </h4>
              <ul className="space-y-1.5">
                {deck.review_notes.map((note, idx) => (
                  <li
                    key={idx}
                    className="text-sm text-bark-600 flex items-start gap-2"
                  >
                    <span className="text-moss-400 mt-1">•</span>
                    <span>{note}</span>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        )}
      </Card>

      {/* 幻灯片网格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {deck.slides.map((slide) => (
          <SlideCard
            key={slide.index}
            slide={slide}
            theme={deck.theme}
          />
        ))}
      </div>
    </div>
  )
}
