import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Leaf, Sparkles, Wand2 } from 'lucide-react'

interface TopicFormProps {
  onSubmit: (data: FormData) => void
  isLoading?: boolean
}

interface FormData {
  topic: string
  audience: string
  slides: number
  style: string
  visualStyle: string
  mode: string
  sourceText: string
}

const visualStyles = [
  { value: 'dark-premium', label: '深色高端' },
  { value: 'glassmorphism', label: '毛玻璃' },
  { value: 'gradient-modern', label: '渐变现代' },
  { value: 'keynote', label: 'Keynote风格' },
  { value: 'minimal-swiss', label: '瑞士极简' },
  { value: 'editorial', label: '编辑排版' },
  { value: '3d-isometric', label: '等距3D' },
]

const modes = [
  { value: 'rule', label: '快速模式', description: '使用模板，秒级生成' },
  { value: 'llm', label: 'AI模式', description: '调用LLM，高质量' },
  { value: 'auto', label: '自动模式', description: '优先AI，失败回退' },
]

export function TopicForm({ onSubmit, isLoading }: TopicFormProps) {
  const [formData, setFormData] = useState<FormData>({
    topic: '',
    audience: '通用商业受众',
    slides: 8,
    style: 'consulting',
    visualStyle: 'dark-premium',
    mode: 'rule',
    sourceText: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card className="relative overflow-hidden">
        {/* 装饰性背景 */}
        <div className="absolute top-0 right-0 w-32 h-32 organic-blob bg-moss-100/50 -z-10 animate-float" />
        <div className="absolute bottom-0 left-0 w-24 h-24 organic-blob bg-sand-200/50 -z-10 animate-float-delayed" />

        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-moss-100">
              <Leaf className="w-6 h-6 text-moss-500" />
            </div>
            <div>
              <CardTitle>创建PPT</CardTitle>
              <CardDescription>输入主题，AI帮你生成专业演示文稿</CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* 主题 */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-bark-700 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-clay-400" />
              PPT主题 *
            </label>
            <Input
              placeholder="例如：AI技术发展趋势、Q4业务汇报、产品发布方案..."
              value={formData.topic}
              onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
              required
              className="text-base"
            />
          </div>

          {/* 受众和页数 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-bark-700">目标受众</label>
              <Input
                placeholder="例如：投资人、技术团队、管理层..."
                value={formData.audience}
                onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-bark-700">页数</label>
              <Input
                type="number"
                min={3}
                max={30}
                value={formData.slides}
                onChange={(e) => setFormData({ ...formData, slides: parseInt(e.target.value) || 8 })}
              />
            </div>
          </div>

          {/* 风格选择 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-bark-700">演示风格</label>
              <Select
                value={formData.style}
                onValueChange={(value) => setFormData({ ...formData, style: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择风格" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consulting">咨询风格</SelectItem>
                  <SelectItem value="tech">技术风格</SelectItem>
                  <SelectItem value="business">商务风格</SelectItem>
                  <SelectItem value="academic">学术风格</SelectItem>
                  <SelectItem value="creative">创意风格</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-bark-700">视觉风格</label>
              <Select
                value={formData.visualStyle}
                onValueChange={(value) => setFormData({ ...formData, visualStyle: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择视觉风格" />
                </SelectTrigger>
                <SelectContent>
                  {visualStyles.map((style) => (
                    <SelectItem key={style.value} value={style.value}>
                      {style.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 生成模式 */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-bark-700 flex items-center gap-2">
              <Wand2 className="w-4 h-4 text-moss-400" />
              生成模式
            </label>
            <div className="grid grid-cols-3 gap-3">
              {modes.map((mode) => (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, mode: mode.value })}
                  className={`p-3 rounded-xl border-2 transition-all duration-200 text-left ${
                    formData.mode === mode.value
                      ? 'border-moss-400 bg-moss-50'
                      : 'border-bark-200 hover:border-bark-300'
                  }`}
                >
                  <div className="font-semibold text-sm">{mode.label}</div>
                  <div className="text-xs text-bark-500 mt-1">{mode.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* 参考资料 */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-bark-700">参考资料（可选）</label>
            <Textarea
              placeholder="粘贴相关资料，AI会从中提取关键洞察..."
              value={formData.sourceText}
              onChange={(e) => setFormData({ ...formData, sourceText: e.target.value })}
              rows={4}
            />
          </div>
        </CardContent>

        <CardFooter>
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={!formData.topic || isLoading}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                开始生成PPT
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
