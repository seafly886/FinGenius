"""
HTML报告完整性验证工具
确保生成的HTML报告完整且包含必要数据
"""

import os
import re
import json
from typing import Dict, Any, Tuple
from pathlib import Path
from src.logger import logger


class HTMLValidator:
    """HTML报告验证器"""
    
    def __init__(self):
        self.min_file_size = 15000  # 最小文件大小（字节）
        self.required_sections = [
            'overview', 'analysis', 'debate', 'disclaimer'
        ]
        self.required_scripts = [
            'bootstrap', 'reportData', 'renderPage'
        ]
    
    async def validate_html_completion(self, html_path: str, expected_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证HTML文件是否完整生成并包含必要数据
        
        Returns:
            Tuple[bool, str]: (是否验证通过, 验证消息)
        """
        try:
            # 1. 检查文件是否存在
            if not os.path.exists(html_path):
                return False, f"HTML文件不存在: {html_path}"
            
            # 2. 检查文件大小
            file_size = os.path.getsize(html_path)
            if file_size < self.min_file_size:
                return False, f"HTML文件过小: {file_size} bytes，可能不完整（期望至少{self.min_file_size}字节）"
            
            # 3. 读取HTML内容
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            except Exception as e:
                return False, f"无法读取HTML文件: {str(e)}"
            
            # 4. 验证HTML基本结构
            structure_valid, structure_msg = self._validate_html_structure(html_content)
            if not structure_valid:
                return False, f"HTML结构验证失败: {structure_msg}"
            
            # 5. 验证必需的页面部分
            sections_valid, sections_msg = self._validate_required_sections(html_content)
            if not sections_valid:
                return False, f"页面部分验证失败: {sections_msg}"
            
            # 6. 验证数据注入
            data_valid, data_msg = self._validate_data_injection(html_content, expected_data)
            if not data_valid:
                return False, f"数据注入验证失败: {data_msg}"
            
            # 7. 验证JavaScript功能
            js_valid, js_msg = self._validate_javascript_functions(html_content)
            if not js_valid:
                return False, f"JavaScript功能验证失败: {js_msg}"
            
            # 8. 验证辩论历史完整性
            debate_valid, debate_msg = self._validate_debate_history(html_content, expected_data)
            if not debate_valid:
                return False, f"辩论历史验证失败: {debate_msg}"
            
            success_msg = f"HTML验证通过 - 文件大小: {file_size} bytes, 包含完整数据和功能"
            logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"HTML验证过程异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _validate_html_structure(self, html_content: str) -> Tuple[bool, str]:
        """验证HTML基本结构"""
        required_tags = [
            (r'<!DOCTYPE\s+html', "DOCTYPE声明"),
            (r'<html[^>]*lang="zh-CN"', "HTML标签和语言设置"),
            (r'<head[^>]*>', "HEAD标签"),
            (r'<meta[^>]*charset[^>]*utf-8', "UTF-8编码声明"),
            (r'<title[^>]*>', "标题标签"),
            (r'<body[^>]*>', "BODY标签"),
            (r'</html>', "HTML结束标签")
        ]
        
        for pattern, description in required_tags:
            if not re.search(pattern, html_content, re.IGNORECASE):
                return False, f"缺少{description}"
        
        return True, "HTML基本结构完整"
    
    def _validate_required_sections(self, html_content: str) -> Tuple[bool, str]:
        """验证必需的页面部分"""
        missing_sections = []
        
        for section in self.required_sections:
            pattern = f'id="{section}"'
            if pattern not in html_content:
                missing_sections.append(section)
        
        if missing_sections:
            return False, f"缺少页面部分: {', '.join(missing_sections)}"
        
        return True, "所有必需页面部分存在"
    
    def _validate_data_injection(self, html_content: str, expected_data: Dict[str, Any]) -> Tuple[bool, str]:
        """验证数据注入"""
        # 检查是否包含数据注入点或实际数据
        data_patterns = [
            r'reportData\s*=\s*{',
            r'const\s+reportData',
            r'let\s+reportData',
            r'var\s+reportData',
            r'页面数据注入点'
        ]
        
        has_data_injection = any(
            re.search(pattern, html_content, re.IGNORECASE) 
            for pattern in data_patterns
        )
        
        if not has_data_injection:
            return False, "未找到数据注入点或数据声明"
        
        # 如果有期望的数据，检查关键字段是否存在
        if expected_data:
            stock_code = expected_data.get('stock_code', '')
            if stock_code and stock_code not in html_content:
                return False, f"HTML中未找到股票代码: {stock_code}"
        
        return True, "数据注入验证通过"
    
    def _validate_javascript_functions(self, html_content: str) -> Tuple[bool, str]:
        """验证JavaScript功能"""
        required_functions = [
            'renderPage',
            'renderOverview', 
            'renderAnalysis',
            'renderDebate',
            'initializeInteractions'
        ]
        
        missing_functions = []
        for func in required_functions:
            pattern = f'function\\s+{func}\\s*\\('
            if not re.search(pattern, html_content):
                missing_functions.append(func)
        
        if missing_functions:
            return False, f"缺少JavaScript函数: {', '.join(missing_functions)}"
        
        # 检查Bootstrap和其他必需脚本
        required_scripts = [
            'bootstrap',
            'DOMContentLoaded'
        ]
        
        missing_scripts = []
        for script in required_scripts:
            if script.lower() not in html_content.lower():
                missing_scripts.append(script)
        
        if missing_scripts:
            return False, f"缺少必需脚本: {', '.join(missing_scripts)}"
        
        return True, "JavaScript功能验证通过"
    
    def _validate_debate_history(self, html_content: str, expected_data: Dict[str, Any]) -> Tuple[bool, str]:
        """验证辩论历史完整性"""
        if not expected_data:
            return True, "无期望数据，跳过辩论历史验证"
        
        debate_history = expected_data.get('debate_history', [])
        if not debate_history:
            return True, "无辩论历史数据，验证通过"
        
        # 检查是否包含辩论时间线相关代码
        timeline_patterns = [
            r'debateTimeline',
            r'timeline-item',
            r'renderDebate',
            r'debate_history'
        ]
        
        missing_timeline_features = []
        for pattern in timeline_patterns:
            if not re.search(pattern, html_content, re.IGNORECASE):
                missing_timeline_features.append(pattern)
        
        if missing_timeline_features:
            return False, f"缺少辩论时间线功能: {', '.join(missing_timeline_features)}"
        
        return True, f"辩论历史验证通过，包含{len(debate_history)}条记录的处理逻辑"
    
    def get_html_summary(self, html_path: str) -> Dict[str, Any]:
        """获取HTML文件摘要信息"""
        try:
            if not os.path.exists(html_path):
                return {"error": "文件不存在"}
            
            file_size = os.path.getsize(html_path)
            
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计各种元素
            summary = {
                "file_size": file_size,
                "content_length": len(content),
                "has_doctype": bool(re.search(r'<!DOCTYPE', content, re.IGNORECASE)),
                "has_bootstrap": "bootstrap" in content.lower(),
                "has_fontawesome": "fontawesome" in content.lower() or "fa-" in content,
                "sections_count": len(re.findall(r'<section[^>]*>', content, re.IGNORECASE)),
                "script_tags_count": len(re.findall(r'<script[^>]*>', content, re.IGNORECASE)),
                "has_data_injection": bool(re.search(r'reportData\s*=', content)),
                "has_timeline": "timeline" in content.lower(),
                "modification_time": os.path.getmtime(html_path)
            }
            
            return summary
            
        except Exception as e:
            return {"error": str(e)}


# 全局验证器实例
html_validator = HTMLValidator()