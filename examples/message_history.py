"""聊天历史消息加载示例

此示例演示如何通过滚动加载当前聊天的历史消息记录。

作者: CMX

使用场景:
    - 导出完整的聊天记录
    - 分析长期聊天数据
    - 备份重要对话
    - 查找特定时间段的 message
    
功能说明:
    - 自动向上滚动聊天窗口
    - 逐页加载历史消息
    - 支持限制加载页数和消息数量
    - 按时间顺序输出消息
    
命令行参数:
    --pages: 加载页数，每页约10-20条消息，默认5页
    --limit: 最大返回消息数量，默认50条
    
运行方式:
    # 先手动打开一个聊天窗口，然后运行：
    
    # 加载默认设置（5页，最多50条）
    uv run python examples/message_history.py
    
    # 加载更多页数
    uv run python examples/message_history.py --pages 10
    
    # 限制消息数量
    uv run python examples/message_history.py --limit 100
    
    # 大量加载
    uv run python examples/message_history.py --pages 20 --limit 500

输出示例:
    message_count: 47
    1. 早上好
    2. 今天天气不错
    3. 是啊，适合出去走走
    ...

注意事项:
    - 运行前需手动打开目标聊天窗口
    - 加载大量消息需要较长时间（每页有延迟）
    - 微信可能对频繁滚动有限制
    - 非常久远的消息可能无法加载（微信服务器只保留一定时间）
    
性能提示:
    - 每页约加载10-20条消息
    - 总耗时 ≈ pages × 0.5秒
    - 建议先用小值测试，再逐步增加
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    
    # 加载所有可用历史（最多10页）
    all_history = client.get_history(max_pages=10)
    
    # 只获取最近的20条
    recent = client.get_history(max_pages=5, limit=20)
    
    # 保存ToFile
    with open("chat_history.txt", "w", encoding="utf-8") as f:
        for msg in all_history:
            f.write(f"{msg.sender}: {msg.content}\n")
"""

from argparse import ArgumentParser

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：加载并打印聊天历史消息
    
    该函数演示了如何批量加载历史消息：
    1. 解析命令行参数（页数和限制）
    2. 创建微信客户端实例
    3. 调用get_history()自动滚动加载
    4. 格式化输出消息列表
    
    加载过程:
        - 从当前可见消息开始
        - 向上滚动一页
        - 读取新出现的消息
        - 去重并添加到结果集
        - 重复直到达到max_pages或limit
        
    返回的消息特点:
        - 按时间顺序排列（旧到新）
        - 已自动去重
        - 包含所有类型的消息（文本、图片等）
        
    实际应用:
        - 聊天记录完整导出
        - 数据分析前的数据采集
        - 法律证据保全
        - 个人回忆整理
        
    注意:
        - 运行前需手动打开目标聊天窗口
        - 大量加载时保持微信窗口可见
        - 避免同时操作微信，可能干扰滚动
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Read current-chat history by scrolling upward.")
    parser.add_argument("--pages", type=int, default=5, 
                       help="加载页数，每页约10-20条消息，默认5页")
    parser.add_argument("--limit", type=int, default=50,
                       help="最大返回消息数量，默认50条")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 加载历史消息
    # max_pages: 控制滚动次数，防止无限循环
    # limit: 限制返回数量，节省内存和处理时间
    messages = client.get_history(max_pages=args.pages, limit=args.limit)
    
    # 输出消息总数
    print(f"message_count: {len(messages)}")
    
    # 遍历并打印每条消息
    # enumerate(start=1) 让序号从1开始
    for index, message in enumerate(messages, start=1):
        # 安全地获取消息内容
        content = getattr(message, "content", str(message))
        print(f"{index}. {content}")


if __name__ == "__main__":
    main()
