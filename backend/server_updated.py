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
import asyncio
import queue
import threading

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
    """在浏览器中查看报告"""
    report_path = request.path_params['report_path']
    
    try:
        # 安全检查
        full_path = Path(report_path).resolve()
        project_root = Path(__file__).parent.parent.resolve()
        
        if not str(full_path).startswith(str(project_root)):
            return HTMLResponse('<h1>无效的文件路径</h1>', status_code=400)
        
        if not full_path.exists():
            return HTMLResponse('<h1>报告文件不存在</h1>', status_code=404)
        
        # 读取HTML文件并返回
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(content)
        
    except Exception as e:
        return HTMLResponse(f'<h1>错误: {str(e)}</h1>', status_code=500)

async def get_reports_list(request: Request):
    """获取历史报告列表"""
    try:
        reports = []
        report_dir = Path("report")
        
        if report_dir.exists():
            # 获取所有HTML文件
            html_files = list(report_dir.glob("*.html"))
            
            for file_path in html_files:
                try:
                    # 从文件名提取股票代码
                    filename = file_path.name
                    stock_code = "未知"
                    
                    # 尝试从文件名中提取股票代码
                    if "_" in filename:
                        parts = filename.split("_")
                        for part in parts:
                            if part.isdigit() and len(part) == 6:
                                stock_code = part
                                break
                    
                    # 获取文件修改时间
                    mtime = file_path.stat().st_mtime
                    date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 尝试读取文件内容获取摘要和建议
                    summary = "股票分析报告"
                    recommendation = "分析中"
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 简单提取一些关键信息
                            if "买入" in content:
                                recommendation = "买入"
                            elif "卖出" in content:
                                recommendation = "卖出"
                            elif "持有" in content:
                                recommendation = "持有"
                            
                            # 提取摘要（简化版本）
                            if "投资建议" in content:
                                summary = "包含投资建议的详细分析报告"
                    except:
                        pass
                    
                    reports.append({
                        'stockCode': stock_code,
                        'date': date,
                        'path': str(file_path),
                        'summary': summary,
                        'recommendation': recommendation,
                        'filename': filename
                    })
                    
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
                    continue
            
            # 按修改时间排序，最新的在前面
            reports.sort(key=lambda x: x['date'], reverse=True)
        
        return JSONResponse({'reports': reports})
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

# 路由配置
routes = [
    Route('/api/analyze', start_analysis, methods=['POST']),
    Route('/api/stream/{session_id}', stream_output, methods=['GET']),
    Route('/api/report/{report_path:path}', get_report, methods=['GET']),
    Route('/api/download/{report_path:path}', download_report, methods=['GET']),
    Route('/api/view/{report_path:path}', view_report, methods=['GET']),
    Route('/api/reports', get_reports_list, methods=['GET']),
    Mount('/', StaticFiles(directory='frontend', html=True), name='static'),
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
    print("📊 访问地址: http://localhost:8001")
    print("🔧 API文档: http://localhost:8001/api/")
    
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8001,
        log_level='info'
    )