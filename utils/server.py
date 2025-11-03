import asyncio
import json
from websockets.asyncio.server import serve
from astrbot.api import AstrBotConfig, logger
from websockets.exceptions import ConnectionClosedOK
from astrbot.api.event import MessageChain
from astrbot.api.star import Context, Star, StarTools


class WebSocketServer:
    def __init__(self, 
                 context: Context = None,
                 config: AstrBotConfig = None,
                 host="0.0.0.0", 
                 port=6215, 
                 valid_token="your-secret-token"
                 ):
        self.host = host
        self.port = port
        self.config = config
        self.valid_token = valid_token
        self.connected_clients = set()
        self.context = context
        self._server = None
        self._server_task = None

    
    async def authenticate(self, websocket):
        """
        验证客户端token
        """
        try:
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get("type") == "auth" and auth_data.get("token") == self.valid_token:
                await websocket.send(json.dumps({
                    "type": "auth_response",
                    "status": "success",
                    "message": "Authentication successful"
                }))
                self.connected_clients.add(websocket)
                logger.info(f"Client authenticated: {websocket.remote_address}")
                return True
            else:
                await websocket.send(json.dumps({
                    "type": "auth_response", 
                    "status": "error",
                    "message": "Invalid token"
                }))
                return False
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"身份验证失败: {e}")
            return False
    
    async def handler(self, websocket):
        """处理WebSocket连接"""
        logger.info(f"新的连接来自: {websocket.remote_address}")
        
        # 首先进行认证
        if not await self.authenticate(websocket):
            await websocket.close()
            return
        
        try:
            # 处理消息循环
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except ConnectionClosedOK:
            logger.info(f"连接正常关闭: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"连接失败: {e}")
        finally:
            # 清理连接
            if websocket in self.connected_clients:
                self.connected_clients.remove(websocket)
            logger.info(f"客户端连接断开: {websocket.remote_address}")
    
    async def handle_message(self, websocket, message):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            logger.info(f"收到消息: {data}")
            
            # 根据消息类型处理
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                # 响应ping
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                }))
            elif message_type == "echo":
                # 回声测试
                await websocket.send(json.dumps({
                    "type": "echo_response",
                    "content": data.get("content"),
                    "timestamp": data.get("timestamp")
                }))
            elif message_type == "minecraft_chat":
                # 处理来自Minecraft的聊天消息
                content = data.get("content", "")
                player = data.get("player", "Unknown")
                await self.handle_minecraft_message(player, content)
            elif message_type == "player_join":
                # 处理玩家加入消息
                player = data.get("player", "Unknown")
                await self.handle_player_join(player)
            elif message_type == "player_quit":
                # 处理玩家退出消息
                player = data.get("player", "Unknown")
                await self.handle_player_quit(player)
            else:
                await websocket.send(json.dumps({
                    "type": "message_response",
                    "status": "received",
                    "original_type": message_type
                }))
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
    
    async def send_to_qq(self, message: str):
        """将消息主动发送到QQ端"""
        if not message:
            logger.warning("收到空消息，取消发送")
            return
        session_list = self.config.get("enable_session")
        for session_str in session_list:
            logger.info(f"准备发送：{session_str},{message}")
            message_chain = MessageChain().message(message)
            await self.context.send_message(session_str, message_chain)
        
    async def handle_minecraft_message(self, player, content):
        """处理来自Minecraft的聊天消息"""
        if self.context:
            try:
                logger.info(f"收到MC服务器聊天消息 - 玩家: {player}, 内容: {content}")
                await self.send_to_qq(message=f"[服务器消息] {player}: {content}")
            except Exception as e:
                logger.error(f"处理MC聊天数据失败: {e}")
    
    async def handle_player_join(self, player):
        """处理玩家加入事件"""
        if self.context:
            try:
                logger.info(f"玩家加入了世界: {player}")
                await self.send_to_qq(message=f"[服务器消息] {player} 加入了服务器")
            except Exception as e:
                logger.error(f"处理玩家加入消息失败: {e}")
    
    async def handle_player_quit(self, player):
        """处理玩家退出事件"""
        if self.context:
            try:
                logger.info(f"玩家退出了世界: {player}")
                await self.send_to_qq(message=f"[服务器消息] {player} 退出了服务器")
            except Exception as e:
                logger.error(f"处理玩家退出消息失败: {e}")
    
    async def send_broadcast(self, message):
        """广播消息给所有已连接的客户端"""
        if not self.connected_clients:
            logger.warning("没有连接的客户端可用于广播")
            return
        disconnected = []
        broadcast_data = {
            "type": "broadcast",
            "content": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(broadcast_data))
                logger.info(f"广播消息发送到 {client.remote_address}")
            except Exception as e:
                logger.error(f"发送广播消息出错: {client.remote_address}: {e}")
                disconnected.append(client)
        
        # 清理断开连接的客户端
        for client in disconnected:
            self.connected_clients.remove(client)
            logger.info(f"移除了断开的客户端: {client.remote_address}")
    

    async def send_command_to_minecraft(self, command):
        """发送命令到Minecraft服务器"""
        if not self.connected_clients:
            logger.error("没有连接的MC服务器")
            return False
        
        command_data = {
            "type": "minecraft_command",
            "command": command,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        disconnected = []
        success = False
        
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(command_data))
                logger.info(f"指令发送到MC服务器: {command}")
                success = True
            except Exception as e:
                logger.error(f"发送指令出错： {client.remote_address}: {e}")
                disconnected.append(client)
        
        # 清理断开连接的客户端
        for client in disconnected:
            self.connected_clients.remove(client)
            logger.info(f"移除了断开的客户端: {client.remote_address}")
        
        return success
    
    async def start_server(self):
        """启动WebSocket服务器"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        self._server = await serve(self.handler, self.host, self.port)
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    async def stop_server(self):
        """停止WebSocket服务器"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")
        
        # 关闭所有客户端连接
        if self.connected_clients:
            for client in list(self.connected_clients):
                try:
                    await client.close()
                except Exception as e:
                    logger.error(f"Error closing client connection: {e}")
            self.connected_clients.clear()
            logger.info("所有客户端均已断开连接")
    
    async def run(self):
        """运行服务器"""
        await self.start_server()