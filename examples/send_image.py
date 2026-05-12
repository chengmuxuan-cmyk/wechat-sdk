"""发送图片示例

此示例演示如何使用 WeChat_SDK 发送图片文件到指定联系人。

作者: CMX

使用场景:
    - 自动发送截图或生成的图片
    - 批量图片分享
    - 图片报告或图表发送
    - 工作流中的图片通知
    
功能说明:
    - 验证图片文件格式
    - 使用send_file接口发送图片
    - 支持多种常见图片格式
    
支持的图片格式:
    - PNG (.png)
    - JPEG (.jpg, .jpeg)
    - GIF (.gif)
    - BMP (.bmp)
    - WebP (.webp)
    
命令行参数:
    image: 必填，本地图片文件路径
    --who: 可选，目标聊天名称，默认"文件传输助手"
    
运行方式:
    # 发送到文件传输助手（默认）
    uv run python examples/send_image.py screenshot.png
    
    # 发送到指定联系人
    uv run python examples/send_image.py photo.jpg --who "张三"
    
    # 使用完整路径
    uv run python examples/send_image.py C:/images/report.png --who "项目组"

注意事项:
    - 图片文件必须存在且可读
    - 微信对图片大小有限制（通常不超过10MB）
    - 过大的图片可能被压缩
    - 确保目标联系人或群组存在
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    
    # 发送截图
    from PIL import ImageGrab
    screenshot = ImageGrab.grab()
    screenshot.save("temp.png")
    client.send_file("temp.png", who="张三")
    
    # 批量发送多张图片
    images = ["img1.png", "img2.jpg", "img3.gif"]
    for img in images:
        client.send_file(img, who="李四")
        
    # 发送生成的图表
    import matplotlib.pyplot as plt
    plt.plot([1, 2, 3], [4, 5, 6])
    plt.savefig("chart.png")
    client.send_file("chart.png", who="经理")
"""

from argparse import ArgumentParser
from pathlib import Path

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：发送图片文件到指定聊天
    
    该函数演示了如何发送图片：
    1. 解析命令行参数（图片路径和目标）
    2. 验证图片文件格式
    3. 创建微信客户端实例
    4. 调用send_file发送图片
    
    验证流程:
        - 解析并规范化文件路径
        - 检查文件扩展名是否在支持的列表中
        - 如果格式不支持，抛出ValueError
        
    发送流程:
        - 复用send_file接口（图片也是文件的一种）
        - 通过剪贴板或拖放方式发送
        - 微信会自动识别并显示为图片消息
        
    实际应用:
        - 自动化截图分享
        - 报表和图表发送
        - 监控告警配图
        - 产品展示图片
        
    注意:
        - 图片路径可以是相对路径或绝对路径
        - 支持~符号表示用户主目录
        - 发送大图片可能需要较长时间
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Send an image file to a WeChat chat.")
    parser.add_argument("image", help="本地图片文件路径")
    parser.add_argument("--who", default="文件传输助手", 
                       help="目标聊天名称，默认为'文件传输助手'")
    args = parser.parse_args()

    # 解析并规范化图片文件路径
    # expanduser(): 展开~为用户主目录
    # resolve(): 转换为绝对路径
    image = Path(args.image).expanduser().resolve()
    
    # 验证图片文件格式
    # 检查文件扩展名是否在支持的列表中
    if image.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
        raise ValueError(f"Not a supported image suffix: {image.suffix}")

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 发送图片文件
    # send_file可以处理所有类型的文件，包括图片
    # 微信会自动识别图片格式并正确显示
    client.send_file(str(image), who=args.who)
    
    print(f"图片发送成功: {image.name} -> {args.who}")


if __name__ == "__main__":
    main()
