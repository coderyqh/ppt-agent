#!/usr/bin/env python3
"""启动PPT Agent API服务"""

import uvicorn
import sys

if __name__ == "__main__":
    print("=" * 50)
    print("PPT Agent API 服务启动中...")
    print("=" * 50)
    print(f"访问地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print("=" * 50)
    print("按 Ctrl+C 停止服务")
    print("=" * 50)

    try:
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,  # 关闭自动重载，避免问题
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        sys.exit(1)
