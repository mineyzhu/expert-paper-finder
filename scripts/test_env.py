#!/usr/bin/env python3
"""简单的 Flask 测试"""
import sys
import os

print("Python 版本:", sys.version)
print("当前目录:", os.getcwd())
print()

# 测试导入
print("测试导入模块...")
try:
    import flask
    print("  [OK] flask")
except ImportError as e:
    print("  [错误] flask:", e)

try:
    import requests
    print("  [OK] requests")
except ImportError as e:
    print("  [错误] requests:", e)

try:
    import pypinyin
    print("  [OK] pypinyin")
except ImportError as e:
    print("  [错误] pypinyin:", e)

print()
print("测试完成!")
