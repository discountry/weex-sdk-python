#!/bin/bash
# 发布脚本 - 将 weex-sdk 发布到 PyPI

set -e  # 遇到错误立即退出

echo "🚀 Weex SDK 发布脚本"
echo "===================="
echo ""

# 检查必要的工具
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 python 命令"
    exit 1
fi

if ! python -c "import build" 2>/dev/null; then
    echo "📦 安装 build 工具..."
    pip install build twine
fi

# 清理旧构建文件
echo "🧹 清理旧构建文件..."
rm -rf build/ dist/ *.egg-info/
echo "✅ 清理完成"
echo ""

# 构建分发包
echo "📦 构建分发包..."
python -m build
echo "✅ 构建完成"
echo ""

# 检查包
echo "✅ 检查包..."
twine check dist/*
echo "✅ 检查通过"
echo ""

# 显示构建的文件
echo "📁 构建的文件:"
ls -lh dist/
echo ""

# 询问是否上传到 TestPyPI
read -p "📤 是否上传到 TestPyPI 进行测试? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 上传到 TestPyPI..."
    twine upload --repository testpypi dist/*
    echo "✅ 已上传到 TestPyPI"
    echo ""
    echo "💡 测试安装命令:"
    echo "   pip install --index-url https://test.pypi.org/simple/ weex-sdk"
    echo ""
fi

# 询问是否上传到正式 PyPI
read -p "📤 是否上传到正式 PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 上传到正式 PyPI..."
    twine upload dist/*
    echo "✅ 已上传到 PyPI"
    echo ""
    echo "🎉 发布完成！"
    echo ""
    echo "💡 安装命令:"
    echo "   pip install weex-sdk"
    echo ""
else
    echo "⏭️  跳过上传到正式 PyPI"
fi

echo "✅ 完成！"
