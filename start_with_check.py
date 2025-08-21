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
import logging
from pathlib import Path
from datetime import datetime

# 设置控制台编码为UTF-8
if platform.system() == 'Windows':
    os.system('chcp 65001 >nul')

# 检测是否在服务器环境中运行
def is_server_environment():
    """检测是否在服务器环境中运行"""
    # 检查环境变量
    server_env_vars = ['TENCENTCLOUD_RUN', 'SERVER_ENV', 'DOCKER_ENV']
    for var in server_env_vars:
        if os.environ.get(var):
            return True
    
    # 检查是否在Docker容器中
    if os.path.exists('/.dockerenv'):
        return True
    
    # 检查是否在无桌面环境的服务器上
    if not os.environ.get('DISPLAY') and platform.system() != 'Windows':
        return True
    
    return False

# 配置日志记录
def setup_logging():
    """配置日志记录"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"fingenius_{timestamp}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# 全局变量
IS_SERVER_ENV = is_server_environment()
logger = setup_logging()

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
            # 根据环境选择绑定地址
            host = '0.0.0.0' if IS_SERVER_ENV else 'localhost'
            s.bind((host, port))
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

def manage_server_process(process):
    """管理服务器进程，特别是在服务器环境中"""
    if IS_SERVER_ENV:
        logger.info("启动服务器进程管理...")
        
        # 创建一个PID文件，记录服务器进程ID
        pid_file = Path("logs/server.pid")
        pid_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            logger.info(f"已创建PID文件: {pid_file}")
        except Exception as e:
            logger.error(f"创建PID文件失败: {e}")
        
        # 在服务器环境中，添加进程监控
        def monitor_process():
            while True:
                try:
                    # 检查进程是否仍在运行
                    if process.poll() is not None:
                        logger.warning(f"服务器进程已退出，返回码: {process.returncode}")
                        break
                    
                    # 定期检查进程状态
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"进程监控出错: {e}")
                    break
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_process)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info("服务器进程监控已启动")

def wait_for_server(port=8000, timeout=30):
    """等待服务器启动完成"""
    print("[⏳] 等待服务器启动完成...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # 根据环境选择连接地址
            host = '0.0.0.0' if IS_SERVER_ENV else 'localhost'
            with socket.create_connection((host, port), timeout=1):
                print("[✅] 服务器启动成功！")
                return True
        except (socket.timeout, ConnectionRefusedError):
            print("[⏳] 服务器启动中...")
            time.sleep(1)
        except OSError as e:
            if IS_SERVER_ENV:
                logger.warning(f"连接服务器时出错: {e}")
            print(f"[⏳] 服务器启动中... ({e})")
            time.sleep(1)
    
    print("[❌] 服务器启动超时")
    return False

def start_server():
    """启动Web服务器"""
    print("[4/4] 启动 Web 服务器...")
    print("[🚀] 服务器启动中...")
    
    # 根据环境显示不同的访问地址
    if IS_SERVER_ENV:
        print("[🌐] 服务器地址: http://0.0.0.0:8000")
        print("[🌐] 外网访问地址: 请使用服务器的公网IP访问")
    else:
        print("[🌐] 访问地址: http://localhost:8000")
    
    print("[📝] 服务器日志输出:")
    print("-" * 50)
    
    # 切换到backend目录并启动服务器
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("[❌] backend目录不存在")
        logger.error("backend目录不存在")
        return False
    
    try:
        # 在服务器环境中使用不同的启动参数
        if IS_SERVER_ENV:
            # 服务器环境 - 使用更稳定的进程管理
            logger.info("在服务器环境中启动服务器进程")
            process = subprocess.Popen(
                [sys.executable, 'server.py'],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                # 在服务器环境中添加以下参数以提高稳定性
                preexec_fn=os.setsid if platform.system() != 'Windows' else None
            )
        else:
            # 本地环境
            logger.info("在本地环境中启动服务器进程")
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
        
        logger.info(f"服务器进程已启动，PID: {process.pid}")
        return process
    except Exception as e:
        print(f"[❌] 启动服务器失败: {e}")
        logger.error(f"启动服务器失败: {e}")
        return None

def read_server_output(process):
    """读取并显示服务器输出"""
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"[服务器] {output.strip()}")
            logger.info(f"[服务器] {output.strip()}")

def open_browser(url="http://localhost:8000"):
    """打开浏览器"""
    # 在服务器环境中不打开浏览器
    if IS_SERVER_ENV:
        logger.info("服务器环境中不自动打开浏览器")
        print("[🌐] 服务器环境中不自动打开浏览器")
        return True
    
    print("[🌐] 正在打开浏览器...")
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"[❌] 打开浏览器失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始启动 FinGenius 系统")
    print_banner()
    
    # 记录环境信息
    logger.info(f"运行环境: {'服务器环境' if IS_SERVER_ENV else '本地环境'}")
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"Python版本: {sys.version}")
    
    # 检查Python环境
    logger.info("检查Python环境...")
    if not check_python_environment():
        logger.error("Python环境检查失败")
        return 1
    
    # 检查项目文件
    logger.info("检查项目文件...")
    if not check_project_files():
        logger.error("项目文件检查失败")
        return 1
    
    # 检查端口
    logger.info("检查端口状态...")
    if not check_port_available(8000):
        logger.warning("端口8000被占用，尝试终止占用进程...")
        if not kill_process_on_port(8000):
            logger.error("无法释放端口8000")
            print("[❌] 无法释放端口8000，请手动处理")
            return 1
        time.sleep(2)  # 等待端口释放
    
    # 启动服务器
    logger.info("启动Web服务器...")
    server_process = start_server()
    if not server_process:
        logger.error("服务器启动失败")
        return 1
    
    # 启动线程读取服务器输出
    output_thread = threading.Thread(target=read_server_output, args=(server_process,))
    output_thread.daemon = True
    output_thread.start()
    
    # 在服务器环境中启动进程管理
    if IS_SERVER_ENV:
        manage_server_process(server_process)
    
    # 等待服务器启动
    logger.info("等待服务器启动完成...")
    if not wait_for_server():
        logger.error("服务器启动超时")
        server_process.terminate()
        return 1
    
    # 在非服务器环境中打开浏览器
    if not IS_SERVER_ENV:
        logger.info("尝试打开浏览器...")
        open_browser()
    
    print()
    print("=" * 80)
    print("[✅] FinGenius 股票分析系统已成功启动！")
    
    # 根据环境显示不同的访问地址
    if IS_SERVER_ENV:
        # 在服务器环境中，显示外网访问地址
        print("[🌐] 服务器地址: http://0.0.0.0:8000")
        print("[🌐] 外网访问地址: 请使用服务器的公网IP访问")
        logger.info("服务器启动成功，监听在 0.0.0.0:8000")
    else:
        print("[🌐] 本地访问地址: http://localhost:8000")
        logger.info("服务器启动成功，监听在 localhost:8000")
    
    print("[📊] 请在浏览器中访问上述地址开始股票分析")
    print("[❌] 关闭此窗口不会影响服务器运行")
    print("=" * 80)
    
    try:
        input("按回车键关闭此窗口...")
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
        pass
    
    logger.info("FinGenius 系统启动完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
