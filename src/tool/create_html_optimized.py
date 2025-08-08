"""
优化的HTML生成工具 - 解决文件截断问题
通过数据外部化和模板分离来避免文件过大
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.tool.base import BaseTool
from src.schema import ToolResult

class OptimizedHtmlTool(BaseTool):
    """优化的HTML生成工具"""
    
    def __init__(self):
        super().__init__()
        self.name = "optimized_html_generator"
        self.description = "生成优化的HTML报告，避免文件截断问题"
    
    async def _run(
        self,
        request: str,
        data: Dict[str, Any],
        output_path: str,
        reference: str = "",
        additional_requirements: str = ""
    ) -> ToolResult:
        """生成优化的HTML报告"""
        try:
            # 1. 生成数据文件
            data_file = self._create_data_file(data, output_path)
            
            # 2. 生成HTML模板
            html_content = self._create_html_template(data, data_file)
            
            # 3. 分块写入HTML文件
            success = self._write_html_safely(html_content, output_path)
            
            if success:
                return ToolResult(
                    success=True,
                    output=output_path,
                    message=f"HTML报告生成成功: {output_path}"
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    message="HTML文件写入失败"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                message=f"生成HTML报告时出错: {str(e)}"
            )
    
    def _create_data_file(self, data: Dict[str, Any], html_path: str) -> str:
        """创建外部数据文件"""
        # 生成数据文件路径
        html_file = Path(html_path)
        data_file = html_file.parent / f"{html_file.stem}_data.js"
        
        # 准备数据
        report_data = {
            "stock_code": data.get("stock_code", "unknown"),
            "timestamp": data.get("timestamp", ""),
            "research_results": self._compress_research_results(data.get("research_results", {})),
            "debate_history": data.get("debate_history", []),
            "battle_results": data.get("battle_results", {})
        }
        
        # 写入JavaScript数据文件
        js_content = f"window.reportData = {json.dumps(report_data, ensure_ascii=False, indent=2)};"
        
        with open(data_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        return str(data_file.name)
    
    def _compress_research_results(self, research_results: Dict[str, str]) -> Dict[str, str]:
        """压缩研究结果，避免过长"""
        compressed = {}
        for key, value in research_results.items():
            if len(value) > 1000:  # 如果内容过长，截取摘要
                lines = value.split('\n')
                summary_lines = []
                char_count = 0
                
                for line in lines:
                    if char_count + len(line) > 800:
                        break
                    summary_lines.append(line)
                    char_count += len(line)
                
                compressed[key] = '\n'.join(summary_lines) + '\n\n[内容已压缩，完整内容请查看原始数据文件]'
            else:
                compressed[key] = value
        
        return compressed
    
    def _create_html_template(self, data: Dict[str, Any], data_file: str) -> str:
        """创建HTML模板"""
        stock_code = data.get("stock_code", "unknown")
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinGenius 股票分析报告 - {stock_code}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <button class="theme-toggle" id="themeToggle">
        <i class="fas fa-moon"></i>
    </button>

    <button class="back-to-top" id="backToTop">
        <i class="fas fa-arrow-up"></i>
    </button>

    <div class="container">
        <!-- 页面概览 -->
        <div id="overview" class="section">
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-2">正在加载报告数据...</p>
            </div>
        </div>

        <!-- 专家分析结果 -->
        <div id="analysis" class="section">
            <!-- 分析内容将通过JavaScript动态生成 -->
        </div>

        <!-- 专家辩论时间线 -->
        <div class="section">
            <div class="text-center mb-4">
                <h2 class="section-title">
                    <i class="fas fa-comments me-2 text-primary"></i>专家辩论过程
                </h2>
                <p class="text-muted">各领域专家的深度讨论与观点交锋</p>
            </div>
            <div class="timeline" id="debateTimeline">
                <!-- 时间线内容将通过JavaScript动态生成 -->
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- 外部数据文件 -->
    <script src="{data_file}"></script>
    
    <!-- 页面逻辑 -->
    <script>
        {self._get_javascript_code()}
    </script>
</body>
</html>'''
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return '''
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --success-color: #27ae60;
            --danger-color: #e74c3c;
            --warning-color: #f39c12;
            --info-color: #17a2b8;
            --light-color: #ecf0f1;
            --dark-color: #2c3e50;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px 0;
        }

        .container {
            max-width: 1200px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            padding: 40px;
            margin: 0 auto;
            backdrop-filter: blur(10px);
        }

        .section {
            margin-bottom: 40px;
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            margin-bottom: 20px;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        }

        .badge-bullish {
            background: linear-gradient(135deg, var(--success-color), #2ecc71);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        .badge-bearish {
            background: linear-gradient(135deg, var(--danger-color), #c0392b);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        .vote-progress {
            background: #f8f9fa;
            border-radius: 25px;
            overflow: hidden;
            height: 40px;
            display: flex;
            margin: 15px 0;
        }

        .vote-progress-bullish {
            background: linear-gradient(135deg, var(--success-color), #2ecc71);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            transition: width 0.6s ease;
        }

        .vote-progress-bearish {
            background: linear-gradient(135deg, var(--danger-color), #c0392b);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            transition: width 0.6s ease;
        }

        .timeline {
            position: relative;
            padding: 20px 0;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(to bottom, var(--secondary-color), var(--info-color));
            transform: translateX(-50%);
        }

        .timeline-item {
            position: relative;
            margin-bottom: 30px;
            width: 45%;
        }

        .timeline-item-left {
            left: 0;
        }

        .timeline-item-right {
            left: 55%;
        }

        .timeline-item::before {
            content: '';
            position: absolute;
            top: 20px;
            width: 20px;
            height: 20px;
            background: var(--secondary-color);
            border: 4px solid white;
            border-radius: 50%;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .timeline-item-left::before {
            right: -62px;
        }

        .timeline-item-right::before {
            left: -62px;
        }

        .theme-toggle, .back-to-top {
            position: fixed;
            z-index: 1000;
            background: var(--secondary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }

        .theme-toggle {
            top: 20px;
            right: 20px;
        }

        .back-to-top {
            bottom: 20px;
            right: 20px;
            opacity: 0;
            visibility: hidden;
        }

        .back-to-top.show {
            opacity: 1;
            visibility: visible;
        }

        @media (max-width: 768px) {
            .timeline::before {
                left: 30px;
            }

            .timeline-item {
                width: calc(100% - 60px);
                left: 60px !important;
            }

            .timeline-item::before {
                left: -50px !important;
            }

            .container {
                padding: 20px;
                margin: 10px;
            }
        }
        '''
    
    def _get_javascript_code(self) -> str:
        """获取JavaScript代码"""
        return '''
        // 页面渲染函数
        function renderPage() {
            if (!window.reportData) {
                console.error('报告数据未加载');
                return;
            }
            
            renderOverview();
            renderAnalysis();
            renderDebateTimeline();
            initializeInteractions();
        }

        function renderOverview() {
            const overview = document.getElementById('overview');
            if (!overview || !reportData) return;

            const stockCode = reportData.stock_code || 'Unknown';
            const battleResults = reportData.battle_results || {};
            const finalDecision = battleResults.final_decision || 'Unknown';
            const voteCount = battleResults.vote_count || {};

            const bullishCount = voteCount.bullish || 0;
            const bearishCount = voteCount.bearish || 0;
            const totalVotes = bullishCount + bearishCount;

            const bullishPercent = totalVotes > 0 ? Math.round((bullishCount / totalVotes) * 100) : 0;
            const bearishPercent = totalVotes > 0 ? Math.round((bearishCount / totalVotes) * 100) : 0;

            overview.innerHTML = `
                <div class="text-center mb-4">
                    <h1 class="display-4 fw-bold text-primary">
                        <i class="fas fa-chart-line me-3"></i>股票分析报告
                    </h1>
                    <p class="lead text-muted">股票代码: ${stockCode}</p>
                </div>
                
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <h3 class="card-title">
                                    <i class="fas fa-vote-yea me-2 text-primary"></i>专家投票结果
                                </h3>
                                <div class="vote-progress mb-3">
                                    <div class="vote-progress-bullish" style="width: ${bullishPercent}%">
                                        看涨 ${bullishCount}票
                                    </div>
                                    <div class="vote-progress-bearish" style="width: ${bearishPercent}%">
                                        看跌 ${bearishCount}票
                                    </div>
                                </div>
                                <h4 class="mt-3">
                                    最终结论: 
                                    <span class="badge ${finalDecision === 'bullish' ? 'badge-bullish' : 'badge-bearish'} fs-6">
                                        ${finalDecision === 'bullish' ? '看涨' : finalDecision === 'bearish' ? '看跌' : '未知'}
                                    </span>
                                </h4>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body">
                                <h3 class="card-title">
                                    <i class="fas fa-info-circle me-2 text-primary"></i>分析摘要
                                </h3>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-users me-2 text-success"></i>参与专家: ${totalVotes}位</li>
                                    <li><i class="fas fa-comments me-2 text-info"></i>辩论轮次: 2轮</li>
                                    <li><i class="fas fa-clock me-2 text-warning"></i>生成时间: ${reportData.timestamp || '未知'}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderAnalysis() {
            const analysisSection = document.getElementById('analysis');
            if (!analysisSection || !reportData.research_results) return;

            const research = reportData.research_results;

            analysisSection.innerHTML = `
                <div class="text-center mb-4">
                    <h2 class="fw-bold">
                        <i class="fas fa-microscope me-2 text-primary"></i>专家分析结果
                    </h2>
                    <p class="text-muted">各领域专家的深度分析</p>
                </div>
                
                <div class="accordion" id="analysisAccordion">
                    ${Object.entries(research).map(([key, value], index) => `
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" 
                                        data-bs-toggle="collapse" data-bs-target="#collapse${index}" 
                                        aria-expanded="${index === 0 ? 'true' : 'false'}" aria-controls="collapse${index}">
                                    <i class="fas fa-chart-bar me-2"></i>${getAnalysisTitle(key)}
                                </button>
                            </h2>
                            <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                                 data-bs-parent="#analysisAccordion">
                                <div class="accordion-body">
                                    <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit;">${value}</pre>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function renderDebateTimeline() {
            const timeline = document.getElementById('debateTimeline');
            if (!timeline || !reportData.debate_history) return;

            const debateHistory = reportData.debate_history;

            timeline.innerHTML = debateHistory.map((item, index) => `
                <div class="timeline-item ${index % 2 === 0 ? 'timeline-item-left' : 'timeline-item-right'}">
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h5 class="card-title mb-0">
                                    <i class="fas fa-user-tie me-2 text-primary"></i>${getAgentName(item.speaker)}
                                </h5>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>${item.timestamp}
                                </small>
                            </div>
                            <div class="card-text">
                                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">${item.content}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function getAnalysisTitle(key) {
            const titles = {
                'sentiment': '市场情绪分析',
                'risk': '风险控制分析',
                'hot_money': '游资行为分析',
                'technical': '技术面分析',
                'chip_analysis': '筹码分析',
                'big_deal': '大单异动分析'
            };
            return titles[key] || key;
        }

        function getAgentName(agentId) {
            const names = {
                'sentiment_agent': '市场情绪分析师',
                'risk_control_agent': '风险控制专家',
                'hot_money_agent': '游资行为分析师',
                'technical_analysis_agent': '技术分析师',
                'chip_analysis_agent': '筹码分析师',
                'big_deal_analysis_agent': '大单异动分析师'
            };
            return names[agentId] || agentId;
        }

        function initializeInteractions() {
            // 主题切换
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', function() {
                    const body = document.body;
                    const currentTheme = body.getAttribute('data-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    body.setAttribute('data-theme', newTheme);

                    const icon = themeToggle.querySelector('i');
                    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                });
            }

            // 回到顶部
            const backToTop = document.getElementById('backToTop');
            if (backToTop) {
                window.addEventListener('scroll', function() {
                    if (window.pageYOffset > 300) {
                        backToTop.classList.add('show');
                    } else {
                        backToTop.classList.remove('show');
                    }
                });

                backToTop.addEventListener('click', function() {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
            }
        }

        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            // 等待数据加载
            if (window.reportData) {
                renderPage();
            } else {
                // 如果数据还没加载，等待一下
                setTimeout(() => {
                    if (window.reportData) {
                        renderPage();
                    } else {
                        document.getElementById('overview').innerHTML = `
                            <div class="alert alert-warning text-center">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                数据加载失败，请刷新页面重试
                            </div>
                        `;
                    }
                }, 1000);
            }
        });
        '''
    
    def _write_html_safely(self, content: str, output_path: str) -> bool:
        """安全地写入HTML文件，避免截断"""
        try:
            # 检查内容长度
            if len(content) > 50000:  # 如果内容过长，分块写入
                return self._write_in_chunks(content, output_path)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
        except Exception as e:
            print(f"写入HTML文件时出错: {e}")
            return False
    
    def _write_in_chunks(self, content: str, output_path: str, chunk_size: int = 8000) -> bool:
        """分块写入大文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    f.write(chunk)
                    f.flush()  # 强制写入磁盘
            return True
        except Exception as e:
            print(f"分块写入文件时出错: {e}")
            return False