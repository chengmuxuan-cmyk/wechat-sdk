"""未读会话查询示例

此示例演示如何获取并显示有未读消息的个人聊天会话。

作者: CMX

使用场景:
    - 快速查看有哪些联系人发送了未读消息
    - 监控重要联系人的消息状态
    - 自动化消息提醒系统的基础
    - 批量处理未读消息前的预检查

功能说明:
    - 扫描微信左侧会话列表
    - 筛选出有未读消息的会话
    - 可选择只查看个人聊天（排除群组和公众号）
    - 显示每个会话的未读数量和免打扰状态
    
命令行参数:
    --max-sessions: 最大显示的会话数量，默认10个
    
运行方式:
    # 查看前10个未读个人会话
    uv run python examples/unread_sessions.py
    
    # 查看所有未读会话（不限制数量）
    uv run python examples/unread_sessions.py --max-sessions 100
    
    # 只查看前3个
    uv run python examples/unread_sessions.py --max-sessions 3

输出示例:
    unread_session_count: 5
    1. 张三 unread=3 muted=False
    2. 李四 unread=1 muted=False
    3. 工作群 unread=15 muted=True
    ...

扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    
    # 获取所有未读会话（包括群组）
    all_unread = client.get_unread_sessions(personal_only=False)
    
    # 获取未读消息内容
    unread_messages = client.get_unread_messages(max_sessions=5)
    for chat, messages in unread_messages.items():
        print(f"{chat}: {len(messages)}条新消息")
"""

from argparse import ArgumentParser

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：读取并显示未读个人会话列表
    
    该函数演示了如何查询未读会话：
    1. 解析命令行参数
    2. 创建微信客户端实例
    3. 调用get_unread_sessions获取未读会话
    4. 格式化输出会话信息
    
    返回的会话信息包含:
        - name: 会话名称（联系人或群组名）
        - unread_count: 未读消息数量
        - muted: 是否开启了"消息免打扰"
        - preview: 最后一条消息预览（可选字段）
        
    实际应用建议:
        - 可以结合get_unread_messages()读取具体消息内容
        - 对重要联系人设置优先级提醒
        - 定期轮询实现消息监控
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Read unread personal sessions from WeChat session list.")
    parser.add_argument("--max-sessions", type=int, default=10, 
                       help="最大显示的会话数量，默认10个")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 获取未读会话列表
    # personal_only=True: 只返回个人聊天，排除群组和公众号
    # max_sessions: 限制返回的最大会话数量
    sessions = client.get_unread_sessions(personal_only=True, max_sessions=args.max_sessions)
    
    # 输出统计信息
    print(f"unread_session_count: {len(sessions)}")
    
    # 遍历并显示每个未读会话的详细信息
    for index, session in enumerate(sessions, start=1):
        print(f"{index}. {session['name']} "
              f"unread={session['unread_count']} "
              f"muted={session['muted']}")


if __name__ == "__main__":
    main()
