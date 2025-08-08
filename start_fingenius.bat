@echo off
chcp 65001 >nul
title FinGenius 股票分析系统 - 一键启动

echo.
echo ================================================================================
echo                          FinGenius 股票分析系统
echo                     AI-Powered Financial Analysis System
echo ================================================================================
echo.
echo [启动] 正在启动 FinGenius Web 服务器...
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到环境变量中
    echo [提示] 请先安装 Python 3.7+ 并添加到 PATH
    pause
    exit /b 1
)

:: 检查是否在正确的目录
if not exist "backend\server.py" (
    echo [错误] 未找到 backend\server.py 文件
    echo [提示] 请确保在 FinGenius-2 项目根目录下运行此脚本
    pause
    exit /b 1
)

:: 检查是否存在虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [环境] 检测到虚拟环境，正在激活...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [环境] 检测到虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
) else (
    echo [环境] 使用系统 Python 环境
)

:: 切换到backend目录并启动服务器
cd backend

echo [服务] 启动 Web 服务器...
echo [地址] http://localhost:8000
echo [提示] 服务器启动后将自动打开浏览器
echo.

:: 延迟5秒后打开浏览器
start "" cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8000"

:: 启动Python服务器
python server.py

:: 如果服务器意外退出
echo.
echo [提示] 服务器已停止运行
pause