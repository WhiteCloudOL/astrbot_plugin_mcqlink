from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, StarTools
from astrbot.api import AstrBotConfig, logger
import astrbot.api.message_components as Comp
from .utils.server import WebSocketServer

class MCQLink(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        self.config = config
        self.context = context
        self.datapath = StarTools.get_data_dir("mcqlink")
        
        super().__init__(context)
        
        self.ws_server = None
        self.minecraft_bridge = None

    async def initialize(self):
        """异步初始化方法"""
        logger.info("MCQLink WebSocket 插件初始化中...")
        
        self.ws_server = WebSocketServer(
            context=self.context,
            config = self.config,
            host=self.config.get("server_ip", "0.0.0.0"),
            port=self.config.get("server_port", 6215),
            valid_token=self.config.get("token", "default-token")
        )
        
        await self.ws_server.run()
        logger.info("MCQLink WebSocket 插件已初始化")

    
    @filter.command("mcqlink")
    async def hello(self, event: AstrMessageEvent):
        """向MC服务器发送QQ消息"""
        group_id = event.get_group_id()
        user_id = event.get_sender_id()
        user_name = event.get_sender_name()
        message_all = event.get_message_str().split(' ',maxsplit=1)
        if len(message_all) == 2:
            message_str = message_all[1]
        else:
            yield event.plain_result("命令格式错误！正确用法:/mcqlink <消息>")
            return
        
        broadcast_msg = f"{user_name}: {message_str}"
        if self.ws_server:
            await self.ws_server.send_broadcast(broadcast_msg)
            yield event.plain_result(f"消息已发送到Minecraft服务器！")
        else:
            yield event.plain_result("WebSocket服务器未启动")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("mccmd")
    async def minecraft_command(self, event: AstrMessageEvent):
        """执行Minecraft命令(管理员命令)"""
        command_all = event.get_message_str().strip().split(' ',maxsplit=1)
        if len(command_all) == 2:
            command = command_all[1]
        else:
            yield event.plain_result("命令格式错误！正确用法:/mccmd <命令>")
            return
        if command:
            if self.ws_server:
                await self.ws_server.send_command_to_minecraft(command)
                yield event.plain_result(f"已发送Minecraft命令: {command}")
            else:
                yield event.plain_result("WebSocket服务器未启动")
        else:
            yield event.plain_result("命令格式错误！正确用法:/mccmd <命令>")

    async def terminate(self):
        """异步销毁方法"""
        if self.ws_server:
            await self.ws_server.stop_server()
        logger.info("MCQLink WebSocket 插件已停止")