@echo off
chcp 65001 >nul
title FinGenius 一键启动

:: 设置颜色
color 0A

echo.
echo  ███████╗██╗███╗   ██╗ ██████╗ ███████╗███╗   ██╗██╗██╗   ██╗███████╗
echo  ██╔════╝██║████╗  ██║██╔════╝ ██╔════╝████╗  ██║██║██║   ██║██╔════╝
echo  █████╗  ██║██╔██╗ ██║██║  ███╗█████╗  ██╔██╗ ██║██║██║   ██║███████╗
echo  ██╔══╝  ██║██║╚██╗██║██║   ██║██╔══╝  ██║╚██╗██║██║██║   ██║╚════██║
echo  ██║     ██║██║ ╚████║╚██████╔╝███████╗██║ ╚████║██║╚██████╔╝███████║
echo  ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚══════╝
echo.
echo                        AI-Powered Financial Analysis System
echo.

:: 检查Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [❌] Python 未安装或未添加到环境变量
    echo [💡] 请安装 Python 3.7+ 并添加到 PATH
    goto :error
)
echo [✅] Python 环境正常

:: 检查项目文件
echo [2/4] 检查项目文件...
if not exist "backend\server.py" (
    echo [❌] 未找到项目文件
    echo [💡] 请在 FinGenius-2 项目根目录运行
    goto :error
)
echo [✅] 项目文件完整

:: 检查端口占用
echo [3/4] 检查端口状态...
netstat -an | find "8000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo [⚠️] 端口 8000 已被占用
    echo [💡] 正在尝试终止占用进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "8000" ^| find "LISTENING"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo [✅] 端口 8000 可用

:: 启动服务器
echo [4/4] 启动 Web 服务器...
echo [🚀] 服务器启动中...
echo [🌐] 访问地址: http://localhost:8000
echo.

:: 后台启动服务器
start /min "FinGenius Server" cmd /c "cd backend && python server.py"

:: 等待服务器完全启动
echo [⏳] 等待服务器启动完成...
:wait_loop
timeout /t 1 /nobreak >nul
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo [⏳] 服务器启动中...
    goto :wait_loop
)

echo [✅] 服务器启动成功！
echo [🌐] 正在打开浏览器...

:: 打开浏览器
start http://localhost:8000

echo.
echo ================================================================================
echo [✅] FinGenius 股票分析系统已成功启动！
echo [🌐] 浏览器地址: http://localhost:8000
echo [📊] 现在可以开始股票分析了
echo [❌] 按任意键关闭此窗口（不会影响服务器运行）
echo ================================================================================
pause >nul
exit

:error
echo.
echo [❌] 启动失败，请检查上述错误信息
pause
exit /b 1