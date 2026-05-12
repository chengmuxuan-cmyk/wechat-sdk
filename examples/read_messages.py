"""读取当前聊天消息示例

此示例演示如何读取当前打开的聊天窗口中的可见消息。

作者: CMX

使用场景:
    - 查看当前聊天的历史消息
    - 分析聊天内容和关键词
    - 消息备份和归档
    - 聊天数据分析
    
功能说明:
    - 获取当前打开的聊天对象名称
    - 读取聊天窗口中所有可见的消息
    - 按顺序输出消息内容
    
运行方式:
    # 先手动打开一个聊天窗口，然后运行：
    uv run python examples/read_messages.py

输出示例:
    chat: 张三
    message_count: 15
    1. 你好
    2. 在吗？
    3. 有个问题想请教
    4. [图片]
    5. 收到了，谢谢

注意事项:
    - 只能读取当前屏幕可见的消息（约10-30条）
    - 如需更多历史消息，使用load_more_message()加载
    - 消息顺序是从上到下（旧到新）
    - 非文本消息（图片、文件等）可能显示为占位符
    
扩展用法:
    # 加载更多历史消息
    client.load_more_message(pages=3)
    messages = client.get_all_message()
    
    # 获取特定数量的历史消息
    history = client.get_history(max_pages=5, limit=50)
    
    # 分析消息内容
    text_messages = [m for m in messages if m.type == "text"]
    keywords = extract_keywords([m.content for m in text_messages])
"""

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：读取并打印当前聊天的消息
    
    该函数演示了如何读取消息：
    1. 创建微信客户端实例
    2. 获取当前聊天对象名称
    3. 读取所有可见消息
    4. 格式化输出消息列表
    
    返回的消息对象包含:
        - sender: 发送者名称
        - content: 消息内容
        - type: 消息类型（text/image/file等）
        - id: 消息唯一标识
        
    实际应用:
        - 聊天记录分析和统计
        - 关键词提取和监控
        - 聊天数据导出
        - 自动化消息处理
        
    注意:
        - 运行前需手动打开一个聊天窗口
        - 如果未打开任何聊天，current_chat()可能返回None
    """
    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 获取当前打开的聊天对象名称
    # 如果未打开任何聊天，可能返回None
    chat = client.current_chat()
    
    # 读取当前聊天窗口中的所有可见消息
    # 只返回屏幕上能看到的消息（约10-30条）
    messages = client.get_all_message()
    
    # 输出聊天信息和消息数量
    print(f"chat: {chat}")
    print(f"message_count: {len(messages)}")
    
    # 遍历并打印每条消息的内容
    # enumerate(start=1) 让序号从1开始
    for index, message in enumerate(messages, start=1):
        # 安全地获取消息内容
        # 使用getattr提供默认值，防止属性不存在
        content = getattr(message, "content", str(message))
        print(f"{index}. {content}")


if __name__ == "__main__":
    main()
