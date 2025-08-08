"""
HTML报告生成工具 - 数据外部化版本
将HTML模板与数据分离，避免截断问题
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

def create_html_template() -> str:
    """创建基础HTML模板，不包含数据"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FinGenius 股票分析报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --success-color: #059669;
            --danger-color: #dc2626;
            --warning-color: #d97706;
            --info-color: #0891b2;
            --light-bg: #f8fafc;
            --dark-bg: #1e293b;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }

        .main-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin: 0 auto;
            max-width: 1200px;
        }

        .header-section {
            background: linear-gradient(135deg, var(--primary-color) 0%, #1d4ed8 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }

        .header-section h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }

        .content-section {
            padding: 2rem;
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            margin-bottom: 2rem;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }

        .card-header {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-bottom: 2px solid var(--primary-color);
            border-radius: 15px 15px 0 0 !important;
            padding: 1.5rem;
        }

        .card-header h3 {
            margin: 0;
            color: var(--primary-color);
            font-weight: 600;
        }

        .vote-progress {
            background: #e5e7eb;
            border-radius: 10px;
            overflow: hidden;
            height: 40px;
            display: flex;
            margin: 1rem 0;
        }

        .vote-progress-bar {
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            transition: width 0.5s ease;
        }

        .vote-progress-bullish {
            background: linear-gradient(135deg, var(--success-color) 0%, #10b981 100%);
        }

        .vote-progress-bearish {
            background: linear-gradient(135deg, var(--danger-color) 0%, #ef4444 100%);
        }

        .badge-bullish {
            background: linear-gradient(135deg, var(--success-color) 0%, #10b981 100%);
            color: white;
        }

        .badge-bearish {
            background: linear-gradient(135deg, var(--danger-color) 0%, #ef4444 100%);
            color: white;
        }

        .timeline {
            position: relative;
            padding: 2rem 0;
        }

        .timeline::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(to bottom, var(--primary-color), var(--info-color));
            transform: translateX(-50%);
        }

        .timeline-item {
            position: relative;
            margin-bottom: 3rem;
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
            width: 20px;
            height: 20px;
            background: var(--primary-color);
            border: 4px solid white;
            border-radius: 50%;
            top: 20px;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.2);
        }

        .timeline-item-left::before {
            right: -62px;
        }

        .timeline-item-right::before {
            left: -62px;
        }

        .timeline-item .card {
            margin-bottom: 0;
        }

        .fade-in-up {
            animation: fadeInUp 0.6s ease forwards;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .theme-toggle {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            box-shadow: var(--card-shadow);
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .theme-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        .back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            cursor: pointer;
            box-shadow: var(--card-shadow);
            transition: all 0.3s ease;
            opacity: 0;
            visibility: hidden;
            z-index: 1000;
        }

        .back-to-top.show {
            opacity: 1;
            visibility: visible;
        }

        .back-to-top:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
        }

        .disclaimer {
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            border-left: 5px solid var(--warning-color);
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 2rem;
        }

        .disclaimer h5 {
            color: var(--warning-color);
            margin-bottom: 1rem;
        }

        .disclaimer p {
            margin: 0;
            color: #92400e;
            line-height: 1.6;
        }

        @media (max-width: 768px) {
            .timeline::before {
                left: 20px;
            }

            .timeline-item {
                width: calc(100% - 40px);
                left: 40px !important;
            }

            .timeline-item::before {
                left: -30px !important;
            }

            .header-section h1 {
                font-size: 2rem;
            }

            .content-section {
                padding: 1rem;
            }
        }
    </style>
</head>
<body>
    <!-- 主题切换按钮 -->
    <button class="theme-toggle" id="themeToggle" title="切换主题">
        <i class="fas fa-moon"></i>
    </button>

    <!-- 回到顶部按钮 -->
    <button class="back-to-top" id="backToTop" title="回到顶部">
        <i class="fas fa-arrow-up"></i>
    </button>

    <div class="container">
        <div class="main-container">
            <!-- 头部区域 -->
            <div class="header-section">
                <h1><i class="fas fa-chart-line me-3"></i>FinGenius 股票分析报告</h1>
                <p class="lead mb-0">AI驱动的多专家智能分析系统</p>
            </div>

            <!-- 内容区域 -->
            <div class="content-section">
                <!-- 概览部分 -->
                <section id="overview">
                    <div class="text-center">
                        <div class="loading-spinner"></div>
                        <p class="mt-3 text-muted">正在加载报告数据...</p>
                    </div>
                </section>

                <!-- 分析结果部分 -->
                <section id="analysis">
                    <!-- 动态填充 -->
                </section>

                <!-- 专家辩论时间线 -->
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-comments me-2"></i>专家辩论过程</h3>
                    </div>
                    <div class="card-body">
                        <div class="timeline" id="debateTimeline">
                            <!-- 动态填充 -->
                        </div>
                    </div>
                </div>

                <!-- 免责声明 -->
                <div class="disclaimer">
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>重要声明</h5>
                    <p>
                        本报告由FinGenius人工智能系统自动生成，基于公开数据和算法模型进行分析。
                        报告内容仅供参考，不构成投资建议。投资有风险，决策需谨慎。
                        请结合自身情况和专业建议做出投资决策。
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // 数据外部化 - 通过外部API加载数据
        let reportData = null;
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadReportData();
        });
        
        // 从URL参数或外部API加载数据
        async function loadReportData() {
            try {
                // 从URL获取报告路径
                const urlParams = new URLSearchParams(window.location.search);
                let reportPath = urlParams.get('report') || window.location.pathname.split('/').pop();
                
                if (reportPath && reportPath !== 'index.html') {
                    // 将HTML文件名转换为对应的JSON数据文件名
                    let dataFileName = reportPath;
                    if (reportPath.startsWith('html_') && reportPath.endsWith('.html')) {
                        dataFileName = reportPath.replace('html_', 'data_').replace('.html', '.json');
                    }
                    
                    console.log('请求数据文件:', dataFileName);
                    
                    // 通过API加载数据
                    const response = await fetch(`/api/report-data/${encodeURIComponent(dataFileName)}`);
                    if (response.ok) {
                        reportData = await response.json();
                        initializeReport(reportData);
                        return;
                    } else {
                        console.error('API请求失败:', response.status, response.statusText);
                        showError(`数据加载失败: ${response.status} ${response.statusText}`);
                        return;
                    }
                }
                
                // 如果没有外部数据，显示占位符
                showPlaceholder();
                
            } catch (error) {
                console.error('加载报告数据失败:', error);
                showError('数据加载失败: ' + error.message);
            }
        }
        
        // 初始化报告显示
        function initializeReport(data) {
            try {
                if (!data) {
                    showPlaceholder();
                    return;
                }
                
                // 填充各个部分
                fillOverviewSection(data);
                fillAnalysisSection(data);
                fillDebateTimeline(data);
                
                // 初始化交互功能
                initializeThemeToggle();
                initializeBackToTop();
                
                console.log('报告初始化完成');
            } catch (error) {
                console.error('报告初始化失败:', error);
                showError('报告初始化失败: ' + error.message);
            }
        }
        
        // 填充概览部分
        function fillOverviewSection(data) {
            const overviewSection = document.getElementById('overview');
            if (!overviewSection || !data) return;
            
            const stockCode = data.stock_code || 'Unknown';
            const battleResults = data.battle_results || {};
            const finalDecision = battleResults.final_decision || 'Unknown';
            const voteCount = battleResults.vote_count || {};
            
            const bullishCount = voteCount.bullish || 0;
            const bearishCount = voteCount.bearish || 0;
            const totalVotes = bullishCount + bearishCount;
            
            const bullishPercent = totalVotes > 0 ? Math.round((bullishCount / totalVotes) * 100) : 0;
            const bearishPercent = totalVotes > 0 ? Math.round((bearishCount / totalVotes) * 100) : 0;
            
            overviewSection.innerHTML = `
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header">
                                <h3><i class="fas fa-info-circle me-2"></i>股票信息</h3>
                            </div>
                            <div class="card-body text-center">
                                <h2 class="text-primary mb-3">${stockCode}</h2>
                                <p class="text-muted">分析时间: ${data.timestamp || '未知'}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-header">
                                <h3><i class="fas fa-vote-yea me-2"></i>专家投票结果</h3>
                            </div>
                            <div class="card-body text-center">
                                <div class="vote-progress mb-3">
                                    <div class="vote-progress-bar vote-progress-bullish" style="width: ${bullishPercent}%">
                                        看涨 ${bullishCount}票
                                    </div>
                                    <div class="vote-progress-bar vote-progress-bearish" style="width: ${bearishPercent}%">
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
                </div>
            `;
        }
        
        // 填充分析部分
        function fillAnalysisSection(data) {
            const analysisSection = document.getElementById('analysis');
            if (!analysisSection || !data.research_results) return;
            
            const research = data.research_results;
            
            analysisSection.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h3><i class="fas fa-microscope me-2"></i>专家分析结果</h3>
                    </div>
                    <div class="card-body">
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
                    </div>
                </div>
            `;
        }
        
        // 填充辩论时间线
        function fillDebateTimeline(data) {
            const timeline = document.getElementById('debateTimeline');
            if (!timeline || !data.battle_results || !data.battle_results.debate_history) return;
            
            const debateHistory = data.battle_results.debate_history;
            
            timeline.innerHTML = debateHistory.map((item, index) => `
                <div class="timeline-item ${index % 2 === 0 ? 'timeline-item-left' : 'timeline-item-right'} fade-in-up">
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
        
        // 显示占位符
        function showPlaceholder() {
            const overviewSection = document.getElementById('overview');
            if (overviewSection) {
                overviewSection.innerHTML = `
                    <div class="card">
                        <div class="card-body text-center py-5">
                            <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                            <h3 class="text-muted">暂无报告数据</h3>
                            <p class="text-muted">请通过分析系统生成报告后查看</p>
                        </div>
                    </div>
                `;
            }
        }
        
        // 显示错误信息
        function showError(message) {
            const overviewSection = document.getElementById('overview');
            if (overviewSection) {
                overviewSection.innerHTML = `
                    <div class="card border-danger">
                        <div class="card-body text-center py-5">
                            <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                            <h3 class="text-danger">加载失败</h3>
                            <p class="text-muted">${message}</p>
                            <button class="btn btn-primary" onclick="location.reload()">重新加载</button>
                        </div>
                    </div>
                `;
            }
        }
        
        // 获取分析标题
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
        
        // 获取专家名称
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
        
        // 初始化主题切换
        function initializeThemeToggle() {
            const themeToggle = document.getElementById('themeToggle');
            const body = document.body;
            
            if (themeToggle) {
                themeToggle.addEventListener('click', function() {
                    const currentTheme = body.getAttribute('data-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    body.setAttribute('data-theme', newTheme);
                    
                    const icon = themeToggle.querySelector('i');
                    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                });
            }
        }
        
        // 初始化回到顶部按钮
        function initializeBackToTop() {
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
    </script>
</body>
</html>"""

def save_data_file(data: Dict[str, Any], data_file_path: str) -> bool:
    """保存数据到外部JSON文件"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(data_file_path), exist_ok=True)
        
        # 保存数据
        with open(data_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {data_file_path}")
        return True
        
    except Exception as e:
        print(f"保存数据文件失败: {e}")
        return False

def create_html_with_external_data(
    stock_code: str,
    data: Dict[str, Any],
    output_dir: str = "report/html"
) -> tuple[str, str]:
    """
    创建HTML报告，使用数据外部化方案
    
    Args:
        stock_code: 股票代码
        data: 报告数据
        output_dir: 输出目录
    
    Returns:
        tuple: (HTML文件路径, 数据文件路径)
    """
    try:
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成文件名
        html_filename = f"html_{stock_code}_{timestamp}.html"
        data_filename = f"data_{stock_code}_{timestamp}.json"
        
        # 生成完整路径
        html_path = os.path.join(output_dir, html_filename)
        data_path = os.path.join(output_dir, data_filename)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建HTML模板
        html_content = create_html_template()
        
        # 保存HTML文件
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 保存数据文件
        save_data_file(data, data_path)
        
        print(f"HTML报告已生成:")
        print(f"  HTML文件: {html_path}")
        print(f"  数据文件: {data_path}")
        
        return html_path, data_path
        
    except Exception as e:
        print(f"生成HTML报告失败: {e}")
        raise

def load_external_data(data_file_path: str) -> Optional[Dict[str, Any]]:
    """从外部文件加载数据"""
    try:
        if not os.path.exists(data_file_path):
            print(f"数据文件不存在: {data_file_path}")
            return None
        
        with open(data_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"成功加载数据文件: {data_file_path}")
        return data
        
    except Exception as e:
        print(f"加载数据文件失败: {e}")
        return None

if __name__ == "__main__":
    # 测试数据外部化方案
    test_data = {
        "stock_code": "000001",
        "timestamp": "20250808_150000",
        "research_results": {
            "sentiment": "市场情绪分析结果...",
            "technical": "技术分析结果...",
            "risk": "风险分析结果..."
        },
        "battle_results": {
            "final_decision": "bullish",
            "vote_count": {"bullish": 4, "bearish": 2},
            "debate_history": [
                {
                    "speaker": "sentiment_agent",
                    "content": "基于情绪分析，市场看涨情绪较强...",
                    "timestamp": "15:01:23"
                }
            ]
        }
    }
    
    try:
        html_path, data_path = create_html_with_external_data("000001", test_data)
        print("测试成功!")
    except Exception as e:
        print(f"测试失败: {e}")