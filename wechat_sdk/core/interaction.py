"""
交互策略模块

定义和控制与微信窗口的交互方式，支持后台、前台和自动模式。
这是SDK的核心组件之一，决定了操作微信时的窗口行为。

作者: CMX

主要类:
    InteractionPolicy: 交互策略管理器
    
交互模式说明:
    - background: 纯后台模式，不激活微信窗口
      * 优点：不打扰用户，可以并行工作
      * 缺点：某些操作可能失败（如剪贴板操作）
      
    - foreground: 纯前台模式，始终激活微信窗口
      * 优点：所有操作都能正常工作
      * 缺点：会打断用户，可见窗口切换
      
    - auto: 自动模式（推荐）
      * 优先尝试后台执行
      * 如果失败，自动切换到前台重试
      * 平衡了可靠性和用户体验

使用示例:
    >>> policy = InteractionPolicy(hwnd, mode="auto")
    >>> result = policy.run("send_text", lambda: send_action())
"""
from contextlib import contextmanager
from typing import Callable, TypeVar

from wechat_sdk.errors import InteractionError
from wechat_sdk.logging import logger

from .window import activate_window, current_foreground_hwnd


T = TypeVar("T")


class InteractionPolicy:
    """交互策略类，控制微信窗口的激活和交互方式
    
    该类封装了Windows窗口激活和焦点管理的逻辑，
    根据不同的模式决定何时激活微信窗口。
    
    设计目标:
        - 提供灵活的交互模式选择
        - 最小化对用户工作的干扰
        - 保证操作的可靠性
        - 优雅的错误恢复
        
    模式选择建议:
        - 开发测试：使用"foreground"便于观察
        - 生产环境：使用"auto"平衡可靠性和体验
        - 后台任务：使用"background"完全不打扰
        
    线程安全:
        - 窗口激活操作影响全局状态
        - 建议在单线程中使用，或确保互斥访问
        
    示例:
        >>> # 创建交互策略
        >>> policy = InteractionPolicy(hwnd, mode="auto")
        >>> 
        >>> # 执行需要前台的操作
        >>> result = policy.run(
        ...     "copy_text",
        ...     lambda: copy_action(),
        ...     foreground_required=True
        ... )
        >>> 
        >>> # 执行可以在后台的操作
        >>> data = policy.run("read_ui", lambda: read_action())
    """
    
    def __init__(self, hwnd: int, mode: str = "auto") -> None:
        """初始化交互策略
        
        Args:
            hwnd: 微信窗口句柄
                 用于激活和操作窗口
            mode: 交互模式，可选值：
                - "auto": 自动模式（默认），先后台后前台
                - "background": 纯后台模式，不激活窗口
                - "foreground": 纯前台模式，始终激活窗口
            
        Raises:
            ValueError: 当mode参数不是上述三个值之一时抛出
            
        示例:
            >>> policy = InteractionPolicy(123456, mode="auto")
            >>> print(policy.mode)  # 输出: auto
        """
        if mode not in {"auto", "background", "foreground"}:
            raise ValueError("mode must be one of: auto, background, foreground")
        self.hwnd = hwnd
        self.mode = mode

    @contextmanager
    def foreground(self):
        """上下文管理器：临时激活窗口并在完成后恢复之前的窗口
        
        这是一个Python上下文管理器，使用with语句确保窗口状态的恢复。
        
        工作流程:
            1. 记录当前活动窗口的句柄
            2. 激活微信窗口
            3. 执行with块中的代码
            4. 恢复之前活动的窗口（如果不是微信窗口）
            
        Yields:
            None: 在微信窗口激活状态下执行代码块
            
        异常处理:
            - 如果恢复原窗口失败，只记录日志不抛出异常
            - 避免掩盖原始异常
            
        使用示例:
            >>> policy = InteractionPolicy(hwnd)
            >>> with policy.foreground():
            ...     # 此时微信窗口处于前台
            ...     send_keys("Hello")
            ... # 退出with块后，恢复原窗口
        """
        # 保存当前活动窗口
        previous = current_foreground_hwnd()
        
        # 激活微信窗口
        activate_window(self.hwnd)
        
        try:
            # 执行用户代码
            yield
        finally:
            # 恢复之前的活动窗口
            # 条件检查：只在之前有窗口且不是微信本身时才恢复
            if previous and previous != self.hwnd:
                try:
                    activate_window(previous)
                except Exception:
                    # 恢复失败不影响主流程，只记录调试日志
                    logger.debug("Failed to restore previous foreground window", exc_info=True)

    def run(self, name: str, action: Callable[[], T], foreground_required: bool = False) -> T:
        """在指定交互策略下执行操作
        
        这是核心方法，根据当前模式和参数决定如何执行操作。
        
        Args:
            name: 操作名称，用于日志记录和错误提示
                 例如："send_text"、"copy_messages"
            action: 要执行的操作函数（无参数 callable）
                   应该返回操作结果
            foreground_required: 是否强制要求前台执行
                                某些操作（如剪贴板）必须在前台
            
        Returns:
            T: 操作的返回值，类型由action决定
            
        Raises:
            InteractionError: 当操作在所有尝试中都失败时抛出
            
        执行策略:
            1. foreground模式或foreground_required=True:
               - 激活窗口
               - 执行操作
               - 恢复窗口
               
            2. background模式:
               - 直接执行操作（不激活窗口）
               
            3. auto模式（最复杂）:
               - 先尝试后台执行
               - 如果失败，记录日志
               - 切换到前台重试
               - 如果再次失败，抛出InteractionError
               
        日志记录:
            - DEBUG级别：记录每次执行的开始
            - INFO级别：记录auto模式下的重试
            
        使用示例:
            >>> # 基本用法
            >>> result = policy.run("get_text", lambda: get_clipboard())
            >>> 
            >>> # 强制前台执行
            >>> data = policy.run(
            ...     "send_keys",
            ...     lambda: keyboard.type("Hello"),
            ...     foreground_required=True
            ... )
            >>> 
            >>> # 在WeChatClient中的典型用法
            >>> def _send_text_impl(self, context):
            ...     return self.interaction.run(
            ...         "message.send_text",
            ...         lambda: self._keyboard_send_text(context["text"]),
            ...         foreground_required=True
            ...     )
            
        错误处理建议:
            >>> try:
            ...     result = policy.run("complex_op", action)
            ... except InteractionError as e:
            ...     logger.error(f"操作失败: {e}")
            ...     # 降级处理或通知用户
        """
        logger.debug("Interaction run: name=%s mode=%s foreground_required=%s", 
                    name, self.mode, foreground_required)
        
        # 情况1：前台模式或要求前台执行
        if self.mode == "foreground" or foreground_required:
            with self.foreground():
                return action()

        # 情况2：后台模式
        if self.mode == "background":
            return action()

        # 情况3：自动模式（先后台，失败后前台重试）
        try:
            # 第一次尝试：后台执行
            return action()
        except Exception as exc:
            # 后台执行失败，记录日志
            logger.info("Background action failed for %s, retrying in foreground: %s", 
                       name, exc)
            
            # 第二次尝试：前台执行
            with self.foreground():
                try:
                    return action()
                except Exception as retry_exc:
                    # 两次都失败，抛出包装后的异常
                    raise InteractionError(f"Interaction failed for {name}") from retry_exc
