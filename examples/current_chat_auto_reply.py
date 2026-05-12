"""当前聊天自动回复示例

此示例演示如何为当前打开的聊天窗口设置自动回复功能。

作者: CMX

使用场景:
    - 临时离开时的自动应答
    - 特定关键词触发回复
    - 测试自动回复逻辑
    - 短时间内的消息监控和响应

注意事项:
    - 仅对当前打开的聊天窗口生效
    - 首次轮询会建立消息基线，只有启动后收到的新消息才会触发回复
    - 适合短时间的自动化任务，长时间运行建议使用 listener.start()
    - 避免在群组中滥用自动回复，可能被视为骚扰
    
命令行参数:
    --reply: 必填，要发送的回复文本
    --contains: 可选，只有消息包含此文本时才回复
    --seconds: 运行时长（秒），默认60秒
    --interval: 轮询间隔（秒），默认1.0秒
    --once: 只回复一次后停止
    
运行方式:
    # 简单自动回复（持续60秒）
    uv run python examples/current_chat_auto_reply.py --reply "我现在不在，稍后回复"
    
    # 关键词触发回复
    uv run python examples/current_chat_auto_reply.py --reply "收到！" --contains "你好"
    
    # 只回复一次
    uv run python examples/current_chat_auto_reply.py --reply "OK" --once
    
    # 自定义运行时间和间隔
    uv run python examples/current_chat_auto_reply.py --reply "忙" --seconds 300 --interval 2.0
"""

from argparse import ArgumentParser
import time

from wechat_sdk import MessageListener, WeChatClient


def main() -> None:
    """主函数：在当前聊天窗口中执行自动回复
    
    该函数实现了一个简单的自动回复机器人：
    1. 解析命令行参数
    2. 获取当前聊天对象
    3. 创建消息监听器
    4. 注册消息处理回调（检查条件并发送回复）
    5. 在指定时间内持续轮询消息
    
    工作流程:
        - 启动时记录当前所有消息ID作为基线
        - 之后只处理新收到的消息
        - 如果设置了--contains参数，则检查消息是否包含关键词
        - 满足条件后发送回复，并根据--once参数决定是否继续监听
        
    扩展建议:
        - 生产环境应添加异常处理和日志记录
        - 可以扩展支持多条回复规则
        - 考虑添加回复频率限制，避免被检测为机器人
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Auto reply in the current WeChat chat.")
    parser.add_argument("--reply", required=True, help="Reply text to send.")
    parser.add_argument("--contains", default="", help="Only reply when message content contains this text.")
    parser.add_argument("--seconds", type=float, default=60.0, help="How long to keep polling.")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds.")
    parser.add_argument("--once", action="store_true", help="Stop after the first reply.")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 获取当前打开的聊天对象名称
    chat = client.current_chat()
    
    # 创建消息监听器，设置轮询间隔
    # 不设置whitelist，因为只关心当前聊天
    listener = MessageListener(client, interval=args.interval)
    
    # 用于跟踪是否已回复（配合--once参数使用）
    replied = {"done": False}

    # 注册消息处理回调函数
    @listener.on_message
    def handle_message(event):
        """处理接收到的消息并自动回复
        
        Args:
            event: 消息事件对象
            
        处理逻辑:
            1. 提取消息内容
            2. 如果设置了--contains参数，检查消息是否包含关键词
            3. 满足条件则发送回复
            4. 标记已回复状态
        """
        # 获取消息内容，兼容不同的消息类型
        content = getattr(event.message, "content", str(event.message))
        
        # 如果设置了关键词过滤，检查消息是否包含该关键词
        if args.contains and args.contains not in content:
            return  # 不满足条件，忽略此消息
        
        # 发送自动回复到当前聊天
        event.client.send_msg(args.reply, who=event.chat_name)
        
        # 标记已回复
        replied["done"] = True
        print(f"replied_to: {event.chat_name}")

    print(f"Auto replying in current chat: {chat}")
    print("The first poll builds the baseline. Only new messages after startup can trigger replies.")

    # 计算结束时间
    deadline = time.time() + args.seconds
    
    # 持续轮询直到超时或满足停止条件
    while time.time() < deadline:
        listener.poll_once()  # 执行一次消息轮询
        
        # 如果设置了--once且已回复过，则提前退出
        if args.once and replied["done"]:
            break
        
        # 等待下一个轮询周期
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
