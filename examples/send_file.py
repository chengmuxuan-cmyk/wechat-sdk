"""发送文件示例

此示例演示如何使用 WeChat_SDK 发送文件到指定联系人。

作者: CMX

使用场景:
    - 自动发送文档、图片、压缩包等文件
    - 批量文件传输任务
    - 工作流自动化（如生成报告后自动发送）
    - 文件备份和同步

支持的文件类型:
    - 图片：JPG, PNG, GIF, BMP等
    - 文档：PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX等
    - 压缩包：ZIP, RAR, 7Z等
    - 其他：TXT, CSV, JSON等任意文件类型

注意事项:
    - 文件路径必须是绝对路径或相对于当前工作目录的相对路径
    - 大文件发送可能需要较长时间，建议添加超时处理
    - 微信对单个文件大小有限制（通常不超过100MB）
    - 确保目标联系人或群组存在且可接收文件
    
运行方式:
    uv run python examples/send_file.py
    
扩展用法:
    # 发送到指定联系人
    client.send_file("C:/report.pdf", who="张三")
    
    # 批量发送多个文件
    client.send_file(["file1.pdf", "file2.docx"], who="李四")
    
    # 发送到当前聊天
    client.send_file("image.png")
"""

from pathlib import Path

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：发送当前脚本文件到文件传输助手
    
    该函数演示了文件发送的基本流程：
    1. 获取要发送的文件路径（本例中使用当前脚本文件）
    2. 创建微信客户端实例
    3. 调用send_file方法发送文件
    
    实际应用中的常见模式:
        # 发送生成的报告
        report_path = generate_monthly_report()
        client.send_file(report_path, who="经理")
        
        # 发送截图
        screenshot = take_screenshot()
        client.send_file(screenshot, who="技术支持")
        
        # 批量发送
        files = ["doc1.pdf", "doc2.docx", "image.png"]
        client.send_file(files, who="项目组")
    """
    # 获取当前脚本文件的路径
    # Path(__file__).resolve() 返回当前Python脚本的绝对路径
    sample = Path(__file__).resolve()
    
    # 自动检测并创建微信客户端实例
    # mode="auto" 表示优先后台操作，必要时切换到前台
    client = WeChatClient.auto(mode="auto")
    
    # 发送文件到文件传输助手
    # send_file 支持单个文件路径（字符串）或文件路径列表
    # who参数指定接收者，可以是联系人名称或群组名称
    client.send_file(str(sample), who="文件传输助手")
    
    print(f"文件发送成功: {sample.name}")


if __name__ == "__main__":
    main()
