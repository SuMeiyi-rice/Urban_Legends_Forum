#!/bin/bash

echo "🎃 都市传说AI论坛 - 启动脚本"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  未找到.env文件，从.env.example复制..."
    cp .env.example .env
    echo "✅ 已创建.env文件"
    echo "⚠️  请编辑.env文件，填入你的API密钥"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# Install dependencies
echo "📥 安装依赖包..."
pip install -q -r requirements.txt

echo ""
echo "✅ 环境配置完成!"
echo ""
echo "🚀 启动Flask服务器..."
echo "   访问地址: http://localhost:5000"
echo ""
echo "⚠️  注意："
echo "   1. 需要在.env中配置OpenAI或Anthropic API密钥"
echo "   2. AI功能需要API密钥才能工作"
echo "   3. 按 Ctrl+C 停止服务器"
echo ""

python app.py
