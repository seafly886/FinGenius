#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FinGenius 一键启动脚本
AI-Powered Financial Analysis System
"""

import os
import sys
import subprocess
import time
import socket
import webbrowser
import platform
import threading
from pathlib import Path

# 设置控制台编码为UTF-8
if platform.system() == 'Windows':
    os.system('chcp 65001 >nul')

def print_banner():
    """打印启动横幅"""
    print()
    print(" ███████╗██╗███╗   ██╗ ██████╗ ███████╗███╗   ██╗██╗██╗   ██╗███████╗")
    print(" ██╔════╝██║████╗  ██║██╔════╝ ██╔════╝████╗  ██║██║██║   ██║██╔════╝")
    print(" █████╗  ██║██╔██╗ ██║██║  ███╗█████╗  ██╔██╗ ██║██║██║   ██║███████╗")
    print(" ██╔══╝  ██║██║╚██╗██║██║   ██║██╔══╝  ██║╚██╗██║██║██║   ██║╚════██║")
    print(" ██║     ██║██║ ╚████║╚██████╔╝███████╗██║ ╚████║██║╚██████╔╝███████║")
    print(" ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚══════╝")
    print()
    print("                       AI-Powered Financial Analysis System")
    print()

def check_python_environment():
    """检查Python环境"""
    print("[1/4] 检查 Python 环境...")
    try:
        # 检查Python版本
        result = subprocess.run([sys.executable, '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[✅] Python 环境正常 ({version})")
            return True
        else:
            print("[❌] Python 环境检查失败")
            return False
    except Exception as e:
        print(f"[❌] Python 未安装或未添加到环境变量: {e}")
        print("[💡] 请安装 Python 3.7+ 并添加到 PATH")
        return False

def check_project_files():
    """检查项目文件完整性"""
    print("[2/4] 检查项目文件...")
    
    # 检查必要文件
    required_files = [
        "backend/server.py",
        "config/config.example.toml",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("[❌] 未找到项目文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("[💡] 请在 FinGenius 项目根目录运行")
        return False
    
    print("[✅] 项目文件完整")
    return True

def check_port_available(port=8000):
    """检查端口是否可用"""
    print(f"[3/4] 检查端口状态...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            print(f"[✅] 端口 {port} 可用")
            return True
        except OSError:
            print(f"[⚠️] 端口 {port} 已被占用")
            return False

def kill_process_on_port(port=8000):
    """终止占用指定端口的进程"""
    print("[💡] 正在尝试终止占用进程...")
    
    try:
        if platform.system() == 'Windows':
            # Windows系统
            result = subprocess.run(['netstat', '-ano'], 
                                  capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(['taskkill', '/f', '/pid', pid], 
                                 capture_output=True)
                    print(f"[✅] 已终止进程 PID: {pid}")
                    return True
        else:
            # Unix系统
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pid = result.stdout.strip()
                subprocess.run(['kill', '-9', pid], capture_output=True)
                print(f"[✅] 已终止进程 PID: {pid}")
                return True
                
    except Exception as e:
        print(f"[❌] 终止进程失败: {e}")
    
    return False

def wait_for_server(port=8000, timeout=30):
    """等待服务器启动完成"""
    print("[⏳] 等待服务器启动完成...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                print("[✅] 服务器启动成功！")
                return True
        except (socket.timeout, ConnectionRefusedError):
            print("[⏳] 服务器启动中...")
            time.sleep(1)
    
    print("[❌] 服务器启动超时")
    return False

def start_server():
    """启动Web服务器"""
    print("[4/4] 启动 Web 服务器...")
    print("[🚀] 服务器启动中...")
    print("[🌐] 访问地址: http://localhost:8000")
    print("[📝] 服务器日志输出:")
    print("-" * 50)
    
    # 切换到backend目录并启动服务器
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("[❌] backend目录不存在")
        return False
    
    try:
        # 启动服务器进程，显示日志输出
        if platform.system() == 'Windows':
            # Windows系统，显示输出
            process = subprocess.Popen(
                [sys.executable, 'server.py'],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        else:
            # Unix系统，显示输出
            process = subprocess.Popen(
                [sys.executable, 'server.py'],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        
        return process
    except Exception as e:
        print(f"[❌] 启动服务器失败: {e}")
        return None

def read_server_output(process):
    """读取并显示服务器输出"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"[服务器] {output.strip()}")

def open_browser(url="http://localhost:8000"):
    """打开浏览器"""
    print("[🌐] 正在打开浏览器...")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"[❌] 打开浏览器失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查Python环境
    if not check_python_environment():
        return 1
    
    # 检查项目文件
    if not check_project_files():
        return 1
    
    # 检查端口
    if not check_port_available(8000):
        if not kill_process_on_port(8000):
            print("[❌] 无法释放端口8000，请手动处理")
            return 1
        time.sleep(2)  # 等待端口释放
    
    # 启动服务器
    server_process = start_server()
    if not server_process:
        return 1
    
    # 启动线程读取服务器输出
    output_thread = threading.Thread(target=read_server_output, args=(server_process,))
    output_thread.daemon = True
    output_thread.start()
    
    # 等待服务器启动
    if not wait_for_server():
        server_process.terminate()
        return 1
    
    # 不打开浏览器
    # open_browser()
    
    print()
    print("=" * 80)
    print("[✅] FinGenius 股票分析系统已成功启动！")
    print("[🌐] 服务器地址: http://localhost:8000")
    print("[📊] 请在浏览器中访问上述地址开始股票分析")
    print("[❌] 关闭此窗口不会影响服务器运行")
    print("=" * 80)
    
    try:
        input("按回车键关闭此窗口...")
    except KeyboardInterrupt:
        pass
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
