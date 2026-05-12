class ChatService:
    """聊天服务类，提供聊天窗口操作功能"""
    
    def __init__(self, client) -> None:
        """初始化聊天服务
        
        Args:
            client: WeChatClient 实例
        """
        self.client = client

    def current(self):
        """获取当前聊天窗口的标题
        
        Returns:
            str: 当前聊天窗口标题
        """
        return self.client.current_chat()

    def get_session_list(self):
        return self.client.get_session_list()

    def get_sessions(self):
        return self.client.get_sessions()

    def get_unread_sessions(self, personal_only: bool = True, max_sessions=None):
        return self.client.get_unread_sessions(personal_only=personal_only, max_sessions=max_sessions)

    def switch_to_chat_tab(self):
        return self.client.switch_to_chat_tab()

    def switch_to_contact_tab(self):
        return self.client.switch_to_contact_tab()

    def chat_with(self, who: str):
        """切换到指定联系人或群聊的聊天窗口
        
        Args:
            who: 联系人或群聊名称
            
        Returns:
            操作结果
        """
        return self.client.chat_with(who)
