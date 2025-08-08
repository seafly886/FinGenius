"""
HTML文件修复工具
用于修复被截断的HTML文件
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

class HtmlFixer:
    """HTML文件修复工具"""
    
    @staticmethod
    def fix_truncated_html(html_path: str, debate_data_path: Optional[str] = None) -> Tuple[bool, str]:
        """修复被截断的HTML文件"""
        try:
            # 读取原始HTML文件
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件是否被截断
            is_truncated = HtmlFixer._is_html_truncated(content)
            
            if not is_truncated:
                return True, "HTML文件完整，无需修复"
            
            # 修复HTML结构
            fixed_content = HtmlFixer._repair_html_structure(content)
            
            # 注入数据
            if debate_data_path and os.path.exists(debate_data_path):
                fixed_content = HtmlFixer._inject_report_data(fixed_content, debate_data_path)
            
            # 保存修复后的文件
            fixed_path = html_path.replace('.html', '_fixed.html')
            HtmlFixer._write_html_safely(fixed_content, fixed_path)
            
            return True, f"HTML文件已修复: {fixed_path}"
            
        except Exception as e:
            return False, f"修复HTML文件时出错: {str(e)}"
    
    @staticmethod
    def _is_html_truncated(content: str) -> bool:
        """检查HTML文件是否被截断"""
        checks = [
            '</html>' not in content,  # 缺少HTML结束标签
            '</body>' not in content,  # 缺少body结束标签
            '</script>' not in content,  # 缺少script结束标签
            'function renderPage()' in content and '}' not in content[content.find('function renderPage()'):],  # 函数不完整
            content.strip().endswith('...'),  # 明显的截断标志
            content.strip().endswith('</'),  # 不完整的标签
        ]
        
        return any(checks)
    
    @staticmethod
    def _repair_html_structure(content: str) -> str:
        """修复HTML结构"""
        try:
            # 找到最后一个完整的标签位置
            last_complete_tag = HtmlFixer._find_last_complete_tag(content)
            
            if last_complete_tag:
                content = content[:last_complete_tag]
            
            # 补全缺失的结束标签
            if '</script>' not in content and '<script' in content:
                content += '\n    </script>'
            
            if '</body>' not in content and '<body' in content:
                content += '\n</body>'
            
            if '</html>' not in content and '<html' in content:
                content += '\n</html>'
            
            return content
            
        except Exception as e:
            print(f"修复HTML结构时出错: {e}")
            return content
    
    @staticmethod
    def _find_last_complete_tag(content: str) -> Optional[int]:
        """找到最后一个完整标签的位置"""
        # 查找常见的完整结束标签
        complete_tags = ['</div>', '</p>', '</span>', '</script>', '</style>']
        
        last_pos = -1
        for tag in complete_tags:
            pos = content.rfind(tag)
            if pos > last_pos:
                last_pos = pos + len(tag)
        
        return last_pos if last_pos > -1 else None
    
    @staticmethod
    def _inject_report_data(content: str, debate_data_path: str) -> str:
        """注入报告数据到HTML"""
        try:
            # 读取辩论数据
            with open(debate_data_path, 'r', encoding='utf-8') as f:
                debate_data = json.load(f)
            
            # 构建完整的reportData对象
            report_data = HtmlFixer._build_report_data(debate_data, debate_data_path)
            
            # 将数据转换为JSON字符串
            report_data_json = json.dumps(report_data, ensure_ascii=False, indent=2)
            
            # 查找数据注入点并替换
            content = HtmlFixer._replace_data_placeholder(content, report_data_json)
            
            return content
            
        except Exception as e:
            print(f"注入报告数据时出错: {e}")
            return content
    
    @staticmethod
    def _build_report_data(debate_data: Dict, file_path: str) -> Dict:
        """构建完整的报告数据对象"""
        # 从文件名提取股票代码和时间戳
        filename = os.path.basename(file_path)
        stock_code = "unknown"
        timestamp = ""
        
        if "_" in filename:
            parts = filename.split("_")
            for part in parts:
                if part.isdigit() and len(part) == 6:
                    stock_code = part
                elif len(part) >= 8 and part.replace('.json', '').isdigit():
                    timestamp = part.replace('.json', '')
        
        # 构建research_results（如果不存在，使用辩论亮点）
        research_results = debate_data.get("research_results", {})
        if not research_results and "battle_highlights" in debate_data:
            research_results = {}
            for highlight in debate_data["battle_highlights"]:
                agent = highlight.get("agent", "unknown")
                content = highlight.get("point", "")
                
                # 映射agent到research_results的key
                key_mapping = {
                    "sentiment_agent": "sentiment",
                    "risk_control_agent": "risk", 
                    "hot_money_agent": "hot_money",
                    "technical_analysis_agent": "technical",
                    "chip_analysis_agent": "chip_analysis",
                    "big_deal_analysis_agent": "big_deal"
                }
                
                key = key_mapping.get(agent, agent)
                if key not in research_results:
                    research_results[key] = content
        
        return {
            "stock_code": stock_code,
            "timestamp": timestamp,
            "research_results": research_results,
            "debate_history": debate_data.get("debate_history", []),
            "battle_results": {
                "final_decision": debate_data.get("final_decision", ""),
                "vote_count": debate_data.get("vote_count", {}),
                "debate_rounds": debate_data.get("debate_rounds", 1)
            }
        }
    
    @staticmethod
    def _replace_data_placeholder(content: str, data_json: str) -> str:
        """替换数据占位符"""
        # 查找并替换各种数据占位符模式
        patterns = [
            # 空对象占位符
            (r'let reportData = \{\};', f'let reportData = {data_json};'),
            (r'const reportData = \{\};', f'const reportData = {data_json};'),
            (r'var reportData = \{\};', f'var reportData = {data_json};'),
            
            # 注释占位符
            (r'// 这里将被实际数据替换\s*reportData = \{[^}]*\};', 
             f'// 实际数据已注入\n            reportData = {data_json};'),
            
            # injectData函数中的占位符
            (r'reportData = \{[^}]*stock_code: "603887"[^}]*\};', 
             f'reportData = {data_json};'),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                break
        
        return content
    
    @staticmethod
    def _write_html_safely(content: str, output_path: str) -> bool:
        """安全地写入HTML文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 分块写入大文件
            chunk_size = 8000
            with open(output_path, 'w', encoding='utf-8') as f:
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    f.write(chunk)
                    f.flush()
            
            return True
            
        except Exception as e:
            print(f"写入HTML文件时出错: {e}")
            return False

# 便捷函数
def fix_html_file(html_path: str, debate_data_path: Optional[str] = None) -> Tuple[bool, str]:
    """修复HTML文件的便捷函数"""
    return HtmlFixer.fix_truncated_html(html_path, debate_data_path)