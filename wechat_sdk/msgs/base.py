"""
消息基础模块

定义微信消息的基础数据结构和通用接口。
所有具体消息类型（文本、图片、文件等）都基于此模块扩展。

作者: CMX

主要类:
    Message: 消息基类，包含发送者、内容、类型等基本信息
    
使用示例:
    >>> msg = Message(sender="张三", content="你好", type="text")
    >>> print(f"{msg.sender}: {msg.content}")
    >>> print(f"消息ID: {msg.id}")
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """消息基类
    
    表示从微信接收到的一条消息，包含基本的消息属性。
    这是一个数据类（dataclass），主要用于存储和传递消息数据。
    
    Attributes:
        sender: 消息发送者名称
               - 个人聊天：联系人姓名
               - 群组聊天：群成员昵称
               - 系统消息：可能为空字符串
               
        content: 消息内容
                - 文本消息：文本字符串
                - 其他类型：可能是描述性文本或占位符
                
        type: 消息类型标识，默认为"text"
             常见类型：
             - "text": 文本消息
             - "image": 图片消息
             - "file": 文件消息
             - "video": 视频消息
             - "voice": 语音消息
             - "quote": 引用消息
             - "time": 时间戳消息
             
        raw: 原始数据字典，包含底层获取的详细信息
            不同来源的消息可能有不同的raw结构：
            - UIA来源：包含runtime_id、control信息等
            - Clipboard来源：包含source、line等
            
    Properties:
        id: 消息的唯一标识符，用于去重和追踪
            生成策略：
            1. 如果raw中有runtime_id，使用"uia:{runtime_id}"
            2. 如果raw中有source和line，使用"{source}:{line}:{content}"
            3. 否则使用"{sender}:{type}:{content}"
            
    使用场景:
        - 消息监听器中接收到的消息对象
        - 历史消息查询的返回结果
        - 消息过滤和处理的数据载体
        
    示例:
        # 创建消息对象
        msg = Message(
            sender="张三",
            content="Hello World",
            type="text"
        )
        
        # 访问消息属性
        print(f"来自: {msg.sender}")
        print(f"内容: {msg.content}")
        print(f"类型: {msg.type}")
        print(f"ID: {msg.id}")
        
        # 在回调中使用
        @listener.on_message
        def handle(event):
            msg = event.message
            if msg.type == "text" and "帮助" in msg.content:
                event.client.send_msg("这里是帮助信息", who=event.chat_name)
    """
    sender: str      # 消息发送者
    content: str     # 消息内容
    type: str = "text"  # 消息类型，默认文本
    raw: Any = None     # 原始数据

    @property
    def id(self) -> str:
        """获取消息的唯一标识符
        
        根据可用信息生成消息ID，用于去重和追踪。
        
        Returns:
            str: 消息ID字符串
            
        ID生成优先级:
            1. UIA runtime_id（最可靠）
            2. source + line + content组合
            3. sender + type + content组合（兜底方案）
            
        注意:
            - ID的稳定性取决于raw数据的完整性
            - 不同来源的消息ID格式可能不同
            - 仅用于短时间内的去重，不适合长期存储引用
        """
        if isinstance(self.raw, dict):
            # 尝试使用UIA runtime_id
            runtime_id = self.raw.get("runtime_id")
            if runtime_id:
                return f"uia:{runtime_id!r}"
            
            # 尝试使用clipboard来源信息
            if "source" in self.raw and "line" in self.raw:
                return f"{self.raw['source']}:{self.raw['line']}:{self.content}"
        
        # 兜底方案：基于内容生成
        return f"{self.sender}:{self.type}:{self.content}"
