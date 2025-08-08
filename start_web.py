#!/usr/bin/env python3
"""
FinGenius Web 启动脚本
"""
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """检查依赖是否安装"""
    try:
        import uvicorn
        import starlette
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install uvicorn starlette")
        return False

def create_directories():
    """创建必要的目录"""
    directories = ['frontend', 'backend', 'report', 'results']
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ 目录结构检查完成")

def start_server():
    """启动Web服务器"""
    try:
        print("🚀 启动 FinGenius Web 服务器...")
        print("📊 前端地址: http://localhost:8000")
        print("🔧 API地址: http://localhost:8000/api/")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        # 启动服务器
        subprocess.run([
            sys.executable, 
            "backend/server.py"
        ], cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🤖 FinGenius 股票分析系统 - Web版")
    print("=" * 60)
    
    # 检查依赖
    if not check_requirements():
        return 1
    
    # 创建目录
    create_directories()
    
    # 启动服务器
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())