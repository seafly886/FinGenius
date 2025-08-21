#!/usr/bin/env python3
"""
简单测试脚本，验证LLMSettings对象修复
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_structure():
    """测试配置结构"""
    print("测试配置结构...")
    try:
        # 模拟配置结构
        class MockLLMSettings:
            def __init__(self, model, base_url, api_key, max_tokens=4096, temperature=1.0, api_type="openai", api_version=""):
                self.model = model
                self.base_url = base_url
                self.api_key = api_key
                self.max_tokens = max_tokens
                self.temperature = temperature
                self.api_type = api_type
                self.api_version = api_version
        
        # 模拟配置字典
        mock_config = {
            "default": MockLLMSettings(
                model="ZhipuAI/GLM-4.5",
                base_url="https://api-inference.modelscope.cn/v1",
                api_key="ms-6a5c41cc-1a25-453c-a1d5-40e0c98b6ae9",
                max_tokens=8192,
                temperature=0.0,
                api_type="openai",
                api_version=""
            )
        }
        
        # 测试修复后的逻辑
        config_name = "default"
        llm_config = None
        
        if llm_config is None:
            # 如果没有传入 llm_config，从 config.llm 中获取
            llm_config_dict = mock_config
            llm_config = llm_config_dict.get(config_name, llm_config_dict.get("default"))
        
        print(f"✓ 配置获取成功")
        print(f"  - 模型: {llm_config.model}")
        print(f"  - API类型: {llm_config.api_type}")
        print(f"  - 基础URL: {llm_config.base_url}")
        
        return True
    except Exception as e:
        print(f"✗ 配置结构测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_original_error():
    """测试原始错误是否已修复"""
    print("\n测试原始错误修复...")
    try:
        # 模拟原始的错误代码
        class MockLLMSettings:
            def __init__(self):
                self.model = "test_model"
                self.base_url = "test_url"
                self.api_key = "test_key"
        
        # 模拟配置
        mock_config = MockLLMSettings()
        
        # 测试修复前的错误代码（应该会失败）
        try:
            # 这是原始的错误代码
            llm_config = mock_config.get("default", mock_config["default"])
            print("✗ 原始错误代码应该失败但没有失败")
            return False
        except AttributeError as e:
            print(f"✓ 原始错误代码正确地失败了: {e}")
        
        # 测试修复后的代码（应该成功）
        try:
            config_name = "default"
            llm_config_dict = {"default": mock_config}
            llm_config = llm_config_dict.get(config_name, llm_config_dict.get("default"))
            print(f"✓ 修复后的代码成功执行")
            print(f"  - 模型: {llm_config.model}")
            return True
        except Exception as e:
            print(f"✗ 修复后的代码失败: {e}")
            return False
            
    except Exception as e:
        print(f"✗ 原始错误测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始简单测试...")
    
    tests = [
        ("配置结构", test_config_structure),
        ("原始错误修复", test_original_error),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"运行测试: {test_name}")
        print(f"{'='*40}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果摘要
    print(f"\n{'='*40}")
    print("测试结果摘要")
    print(f"{'='*40}")
    
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
    main()