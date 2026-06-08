#!/usr/bin/env python3
"""AI Factory CLI — 入口包装器"""
import sys
import os

# 确保能找到 ai-factory-runtime 包
_runtime_dir = os.path.dirname(os.path.abspath(__file__))
if _runtime_dir not in sys.path:
    sys.path.insert(0, _runtime_dir)

from cli import main

if __name__ == "__main__":
    main()
