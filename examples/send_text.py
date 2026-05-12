"""发送文本消息示例

此示例演示如何使用 WeChat_SDK 发送文本消息到指定联系人。

作者: CMX

使用场景:
    - 测试消息发送功能是否正常
    - 自动化发送通知或提醒
    - 批量消息发送脚本的基础模板

注意事项:
    - 确保微信客户端已登录并运行
    - 首次运行时可能需要手动授权窗口焦点
    - "文件传输助手"是微信内置的安全测试对象，建议优先使用
    
运行方式:
    uv run python examples/send_text.py
"""

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：发送测试文本消息到文件传输助手
    
    该函数演示了最基本的消息发送流程：
    1. 自动检测并连接微信客户端
    2. 发送一条测试消息到"文件传输助手"
    
    扩展用法:
        # 发送到指定联系人
        client.send_msg("你好！", who="张三")
        
        # 发送到当前聊天（需先切换）
        client.chat_with("李四")
        client.send_msg("当前聊天消息")
    """
    # 自动检测并创建微信客户端实例
    # mode参数可选: "auto"(默认), "background", "foreground"
    client = WeChatClient.auto(mode="auto")
    
    # 发送文本消息到文件传输助手
    # who参数指定接收者，可以是联系人名称或群组名称
    client.send_msg("WeChat_SDK text send test", who="文件传输助手")
    
    print("消息发送成功！")


if __name__ == "__main__":
    main()
