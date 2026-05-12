from wechat_sdk.errors import CapabilityNotSupportedError


class DialogService:
    """对话框服务类（待迁移）"""
    
    def __getattr__(self, name):
        """抛出功能未迁移异常
        
        Args:
            name: 属性名
            
        Raises:
            CapabilityNotSupportedError: 功能尚未迁移到新架构
        """
        raise CapabilityNotSupportedError(f"dialog.{name} is not migrated yet")
