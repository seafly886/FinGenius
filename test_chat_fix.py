#!/usr/bin/env python3
"""
测试聊天接口修复的脚本
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.llm import LLM

async def test_llm_initialization():
    """测试LLM初始化是否正常"""
    print("测试LLM初始化...")
    try:
        # 测试默认配置
        llm = LLM(config_name="default")
        print(f"✓ LLM初始化成功")
        print(f"  - 模型: {llm.model}")
        print(f"  - API类型: {llm.api_type}")
        print(f"  - 基础URL: {llm.base_url}")
        return True
    except Exception as e:
        print(f"✗ LLM初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_chat_handler():
    """测试聊天处理器"""
    print("\n测试聊天处理器...")
    try:
        # 导入聊天处理器
        from backend.chat_handler import ModelConfigManager, ChatSession
        
        # 测试模型配置管理器
        model_manager = ModelConfigManager()
        available_models = model_manager.get_model_names()
        print(f"✓ 可用模型: {available_models}")
        
        # 测试聊天会话创建
        session_id = "test_session"
        message = "你好，这是一个测试消息"
        session = ChatSession(session_id, message, model_name="default")
        print(f"✓ 聊天会话创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 聊天处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_loading():
    """测试配置加载"""
    print("\n测试配置加载...")
    try:
        # 检查配置是否正确加载
        llm_configs = config.llm
        print(f"✓ LLM配置加载成功")
        print(f"  - 配置键: {list(llm_configs.keys())}")
        
        # 检查默认配置
        if "default" in llm_configs:
            default_config = llm_configs["default"]
            print(f"✓ 默认配置存在")
            print(f"  - 模型: {default_config.model}")
            print(f"  - API类型: {default_config.api_type}")
        else:
            print("✗ 默认配置不存在")
            return False
            
        return True
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("开始测试聊天接口修复...")
    
    tests = [
        ("配置加载", test_config_loading),
        ("LLM初始化", test_llm_initialization),
        ("聊天处理器", test_chat_handler),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"运行测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print("测试结果摘要")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！修复成功！")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    asyncio.run(main())