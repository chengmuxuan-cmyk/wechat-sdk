"""会话列表示例

此示例演示如何获取并显示微信左侧的可见聊天会话列表。

作者: CMX

使用场景:
    - 查看当前有哪些聊天会话（个人+群组）
    - 验证特定联系人是否在会话列表中
    - 批量处理会话前的预检查
    - 监控新会话的出现
    
功能说明:
    - 读取微信左侧会话列表面板
    - 获取所有可见的会话名称
    - 按顺序编号输出
    
运行方式:
    uv run python examples/session_list.py

输出示例:
    1. 文件传输助手
    2. 张三
    3. 工作群
    4. 李四
    5. 家庭群
    ...

注意事项:
    - 只返回当前屏幕可见的会话（约10-20个）
    - 如需更多会话，需要滚动列表（SDK暂未提供此功能）
    - 会话顺序与微信界面显示一致（最近聊天的在上）
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    sessions = client.get_session_list()
    
    # 检查特定联系人是否在列表中
    if "张三" in sessions:
        print("张三在会话列表中")
    
    # 获取前5个会话
    top5 = sessions[:5]
    
    # 统计会话数量
    print(f"共有{len(sessions)}个会话")
"""

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：获取并打印会话列表
    
    该函数演示了如何读取会话列表：
    1. 创建微信客户端实例
    2. 调用get_session_list()获取会话
    3. 按序号格式化输出
    
    返回的会话包括:
        - 个人聊天（好友）
        - 群组聊天
        - 公众号（如果置顶）
        - 其他类型的会话
        
    实际应用:
        - 自动化脚本中选择目标会话
        - 监控重要联系人的在线状态
        - 批量消息发送前的名单确认
    """
    # 自动检测并创建微信客户端实例
    # mode="auto" 表示优先后台操作
    client = WeChatClient.auto(mode="auto")
    
    # 获取会话列表
    # 返回的是字符串列表，每个元素是会话名称
    sessions = client.get_session_list()
    
    # 遍历并打印每个会话，带序号
    # enumerate(start=1) 让序号从1开始
    for index, session in enumerate(sessions, start=1):
        print(f"{index}. {session}")


if __name__ == "__main__":
    main()
