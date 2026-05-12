"""
WeChat_SDK 异常定义模块

定义SDK使用的所有自定义异常类，形成清晰的异常层次结构。
所有异常都继承自 WeChatSDKError，便于统一捕获和处理。

作者: CMX

异常层次:
    WeChatSDKError (基类)
    ├── WeChatWindowNotFoundError - 找不到微信窗口
    ├── UnsupportedWeChatVersionError - 不支持的微信版本
    ├── CapabilityNotSupportedError - 能力不被支持
    ├── CapabilityUnknownError - 能力未注册
    ├── ControlNotFoundError - UI控件找不到
    ├── ClipboardError - 剪贴板操作失败
    └── InteractionError - 交互操作失败

使用示例:
    >>> from wechat_sdk.errors import WeChatSDKError
    >>> try:
    ...     client = WeChatClient.auto()
    ... except WeChatSDKError as e:
    ...     print(f"初始化失败: {e}")
    
    # 或者捕获特定异常
    >>> from wechat_sdk.errors import WeChatWindowNotFoundError
    >>> try:
    ...     client = WeChatClient.auto()
    ... except WeChatWindowNotFoundError:
    ...     print("请先启动微信客户端")
"""


class WeChatSDKError(Exception):
    """WeChat_SDK 的基础异常类
    
    所有SDK抛出的异常都继承自此类。
    可以通过捕获此异常来处理所有SDK相关的错误。
    
    示例:
        >>> try:
        ...     # 任何SDK操作
        ... except WeChatSDKError as e:
        ...     logger.error(f"SDK错误: {e}")
    """
    pass


class WeChatWindowNotFoundError(WeChatSDKError):
    """找不到匹配的微信客户端窗口
    
    触发场景:
        - 微信未启动
        - 微信窗口被隐藏或最小化
        - 系统中没有运行微信进程
        
    解决方案:
        - 确保微信客户端已启动并登录
        - 检查任务管理器中是否有WeChat.exe进程
        - 尝试手动打开微信窗口
    """
    pass


class UnsupportedWeChatVersionError(WeChatSDKError):
    """检测到的微信版本不被任何配置文件支持
    
    触发场景:
        - 使用了过旧或过新的微信版本
        - 使用了非官方修改版微信
        - SDK尚未适配该版本
        
    支持的版本:
        - WeChat 3.9.x (wechat39 profile)
        - WeChat 4.x (wechat4 profile)
        
    解决方案:
        - 更新或降级到支持的版本
        - 查看README中的版本兼容性说明
        - 提交issue请求支持新版本
    """
    pass


class CapabilityNotSupportedError(WeChatSDKError):
    """当前客户端配置文件不支持请求的功能
    
    触发场景:
        - 在不支持的微信版本上使用某功能
        - 某些功能只在特定模式下可用
        
    示例:
        >>> try:
        ...     client.send_msg("Hello")
        ... except CapabilityNotSupportedError:
        ...     print("当前版本不支持发送消息")
        
    解决方案:
        - 检查capabilities.yaml中的支持情况
        - 升级到支持该功能的微信版本
        - 使用替代方案
    """
    pass


class CapabilityUnknownError(WeChatSDKError):
    """请求的功能未在能力注册表中注册
    
    触发场景:
        - 代码中引用了不存在的能力ID
        - capabilities.yaml配置有误
        
    这通常是开发错误，而非运行时错误。
    
    解决方案:
        - 检查能力ID拼写是否正确
        - 确认capabilities.yaml中已定义该能力
        - 联系SDK维护者
    """
    pass


class ControlNotFoundError(WeChatSDKError):
    """无法找到必需的UIAutomation控件
    
    触发场景:
        - 微信界面布局发生变化
        - UI元素ID或属性改变
        - 选择器配置不正确
        
    常见于:
        - 微信版本更新后
        - 切换语言设置后
        - 使用不同主题时
        
    解决方案:
        - 运行dump_uia_tree.py检查UI结构
        - 更新selectors.yaml配置
        - 调整选择器参数
    """
    pass


class ClipboardError(WeChatSDKError):
    """剪贴板操作失败
    
    触发场景:
        - 剪贴板被其他程序占用
        - 权限不足
        - 数据格式不支持
        
    影响的操作:
        - send_text (通过剪贴板粘贴文本)
        - send_file (通过剪贴板复制文件路径)
        
    解决方案:
        - 关闭可能占用剪贴板的程序
        - 尝试使用foreground模式
        - 检查Windows剪贴板服务是否正常
    """
    pass


class InteractionError(WeChatSDKError):
    """后台或前台交互操作失败
    
    触发场景:
        - 窗口激活失败
        - 键盘/鼠标模拟失败
        - UI元素不可见或不可用
        
    这是较通用的交互层异常，通常在auto模式重试后仍失败时抛出。
    
    解决方案:
        - 尝试使用foreground模式
        - 确保微信窗口可见且未被遮挡
        - 检查是否有管理员权限
        - 查看详细日志了解具体失败原因
    """
    pass
