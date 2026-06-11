from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class PPTAgentConfig:
    model: str = "openai:mimo-v2.5-pro"
    base_url: str = "https://token-plan-cn.xiaomimimo.com/v1"
    api_key: str = ""
    visual_style: str = "dark-premium"
    output_dir: str = "outputs"

    @classmethod
    def from_env(cls) -> "PPTAgentConfig":
        _load_dotenv()
        return cls(
            model=os.getenv("PPT_AGENT_MODEL", "openai:mimo-v2.5-pro"),
            base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"),
            api_key=os.getenv("MIMO_API_KEY") or os.getenv("OPENAI_API_KEY", ""),
            visual_style=os.getenv("PPT_VISUAL_STYLE", "dark-premium"),
            output_dir=os.getenv("PPT_OUTPUT_DIR", "outputs"),
        )


def _load_dotenv() -> None:
    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
