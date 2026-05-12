from wechat_sdk.errors import CapabilityNotSupportedError


class GroupService:
    """群组服务类（待迁移）"""
    
    def __init__(self, client=None):
        self.client = client

    def get_members(self, max_pages: int = 50):
        if not self.client:
            raise CapabilityNotSupportedError("group.get_members requires a WeChatClient")
        return self.client.get_group_members(max_pages=max_pages)

    def __getattr__(self, name):
        """抛出功能未迁移异常
        
        Args:
            name: 属性名
            
        Raises:
            CapabilityNotSupportedError: 功能尚未迁移到新架构
        """
        raise CapabilityNotSupportedError(f"group.{name} is not migrated yet")
