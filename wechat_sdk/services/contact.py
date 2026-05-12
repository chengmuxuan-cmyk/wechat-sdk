from wechat_sdk.errors import CapabilityNotSupportedError


class ContactService:
    """联系人服务类（待迁移）"""
    
    def __init__(self, client) -> None:
        self.client = client

    def get_all_friends(self, max_pages: int = 20):
        return self.client.get_all_friends(max_pages=max_pages)

    def search(self, keyword: str):
        return self.client.search_contact(keyword)

    def get_friend_details(self, who=None):
        return self.client.get_friend_details(who=who)

    def get_new_friends(self, max_pages: int = 5):
        return self.client.get_new_friends(max_pages=max_pages)

    def __getattr__(self, name):
        """抛出功能未迁移异常
        
        Args:
            name: 属性名
            
        Raises:
            CapabilityNotSupportedError: 功能尚未迁移到新架构
        """
        raise CapabilityNotSupportedError(f"contact.{name} is not migrated yet")
