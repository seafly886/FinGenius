import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import queue
import threading
import uuid
from starlette.responses import JSONResponse

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入配置和LLM相关模块
from src.config import config, LLMSettings
from src.llm import LLM
from src.schema import Message
from src.logger import logger

class ModelConfigManager:
    """模型配置管理器，用于获取和管理模型配置"""
    
    def __init__(self):
        self.available_models = self._get_available_models()
        self.has_only_default_config = self._check_has_only_default_config()
    
    def _get_available_models(self) -> Dict[str, LLMSettings]:
        """从配置中获取所有可用的模型"""
        models = {}
        
        # 获取默认配置
        if "default" in config.llm:
            models["default"] = config.llm["default"]
        
        # 获取其他模型配置
        for model_name, llm_config in config.llm.items():
            if model_name != "default":
                models[model_name] = llm_config
        
        return models
    
    def _check_has_only_default_config(self) -> bool:
        """检查是否只有默认配置可用"""
        # 如果只有一个配置（default），则返回True
        return len(self.available_models) == 1
    
    def get_model_config(self, model_name: str) -> Optional[LLMSettings]:
        """获取指定模型的配置"""
        # 如果只有一个默认配置，忽略传入的model_name，直接返回默认配置
        if self.has_only_default_config:
            return self.available_models.get("default")
        
        # 否则根据model_name返回对应的配置
        return self.available_models.get(model_name)
    
    def get_model_names(self) -> List[str]:
        """获取所有可用的模型名称"""
        # 如果只有一个默认配置，只返回["default"]
        if self.has_only_default_config:
            return ["default"]
        
        # 否则返回所有模型名称
        return list(self.available_models.keys())
    
    def get_model_info(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模型的详细信息"""
        model_info = {}
        for name, llm_config in self.available_models.items():
            model_info[name] = {
                "model": llm_config.model,
                "api_type": llm_config.api_type,
                "base_url": llm_config.base_url,
                "max_tokens": llm_config.max_tokens,
                "temperature": llm_config.temperature
            }
        return model_info
    
    def is_single_config_mode(self) -> bool:
        """检查是否为单一配置模式"""
        return self.has_only_default_config


class ChatSession:
    """聊天会话类"""
    def __init__(self, session_id: str, message: str, model_name: str = None, agents: List[str] = None):
        self.session_id = session_id
        self.message = message
        self.model_name = model_name or "default"  # 使用的模型名称
        self.agents = agents or []  # 群聊智能体列表
        self.process = None
        self.output_queue = queue.Queue()
        self.is_complete = False
        self.error = None
        self.responses = []
        self.model_manager = ModelConfigManager()
        
    async def start_chat(self):
        """启动聊天会话"""
        try:
            # 获取模型配置
            model_config = self.model_manager.get_model_config(self.model_name)
            if not model_config:
                self.error = f"未找到模型配置: {self.model_name}"
                self.output_queue.put(('error', {'message': self.error}))
                self.is_complete = True
                return
            
            # 创建LLM实例
            llm = LLM(config_name=self.model_name, llm_config=model_config)
            
            # 构建消息
            messages = [Message.user_message(self.message)]
            
            # 如果是群聊，添加系统消息
            if self.agents:
                agent_names = ", ".join(self.agents)
                system_message = f"你是一个专业的金融分析师，正在与以下专家进行讨论：{agent_names}。请以专业、准确的方式回答用户的问题。"
                messages.insert(0, Message.system_message(system_message))
            
            # 调用LLM API
            try:
                response = await llm.ask(messages=messages, stream=False)
                
                # 保存响应
                self.responses.append({
                    "model": self.model_name,
                    "response": response
                })
                
                # 输出响应
                self.output_queue.put(('output', json.dumps({
                    "type": "model_response",
                    "model": self.model_name,
                    "content": response
                }, ensure_ascii=False) + "\n"))
                
                self.output_queue.put(('complete', {'responses': self.responses}))
                
            except Exception as e:
                self.error = f"调用LLM API失败: {str(e)}"
                self.output_queue.put(('error', {'message': self.error}))
                
            self.is_complete = True
            
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
    """处理单个模型聊天"""
    try:
        data = await request.json()
        model_name = data.get('model', 'default').strip()
        message = data.get('message', '').strip()
        
        if not message:
            return JSONResponse({'success': False, 'error': '消息内容不能为空'})
        
        # 创建模型管理器并验证模型是否存在
        model_manager = ModelConfigManager()
        available_models = model_manager.get_model_names()
        
        if model_name not in available_models:
            return JSONResponse({
                'success': False,
                'error': f'模型不存在: {model_name}，可用模型: {", ".join(available_models)}'
            })
        
        # 创建新的聊天会话
        session_id = str(uuid.uuid4())
        session = ChatSession(session_id, message, model_name=model_name)
        active_chat_sessions[session_id] = session
        
        # 启动聊天
        await session.start_chat()
        
        # 等待聊天完成并获取结果
        while not session.is_complete:
            await asyncio.sleep(0.1)
        
        if session.error:
            return JSONResponse({'success': False, 'error': session.error})
        
        # 返回响应
        if session.responses:
            return JSONResponse({
                'success': True,
                'model': session.responses[0]['model'],
                'response': session.responses[0]['response']
            })
        else:
            return JSONResponse({'success': False, 'error': '未获取到响应'})
        
    except Exception as e:
        logger.error(f"单个聊天处理失败: {str(e)}")
        return JSONResponse({'success': False, 'error': str(e)})

async def handle_group_chat(request):
    """处理群聊（多模型讨论）"""
    try:
        data = await request.json()
        models = data.get('models', ['default'])
        message = data.get('message', '').strip()
        
        if not models or len(models) == 0:
            return JSONResponse({'success': False, 'error': '请选择至少一个模型'})
        
        if not message:
            return JSONResponse({'success': False, 'error': '消息内容不能为空'})
        
        # 创建模型管理器并验证模型是否存在
        model_manager = ModelConfigManager()
        available_models = model_manager.get_model_names()
        
        invalid_models = [m for m in models if m not in available_models]
        if invalid_models:
            return JSONResponse({
                'success': False,
                'error': f'以下模型不存在: {", ".join(invalid_models)}，可用模型: {", ".join(available_models)}'
            })
        
        # 为每个模型创建聊天会话并获取响应
        responses = []
        for model_name in models:
            try:
                session_id = str(uuid.uuid4())
                session = ChatSession(session_id, message, model_name=model_name)
                active_chat_sessions[session_id] = session
                
                # 启动聊天
                await session.start_chat()
                
                # 等待聊天完成并获取结果
                while not session.is_complete:
                    await asyncio.sleep(0.1)
                
                if session.error:
                    responses.append({
                        'model': model_name,
                        'response': f'错误: {session.error}',
                        'success': False
                    })
                elif session.responses:
                    responses.append({
                        'model': session.responses[0]['model'],
                        'response': session.responses[0]['response'],
                        'success': True
                    })
                else:
                    responses.append({
                        'model': model_name,
                        'response': '未获取到响应',
                        'success': False
                    })
                    
            except Exception as e:
                logger.error(f"模型 {model_name} 聊天失败: {str(e)}")
                responses.append({
                    'model': model_name,
                    'response': f'处理失败: {str(e)}',
                    'success': False
                })
        
        return JSONResponse({
            'success': True,
            'responses': responses
        })
        
    except Exception as e:
        logger.error(f"群聊处理失败: {str(e)}")
        return JSONResponse({'success': False, 'error': str(e)})


async def get_available_models(request):
    """获取所有可用的模型列表"""
    try:
        model_manager = ModelConfigManager()
        model_info = model_manager.get_model_info()
        
        return JSONResponse({
            'success': True,
            'models': model_info
        })
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return JSONResponse({'success': False, 'error': str(e)})