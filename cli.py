from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from ppt_agent.agent import create_ppt_agent
from ppt_agent.config import PPTAgentConfig
from ppt_agent.tools import generate_html_preview, render_pptx
import json


def main() -> None:
    parser = argparse.ArgumentParser(description="PPT Agent - 基于 deepagents 的智能PPT生成工具")
    parser.add_argument("generate", nargs="?", help="运行PPT生成。")
    parser.add_argument("--topic", required=True, help="PPT主题。")
    parser.add_argument("--audience", default="通用商业受众", help="目标受众。")
    parser.add_argument("--slides", type=int, default=8, help="页数，3-30。")
    parser.add_argument("--style", default="consulting", help="演示风格。")
    parser.add_argument("--visual-style", default="dark-premium", help="视觉风格。")
    parser.add_argument("--source", default="", help="资料文件路径。")
    parser.add_argument("--out", default="outputs", help="输出目录。")
    parser.add_argument("--model", default=None, help="模型名称。")
    parser.add_argument("--mode", default="rule", choices=["rule", "llm", "auto"], help="内容生成模式。")
    parser.add_argument("--skip-preview", action="store_true", help="跳过HTML预览，直接生成PPTX。")
    parser.add_argument("--quiet", action="store_true", help="静默模式。")
    args = parser.parse_args()

    config = PPTAgentConfig.from_env()
    if args.model:
        config.model = args.model
    config.visual_style = args.visual_style
    config.output_dir = args.out

    source_text = ""
    if args.source:
        source_text = Path(args.source).read_text(encoding="utf-8")

    agent = create_ppt_agent(
        model=config.model,
        visual_style=config.visual_style,
    )

    prompt = f"""请为以下需求生成PPT：

主题：{args.topic}
受众：{args.audience}
页数：{args.slides}
风格：{args.style}
视觉风格：{args.visual_style}
内容生成模式：{args.mode}
{f"参考资料：{source_text}" if source_text else ""}

请按照工作流程依次执行所有步骤：
1. create_brief
2. extract_insights (mode={args.mode})
3. build_outline (mode={args.mode})
4. write_slides (mode={args.mode})
5. apply_design
6. review_deck (mode={args.mode})
7. generate_html_preview

完成后告诉我HTML预览文件的位置，等待用户确认后再渲染PPTX。"""

    print("=" * 60)
    print("PPT Agent - 智能PPT生成工具")
    print("=" * 60)
    print(f"主题：{args.topic}")
    print(f"受众：{args.audience}")
    print(f"页数：{args.slides}")
    print(f"风格：{args.style}")
    print(f"视觉风格：{args.visual_style}")
    print(f"生成模式：{args.mode}")
    print("=" * 60)

    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"configurable": {"thread_id": "ppt-generation"}},
    )

    # 检查是否生成了预览文件
    preview_path = Path("workspace/preview.html")
    deck_path = Path("workspace/deck.json")

    if preview_path.exists():
        print("\n" + "=" * 60)
        print("HTML预览已生成！")
        print(f"预览文件：{preview_path.absolute()}")
        print("=" * 60)

        if not args.skip_preview:
            # 打开浏览器预览
            try:
                webbrowser.open(f"file://{preview_path.absolute()}")
                print("\n已在浏览器中打开预览...")
            except Exception:
                print(f"\n请手动打开预览文件：{preview_path.absolute()}")

            # 等待用户确认
            print("\n" + "-" * 60)
            while True:
                user_input = input("是否继续生成PPTX？(y=确认/n=取消/修改意见): ").strip()

                if user_input.lower() == 'y':
                    if deck_path.exists():
                        print("\n正在渲染PPTX...")
                        pptx_path = render_pptx(str(deck_path))
                        print(f"\n✅ PPTX已生成：{pptx_path}")
                        print(f"输出目录：{config.output_dir}")
                    else:
                        print("❌ 未找到deck.json文件")
                    break
                elif user_input.lower() == 'n':
                    print("\n已取消生成。")
                    break
                else:
                    # 处理修改意见
                    print(f"\n收到修改意见：{user_input}")
                    print("请重新运行命令并调整参数。")
                    break
        else:
            # 跳过预览，直接生成PPTX
            if deck_path.exists():
                print("\n正在渲染PPTX...")
                pptx_path = render_pptx(str(deck_path))
                print(f"\n✅ PPTX已生成：{pptx_path}")
            else:
                print("❌ 未找到deck.json文件")
    else:
        print("\n❌ 未生成HTML预览文件")
        print("请检查workspace目录中的中间文件。")


if __name__ == "__main__":
    main()
