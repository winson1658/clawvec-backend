"""
Vercel Serverless 入口點
將根目錄加入 sys.path 後導入 FastAPI app
"""

import sys
import os

# 將項目根目錄加入 Python 路徑，讓 main.py 的絕對導入能正確解析
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app  # noqa: E402 — 必須在 sys.path 設置後導入
