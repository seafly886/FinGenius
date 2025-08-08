@echo off
chcp 65001 >nul
echo.
echo ========================================
echo           停止 FinGenius 服务
echo ========================================
echo.

echo 正在查找并停止 FinGenius 相关进程...

:: 停止Python进程（通过端口8000）
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo 发现端口8000被进程 %%a 占用，正在停止...
    taskkill /f /pid %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✓ 成功停止进程 %%a
    )
)

:: 停止可能的Python进程
tasklist | findstr python.exe >nul
if %errorlevel% equ 0 (
    echo 正在停止Python相关进程...
    taskkill /f /im python.exe >nul 2>&1
    echo ✓ Python进程已停止
)

:: 停止可能的uvicorn进程
tasklist | findstr uvicorn >nul
if %errorlevel% equ 0 (
    echo 正在停止uvicorn进程...
    taskkill /f /im uvicorn.exe >nul 2>&1
    echo ✓ uvicorn进程已停止
)

echo.
echo ========================================
echo        FinGenius 服务已停止
echo ========================================
echo.
echo 按任意键退出...
pause >nul