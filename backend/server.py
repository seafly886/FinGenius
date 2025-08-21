import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, StreamingResponse, FileResponse, HTMLResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
import queue
import threading

# 导入聊天处理器
from chat_handler import handle_single_chat, handle_group_chat, get_available_models

# 全局会话存储
active_sessions: Dict[str, Dict[str, Any]] = {}

class AnalysisSession:
    def __init__(self, session_id: str, stock_code: str, options: Dict[str, Any] = None):
        self.session_id = session_id
        self.stock_code = stock_code
        self.options = options or {}
        self.process = None
        self.output_queue = queue.Queue()
        self.is_complete = False
        self.error = None
        self.report_path = None
        
    async def start_analysis(self):
        """启动股票分析进程"""
        try:
            # 构建命令，包含可选参数
            cmd = [sys.executable, "main.py", self.stock_code]
            
            # 添加可选参数
            if self.options.get('format'):
                cmd.extend(['-f', self.options['format']])
            if self.options.get('output'):
                cmd.extend(['-o', self.options['output']])
            if self.options.get('tts'):
                cmd.append('--tts')
            if self.options.get('max_steps'):
                cmd.extend(['--max-steps', str(self.options['max_steps'])])
            if self.options.get('debate_rounds'):
                cmd.extend(['--debate-rounds', str(self.options['debate_rounds'])])
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
            # 在后台线程中读取输出
            def read_output():
                try:
                    for line in iter(self.process.stdout.readline, ''):
                        if line:
                            self.output_queue.put(('output', line))
                    
                    # 等待进程完成
                    return_code = self.process.wait()
                    
                    if return_code == 0:
                        # 查找生成的报告文件
                        report_path = self.find_report_file()
                        self.report_path = report_path
                        self.output_queue.put(('complete', {'report_path': report_path}))
                    else:
                        self.output_queue.put(('error', {'message': f'分析进程异常退出，返回码: {return_code}'}))
                    
                    self.is_complete = True
                    
                except Exception as e:
                    self.output_queue.put(('error', {'message': f'读取输出时发生错误: {str(e)}'}))
                    self.is_complete = True
            
            # 启动输出读取线程
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()
            
        except Exception as e:
            self.error = str(e)
            self.output_queue.put(('error', {'message': str(e)}))
            self.is_complete = True
    
    def find_report_file(self):
        """查找生成的报告文件"""
        try:
            # 查找report目录下最新的HTML文件
            report_dir = Path("report")
            if report_dir.exists():
                html_files = list(report_dir.glob(f"*{self.stock_code}*.html"))
                if html_files:
                    # 返回最新的文件
                    latest_file = max(html_files, key=lambda f: f.stat().st_mtime)
                    return str(latest_file)
            return None
        except Exception as e:
            print(f"查找报告文件时出错: {e}")
            return None
    
    def get_output_stream(self):
        """获取输出流生成器"""
        while not self.is_complete or not self.output_queue.empty():
            try:
                # 非阻塞获取队列中的数据
                event_type, data = self.output_queue.get(timeout=1)
                
                if event_type == 'output':
                    yield f"data: {json.dumps({'type': 'output', 'content': data})}\n\n"
                elif event_type == 'complete':
                    yield f"data: {json.dumps({'type': 'complete', **data})}\n\n"
                    break
                elif event_type == 'error':
                    yield f"data: {json.dumps({'type': 'error', **data})}\n\n"
                    break
                    
            except queue.Empty:
                # 发送心跳
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                continue
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break

async def start_analysis(request: Request):
    """启动股票分析"""
    try:
        data = await request.json()
        stock_code = data.get('stock_code', '').strip()
        options = data.get('options', {})
        
        if not stock_code:
            return JSONResponse({'success': False, 'error': '股票代码不能为空'})
        
        # 创建新的分析会话
        session_id = str(uuid.uuid4())
        session = AnalysisSession(session_id, stock_code, options)
        active_sessions[session_id] = session
        
        # 启动分析
        await session.start_analysis()
        
        return JSONResponse({
            'success': True,
            'session_id': session_id,
            'message': f'开始分析股票 {stock_code}'
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)})

async def stream_output(request: Request):
    """流式输出分析结果"""
    session_id = request.path_params['session_id']
    
    if session_id not in active_sessions:
        return JSONResponse({'error': '会话不存在'}, status_code=404)
    
    session = active_sessions[session_id]
    
    async def generate():
        yield "data: {\"type\": \"connected\"}\n\n"
        
        # 使用异步生成器包装同步生成器
        for chunk in session.get_output_stream():
            yield chunk
            await asyncio.sleep(0.01)  # 小延迟避免过快输出
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

async def get_report(request: Request):
    """获取报告内容"""
    report_path = request.path_params['report_path']
    
    try:
        # 安全检查：确保路径在项目目录内
        full_path = Path(report_path).resolve()
        project_root = Path(__file__).parent.parent.resolve()
        
        if not str(full_path).startswith(str(project_root)):
            return JSONResponse({'error': '无效的文件路径'}, status_code=400)
        
        if not full_path.exists():
            return JSONResponse({'error': '报告文件不存在'}, status_code=404)
        
        # 读取文件内容
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return JSONResponse({'content': content})
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

async def download_report(request: Request):
    """下载报告文件"""
    report_path = request.path_params['report_path']
    
    try:
        # 安全检查
        full_path = Path(report_path).resolve()
        project_root = Path(__file__).parent.parent.resolve()
        
        if not str(full_path).startswith(str(project_root)):
            return JSONResponse({'error': '无效的文件路径'}, status_code=400)
        
        if not full_path.exists():
            return JSONResponse({'error': '报告文件不存在'}, status_code=404)
        
        return FileResponse(
            full_path,
            filename=full_path.name,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

async def view_report(request: Request):
    """在浏览器中查看报告，支持外部数据加载"""
    report_path = request.path_params['report_path']
    
    try:
        # 安全检查
        full_path = Path(report_path).resolve()
        project_root = Path(__file__).parent.parent.resolve()
        
        if not str(full_path).startswith(str(project_root)):
            return HTMLResponse('<h1>无效的文件路径</h1>', status_code=400)
        
        if not full_path.exists():
            return HTMLResponse('<h1>报告文件不存在</h1>', status_code=404)
        
        # 读取HTML文件
        with open(full_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 检查是否为外部化数据的HTML模板
        if "loadExternalData" in html_content:
            # 这是外部化数据的HTML模板，直接返回
            return HTMLResponse(html_content)
        
        # 兼容旧版本的内嵌数据HTML文件
        # 尝试从文件名提取股票代码和时间戳
        filename = full_path.name
        stock_code = "unknown"
        timestamp = ""
        
        if "_" in filename:
            parts = filename.split("_")
            for part in parts:
                if part.isdigit() and len(part) == 6:
                    stock_code = part
                elif len(part) == 15 and part.isdigit():  # 时间戳格式
                    timestamp = part
        
        # 查找对应的debate和vote数据
        report_data = load_report_data(stock_code, timestamp)
        
        # 注入数据到HTML（兼容旧版本）
        if report_data and "页面数据注入点" in html_content:
            data_script = f"""
        // 页面数据注入点
        const reportData = {json.dumps(report_data, ensure_ascii=False, indent=2)};
        
        // 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {{
            initializeReport(reportData);
        }});
        
        // 初始化报告函数
        function initializeReport(data) {{
            try {{
                // 填充概览部分
                fillOverviewSection(data);
                
                // 填充分析部分
                fillAnalysisSection(data);
                
                // 填充辩论时间线
                fillDebateTimeline(data);
                
                // 初始化其他功能
                initializeThemeToggle();
                initializeBackToTop();
                
                console.log('报告初始化完成');
            }} catch (error) {{
                console.error('报告初始化失败:', error);
            }}
        }}
        
        // 填充概览部分
        function fillOverviewSection(data) {{
            const overviewSection = document.getElementById('overview');
            if (!overviewSection || !data) return;
            
            const stockCode = data.stock_code || 'Unknown';
            const battleResults = data.battle_results || {{}};
            const finalDecision = battleResults.final_decision || 'Unknown';
            const voteCount = battleResults.vote_count || {{}};
            
            const bullishCount = voteCount.bullish || 0;
            const bearishCount = voteCount.bearish || 0;
            const totalVotes = bullishCount + bearishCount;
            
            const bullishPercent = totalVotes > 0 ? Math.round((bullishCount / totalVotes) * 100) : 0;
            const bearishPercent = totalVotes > 0 ? Math.round((bearishCount / totalVotes) * 100) : 0;
            
            overviewSection.innerHTML = `
                <div class="text-center mb-4">
                    <h1 class="display-4 fw-bold text-primary">
                        <i class="fas fa-chart-line me-3"></i>股票分析报告
                    </h1>
                    <p class="lead text-muted">股票代码: ${{stockCode}}</p>
                </div>
                
                <div class="row g-4">
                    <div class="col-md-6">
                        <div class="card h-100">
                            <div class="card-body text-center">
                                <h3 class="card-title">
                                    <i class="fas fa-vote-yea me-2 text-primary"></i>专家投票结果
                                </h3>
                                <div class="vote-progress mb-3">
                                    <div class="vote-progress-bar vote-progress-bullish" style="width: ${{bullishPercent}}%">
                                        看涨 ${{bullishCount}}票
                                    </div>
                                    <div class="vote-progress-bar vote-progress-bearish" style="width: ${{bearishPercent}}%">
                                        看跌 ${{bearishCount}}票
                                    </div>
                                </div>
                                <h4 class="mt-3">
                                    最终结论: 
                                    <span class="badge ${{finalDecision === 'bullish' ? 'badge-bullish' : 'badge-bearish'}} fs-6">
                                        ${{finalDecision === 'bullish' ? '看涨' : finalDecision === 'bearish' ? '看跌' : '未知'}}
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
                                    <li><i class="fas fa-users me-2 text-success"></i>参与专家: ${{totalVotes}}位</li>
                                    <li><i class="fas fa-comments me-2 text-info"></i>辩论轮次: ${{battleResults.debate_rounds || 1}}轮</li>
                                    <li><i class="fas fa-clock me-2 text-warning"></i>生成时间: ${{data.timestamp || '未知'}}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }}
        
        // 填充分析部分
        function fillAnalysisSection(data) {{
            const analysisSection = document.getElementById('analysis');
            if (!analysisSection || !data.research_results) return;
            
            const research = data.research_results;
            
            analysisSection.innerHTML = `
                <div class="text-center mb-4">
                    <h2 class="fw-bold">
                        <i class="fas fa-microscope me-2 text-primary"></i>专家分析结果
                    </h2>
                    <p class="text-muted">各领域专家的深度分析</p>
                </div>
                
                <div class="accordion" id="analysisAccordion">
                    ${{Object.entries(research).map(([key, value], index) => `
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button ${{index === 0 ? '' : 'collapsed'}}" type="button" 
                                        data-bs-toggle="collapse" data-bs-target="#collapse${{index}}" 
                                        aria-expanded="${{index === 0 ? 'true' : 'false'}}" aria-controls="collapse${{index}}">
                                    <i class="fas fa-chart-bar me-2"></i>${{getAnalysisTitle(key)}}
                                </button>
                            </h2>
                            <div id="collapse${{index}}" class="accordion-collapse collapse ${{index === 0 ? 'show' : ''}}" 
                                 data-bs-parent="#analysisAccordion">
                                <div class="accordion-body">
                                    <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit;">${{value}}</pre>
                                </div>
                            </div>
                        </div>
                    `).join('')}}
                </div>
            `;
        }}
        
        // 填充辩论时间线
        function fillDebateTimeline(data) {{
            const timeline = document.getElementById('debateTimeline');
            if (!timeline || !data.battle_results || !data.battle_results.debate_history) return;
            
            const debateHistory = data.battle_results.debate_history;
            
            timeline.innerHTML = debateHistory.map((item, index) => `
                <div class="timeline-item ${{index % 2 === 0 ? 'timeline-item-left' : 'timeline-item-right'}} fade-in-up">
                    <div class="card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h5 class="card-title mb-0">
                                    <i class="fas fa-user-tie me-2 text-primary"></i>${{getAgentName(item.speaker)}}
                                </h5>
                                <small class="text-muted">
                                    <i class="fas fa-clock me-1"></i>${{item.timestamp}}
                                </small>
                            </div>
                            <div class="card-text">
                                <pre style="white-space: pre-wrap; font-family: inherit; margin: 0;">${{item.content}}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }}
        
        // 获取分析标题
        function getAnalysisTitle(key) {{
            const titles = {{
                'sentiment': '市场情绪分析',
                'risk': '风险控制分析', 
                'hot_money': '游资行为分析',
                'technical': '技术面分析',
                'chip_analysis': '筹码分析',
                'big_deal': '大单异动分析'
            }};
            return titles[key] || key;
        }}
        
        // 获取专家名称
        function getAgentName(agentId) {{
            const names = {{
                'sentiment_agent': '市场情绪分析师',
                'risk_control_agent': '风险控制专家',
                'hot_money_agent': '游资行为分析师', 
                'technical_analysis_agent': '技术分析师',
                'chip_analysis_agent': '筹码分析师',
                'big_deal_analysis_agent': '大单异动分析师'
            }};
            return names[agentId] || agentId;
        }}
        
        // 初始化主题切换
        function initializeThemeToggle() {{
            const themeToggle = document.getElementById('themeToggle');
            const body = document.body;
            
            if (themeToggle) {{
                themeToggle.addEventListener('click', function() {{
                    const currentTheme = body.getAttribute('data-theme');
                    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                    body.setAttribute('data-theme', newTheme);
                    
                    const icon = themeToggle.querySelector('i');
                    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }});
            }}
        }}
        
        // 初始化回到顶部按钮
        function initializeBackToTop() {{
            const backToTop = document.getElementById('backToTop');
            
            if (backToTop) {{
                window.addEventListener('scroll', function() {{
                    if (window.pageYOffset > 300) {{
                        backToTop.classList.add('show');
                    }} else {{
                        backToTop.classList.remove('show');
                    }}
                }});
                
                backToTop.addEventListener('click', function() {{
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                }});
            }}
        }}
            """
            
            html_content = html_content.replace("// 页面数据注入点", data_script)
        
        return HTMLResponse(html_content)
        
    except Exception as e:
        return HTMLResponse(f'<h1>错误: {str(e)}</h1>', status_code=500)

def load_report_data(stock_code: str, timestamp: str) -> Dict[str, Any]:
    """加载报告相关数据，优先加载外部化数据文件"""
    try:
        # 首先尝试加载外部化的数据文件
        project_root = Path(__file__).parent.parent
        
        # 确保时间戳不为空
        if timestamp:
            data_filename = f"data_{stock_code}_{timestamp}.json"
        else:
            # 如果时间戳为空，查找最新的数据文件
            html_dir = project_root / "report" / "html"
            data_files = list(html_dir.glob(f"data_{stock_code}_*.json"))
            if data_files:
                latest_data_file = max(data_files, key=lambda f: f.stat().st_mtime)
                data_filename = latest_data_file.name
            else:
                data_filename = f"data_{stock_code}_.json"  # 这会导致文件不存在
        
        data_path = project_root / "report" / "html" / data_filename
        
        print(f"尝试加载外部化数据文件: {data_path}")
        
        if data_path.exists():
            print(f"找到外部化数据文件: {data_path}")
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"成功加载外部化数据，包含键: {list(data.keys())}")
                return data
        
        # 如果外部化数据文件不存在，回退到原有的加载方式
        print(f"外部化数据文件不存在，使用传统方式加载")
        
        report_data = {
            "stock_code": stock_code,
            "timestamp": timestamp,
            "research_results": {},
            "battle_results": {}
        }
        
        # 查找对应的debate文件 - 更灵活的匹配策略
        debate_dir = Path("report/debate")
        if debate_dir.exists():
            # 首先尝试精确匹配
            debate_files = list(debate_dir.glob(f"debate_{stock_code}_{timestamp}.json"))
            if not debate_files:
                # 如果精确匹配失败，查找同一股票代码的所有文件
                debate_files = list(debate_dir.glob(f"debate_{stock_code}_*.json"))
            
            if debate_files:
                # 选择最新的文件
                latest_debate = max(debate_files, key=lambda f: f.stat().st_mtime)
                print(f"加载debate文件: {latest_debate}")
                with open(latest_debate, 'r', encoding='utf-8') as f:
                    debate_data = json.load(f)
                    report_data["battle_results"] = debate_data
        
        # 查找对应的vote文件 - 同样使用灵活匹配
        vote_dir = Path("report/vote")
        if vote_dir.exists():
            # 首先尝试精确匹配
            vote_files = list(vote_dir.glob(f"vote_{stock_code}_{timestamp}.json"))
            if not vote_files:
                # 如果精确匹配失败，查找同一股票代码的所有文件
                vote_files = list(vote_dir.glob(f"vote_{stock_code}_*.json"))
            
            if vote_files:
                latest_vote = max(vote_files, key=lambda f: f.stat().st_mtime)
                print(f"加载vote文件: {latest_vote}")
                with open(latest_vote, 'r', encoding='utf-8') as f:
                    vote_data = json.load(f)
                    # 合并vote数据到battle_results
                    if "battle_results" not in report_data:
                        report_data["battle_results"] = {}
                    report_data["battle_results"].update(vote_data)
        
        # 从debate数据中提取research_results（如果有的话）
        if "battle_results" in report_data and "research_results" in report_data["battle_results"]:
            report_data["research_results"] = report_data["battle_results"]["research_results"]
        
        print(f"成功加载报告数据，包含battle_results: {'battle_results' in report_data and bool(report_data['battle_results'])}")
        return report_data
        
    except Exception as e:
        print(f"加载报告数据失败: {e}")
        return {}

async def get_reports_list(request: Request):
    """获取历史报告列表"""
    try:
        reports = []
        
        # 使用绝对路径确保正确找到文件
        project_root = Path(__file__).parent.parent
        report_dir = project_root / "report"
        
        print(f"查找报告目录: {report_dir}")
        print(f"报告目录是否存在: {report_dir.exists()}")
        
        if report_dir.exists():
            # 获取所有HTML文件，特别是report/html目录下的文件
            html_dir = report_dir / "html"
            print(f"HTML目录: {html_dir}")
            print(f"HTML目录是否存在: {html_dir.exists()}")
            
            if html_dir.exists():
                html_files = list(html_dir.glob("*.html"))
                print(f"在 {html_dir} 中找到 {len(html_files)} 个HTML文件")
                for f in html_files:
                    print(f"  - {f.name}")
            else:
                html_files = list(report_dir.glob("**/*.html"))
                print(f"在整个report目录中找到 {len(html_files)} 个HTML文件")
            
            for file_path in html_files:
                try:
                    # 从文件名提取股票代码和时间戳
                    filename = file_path.name
                    stock_code = "未知"
                    timestamp = ""
                    
                    # 尝试从文件名中提取股票代码和时间戳
                    # 文件名格式: html_603887_20250808_165058.html
                    if "_" in filename:
                        parts = filename.replace(".html", "").split("_")
                        if len(parts) >= 4:  # html_603887_20250808_165058
                            # 提取股票代码 (第二部分)
                            if parts[1].isdigit() and len(parts[1]) == 6:
                                stock_code = parts[1]
                            # 提取时间戳 (第三和第四部分组合)
                            if len(parts) >= 4 and parts[2].isdigit() and parts[3].isdigit():
                                timestamp = f"{parts[2]}_{parts[3]}"
                    
                    # 获取文件修改时间
                    mtime = file_path.stat().st_mtime
                    date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 加载相关数据获取更准确的信息
                    report_data = load_report_data(stock_code, timestamp)
                    
                    # 从数据中提取摘要和建议
                    summary = "股票分析报告"
                    recommendation = "分析中"
                    
                    if report_data and "battle_results" in report_data:
                        battle_results = report_data["battle_results"]
                        final_decision = battle_results.get("final_decision", "")
                        vote_count = battle_results.get("vote_count", {})
                        
                        if final_decision == "bullish":
                            recommendation = "看涨"
                        elif final_decision == "bearish":
                            recommendation = "看跌"
                        
                        # 生成摘要
                        bullish_count = vote_count.get("bullish", 0)
                        bearish_count = vote_count.get("bearish", 0)
                        total_votes = bullish_count + bearish_count
                        
                        if total_votes > 0:
                            summary = f"专家投票: {bullish_count}票看涨, {bearish_count}票看跌"
                    
                    reports.append({
                        'stockCode': stock_code,
                        'date': date,
                        'path': str(file_path),
                        'summary': summary,
                        'recommendation': recommendation,
                        'filename': filename,
                        'timestamp': timestamp
                    })
                    
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
                    continue
            
            # 按修改时间排序，最新的在前面
            reports.sort(key=lambda x: x['date'], reverse=True)
        
        return JSONResponse({'reports': reports})
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

async def delete_report(request: Request):
    """删除报告及相关文件"""
    try:
        data = await request.json()
        report_path = data.get('path', '').strip()
        
        if not report_path:
            return JSONResponse({'success': False, 'error': '报告路径不能为空'})
        
        # 安全检查
        full_path = Path(report_path).resolve()
        project_root = Path(__file__).parent.parent.resolve()
        
        if not str(full_path).startswith(str(project_root)):
            return JSONResponse({'success': False, 'error': '无效的文件路径'})
        
        if not full_path.exists():
            return JSONResponse({'success': False, 'error': '报告文件不存在'})
        
        # 从文件名提取股票代码和时间戳
        filename = full_path.name
        stock_code = "unknown"
        timestamp = ""
        
        if "_" in filename:
            parts = filename.split("_")
            for part in parts:
                if part.isdigit() and len(part) == 6:
                    stock_code = part
                elif len(part) == 15 and part.isdigit():
                    timestamp = part
        
        deleted_files = []
        
        # 删除HTML文件
        if full_path.exists():
            full_path.unlink()
            deleted_files.append(str(full_path))
        
        # 删除对应的meta文件
        meta_path = full_path.with_suffix('.meta.json')
        if meta_path.exists():
            meta_path.unlink()
            deleted_files.append(str(meta_path))
        
        # 删除相关的debate文件
        debate_dir = Path("report/debate")
        if debate_dir.exists():
            debate_files = list(debate_dir.glob(f"debate_{stock_code}_{timestamp}.*"))
            for debate_file in debate_files:
                debate_file.unlink()
                deleted_files.append(str(debate_file))
        
        # 删除相关的vote文件
        vote_dir = Path("report/vote")
        if vote_dir.exists():
            vote_files = list(vote_dir.glob(f"vote_{stock_code}_{timestamp}.*"))
            for vote_file in vote_files:
                vote_file.unlink()
                deleted_files.append(str(vote_file))
        
        return JSONResponse({
            'success': True,
            'message': f'成功删除报告及相关文件',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)

async def get_debate_data(request: Request):
    """获取指定股票的辩论数据"""
    try:
        stock_code = request.path_params['stock_code']
        print(f"正在获取股票 {stock_code} 的辩论数据")
        
        if not stock_code:
            return JSONResponse({
                'success': False,
                'message': '缺少股票代码参数'
            })
        
        # 使用绝对路径查找辩论文件
        # 服务器在backend目录下运行，所以需要向上一级找到项目根目录
        current_dir = Path(__file__).parent  # backend目录
        project_root = current_dir.parent    # 项目根目录
        debate_dir = project_root / "report" / "debate"
        
        print(f"当前文件路径: {Path(__file__)}")
        print(f"当前目录: {current_dir}")
        print(f"项目根目录: {project_root}")
        print(f"辩论数据目录: {debate_dir}")
        print(f"辩论数据目录绝对路径: {debate_dir.resolve()}")
        print(f"目录是否存在: {debate_dir.exists()}")
        
        # 如果路径不存在，尝试其他可能的路径
        if not debate_dir.exists():
            # 尝试从当前工作目录查找
            alt_debate_dir = Path.cwd() / "report" / "debate"
            print(f"尝试备用路径: {alt_debate_dir}")
            print(f"备用路径是否存在: {alt_debate_dir.exists()}")
            
            if alt_debate_dir.exists():
                debate_dir = alt_debate_dir
            else:
                # 尝试从项目根目录的上级查找
                alt_debate_dir2 = Path.cwd().parent / "report" / "debate"
                print(f"尝试备用路径2: {alt_debate_dir2}")
                print(f"备用路径2是否存在: {alt_debate_dir2.exists()}")
                
                if alt_debate_dir2.exists():
                    debate_dir = alt_debate_dir2
        
        if not debate_dir.exists():
            return JSONResponse({
                'success': False,
                'message': f'辩论数据目录不存在: {debate_dir}'
            })
        
        # 查找匹配的辩论文件，只查找.json文件（不包括.meta.json）
        debate_files = []
        pattern = f'debate_{stock_code}_*.json'
        print(f"搜索模式: {pattern}")
        
        for file_path in debate_dir.glob(pattern):
            if file_path.is_file() and not file_path.name.endswith('.meta.json'):
                print(f"找到文件: {file_path}")
                # 提取时间戳
                try:
                    timestamp_part = file_path.name.replace(f'debate_{stock_code}_', '').replace('.json', '')
                    debate_files.append({
                        'filename': file_path.name,
                        'path': file_path,
                        'timestamp': timestamp_part,
                        'mtime': file_path.stat().st_mtime
                    })
                    print(f"成功解析文件: {file_path.name}, 时间戳: {timestamp_part}")
                except Exception as parse_error:
                    print(f"解析文件名失败: {file_path.name}, 错误: {parse_error}")
                    continue
        
        print(f"找到 {len(debate_files)} 个匹配的辩论文件")
        
        if not debate_files:
            # 列出目录中的所有文件用于调试
            all_files = list(debate_dir.glob("*"))
            print(f"目录中的所有文件: {[f.name for f in all_files]}")
            
            return JSONResponse({
                'success': False,
                'message': f'未找到股票 {stock_code} 的辩论数据。目录中有 {len(all_files)} 个文件。'
            })
        
        # 选择最新的文件
        latest_file = max(debate_files, key=lambda x: x['mtime'])
        print(f"选择最新文件: {latest_file['path']}")
        
        # 读取辩论数据
        try:
            with open(latest_file['path'], 'r', encoding='utf-8') as f:
                debate_data = json.load(f)
            print(f"成功读取辩论数据，数据键: {list(debate_data.keys())}")
        except Exception as read_error:
            print(f"读取文件失败: {read_error}")
            return JSONResponse({
                'success': False,
                'message': f'读取辩论数据文件失败: {str(read_error)}'
            })
        
        # 处理数据格式，确保包含必要字段
        processed_data = {
            'stock_code': stock_code,
            'timestamp': latest_file['timestamp'],
            'filename': latest_file['filename'],
            'agent_order': debate_data.get('agent_order', []),
            'debate_history': debate_data.get('debate_history', []),
            'battle_highlights': debate_data.get('battle_highlights', []),
            'vote_count': debate_data.get('vote_count', {}),
            'final_decision': debate_data.get('final_decision', ''),
            'debate_rounds': debate_data.get('debate_rounds', 1),
            'total_messages': len(debate_data.get('debate_history', [])),
            'participants': len(debate_data.get('agent_order', []))
        }
        
        print(f"成功处理辩论数据，包含 {processed_data['total_messages']} 条消息，{processed_data['participants']} 个参与者")
        
        return JSONResponse({
            'success': True,
            'data': processed_data
        })
        
    except Exception as e:
        error_msg = f'获取辩论数据失败: {str(e)}'
        print(error_msg)
        import traceback
        traceback.print_exc()
        return JSONResponse({
            'success': False,
            'message': error_msg
        })

async def get_report_data(request: Request):
    """获取外部化报告数据的API端点"""
    data_filename = request.path_params['data_path']
    
    try:
        print(f"API请求数据文件名: {data_filename}")
        
        # 构建完整路径 - 数据文件在report/html目录下
        project_root = Path(__file__).parent.parent
        data_path = project_root / "report" / "html" / data_filename
        full_path = data_path.resolve()
        
        print(f"构建的数据文件路径: {data_path}")
        print(f"解析后的完整路径: {full_path}")
        print(f"文件是否存在: {full_path.exists()}")
        
        # 安全检查：确保路径在项目目录内
        if not str(full_path).startswith(str(project_root.resolve())):
            print(f"路径安全检查失败: {full_path} 不在 {project_root.resolve()} 内")
            return JSONResponse({'error': '无效的文件路径'}, status_code=400)
        
        if not full_path.exists():
            print(f"文件不存在: {full_path}")
            # 列出目录中的文件用于调试
            html_dir = project_root / "report" / "html"
            if html_dir.exists():
                files = [f.name for f in html_dir.glob("*.json")]
                print(f"HTML目录中的JSON文件: {files}")
            return JSONResponse({'error': f'数据文件不存在: {data_filename}'}, status_code=404)
        
        # 读取JSON数据文件
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"成功加载数据文件，数据大小: {len(str(data))} 字符")
        return JSONResponse(data)
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return JSONResponse({'error': f'JSON格式错误: {str(e)}'}, status_code=400)
    except Exception as e:
        print(f"获取报告数据失败: {e}")
        return JSONResponse({'error': str(e)}, status_code=500)

# 自定义静态文件类，为JavaScript文件添加缓存控制
class NoCacheStaticFiles(StaticFiles):
    def file_response(self, full_path, stat_result, scope, status_code=200):
        response = FileResponse(full_path, status_code=status_code, stat_result=stat_result)
        if full_path.endswith('.js'):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

# 路由配置
routes = [
    Route('/api/analyze', start_analysis, methods=['POST']),
    Route('/api/stream/{session_id}', stream_output, methods=['GET']),
    Route('/api/report/{report_path:path}', get_report, methods=['GET']),
    Route('/api/download/{report_path:path}', download_report, methods=['GET']),
    Route('/api/view/{report_path:path}', view_report, methods=['GET']),
    Route('/api/reports', get_reports_list, methods=['GET']),
    Route('/api/reports/history', get_reports_list, methods=['GET']),
    Route('/api/reports/delete', delete_report, methods=['POST']),
    Route('/api/debate/{stock_code}', get_debate_data, methods=['GET']),
    Route('/api/report-data/{data_path:path}', get_report_data, methods=['GET']),
    # 聊天功能API
    Route('/api/chat/single', handle_single_chat, methods=['POST']),
    Route('/api/chat/group', handle_group_chat, methods=['POST']),
    Route('/api/chat/models', get_available_models, methods=['GET']),
    # 静态文件路由 - 报告文件
    Mount('/report', StaticFiles(directory=Path(__file__).parent.parent / 'report'), name='reports'),
    # 静态文件路由 - 前端文件（使用无缓存版本）
    Mount('/', NoCacheStaticFiles(directory=Path(__file__).parent.parent / 'frontend', html=True), name='static'),
]

# 中间件配置
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
]

# 创建应用
app = Starlette(debug=True, routes=routes, middleware=middleware)

if __name__ == '__main__':
    print("🚀 启动 FinGenius Web 服务器...")
    print("📊 访问地址: http://localhost:8000")
    print("🔧 API文档: http://localhost:8000/api/")
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        log_level='info'
    )
