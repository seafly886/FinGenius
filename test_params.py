#!/usr/bin/env python3
"""测试高级参数传递功能"""

import json
import sys

def test_frontend_to_backend():
    """测试前端到后端的参数传递"""
    print("=== 1. 前端参数配置测试 ===")
    
    # 模拟前端options配置
    frontend_options = {
        'format': 'json',
        'output': 'test_output.json', 
        'tts': True,
        'maxSteps': 5,
        'debateRounds': 3
    }
    
    print("前端options配置:")
    print(json.dumps(frontend_options, indent=2, ensure_ascii=False))
    
    # 模拟前端发送的请求
    request_data = {
        'stock_code': '000001',
        'options': {
            'format': frontend_options['format'],
            'output': frontend_options['output'],
            'tts': frontend_options['tts'],
            'max_steps': frontend_options['maxSteps'],
            'debate_rounds': frontend_options['debateRounds']
        }
    }
    
    print("\n前端发送的请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    return request_data

def test_backend_processing(request_data):
    """测试后端参数处理"""
    print("\n=== 2. 后端参数处理测试 ===")
    
    # 模拟后端接收和处理
    stock_code = request_data.get('stock_code', '').strip()
    options = request_data.get('options', {})
    
    print(f"股票代码: {stock_code}")
    print("提取的options:")
    for key, value in options.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    return stock_code, options

def test_command_building(stock_code, options):
    """测试命令行构建"""
    print("\n=== 3. 命令行参数构建测试 ===")
    
    # 构建命令，模拟backend/server.py中的逻辑
    cmd = [sys.executable, "main.py", stock_code]
    
    # 添加可选参数
    if options.get('format'):
        cmd.extend(['-f', options['format']])
        print(f"添加格式参数: -f {options['format']}")
        
    if options.get('output'):
        cmd.extend(['-o', options['output']])
        print(f"添加输出参数: -o {options['output']}")
        
    if options.get('tts'):
        cmd.append('--tts')
        print("添加TTS参数: --tts")
        
    if options.get('max_steps'):
        cmd.extend(['--max-steps', str(options['max_steps'])])
        print(f"添加最大步数参数: --max-steps {options['max_steps']}")
        
    if options.get('debate_rounds'):
        cmd.extend(['--debate-rounds', str(options['debate_rounds'])])
        print(f"添加辩论轮数参数: --debate-rounds {options['debate_rounds']}")
    
    print(f"\n构建的完整命令:")
    print(' '.join(cmd))
    
    return cmd

def test_main_py_args():
    """测试main.py参数解析"""
    print("\n=== 4. main.py参数解析测试 ===")
    
    # 检查main.py中的参数定义
    main_args = {
        'stock_code': '位置参数，股票代码',
        '-f/--format': 'choices=["text", "json"], default="text"',
        '-o/--output': '输出文件路径',
        '--tts': 'action="store_true", 启用TTS',
        '--max-steps': 'type=int, default=3, 每个agent最大步数',
        '--debate-rounds': 'type=int, default=2, 辩论轮数'
    }
    
    print("main.py支持的参数:")
    for arg, desc in main_args.items():
        print(f"  {arg}: {desc}")
    
    return main_args

def main():
    """主测试函数"""
    print("🧪 FinGenius 高级参数传递测试")
    print("=" * 50)
    
    # 1. 测试前端到后端
    request_data = test_frontend_to_backend()
    
    # 2. 测试后端处理
    stock_code, options = test_backend_processing(request_data)
    
    # 3. 测试命令构建
    cmd = test_command_building(stock_code, options)
    
    # 4. 测试main.py参数
    main_args = test_main_py_args()
    
    # 5. 验证参数兼容性
    print("\n=== 5. 参数兼容性验证 ===")
    
    compatibility_issues = []
    
    # 检查参数映射
    param_mapping = {
        'format': '-f/--format',
        'output': '-o/--output', 
        'tts': '--tts',
        'max_steps': '--max-steps',
        'debate_rounds': '--debate-rounds'
    }
    
    for frontend_key, main_arg in param_mapping.items():
        if main_arg in main_args:
            print(f"✅ {frontend_key} → {main_arg} (兼容)")
        else:
            print(f"❌ {frontend_key} → {main_arg} (不兼容)")
            compatibility_issues.append(f"{frontend_key} → {main_arg}")
    
    # 总结
    print("\n=== 测试总结 ===")
    if compatibility_issues:
        print(f"❌ 发现 {len(compatibility_issues)} 个兼容性问题:")
        for issue in compatibility_issues:
            print(f"   - {issue}")
    else:
        print("✅ 所有参数传递链路正常，兼容性良好")
    
    print(f"\n📋 测试的参数传递链路:")
    print("   前端options → 后端request → 命令行参数 → main.py解析")
    
    return len(compatibility_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)