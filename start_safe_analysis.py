#!/usr/bin/env python3
"""
安全启动脚本 - 解决Windows GBK编码问题
"""

import os
import sys
import subprocess
import locale

def setup_encoding():
    """设置安全的编码环境"""
    if sys.platform == "win32":
        try:
            # 设置环境变量强制使用UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['PYTHONUTF8'] = '1'
            
            # 尝试设置控制台代码页为UTF-8
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
            
            print("✅ 编码环境设置完成")
            return True
        except Exception as e:
            print(f"⚠️ 编码设置警告: {e}")
            return False
    return True

def run_analysis(stock_code, **options):
    """运行股票分析"""
    # 设置编码
    setup_encoding()
    
    # 构建命令
    cmd = [sys.executable, 'main.py', stock_code]
    
    # 添加选项参数
    if options.get('format'):
        cmd.extend(['-f', options['format']])
    if options.get('output'):
        cmd.extend(['-o', options['output']])
    if options.get('tts'):
        cmd.append('--tts')
    if options.get('max_steps'):
        cmd.extend(['--max-steps', str(options['max_steps'])])
    if options.get('debate_rounds'):
        cmd.extend(['--debate-rounds', str(options['debate_rounds'])])
    
    print(f"🚀 启动分析命令: {' '.join(cmd)}")
    
    try:
        # 使用安全的编码环境运行
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        result = subprocess.run(
            cmd,
            env=env,
            text=True,
            encoding='utf-8',
            errors='replace'  # 替换无法编码的字符
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 分析执行失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python start_safe_analysis.py <股票代码> [选项]")
        print("示例: python start_safe_analysis.py 000001 --max-steps 2")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    
    # 解析其他参数
    options = {}
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-f' and i + 1 < len(sys.argv):
            options['format'] = sys.argv[i + 1]
            i += 2
        elif arg == '-o' and i + 1 < len(sys.argv):
            options['output'] = sys.argv[i + 1]
            i += 2
        elif arg == '--tts':
            options['tts'] = True
            i += 1
        elif arg == '--max-steps' and i + 1 < len(sys.argv):
            options['max_steps'] = int(sys.argv[i + 1])
            i += 2
        elif arg == '--debate-rounds' and i + 1 < len(sys.argv):
            options['debate_rounds'] = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    success = run_analysis(stock_code, **options)
    sys.exit(0 if success else 1)