"""消息监听器示例

此示例演示如何使用 MessageListener 监听和响应微信消息。

作者: CMX

使用场景:
    - 自动回复机器人
    - 消息监控和日志记录
    - 关键词触发自动化任务
    - 客户服务自动应答系统

注意事项:
    - 此示例仅执行一次轮询（poll_once），用于测试
    - 长时间运行的应用应使用 listener.start() 启动后台监听线程
    - whitelist参数可限制只监听特定联系人，避免处理无关消息
    - 生产环境建议添加异常处理和日志记录
    
运行方式:
    uv run python examples/listener.py
    
扩展用法:
    # 启动持续监听（后台线程）
    listener.start(daemon=True)
    
    # 停止监听
    listener.stop()
    
    # 监听多个联系人
    listener = MessageListener(client, whitelist=["张三", "李四"])
    
    # 添加黑名单
    listener = MessageListener(client, blacklist=["广告群"])
"""

from wechat_sdk import MessageListener, WeChatClient


def main() -> None:
    """主函数：设置消息监听器并执行一次轮询
    
    该函数演示了消息监听器的基本用法：
    1. 创建微信客户端实例
    2. 配置监听器（设置白名单）
    3. 注册消息处理回调函数
    4. 执行一次消息轮询测试
    
    回调函数说明:
        - 通过 @listener.on_message 装饰器注册
        - 接收 MessageEvent 对象作为参数
        - event.chat_name: 消息来源的聊天名称
        - event.message: 消息对象，包含content等属性
        - event.received_at: 消息接收时间
        
    完整应用示例:
        def handle_message(event):
            # 业务逻辑：根据消息内容做出响应
            if "帮助" in event.message.content:
                event.client.send_msg("这里是帮助信息...", who=event.chat_name)
            elif "价格" in event.message.content:
                event.client.send_msg("产品价格详见官网", who=event.chat_name)
        
        listener = MessageListener(client)
        listener.on_message(handle_message)
        listener.start()  # 启动持续监听
    """
    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto()
    
    # 创建消息监听器，仅监听"文件传输助手"的消息
    # whitelist: 白名单列表，只处理这些联系人的消息
    # blacklist: 黑名单列表，忽略这些联系人的消息
    # interval: 轮询间隔（秒），默认1.0秒
    listener = MessageListener(client, whitelist=["文件传输助手"])

    # 注册消息处理回调函数
    @listener.on_message
    def handle_message(event):
        """处理接收到的消息
        
        Args:
            event: 消息事件对象，包含以下属性：
                - client: WeChatClient实例，可用于发送回复
                - chat_name: 消息来源的聊天名称（字符串）
                - message: 消息对象，包含content、sender等属性
                - received_at: 消息接收时间（datetime对象）
                - source: 消息来源类型（"poll"表示轮询获取）
        
        注意:
            - 回调函数中应避免耗时操作，以免阻塞后续消息处理
            - 如需发送回复，使用 event.client.send_msg()
            - 异常会自动被捕获并记录到日志
        """
        print(f"[{event.chat_name}] {event.message}")

    print("Polling once. Use listener.start() in long-running applications.")
    # 执行一次消息轮询（长时间运行应使用 listener.start()）
    # poll_once() 适合测试和调试，start() 适合生产环境
    listener.poll_once()


if __name__ == "__main__":
    main()
