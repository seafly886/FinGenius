"""
修复当前HTML报告的脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.utils.html_fixer import HtmlFixer

def main():
    """修复当前的HTML报告"""
    # 目标文件
    html_file = "report/html/html_603887_20250808_145115.html"
    debate_file = "report/debate/debate_603887_20250808_145115.json"
"""
修复当前HTML报告的脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.utils.html_fixer import HtmlFixer

def main():
    """修复当前的HTML报告"""
"""
修复当前HTML报告的脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.utils.html_fixer import HtmlFixer

def main():
    """修复当前的HTML报告"""
    # 目标文件
    html_file = "report/html/html_603887_20250808_145115.html"
    debate_file = "report/debate/debate_603887_20250808_145115.json"
    
    print(f"开始修复HTML文件: {html_file}")
    
    # 检查文件是否存在
    if not os.path.exists(html_file):
        print(f"错误: HTML文件不存在: {html_file}")
        return
    
    if not os.path.exists(debate_file):
        print(f"警告: 辩论数据文件不存在: {debate_file}")
        debate_file = None
    
    # 修复HTML文件
    success, message = HtmlFixer.fix_truncated_html(html_file, debate_file)
    
    if success:
        print(f"✅ 修复成功: {message}")
        
        # 验证修复结果
        fixed_file = html_file.replace('.html', '_fixed.html')
        if os.path.exists(fixed_file):
            with open(fixed_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"修复后文件大小: {len(content)} 字符")
            print(f"包含完整HTML结构: {'✅' if '</html>' in content else '❌'}")
            print(f"包含数据注入: {'✅' if 'reportData' in content else '❌'}")
            print(f"修复后文件路径: {fixed_file}")
        
    else:
        print(f"❌ 修复失败: {message}")

if __name__ == "__main__":
    main()