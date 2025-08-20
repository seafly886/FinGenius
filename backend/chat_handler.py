import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import queue
import threading
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入智能体相关模块
from src.environment.research import ResearchEnvironment

class ChatSession:
    """聊天会话类"""
    def __init__(self, session_id: str, message: str, agent: str = None, agents: List[str] = None):
        self.session_id = session_id
        self.message = message
        self.agent = agent  # 单个智能体聊天
        self.agents = agents or []  # 群聊智能体列表
        self.process = None
        self.output_queue = queue.Queue()
        self.is_complete = False
        self.error = None
        self.responses = []
        
    async def start_chat(self):
        """启动聊天会话"""
        try:
            # 创建临时输入文件
            input_file = f"temp_chat_input_{self.session_id}.json"
            input_data = {
                "message": self.message,
                "agent": self.agent,
                "agents": self.agents
            }
            
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(input_data, f, ensure_ascii=False)
            
            # 构建命令
            cmd = [sys.executable, "chat_handler.py", input_file]
            
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
                cwd=str(project_root)
            )
            
            # 在后台线程中读取输出
            def read_output():
                try:
                    current_response = ""
                    current_agent = ""
                    
                    for line in iter(self.process.stdout.readline, ''):
                        if line:
                            # 尝试解析JSON格式的输出
                            try:
                                data = json.loads(line.strip())
                                if data.get("type") == "agent_response":
                                    # 保存当前智能体的响应
                                    if current_agent and current_response:
                                        self.responses.append({
                                            "agent": current_agent,
                                            "response": current_response
                                        })
                                    
                                    # 开始新的响应
                                    current_agent = data.get("agent")
                                    current_response = data.get("content", "")
                                elif data.get("type") == "response_chunk":
                                    # 继续当前响应
                                    current_response += data.get("content", "")
                            except json.JSONDecodeError:
                                # 如果不是JSON格式，直接添加到当前响应
                                current_response += line
                            
                            self.output_queue.put(('output', line))
                    
                    # 保存最后一个响应
                    if current_agent and current_response:
                        self.responses.append({
                            "agent": current_agent,
                            "response": current_response
                        })
                    
                    # 等待进程完成
                    return_code = self.process.wait()
                    
                    if return_code == 0:
                        self.output_queue.put(('complete', {'responses': self.responses}))
                    else:
                        self.output_queue.put(('error', {'message': f'聊天进程异常退出，返回码: {return_code}'}))
                    
                    self.is_complete = True
                    
                except Exception as e:
                    self.output_queue.put(('error', {'message': f'读取输出时发生错误: {str(e)}'}))
                    self.is_complete = True
                finally:
                    # 清理临时文件
                    try:
                        if os.path.exists(input_file):
                            os.remove(input_file)
                    except:
                        pass
            
            # 启动输出读取线程
            output_thread = threading.Thread(target=read_output)
            output_thread.daemon = True
            output_thread.start()
            
        except Exception as e:
            self.error = str(e)
            self.output_queue.put(('error', {'message': str(e)}))
            self.is_complete = True
    
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

# 全局聊天会话存储
active_chat_sessions: Dict[str, ChatSession] = {}

async def handle_single_chat(request):
    """处理单个智能体聊天"""
    try:
        data = await request.json()
        agent = data.get('agent', '').strip()
        message = data.get('message', '').strip()
        
        if not agent:
            return {'success': False, 'error': '请选择智能体'}
        
        if not message:
            return {'success': False, 'error': '消息内容不能为空'}
        
        # 创建新的聊天会话
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id, message, agent=agent)
        active_chat_sessions[session_id] = session
        
        # 启动聊天
        await session.start_chat()
        
        # 等待聊天完成并获取结果
        while not session.is_complete:
            await asyncio.sleep(0.1)
        
        if session.error:
            return {'success': False, 'error': session.error}
        
        # 返回第一个响应（单个智能体聊天只有一个响应）
        if session.responses:
            return {
                'success': True,
                'response': session.responses[0]['response']
            }
        else:
            return {'success': False, 'error': '未获取到响应'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def handle_group_chat(request):
    """处理群聊"""
    try:
        data = await request.json()
        agents = data.get('agents', [])
        message = data.get('message', '').strip()
        
        if not agents or len(agents) == 0:
            return {'success': False, 'error': '请选择至少一个智能体'}
        
        if not message:
            return {'success': False, 'error': '消息内容不能为空'}
        
        # 创建新的聊天会话
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id, message, agents=agents)
        active_chat_sessions[session_id] = session
        
        # 启动聊天
        await session.start_chat()
        
        # 等待聊天完成并获取结果
        while not session.is_complete:
            await asyncio.sleep(0.1)
        
        if session.error:
            return {'success': False, 'error': session.error}
        
        # 返回所有响应
        responses = []
        for resp in session.responses:
            responses.append({
                'agent': resp['agent'],
                'response': resp['response']
            })
        
        return {
            'success': True,
            'responses': responses
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}