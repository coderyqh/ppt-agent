# PPT Agent MVP

一个可扩展的 PPT 创建 Agent 骨架。它把“生成 PPT”拆成多个 skill：

- `BriefSkill`：解析主题、受众、页数、风格。
- `ResearchSkill`：整理用户资料或输入文本。
- `OutlineSkill`：生成叙事结构和每页意图。
- `SlideWriterSkill`：生成每页标题、正文和演讲备注。
- `DesignSkill`：选择基础版式、主题色和视觉建议。
- `ReviewSkill`：检查页面密度、标题、结构完整性。
- `PptxRenderer`：把结构化 deck 渲染成 `.pptx`。

核心设计是先生成可审稿的 `deck.json`，再渲染成 PPTX，避免让模型直接写难维护的 PPT 代码。

## 快速开始

```powershell
cd "C:\Users\11989\Desktop\opencode test\ppt-agent"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm install
python cli.py generate --topic "AI Agent 商业化趋势" --audience "投资人" --slides 8 --style "consulting" --out outputs
```

生成文件：

- `outputs/deck.json`
- `outputs/deck.md`
- `outputs/deck.pptx`

PPTX 渲染现在接入 skills.sh 的 `anthropics/skills/pptx` 工作流，使用 PptxGenJS 生成可编辑 PowerPoint。因此需要先运行 `npm install` 安装 Node 依赖。如果没有安装 Node 依赖，仍会输出 `deck.json` 和 `deck.md`，但 `deck.pptx` 会报出缺少 PptxGenJS 的错误。

视觉风格参考了 skills.sh 的 `bytedance/deer-flow/ppt-generation`。默认使用 `dark-premium`，也可以切换：

```powershell
python cli.py generate --llm --visual-style glassmorphism --topic "AI Agent 商业化趋势" --audience "投资人" --slides 8 --out outputs
```

可选值：`dark-premium`、`glassmorphism`、`gradient-modern`、`keynote`、`minimal-swiss`、`editorial`、`3d-isometric`。

## 使用 Xiaomi MiMo Token Plan API

项目支持 OpenAI-compatible Chat Completions 接口。不要把 API key 写进代码；推荐放在当前终端环境变量或本地 `.env` 文件。

MiMo Token Plan 的 key 格式是 `tp-xxxxx`，与按量付费的 `sk-xxxxx` 不通用。Base URL 以订阅管理页展示为准；国内集群通常是 `https://token-plan-cn.xiaomimimo.com/v1`。

PowerShell 临时设置：

```powershell
$env:MIMO_API_KEY="你的_tp_token_plan_key"
$env:MIMO_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
$env:PPT_AGENT_MODEL="mimo-v2.5-pro"
```

也可以创建本地 `.env` 文件：

```env
MIMO_API_KEY=你的_tp_token_plan_key
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
PPT_AGENT_MODEL=mimo-v2.5-pro
```

然后启用 LLM 写作：

```powershell
python cli.py generate --llm --topic "AI Agent 商业化趋势" --audience "投资人" --slides 8 --style "consulting" --out outputs
```

也可以显式指定模型：

```powershell
python cli.py generate --llm --model "mimo-v2.5-pro" --topic "企业级 PPT Agent 产品方案" --audience "CTO" --slides 10 --out outputs
```

## 项目结构

```text
ppt-agent/
  cli.py
  requirements.txt
  ppt_agent/
    agent.py
    models.py
    render.py
    skills.py
  examples/
    brief.md
```

## 下一步可扩展方向

- 接入 OpenAI/Claude：让 `SlideWriterSkill` 生成更强内容。
- 接入 RAG：从 PDF、Word、网页、企业知识库提取资料。
- 接入品牌模板：读取企业模板的字体、颜色、母版。
- 接入视觉 QA：导出每页图片后检查文字溢出、视觉拥挤。
- 接入 Web 前端：聊天、上传资料、逐页预览和修改。
