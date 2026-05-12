"""
WeChat_SDK 数据模型模块

定义SDK使用的核心数据结构，包括窗口信息和能力信息。
使用dataclass确保数据的不可变性和类型安全。

作者: CMX

主要类:
    WindowInfo: 微信窗口的完整信息
    CapabilityInfo: 功能能力的详细信息
    
常量:
    CALLBACK_STOP_SIGN: 回调停止标志，用于中断监听器循环

设计理念:
    - 不可变性：所有dataclass都是frozen的，防止意外修改
    - 类型提示：完整的类型注解，便于IDE支持
    - 简洁性：只包含必要字段，避免冗余
    
使用示例:
    >>> from wechat_sdk.params import WindowInfo
    >>> info = WindowInfo(
    ...     hwnd=123456,
    ...     title="微信",
    ...     class_name="WeChatMainWndForPC",
    ...     process_name="WeChat.exe",
    ...     exe_path="C:/Program Files/WeChat/WeChat.exe",
    ...     version="3.9.0.0",
    ...     visible=True,
    ...     profile_id="wechat39"
    ... )
    >>> print(info.title)  # 输出: 微信
"""
from dataclasses import dataclass
from typing import Any, Optional


# 回调函数停止标志
# 当回调函数返回此字符串时，监听器会停止轮询
# 用于动态控制监听器的生命周期
CALLBACK_STOP_SIGN = "__WECHAT_SDK_CALLBACK_STOP__"


@dataclass(frozen=True)
class WindowInfo:
    """微信窗口信息数据类
    
    封装Windows窗口的完整信息，用于窗口检测和选择。
    
    Attributes:
        hwnd: 窗口句柄（整数）
              Windows系统中窗口的唯一标识符
              用于API调用和窗口操作
              
        title: 窗口标题（字符串）
              显示在窗口标题栏的文本
              例如："微信"、"WeChat"
              
        class_name: 窗口类名（字符串）
                   Windows窗口类的名称
                   例如："WeChatMainWndForPC"
                   用于精确识别窗口类型
                   
        process_name: 进程名称（字符串）
                     创建窗口的进程名
                     例如："WeChat.exe"
                     
        exe_path: 可执行文件路径（字符串）
                 进程的完整路径
                 例如："C:/Program Files/Tencent/WeChat/WeChat.exe"
                 可用于版本检测
                 
        version: 微信版本号（可选字符串）
                例如："3.9.0.0"、"4.0.0.0"
                None表示无法检测版本
                
        visible: 窗口是否可见（布尔值）
                True: 窗口在屏幕上可见
                False: 窗口被隐藏或最小化
                
        profile_id: 配置文件ID（可选字符串）
                   匹配的配置档案名称
                   例如："wechat39"、"wechat4"
                   None表示未找到匹配的配置
    
    使用场景:
        - WeChatClient.auto() 返回检测到的窗口信息
        - 多开环境下选择合适的微信实例
        - 调试时查看窗口状态
        
    示例:
        >>> client = WeChatClient.auto()
        >>> info = client.window_info
        >>> print(f"检测到微信 {info.version}")
        >>> if not info.visible:
        ...     print("警告：微信窗口不可见")
        
    注意:
        - 对象是不可变的（frozen），创建后不能修改
        - 适合用作字典键或集合元素
        - 支持直接比较（基于所有字段）
    """
    hwnd: int
    title: str
    class_name: str
    process_name: str
    exe_path: str
    version: Optional[str]
    visible: bool
    profile_id: Optional[str] = None


@dataclass(frozen=True)
class CapabilityInfo:
    """功能能力信息数据类
    
    描述SDK中某个功能的详细配置和状态。
    
    Attributes:
        capability_id: 能力唯一标识符（字符串）
                      格式："{模块}.{功能}"
                      例如："message.send_text"、"session.list"
                      
        status: 支持状态（字符串）
               可能的值：
               - "supported": 完全支持
               - "unsupported": 不支持
               - "partial": 部分支持
               - "unknown": 未知状态
               
        default_mode: 默认交互模式（字符串）
                     可能的值：
                     - "auto": 自动模式（推荐）
                     - "background": 纯后台模式
                     - "foreground": 纯前台模式
                     
        pipeline: 关联的管道处理器（可选字符串）
                 如果设置，该能力通过PipelineRunner执行
                 None表示直接调用方法
                 
        metadata: 额外元数据（任意类型）
                 存储特定于能力的附加信息
                 默认为None
    
    使用场景:
        - 查询功能的支持情况
        - 生成能力支持矩阵文档
        - 运行时检查功能可用性
        
    示例:
        >>> cap = CapabilityInfo(
        ...     capability_id="message.send_text",
        ...     status="supported",
        ...     default_mode="auto",
        ...     pipeline="send_text"
        ... )
        >>> 
        >>> # 检查是否可用
        >>> if cap.status == "supported":
        ...     print("可以发送文本消息")
        >>> 
        >>> # 获取推荐模式
        >>> print(f"建议使用 {cap.default_mode} 模式")
        
    与Capability的区别:
        - Capability: 内部使用，包含更多技术细节
        - CapabilityInfo: 对外暴露，简化版信息
    """
    capability_id: str
    status: str
    default_mode: str
    pipeline: Optional[str] = None
    metadata: Any = None
