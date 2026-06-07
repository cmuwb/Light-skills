"""共享 fixture / 路径设置。

把 src/ 加入 import 路径，使 `import example.stats` 在未安装包时也能跑测试。
✅ 已实测：`pip install -e ".[dev]"` 装包成功后，删掉下面的 sys.path hack
仍可 `import example.stats`（解析到已安装包），故正式项目装包后应删除此 hack。
（本环境无 uv，uv sync 路径未实测；pip 可编辑安装路径已实测通过。）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
