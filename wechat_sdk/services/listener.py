"""
消息监听服务模块

提供消息监听和事件处理功能，支持白名单/黑名单过滤、自定义谓词函数、
后台线程轮询等特性。是构建微信自动回复机器人、消息监控系统的基础组件。

作者: CMX

主要类:
    MessageEvent: 消息事件数据类，封装接收到的消息信息
    MessageListener: 消息监听器，用于监听和响应微信消息

使用示例:
    >>> from wechat_sdk import WeChatClient, MessageListener
    >>> client = WeChatClient.auto()
    >>> listener = MessageListener(client, whitelist=["张三"])
    >>> 
    >>> @listener.on_message
    ... def handle(event):
    ...     print(f"收到消息: {event.message.content}")
    >>> 
    >>> listener.start()  # 启动后台监听
"""
from dataclasses import dataclass
from datetime import datetime
import threading
import time
from typing import Callable, Iterable, Optional

from wechat_sdk.logging import logger


@dataclass(frozen=True)
class MessageEvent:
    """消息事件数据类，封装接收到的消息信息
    
    该类是不可变的（frozen），确保事件数据在传递过程中不会被修改。
    
    Attributes:
        client: WeChatClient实例，可用于发送回复消息
        chat_name: 聊天名称（联系人姓名或群组名称）
        message: 消息对象，包含content、sender、timestamp等属性
        received_at: 消息接收时间（datetime对象）
        source: 消息来源类型，默认为"poll"（轮询获取）
        
    使用示例:
        @listener.on_message
        def handle(event: MessageEvent):
            # 访问消息内容
            content = event.message.content
            
            # 发送回复
            event.client.send_msg("收到", who=event.chat_name)
            
            # 检查接收时间
            if event.received_at.hour < 8:
                print("清晨消息")
    """
    client: object  # 客户端实例
    chat_name: str  # 聊天名称
    message: object  # 消息对象
    received_at: datetime  # 接收时间
    source: str = "poll"  # 消息来源


class MessageListener:
    """消息监听器，用于监听和响应微信消息
    
    该类实现了基于轮询的消息监听机制，支持：
    - 白名单/黑名单过滤
    - 自定义过滤函数（predicate）
    - 可配置的轮询间隔
    - 后台线程持续监听
    - 消息去重（避免重复处理）
    - 错误处理和回调
    
    架构说明:
        - 采用观察者模式，通过回调函数处理消息
        - 内部维护已见消息ID集合，防止重复处理
        - 支持单线程轮询（poll_once）和多线程持续监听（start）
        - 所有异常都会被捕获并记录，不会导致监听器崩溃
        
    线程安全:
        - start()方法会创建后台线程执行轮询
        - 回调函数在后台线程中执行，注意线程安全问题
        - stop()方法会优雅地停止后台线程
        
    性能考虑:
        - interval参数控制轮询频率，建议1-5秒
        - max_seen限制内存中保留的消息ID数量，防止内存泄漏
        - 大量消息场景下建议设置合理的whitelist减少处理量
    
    示例:
        >>> client = WeChatClient.auto()
        >>> listener = MessageListener(
        ...     client,
        ...     whitelist=["张三", "李四"],
        ...     interval=2.0
        ... )
        >>> 
        >>> @listener.on_message
        ... def handle(event):
        ...     print(f"[{event.chat_name}] {event.message.content}")
        >>> 
        >>> listener.start()
        >>> # ... 运行一段时间后
        >>> listener.stop()
    """
    
    def __init__(
        self,
        client,
        whitelist: Optional[Iterable[str]] = None,
        blacklist: Optional[Iterable[str]] = None,
        predicate: Optional[Callable[[MessageEvent], bool]] = None,
        interval: float = 1.0,
        max_seen: int = 1000,
    ) -> None:
        """初始化消息监听器
        
        Args:
            client: WeChatClient实例，用于获取消息和发送回复
            whitelist: 白名单列表，只监听这些联系人/群聊的消息
                      如果为空，则监听所有联系人（除非在blacklist中）
            blacklist: 黑名单列表，不监听这些联系人/群聊的消息
                      即使它们在whitelist中也会被忽略
            predicate: 自定义过滤函数，接收MessageEvent参数，返回bool
                      只有返回True的消息才会被处理
                      可实现复杂的过滤逻辑（如关键词、时间范围等）
            interval: 轮询间隔（秒），默认1.0秒
                     建议值：1-5秒，过短会增加CPU占用，过长会延迟响应
            max_seen: 内存中保留的最大消息ID数量，默认1000
                     用于防止内存泄漏，超出后会移除最早的消息ID
            
        过滤优先级:
            1. whitelist检查（如果设置了）
            2. blacklist检查
            3. predicate函数检查
            只有全部通过的消息才会触发回调
            
        示例:
            # 基本用法
            listener = MessageListener(client)
            
            # 只监听特定联系人
            listener = MessageListener(client, whitelist=["张三", "李四"])
            
            # 排除某些群组
            listener = MessageListener(client, blacklist=["广告群", "测试群"])
            
            # 自定义过滤：只处理包含"紧急"的消息
            def urgent_only(event):
                return "紧急" in event.message.content
            listener = MessageListener(client, predicate=urgent_only)
            
            # 组合使用
            listener = MessageListener(
                client,
                whitelist=["张三", "工作群"],
                blacklist=["闲聊群"],
                interval=2.0,
                max_seen=500
            )
        """
        self.client = client
        self.whitelist = set(whitelist or [])  # 转换为set提高查找效率
        self.blacklist = set(blacklist or [])
        self.predicate = predicate
        self.interval = interval
        self.max_seen = max(0, max_seen)
        self._callbacks: list[Callable[[MessageEvent], None]] = []  # 消息处理回调列表
        self._error_callbacks: list[Callable[[Exception], None]] = []  # 错误处理回调列表
        self._seen: set[str] = set()  # 已处理的消息ID集合
        self._seen_order: list[str] = []  # 消息ID的顺序列表（用于FIFO淘汰）
        self._running = False  # 监听器运行状态标志
        self._thread: Optional[threading.Thread] = None  # 后台监听线程

    def on_message(self, callback: Callable[[MessageEvent], None]) -> Callable[[MessageEvent], None]:
        """注册消息处理回调函数
        
        使用装饰器语法注册消息处理器。可以注册多个回调函数，
        它们会按注册顺序依次执行。
        
        Args:
            callback: 消息处理函数，接收MessageEvent参数
                     函数中应避免耗时操作，以免阻塞后续消息处理
                     如需异步处理，建议在回调中启动新线程或使用队列
            
        Returns:
            注册的回调函数（便于链式调用）
            
        异常处理:
            回调函数中的异常会被自动捕获并记录到日志，
            不会导致监听器停止。可通过on_error注册错误处理器。
            
        示例:
            # 方式1：作为装饰器使用（推荐）
            @listener.on_message
            def handle_message(event):
                print(f"收到: {event.message.content}")
            
            # 方式2：直接注册
            def another_handler(event):
                log_message(event)
            listener.on_message(another_handler)
            
            # 多个回调
            @listener.on_message
            def handler1(event):
                save_to_database(event)
            
            @listener.on_message
            def handler2(event):
                send_notification(event)
        """
        self._callbacks.append(callback)
        return callback

    def on_error(self, callback: Callable[[Exception], None]) -> Callable[[Exception], None]:
        """注册错误处理回调函数
        
        当消息轮询或回调函数执行出错时，会调用此错误处理器。
        可用于记录错误日志、发送告警通知等。
        
        Args:
            callback: 错误处理函数，接收Exception参数
                     可用于记录错误、发送告警、恢复状态等
            
        Returns:
            注册的回调函数
            
        注意:
            - 错误处理器本身的异常会被忽略（防止无限循环）
            - 可以注册多个错误处理器
            - 错误不会中断监听器的运行
            
        示例:
            import logging
            
            logger = logging.getLogger(__name__)
            
            @listener.on_error
            def handle_error(exc):
                logger.error(f"监听器错误: {exc}", exc_info=True)
                # 可选：发送告警通知
                send_alert(f"WeChat监听异常: {exc}")
        """
        self._error_callbacks.append(callback)
        return callback

    def poll_once(self) -> list[MessageEvent]:
        """执行一次消息轮询
        
        从微信客户端获取新消息，触发相应的回调函数。
        这是同步方法，会阻塞直到完成本次轮询。
        
        Returns:
            list[MessageEvent]: 本次轮询处理的新消息事件列表
                               如果没有新消息或所有消息都被过滤，返回空列表
            
        工作流程:
            1. 调用client.get_next_new_message()获取新消息
            2. 对每条消息进行过滤（whitelist/blacklist/predicate）
            3. 检查消息是否已处理过（去重）
            4. 触发所有注册的回调函数
            5. 记录消息ID到已见集合
            
        适用场景:
            - 测试和调试
            - 集成到其他事件循环中
            - 需要精确控制轮询时机
            - 单次消息检查
            
        示例:
            # 手动轮询
            events = listener.poll_once()
            print(f"处理了{len(events)}条消息")
            
            # 在自定义循环中使用
            while running:
                events = listener.poll_once()
                process_events(events)
                time.sleep(1)
        """
        payload = self.client.get_next_new_message()
        return self._emit_payload(payload)

    def poll_unread_sessions(self, personal_only: bool = True, max_sessions: Optional[int] = None) -> list[MessageEvent]:
        """轮询未读会话的消息
        
        专门处理有未读消息的会话，适合批量处理积压消息的场景。
        
        Args:
            personal_only: 是否只处理个人聊天，默认为True
            max_sessions: 最大处理的会话数量，None表示不限制
            
        Returns:
            list[MessageEvent]: 处理的消息事件列表
            
        与poll_once的区别:
            - poll_once: 只检查当前打开的聊天窗口
            - poll_unread_sessions: 扫描所有未读会话并读取其消息
            
        示例:
            # 处理所有未读个人消息
            events = listener.poll_unread_sessions()
            
            # 处理前5个未读会话（包括群组）
            events = listener.poll_unread_sessions(
                personal_only=False,
                max_sessions=5
            )
        """
        payload = self.client.get_unread_messages(personal_only=personal_only, max_sessions=max_sessions)
        return self._emit_payload(payload)

    def _emit_payload(self, payload) -> list[MessageEvent]:
        """处理消息负载并触发回调
        
        内部方法，负责将原始消息数据转换为MessageEvent对象，
        执行过滤、去重，并触发回调函数。
        
        Args:
            payload: 消息负载字典，格式为 {chat_name: [messages]}
            
        Returns:
            list[MessageEvent]: 实际处理的消息事件列表
            
        处理流程:
            1. 遍历payload中的每个聊天和消息
            2. 创建MessageEvent对象
            3. 执行_accept()检查是否接受该消息
            4. 生成消息ID并检查是否已处理
            5. 记录消息ID到已见集合
            6. 依次调用所有回调函数
            7. 捕获并处理回调中的异常
        """
        events = []
        if not payload:
            return events
        for chat_name, messages in payload.items():
            for message in messages:
                # 创建消息事件对象
                event = MessageEvent(
                    client=self.client,
                    chat_name=chat_name,
                    message=message,
                    received_at=datetime.now(),
                )
                
                # 检查是否接受该消息（白名单/黑名单/predicate）
                if not self._accept(event):
                    continue
                
                # 生成消息唯一标识
                event_id = self._event_id(event)
                
                # 检查是否已处理过（去重）
                if event_id in self._seen:
                    continue
                
                # 记录到已见集合
                self._remember(event_id)
                
                # 添加到事件列表
                events.append(event)
                
                # 触发所有回调函数
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception as exc:
                        logger.exception("Message callback failed")
                        self._emit_error(exc)
        return events

    def start(self, daemon: bool = True) -> None:
        """启动消息监听器
        
        创建后台线程，持续执行消息轮询。这是一个非阻塞方法，
        调用后立即返回，监听在后台运行。
        
        Args:
            daemon: 是否以守护线程运行，默认为True
                   守护线程会在主程序退出时自动终止
                   如果设为False，需要显式调用stop()才能退出
            
        线程特性:
            - 后台线程会持续调用poll_once()进行轮询
            - 每次轮询后等待interval秒
            - 异常不会导致线程终止，会被记录并继续运行
            - 调用stop()可优雅地停止线程
            
        注意事项:
            - 确保在主程序中保持运行，否则守护线程会随主程序退出
            - 回调函数在后台线程中执行，注意线程安全问题
            - 不要在同一监听器上多次调用start()
            
        示例:
            # 启动守护线程（推荐）
            listener.start(daemon=True)
            # 主程序可以继续执行其他任务
            do_other_work()
            # 程序退出时线程自动终止
            
            # 启动非守护线程
            listener.start(daemon=False)
            try:
                time.sleep(3600)  # 运行1小时
            finally:
                listener.stop()  # 必须显式停止
        """
        if self._running:
            return  # 已在运行，避免重复启动
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=daemon)
        self._thread.start()

    def stop(self) -> None:
        """停止消息监听器
        
        优雅地停止后台监听线程。会等待当前正在执行的轮询完成，
        然后终止线程。
        
        注意:
            - 如果线程未在运行，此方法无效果
            - 最多等待interval+1秒，超时后强制返回
            - 停止后可以再次调用start()重新启动
            
        示例:
            listener.start()
            try:
                time.sleep(60)  # 运行1分钟
            finally:
                listener.stop()  # 确保停止
        """
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval + 1)

    def _loop(self) -> None:
        """消息轮询循环
        
        后台线程的主循环，持续执行消息轮询直到被停止。
        这是内部方法，不应直接调用。
        
        循环逻辑:
            1. 检查_running标志，如果为False则退出循环
            2. 执行poll_once()获取新消息
            3. 如果发生异常，记录错误并继续
            4. 等待interval秒后进入下一轮
            
        异常处理:
            - poll_once()中的异常会被捕获
            - 触发错误回调（如果注册了）
            - 记录异常到日志
            - 继续下一轮轮询（不会退出）
        """
        while self._running:
            try:
                self.poll_once()
            except Exception as exc:
                logger.exception("Listener polling failed")
                self._emit_error(exc)
            time.sleep(self.interval)

    def _accept(self, event: MessageEvent) -> bool:
        """判断是否接受该消息事件
        
        根据白名单、黑名单和自定义谓词函数决定消息是否应该被处理。
        
        Args:
            event: 消息事件对象
            
        Returns:
            bool: True表示接受该消息，False表示忽略
            
        过滤逻辑（按顺序）:
            1. 如果设置了whitelist且chat_name不在其中 → 拒绝
            2. 如果chat_name在blacklist中 → 拒绝
            3. 如果设置了predicate且返回False → 拒绝
            4. 以上都通过 → 接受
            
        示例:
            # whitelist示例
            listener = MessageListener(client, whitelist=["张三"])
            # 只有"张三"的消息会被接受
            
            # blacklist示例
            listener = MessageListener(client, blacklist=["广告群"])
            # "广告群"的消息会被拒绝
            
            # predicate示例
            def daytime_only(event):
                return 8 <= event.received_at.hour <= 22
            listener = MessageListener(client, predicate=daytime_only)
            # 只在白天8-22点接受消息
        """
        if self.whitelist and event.chat_name not in self.whitelist:
            return False
        if event.chat_name in self.blacklist:
            return False
        if self.predicate and not self.predicate(event):
            return False
        return True

    def _emit_error(self, exc: Exception) -> None:
        """触发错误处理回调
        
        当发生错误时，依次调用所有注册的错误处理器。
        
        Args:
            exc: 异常对象
            
        注意:
            - 错误处理器本身的异常会被忽略（防止无限循环）
            - 所有错误处理器都会被调用，不会因为某个失败而中断
        """
        for callback in self._error_callbacks:
            try:
                callback(exc)
            except Exception:
                logger.exception("Listener error callback failed")

    def _remember(self, event_id: str) -> None:
        """记录消息ID到已见集合
        
        将消息ID添加到已见集合和顺序列表中，用于去重。
        如果超出max_seen限制，会移除最早的消息ID。
        
        Args:
            event_id: 消息的唯一标识字符串
            
        实现细节:
            - _seen: set类型，用于快速查找（O(1)）
            - _seen_order: list类型，保持插入顺序
            - 当超过max_seen时，从头部移除最旧的ID
            - 这种设计平衡了查找性能和内存控制
        """
        self._seen.add(event_id)
        self._seen_order.append(event_id)
        # 如果超出限制，移除最早的消息ID
        while len(self._seen_order) > self.max_seen:
            expired = self._seen_order.pop(0)
            self._seen.discard(expired)

    @staticmethod
    def _event_id(event: MessageEvent) -> str:
        """生成消息事件的唯一标识
        
        用于消息去重，确保同一条消息不会被重复处理。
        
        Args:
            event: 消息事件对象
            
        Returns:
            str: 消息的唯一标识字符串，格式为 "{chat_name}:{message_id}"
            
        生成策略:
            - 优先使用消息对象的id属性
            - 如果没有id，使用消息对象的repr()
            - 结合chat_name确保不同聊天中的相同消息ID不会冲突
            
        示例:
            # 有id的消息
            _event_id(event) -> "张三:msg_12345"
            
            # 没有id的消息
            _event_id(event) -> "李四:Message(content='hello', ...)"
        """
        message_id = getattr(event.message, "id", None)
        if message_id:
            return f"{event.chat_name}:{message_id}"
        return f"{event.chat_name}:{repr(event.message)}"
