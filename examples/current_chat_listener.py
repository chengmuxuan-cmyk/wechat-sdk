"""当前聊天消息监听示例

此示例演示如何监听当前打开的聊天窗口中的新消息。

作者: CMX

使用场景:
    - 实时监控特定聊天的新消息
    - 消息提醒和通知系统
    - 聊天记录实时采集
    - 关键词监控和告警
    - 自动化响应系统的基础
    
功能说明:
    - 连接到当前打开的聊天窗口
    - 持续轮询检测新消息
    - 实时打印接收到的消息内容
    - 支持自定义监听时长和轮询间隔
    
命令行参数:
    --seconds: 监听时长（秒），默认30秒
    --interval: 轮询间隔（秒），默认1.0秒
    
运行方式:
    # 先手动打开一个聊天窗口，然后运行：
    
    # 使用默认设置（监听30秒）
    uv run python examples/current_chat_listener.py
    
    # 自定义监听时长
    uv run python examples/current_chat_listener.py --seconds 60
    
    # 调整轮询频率（更频繁）
    uv run python examples/current_chat_listener.py --interval 0.5
    
    # 长时间监听
    uv run python examples/current_chat_listener.py --seconds 300 --interval 2.0

输出示例:
    Listening current chat: 张三
    The first poll builds the baseline. New messages after that will be printed.
    [张三] 你好
    [张三] 在吗？
    [张三] [图片]

注意事项:
    - 运行前需手动打开目标聊天窗口
    - 首次轮询会建立消息基线，只打印之后收到的新消息
    - 轮询间隔不宜过短，建议0.5-5秒
    - 长时间监听建议使用 listener.start() 后台线程模式
    
与listener.py的区别:
    - listener.py: 可以指定whitelist监听多个联系人
    - current_chat_listener.py: 只监听当前打开的单个聊天
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    listener = MessageListener(client, interval=1.0)
    
    @listener.on_message
    def handle(event):
        # 业务逻辑：保存、分析、转发等
        save_to_database(event)
        if "紧急" in event.message.content:
            send_alert(event)
    
    # 启动后台监听（推荐用于生产环境）
    listener.start(daemon=True)
    
    # 或者手动控制轮询
    while running:
        listener.poll_once()
        time.sleep(1)
"""

from argparse import ArgumentParser
import time

from wechat_sdk import MessageListener, WeChatClient


def main() -> None:
    """主函数：监听当前聊天的新消息
    
    该函数演示了如何实时监控单个聊天的消息：
    1. 解析命令行参数（时长和间隔）
    2. 创建微信客户端实例
    3. 获取当前聊天对象名称
    4. 创建消息监听器
    5. 注册消息处理回调（打印消息）
    6. 在指定时间内持续轮询
    
    工作流程:
        - 启动时执行第一次轮询，建立消息基线
        - 记录当前所有消息的ID
        - 之后的轮询只处理新出现的消息
        - 每条新消息都会触发回调函数
        
    轮询机制:
        - 每隔interval秒执行一次poll_once()
        - 每次轮询检查是否有新消息
        - 新消息通过回调函数处理
        - 循环直到达到设定的时长
        
    回调函数说明:
        - 通过@listener.on_message装饰器注册
        - 接收MessageEvent对象作为参数
        - event.chat_name: 聊天名称
        - event.message: 消息对象
        - 可以访问event.client发送回复
        
    实际应用:
        - 客服系统的实时消息接收
        - 重要联系人的消息提醒
        - 群聊关键词监控
        - 聊天数据实时采集和分析
        
    性能考虑:
        - 轮询间隔影响响应速度和CPU占用
        - 较短间隔（<1秒）会增加系统负载
        - 较长间隔（>5秒）会延迟消息接收
        - 建议根据实际需求平衡
        
    注意:
        - 运行前必须手动打开目标聊天窗口
        - 如果切换聊天，需要重新启动监听
        - 本示例使用时间控制的循环，生产环境建议用listener.start()
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Poll new messages from the current WeChat chat.")
    parser.add_argument("--seconds", type=float, default=30.0,
                       help="监听时长（秒），默认30秒")
    parser.add_argument("--interval", type=float, default=1.0,
                       help="轮询间隔（秒），默认1.0秒")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 获取当前打开的聊天对象名称
    # 如果未打开任何聊天，可能返回None
    chat = client.current_chat()
    
    # 创建消息监听器
    # interval参数控制轮询频率
    # 不设置whitelist，因为只关心当前聊天
    listener = MessageListener(client, interval=args.interval)

    # 注册消息处理回调函数
    @listener.on_message
    def handle_message(event):
        """处理接收到的新消息
        
        Args:
            event: 消息事件对象，包含：
                - chat_name: 聊天名称
                - message: 消息对象
                - received_at: 接收时间
                
        处理逻辑:
            1. 安全地提取消息内容
            2. 格式化打印消息
            3. 可以在此添加其他处理逻辑
            
        扩展建议:
            - 保存到数据库
            - 关键词检测和告警
            - 自动回复
            - 消息转发
        """
        # 安全地获取消息内容
        # 使用getattr提供默认值，防止属性不存在
        content = getattr(event.message, "content", str(event.message))
        
        # 格式化打印消息
        # 格式：[聊天名称] 消息内容
        print(f"[{event.chat_name}] {content}")

    # 打印提示信息
    print(f"Listening current chat: {chat}")
    print("The first poll builds the baseline. New messages after that will be printed.")

    # 计算结束时间
    deadline = time.time() + args.seconds
    
    # 持续轮询直到超时
    while time.time() < deadline:
        # 执行一次消息轮询
        # 这会检查是否有新消息并触发回调
        listener.poll_once()
        
        # 等待下一个轮询周期
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
