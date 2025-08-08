#!/usr/bin/env python3
"""
测试修复后的HTML生成功能
"""
import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.tool.create_html import CreateHtmlTool

async def test_html_generation():
    """测试HTML生成功能"""
    tool = CreateHtmlTool()
    
    # 测试数据
    test_data = {
        "stock_code": "603887",
        "research_results": {
            "sentiment": "市场情绪积极",
            "risk": "风险可控",
            "technical": "技术面良好"
        },
        "battle_results": {
            "final_decision": "bullish",
            "vote_count": {"bullish": 4, "bearish": 2},
            "debate_history": [
                {"agent": "sentiment_agent", "content": "市场情绪积极", "timestamp": "2025-01-07 23:50:00"},
                {"agent": "risk_agent", "content": "风险可控", "timestamp": "2025-01-07 23:51:00"}
            ]
        }
    }
    
    # 生成HTML报告
    request = """
    生成一份简洁的股票分析报告，包含：
    1. 股票基本信息
    2. 分析结果摘要
    3. 专家辩论记录
    4. 投票结果
    """
    
    try:
        result = await tool.execute(
            request=request,
            data=test_data,
            output_path="report/html/test_report.html"
        )
        
        print(f"HTML生成结果: {result.output.get('message', 'Unknown')}")
        print(f"内容长度: {result.output.get('content_length', 0)} 字符")
        print(f"验证通过: {result.output.get('validation_passed', False)}")
        
        # 验证生成的HTML
        if os.path.exists("report/html/test_report.html"):
            with open("report/html/test_report.html", 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"生成的HTML文件大小: {len(html_content)} 字符")
            
            # 检查HTML完整性
            is_complete = tool._validate_html_completeness(html_content)
            print(f"HTML完整性验证: {is_complete}")
            
            # 检查是否干净（无JSON污染）
            is_clean = tool._is_clean_html(html_content)
            print(f"HTML内容干净: {is_clean}")
            
            # 显示文件开头和结尾
            print(f"文件开头: {html_content[:200]}...")
            print(f"文件结尾: ...{html_content[-200:]}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_html_generation())