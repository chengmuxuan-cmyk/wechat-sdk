class MessageService:
    """消息服务类，提供消息发送和接收功能"""
    
    def __init__(self, client) -> None:
        """初始化消息服务
        
        Args:
            client: WeChatClient 实例
        """
        self.client = client

    def send_text(self, text: str, who=None, at=None):
        """发送文本消息
        
        Args:
            text: 要发送的文本内容
            who: 接收者（联系人或群聊名称）
            at: @某人（群聊中使用）
            
        Returns:
            发送结果
        """
        return self.client.send_msg(text, who=who, at=at)

    def get_all(self):
        """获取所有消息
        
        Returns:
            消息列表
        """
        return self.client.get_all_message()

    def get_next_new(self):
        return self.client.get_next_new_message()

    def get_new(self):
        return self.client.get_new_message()

    def get_all_new(self):
        return self.client.get_all_new_message()

    def get_unread(self, personal_only: bool = True, max_sessions=None):
        return self.client.get_unread_messages(personal_only=personal_only, max_sessions=max_sessions)

    def load_more(self, pages: int = 1):
        return self.client.load_more_message(pages=pages)

    def get_history(self, max_pages: int = 10, limit=None):
        return self.client.get_history(max_pages=max_pages, limit=limit)
