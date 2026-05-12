"""未读个人聊天自动回复示例

此示例演示如何扫描未读会话列表并自动回复个人聊天。

作者: CMX

使用场景:
    - 批量处理积压的未读消息
    - 临时离开时的统一应答
    - 客户服务自动化
    - 多联系人同时监控和响应
    - 关键词触发的自动回复
    
功能说明:
    - 扫描左侧会话列表中的未读消息
    - 过滤出个人聊天（排除群组和公众号）
    - 对符合条件的消息发送自动回复
    - 支持关键词过滤和批量控制
    
命令行参数:
    --reply: 必填，要发送的回复文本
    --contains: 可选，只有消息包含此文本时才回复
    --seconds: 运行时长（秒），默认60秒
    --interval: 轮询间隔（秒），默认2.0秒
    --max-sessions: 每次轮询处理的最大会话数，默认5个
    --once: 只回复一批后停止
    
运行方式:
    # 简单自动回复（持续60秒）
    uv run python examples/unread_personal_auto_reply.py --reply "我现在不在，稍后回复"
    
    # 关键词触发回复
    uv run python examples/unread_personal_auto_reply.py \
        --reply "收到！" \
        --contains "你好"
    
    # 只处理一次未读消息
    uv run python examples/unread_personal_auto_reply.py \
        --reply "OK" \
        --once
    
    # 自定义参数
    uv run python examples/unread_personal_auto_reply.py \
        --reply "忙" \
        --seconds 300 \
        --interval 3.0 \
        --max-sessions 10

输出示例:
    Polling unread personal sessions. Group-like sessions are skipped by name heuristics.
    replied_to: 张三
    replied_to: 李四
    replied_to: 王五

注意事项:
    - 只处理个人聊天，自动跳过群组（通过名称启发式判断）
    - 首次轮询会建立基线，只回复启动后的新消息
    - 避免在重要对话中使用，可能显得不礼貌
    - 建议配合whitelist/blacklist使用更精确的控制
    
与current_chat_auto_reply的区别:
    - current_chat_auto_reply: 只监听当前打开的单个聊天
    - unread_personal_auto_reply: 扫描所有未读的个人聊天
    - 后者更适合批量处理和多联系人场景
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    listener = MessageListener(client, interval=2.0)
    
    @listener.on_message
    def handle(event):
        # 智能回复逻辑
        if "价格" in event.message.content:
            reply = "产品价格详见官网"
        elif "帮助" in event.message.content:
            reply = "客服工作时间：9:00-18:00"
        else:
            reply = "收到，稍后回复"
        
        event.client.send_msg(reply, who=event.chat_name)
    
    # 持续监听未读会话
    while True:
        listener.poll_unread_sessions(personal_only=True, max_sessions=5)
        time.sleep(2)
"""

from argparse import ArgumentParser
import time

from wechat_sdk import MessageListener, WeChatClient


def main() -> None:
    """主函数：自动回复未读个人聊天
    
    该函数实现了一个批量自动回复机器人：
    1. 解析命令行参数
    2. 创建微信客户端和监听器
    3. 注册消息处理回调（检查条件并回复）
    4. 持续轮询未读会话直到超时或满足条件
    
    工作流程:
        - 每隔interval秒执行一次poll_unread_sessions
        - 扫描会话列表，找出有未读消息的个人聊天
        - 读取这些聊天中的未读消息
        - 对每条消息执行过滤和回复
        - 统计回复数量
        
    过滤逻辑:
        1. personal_only=True: 只处理个人聊天
           - 排除名称包含"群"、"公众号"等的会话
        2. --contains参数: 如果设置，检查消息内容
           - 只有包含指定文本的消息才回复
        3. 去重机制: MessageListener内部维护已见消息ID
           - 同一条消息不会重复回复
        
    批处理控制:
        - max_sessions限制每次处理的会话数量
        - 防止一次性处理过多消息造成卡顿
        - 建议值：3-10个
        
    停止条件:
        1. 达到设定的运行时长（--seconds）
        2. 设置了--once且已回复过至少一条消息
        3. 用户手动中断（Ctrl+C）
        
    实际应用:
        - 下班后的统一应答
        - 会议期间的自动回复
        - 客服系统的初步响应
        - 多联系人消息监控
        
    性能考虑:
        - 轮询间隔建议2-5秒
        - max_sessions不宜过大，避免单次处理过久
        - 大量未读消息时可能需要较长时间
        
    注意:
        - 确保微信已登录且网络正常
        - 避免过于频繁的回复，可能被检测为机器人
        - 建议在测试环境充分验证后再用于生产
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Auto reply to unread personal WeChat sessions.")
    parser.add_argument("--reply", required=True, help="要发送的回复文本")
    parser.add_argument("--contains", default="", 
                       help="只有消息包含此文本时才回复（可选）")
    parser.add_argument("--seconds", type=float, default=60.0,
                       help="运行时长（秒），默认60秒")
    parser.add_argument("--interval", type=float, default=2.0,
                       help="轮询间隔（秒），默认2.0秒")
    parser.add_argument("--max-sessions", type=int, default=5,
                       help="每次轮询处理的最大会话数，默认5个")
    parser.add_argument("--once", action="store_true",
                       help="只回复一批后停止")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 创建消息监听器
    # 不设置whitelist，因为要处理所有未读个人聊天
    listener = MessageListener(client, interval=args.interval)
    
    # 用于统计回复数量
    replied = {"count": 0}

    # 注册消息处理回调函数
    @listener.on_message
    def handle_message(event):
        """处理接收到的消息并自动回复
        
        Args:
            event: 消息事件对象
            
        处理逻辑:
            1. 提取消息内容
            2. 如果设置了--contains，检查是否包含关键词
            3. 满足条件则发送回复
            4. 更新回复计数
        """
        # 获取消息内容
        content = getattr(event.message, "content", str(event.message))
        
        # 如果设置了关键词过滤，检查消息是否包含该关键词
        if args.contains and args.contains not in content:
            return  # 不满足条件，忽略此消息
        
        # 发送自动回复到对应的聊天
        event.client.send_msg(args.reply, who=event.chat_name)
        
        # 更新回复计数
        replied["count"] += 1
        print(f"replied_to: {event.chat_name}")

    print("Polling unread personal sessions. Group-like sessions are skipped by name heuristics.")
    
    # 计算结束时间
    deadline = time.time() + args.seconds
    
    # 持续轮询直到超时或满足停止条件
    while time.time() < deadline:
        # 轮询未读个人会话
        # personal_only=True: 只处理个人聊天
        # max_sessions: 限制每次处理的会话数量
        listener.poll_unread_sessions(personal_only=True, max_sessions=args.max_sessions)
        
        # 如果设置了--once且已回复过，则提前退出
        if args.once and replied["count"]:
            break
        
        # 等待下一个轮询周期
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
