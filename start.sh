#!/bin/bash
# 专家文献检索工具 - Mac/Linux 便携版

echo "================================================"
echo "  专家文献检索工具 - 便携版"
echo "================================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ 未找到 Python3！"
        echo "请先安装 Python 3.7+"
        echo "下载地址: https://www.python.org/downloads/"
        exit 1
    fi
    PYTHON=python
else
    PYTHON=python3
fi

echo "✅ Python 已安装"
$PYTHON --version
echo ""

# 获取当前目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查依赖是否已安装
echo "📦 检查依赖..."
if $PYTHON -c "import flask, requests, pypinyin" 2>/dev/null; then
    echo "✅ 依赖已安装"
else
    echo "📦 安装依赖（首次使用）..."
    $PYTHON -m pip install -r requirements.txt --user
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
fi

echo ""
echo "================================================"
echo "  🚀 启动服务器..."
echo "================================================"
echo ""
echo "启动后，请在浏览器访问："
echo "http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

$PYTHON scripts/server.py
