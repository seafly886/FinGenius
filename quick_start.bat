@echo off
chcp 65001 >nul

echo FinGenius 股票分析系统启动中...

:: 启动服务器（后台运行）
start /min cmd /c "cd backend && python server.py"

:: 等待服务器启动
timeout /t 3 /nobreak >nul

:: 打开浏览器
start http://localhost:8000

echo 系统已启动，浏览器将自动打开
echo 访问地址: http://localhost:8000
pause