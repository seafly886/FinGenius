#!/usr/bin/env python3
"""
聊天处理器 - 处理与智能体的聊天交互
"""
import json
import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.llm import LLM
from src.logger import logger

# 智能体名称映射
AGENT_NAMES = {
    'big_deal_analysis': '大单异动分析智能体',
    'chip_analysis': '筹码分析智能体',
    'hot_money': '游资分析智能体',
    'risk_control': '风险控制智能体',
    'sentiment': '舆情分析智能体',
    'technical_analysis': '技术分析智能体'
}

# 智能体配置文件路径
AGENT_CONFIGS = {
    'big_deal_analysis': 'config/big_deal_analysis_agent.json',
    'chip_analysis': 'config/chip_analysis_agent.json',
    'hot_money': 'config/hot_money_agent.json',
    'risk_control': 'config/risk_control_agent.json',
    'sentiment': 'config/sentiment_agent.json',
    'technical_analysis': 'config/technical_analysis_agent.json'
}

async def load_agent_config(agent_name: str) -> Dict[str, Any]:
    """加载智能体配置"""
    config_path = AGENT_CONFIGS.get(agent_name)
    if not config_path or not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载智能体配置失败: {e}")
        return {}

async def chat_with_agent(agent_name: str, message: str) -> str:
    """与单个智能体聊天"""
    try:
        # 加载智能体配置
        config = await load_agent_config(agent_name)
        if not config:
            return f"无法加载智能体 {agent_name} 的配置"
        
        # 获取系统提示词
        system_prompt = config.get('system_prompt', '')
        if not system_prompt:
            return f"智能体 {agent_name} 没有配置系统提示词"
        
        # 创建LLM实例
        llm = LLM()
        
        # 构建聊天消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        # 调用LLM获取响应
        response = await llm.generate_response(messages)
        
        # 输出响应
        output_data = {
            "type": "agent_response",
            "agent": agent_name,
            "content": response
        }
        print(json.dumps(output_data, ensure_ascii=False))
        
        return response
        
    except Exception as e:
        logger.error(f"与智能体 {agent_name} 聊天失败: {e}")
        error_msg = f"聊天过程中发生错误: {str(e)}"
        
        # 输出错误信息
        error_data = {
            "type": "error",
            "message": error_msg
        }
        print(json.dumps(error_data, ensure_ascii=False))
        
        return error_msg

async def group_chat(agents: List[str], message: str) -> List[Dict[str, str]]:
    """群聊功能"""
    responses = []
    
    for agent_name in agents:
        try:
            # 与每个智能体聊天
            response = await chat_with_agent(agent_name, message)
            responses.append({
                "agent": agent_name,
                "response": response
            })
            
            # 添加小延迟避免过快请求
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"群聊中与智能体 {agent_name} 交互失败: {e}")
            responses.append({
                "agent": agent_name,
                "response": f"与智能体交互时发生错误: {str(e)}"
            })
    
    return responses

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(json.dumps({"type": "error", "message": "缺少输入文件参数"}))
        return 1
    
    input_file = sys.argv[1]
    
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        message = input_data.get('message', '')
        agent = input_data.get('agent')
        agents = input_data.get('agents', [])
        
        if not message:
            print(json.dumps({"type": "error", "message": "消息内容不能为空"}))
            return 1
        
        # 处理单个智能体聊天
        if agent:
            await chat_with_agent(agent, message)
        
        # 处理群聊
        elif agents:
            responses = await group_chat(agents, message)
            
            # 输出所有响应
            for resp in responses:
                output_data = {
                    "type": "agent_response",
                    "agent": resp["agent"],
                    "content": resp["response"]
                }
                print(json.dumps(output_data, ensure_ascii=False))
        
        else:
            print(json.dumps({"type": "error", "message": "请指定智能体或智能体列表"}))
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        print(json.dumps({"type": "error", "message": str(e)}))
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))