class FileService:
    """文件服务类，提供文件发送功能"""
    
    def __init__(self, client) -> None:
        """初始化文件服务
        
        Args:
            client: WeChatClient 实例
        """
        self.client = client

    def send(self, path_or_paths, who=None):
        """发送文件
        
        Args:
            path_or_paths: 文件路径或路径列表
            who: 接收者（联系人或群聊名称）
            
        Returns:
            发送结果
        """
        return self.client.send_file(path_or_paths, who=who)
