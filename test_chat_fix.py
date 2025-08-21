#!/usr/bin/env python3
"""
测试聊天API修复
"""
import json
import requests
import time

def test_single_chat():
    """测试单个智能体聊天API"""
    url = "http://localhost:8000/api/chat/single"
    
    # 测试数据
    data = {
        "agent": "sentiment",
        "message": "测试消息"
    }
    
    try:
        print("测试单个智能体聊天API...")
        response = requests.post(url, json=data, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 单个智能体聊天API测试成功")
            return True
        else:
            print("❌ 单个智能体聊天API测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_group_chat():
    """测试群聊API"""
    url = "http://localhost:8000/api/chat/group"
    
    # 测试数据
    data = {
        "agents": ["sentiment", "risk_control"],
        "message": "测试群聊消息"
    }
    
    try:
        print("\n测试群聊API...")
        response = requests.post(url, json=data, timeout=60)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 群聊API测试成功")
            return True
        else:
            print("❌ 群聊API测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试聊天API修复...")
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    # 运行测试
    success_count = 0
    total_tests = 2
    
    if test_single_chat():
        success_count += 1
    
    if test_group_chat():
        success_count += 1
    
    print(f"\n📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！修复成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")