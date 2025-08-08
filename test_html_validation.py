#!/usr/bin/env python3
"""
测试HTML完整性验证功能
"""
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.tool.create_html import CreateHtmlTool

def test_html_validation():
    """测试HTML完整性验证"""
    tool = CreateHtmlTool()
    
    # 读取最新的HTML文件
    html_file = "report/html/html_603887_20250807_234915.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        print(f"文件大小: {len(html_content)} 字符")
        print(f"文件大小: {len(html_content.encode('utf-8'))} 字节")
        
        # 测试完整性验证
        is_complete = tool._validate_html_completeness(html_content)
        print(f"HTML完整性验证结果: {is_complete}")
        
        # 检查基本结构
        has_doctype = "<!doctype" in html_content.lower() or "<!DOCTYPE" in html_content
        has_html_start = "<html" in html_content.lower()
        has_html_end = "</html>" in html_content.lower()
        has_head = "<head" in html_content.lower() and "</head>" in html_content.lower()
        has_body = "<body" in html_content.lower() and "</body>" in html_content.lower()
        
        print(f"DOCTYPE: {has_doctype}")
        print(f"HTML开始标签: {has_html_start}")
        print(f"HTML结束标签: {has_html_end}")
        print(f"HEAD标签: {has_head}")
        print(f"BODY标签: {has_body}")
        
        # 检查文件结尾
        content_end = html_content.strip()[-100:]
        print(f"文件结尾内容: {repr(content_end)}")
        
        return is_complete
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    test_html_validation()