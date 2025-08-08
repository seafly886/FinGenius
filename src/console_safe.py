import json
import sys
import os
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.rule import Rule
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.markdown import Markdown
import time

# 创建Windows安全的控制台
def create_safe_console():
    """创建Windows安全的控制台，避免编码问题"""
    if sys.platform == "win32":
        # Windows系统使用安全模式
        return Console(
            force_terminal=True, 
            legacy_windows=True,
            width=120,
            no_color=False
        )
    else:
        return Console()

console = create_safe_console()

class FinGeniusVisualizer:
    """Enhanced visualizer for FinGenius analysis process - Windows Safe Version"""
    
    def __init__(self):
        self.progress_stats = {
            "tool_calls": 0,
            "llm_calls": 0,
            "agents_active": 0
        }
        
        # 使用纯文本标识符，避免emoji编码问题
        self.agent_name_mapping = {
            "sentiment_agent": "[情绪] 市场情绪分析师",
            "risk_control_agent": "[风控] 风险控制专家", 
            "hot_money_agent": "[游资] 游资分析师",
            "technical_analysis_agent": "[技术] 技术分析师",
            "chip_analysis_agent": "[筹码] 筹码分析师",
            "big_deal_analysis_agent": "[大单] 大单分析师",
            "report_agent": "[报告] 报告生成专家",
            "System": "[系统] 系统"
        }
    
    def _clean_text(self, text: str) -> str:
        """清理可能导致编码问题的字符"""
        if not isinstance(text, str):
            text = str(text)
        
        # 清理各种可能导致GBK编码问题的字符
        replacements = {
            '\xa0': ' ',      # non-breaking space
            '\u00a0': ' ',    # non-breaking space (alternative)
            '\u2022': '-',    # bullet point
            '\u2013': '-',    # en dash
            '\u2014': '-',    # em dash
            '\u201c': '"',    # left double quote
            '\u201d': '"',    # right double quote
            '\u2018': "'",    # left single quote
            '\u2019': "'",    # right single quote
            '\u2026': '...',  # ellipsis
        }
        
        for old_char, new_char in replacements.items():
            text = text.replace(old_char, new_char)
        
        return text
    
    def _get_friendly_agent_name(self, agent_name: str) -> str:
        """Get friendly display name for agent"""
        return self.agent_name_mapping.get(agent_name, f"[AI] {agent_name}")

    def show_logo(self):
        """Display the FinGenius ASCII logo - 纯ASCII版本"""
        logo = """
================================================================================
                                                                                
    ███████ ██ ███   ██  ██████  ███████ ███   ██ ██ ██   ██ ███████           
    ██      ██ ████  ██ ██       ██      ████  ██ ██ ██   ██ ██                
    █████   ██ ██ ██ ██ ██   ███ █████   ██ ██ ██ ██ ██   ██ ███████           
    ██      ██ ██  ████ ██    ██ ██      ██  ████ ██ ██   ██      ██           
    ██      ██ ██   ███  ██████  ███████ ██   ███ ██  █████  ███████           
                                                                                
                          [AI] FinGenius [CHART]                               
                   AI-Powered Financial Analysis System                        
                                                                                
================================================================================
        """
        try:
            console.print(logo, style="bold cyan")
            console.print()
        except Exception as e:
            # 如果Rich也失败，使用基本print
            print("=" * 80)
            print("                    FinGenius 股票分析系统")
            print("                AI-Powered Financial Analysis System")
            print("=" * 80)
            print()

    def show_tool_call(self, tool_name: str, parameters: Dict[str, Any], agent_name: str = "System"):
        """Display tool call - 安全版本"""
        friendly_name = self._get_friendly_agent_name(agent_name)
        
        param_text = ""
        if parameters:
            for key, value in parameters.items():
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                param_text += f"  * {key}: {value}\n"
        
        content = f"[AI] 专家: {friendly_name}\n[工具] 工具: {tool_name}"
        if param_text:
            content += f"\n[参数] 参数:\n{param_text.rstrip()}"
        
        try:
            panel = Panel(
                content,
                title="[工具调用] Tool Call",
                title_align="left",
                border_style="blue",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[工具调用] {friendly_name} -> {tool_name}")
            if param_text:
                print(f"参数: {param_text.strip()}")
        
        self.progress_stats["tool_calls"] += 1

    def show_tool_result(self, result: Any, success: bool = True):
        """Display tool result - 安全版本"""
        if success:
            title = "[成功] 工具结果"
            style = "green"
        else:
            title = "[错误] 工具错误"
            style = "red"
        
        if isinstance(result, dict):
            if len(str(result)) > 200:
                content = f"[数据] 接收到结果数据 (JSON格式)\n[大小] 大小: {len(str(result))} 字符"
            else:
                content = f"[数据] 结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
        elif isinstance(result, str):
            # 清理可能导致编码问题的字符
            clean_result = result.replace('\xa0', ' ').replace('\u00a0', ' ')
            if len(clean_result) > 200:
                content = f"[结果] {clean_result[:197]}..."
            else:
                content = f"[结果] {clean_result}"
        else:
            content = f"[结果] {str(result)}"
        
        try:
            panel = Panel(
                content,
                title=title,
                title_align="left",
                border_style=style,
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n{title}: {content}")

    def show_progress_update(self, stage: str, details: str = ""):
        """Show progress updates - 安全版本"""
        self.progress_stats["llm_calls"] += 1
        
        progress_text = f"[进度] {stage}"
        if details:
            progress_text += f"\n{details}"
        
        progress_text += f"\n[统计] 工具调用: {self.progress_stats['tool_calls']} | LLM调用: {self.progress_stats['llm_calls']}"
        
        try:
            panel = Panel(
                progress_text,
                title="[分析进度] Analysis Progress",
                title_align="left",
                border_style="blue",
                box=ROUNDED,
                padding=(0, 1)
            )
            console.print(panel)
        except Exception:
            print(f"\n[进度] {stage}")
            if details:
                print(f"详情: {details}")

    def show_section_header(self, title: str, emoji: str = "[SECTION]"):
        """Show section headers - 安全版本"""
        console.print()
        try:
            console.print(Rule(f"{emoji} {title}", style="bold blue"))
        except Exception:
            print(f"\n{'='*20} {title} {'='*20}")
        console.print()

    def show_error(self, error_msg: str, context: str = ""):
        """Display errors - 安全版本"""
        content = f"[错误] 错误: {error_msg}"
        if context:
            content += f"\n[上下文] 上下文: {context}"
        
        try:
            panel = Panel(
                content,
                title="[警告] 错误信息",
                title_align="left",
                border_style="red",
                box=HEAVY,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[错误] {error_msg}")
            if context:
                print(f"[上下文] {context}")

    def show_completion(self, total_time: float):
        """Show completion message - 安全版本"""
        content = f"[完成] 分析完成!\n[时间] 总用时: {total_time:.2f} 秒\n[统计] 工具调用: {self.progress_stats['tool_calls']}\n[统计] LLM调用: {self.progress_stats['llm_calls']}"
        
        try:
            panel = Panel(
                content,
                title="[任务完成] Task Complete",
                title_align="center",
                border_style="green",
                box=DOUBLE,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[完成] 分析完成!")
            print(f"[时间] 总用时: {total_time:.2f} 秒")
            print(f"[统计] 工具调用: {self.progress_stats['tool_calls']}, LLM调用: {self.progress_stats['llm_calls']}")

    # 添加其他必要的方法，都使用安全的文本输出
    def show_agent_starting(self, agent_name: str, current: int, total: int):
        """Display which agent is starting analysis"""
        friendly_name = self._get_friendly_agent_name(agent_name)
        content = f"[启动] 正在启动专家分析\n\n专家: {friendly_name}\n进度: {current}/{total}"
        
        try:
            panel = Panel(
                content,
                title=f"[专家分析] Expert Analysis ({current}/{total})",
                title_align="left",
                border_style="green",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[启动] {friendly_name} ({current}/{total})")
        
    def show_agent_completed(self, agent_name: str, current: int, total: int):
        """Display when agent completes analysis"""
        friendly_name = self._get_friendly_agent_name(agent_name)
        content = f"[完成] 专家分析完成\n\n专家: {friendly_name}\n进度: {current}/{total}"
        
        try:
            panel = Panel(
                content,
                title=f"[分析完成] Analysis Complete ({current}/{total})",
                title_align="left",
                border_style="green",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[完成] {friendly_name} ({current}/{total})")

    def show_waiting_next_agent(self, seconds: int = 3):
        """Display waiting message between agents"""
        content = f"[等待] 等待下一个专家\n\n等待时间: {seconds} 秒\n目的: 降低资源消耗"
        
        try:
            panel = Panel(
                content,
                title="[间隔等待] Interval Wait",
                title_align="left",
                border_style="yellow",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[等待] 等待 {seconds} 秒...")
        console.print()

    def show_research_summary(self, research_results: Dict[str, Any]):
        """Display research summary - 安全版本"""
        if not research_results:
            return
            
        console.print()
        try:
            console.print(Rule("[研究结果] 研究阶段完整分析结果", style="bold green"))
        except Exception:
            print("\n" + "="*50)
            print("研究阶段完整分析结果")
            print("="*50)
        console.print()
        
        # Show each agent's analysis
        agent_results = {
            "sentiment": ("[情绪] 市场情绪分析师", research_results.get("sentiment", "")),
            "risk": ("[风控] 风险控制专家", research_results.get("risk", "")),
            "hot_money": ("[游资] 游资分析师", research_results.get("hot_money", "")),
            "technical": ("[技术] 技术分析师", research_results.get("technical", "")),
            "chip_analysis": ("[筹码] 筹码分析师", research_results.get("chip_analysis", "")),
            "big_deal": ("[大单] 大单分析师", research_results.get("big_deal", ""))
        }
        
        for analysis_key, (agent_name, analysis_content) in agent_results.items():
            if analysis_content and analysis_content.strip():
                self.show_agent_analysis_result(
                    analysis_key + "_agent", 
                    analysis_content, 
                    analysis_key.replace("_", " ").title()
                )
                console.print()

    def show_agent_thought(self, agent_name: str, thought: str, thought_type: str = "analysis"):
        """Display agent's thinking process"""
        friendly_name = self._get_friendly_agent_name(agent_name)
        
        clean_thought = self._clean_text(thought)
        
        if len(clean_thought) > 500:
            display_thought = clean_thought[:497] + "..."
        else:
            display_thought = clean_thought
        
        content = f"[思考类型] 类型: {thought_type}\n\n[思考内容] {display_thought}"
        
        try:
            panel = Panel(
                content,
                title=f"[思考过程] {friendly_name} 思考过程",
                title_align="left",
                border_style="cyan",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[思考过程] {friendly_name}:")
            print(f"{display_thought}")

    def show_agent_analysis_result(self, agent_name: str, analysis_content: str, analysis_type: str = "综合分析"):
        """Display individual agent analysis results"""
        friendly_name = self._get_friendly_agent_name(agent_name)
        
        clean_content = self._clean_text(analysis_content)
        
        if len(clean_content) > 1000:
            display_content = clean_content[:997] + "..."
            full_content_note = f"\n\n[注意] 完整分析内容共 {len(clean_content)} 字符"
        else:
            display_content = clean_content
            full_content_note = ""
        
        content = f"[分析类型] 分析类型: {analysis_type}\n\n{display_content}{full_content_note}"
        
        try:
            panel = Panel(
                content,
                title=f"[分析结果] {friendly_name} 分析结果",
                title_align="left",
                border_style="green",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[分析结果] {friendly_name}:")
            print(f"{display_content}")

    def show_debate_summary(self, debate_results: Dict[str, Any]):
        """Display debate summary - 安全版本"""
        content_parts = []
        
        if "vote_results" in debate_results:
            votes = debate_results["vote_results"]
            total_votes = sum(votes.values())
            
            content_parts.append("[投票] 投票结果:")
            for option, count in votes.items():
                percentage = (count / total_votes * 100) if total_votes > 0 else 0
                emoji = "[上涨]" if option == "bullish" else "[下跌]"
                content_parts.append(f"  {emoji} {option.title()}: {count} 票 ({percentage:.1f}%)")
            content_parts.append("")
        
        if "battle_highlights" in debate_results and debate_results["battle_highlights"]:
            content_parts.append("[观点] 关键观点:")
            for highlight in debate_results["battle_highlights"][:3]:
                content_parts.append(f"  * {highlight.get('agent', 'Agent')}: {highlight.get('point', '')[:100]}...")
            content_parts.append("")
        
        if "tool_calls" in debate_results and "llm_calls" in debate_results:
            content_parts.append(f"[统计] 统计信息: {debate_results['tool_calls']} 工具调用, {debate_results['llm_calls']} LLM调用")
        
        content = "\n".join(content_parts)
        
        try:
            panel = Panel(
                content,
                title="[辩论总结] Debate Summary",
                title_align="center",
                border_style="magenta",
                box=DOUBLE,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[辩论总结]")
            print(content)

# Global visualizer instance
visualizer = FinGeniusVisualizer()

# Export functions for backward compatibility
def show_logo():
    visualizer.show_logo()

def show_header(stock_code: str):
    header = f"[分析] {stock_code} (获取中...) 投资分析与交易建议"
    try:
        panel = Panel(
            "",
            title=header,
            title_align="center",
            border_style="yellow",
            box=DOUBLE,
            height=3
        )
        console.print(panel)
    except Exception:
        print(f"\n{header}")

def show_analysis_results(results: Dict[str, Any]):
    """Display final analysis results"""
    if not results:
        return
    
    stock_code = results.get('stock_code', 'Unknown')
    
    if 'recommendation' in results:
        recommendation = results['recommendation']
        rec_emoji = "[上涨]" if any(word in recommendation.lower() for word in ['买入', '看涨', 'buy']) else "[下跌]"
        
        content = f"{rec_emoji} 投资建议: {recommendation}\n"
        
        if 'target_price_range' in results:
            content += f"[目标] 目标价格区间: {results['target_price_range']}\n"
        
        if 'risk_score' in results and 'value_score' in results:
            risk_emoji = "[低风险]" if results['risk_score'] <= 3 else "[中风险]" if results['risk_score'] <= 6 else "[高风险]"
            value_stars = "[价值]" * min(int(results.get('value_score', 0)), 5)
            content += f"{risk_emoji} 风险评分: {results['risk_score']}/10  {value_stars} 价值评分: {results['value_score']}/10"
        
        try:
            panel = Panel(
                content,
                title=f"[最终结果] {stock_code} 最终分析结果",
                title_align="center",
                border_style="cyan",
                box=DOUBLE,
                padding=(1, 2)
            )
            console.print(panel)
        except Exception:
            print(f"\n[最终结果] {stock_code}")
            print(content)

def show_debate_results(results: Dict[str, Any]):
    """Display debate results"""
    visualizer.show_debate_summary(results)

def show_progress_stats(tool_calls: int, llm_calls: int):
    """Show progress statistics"""
    visualizer.progress_stats["tool_calls"] = tool_calls
    visualizer.progress_stats["llm_calls"] = llm_calls
    
    stats_text = f"[统计] 统计信息: {tool_calls} 工具调用 | {llm_calls} LLM调用"
    try:
        console.print(stats_text, style="dim")
    except Exception:
        print(stats_text)
    console.print()

def clear_screen():
    """Clear the screen"""
    try:
        console.clear()
    except Exception:
        os.system('cls' if os.name == 'nt' else 'clear')

def print_separator():
    """Print a separator line"""
    try:
        console.print(Rule(style="dim"))
    except Exception:
        print("-" * 80)