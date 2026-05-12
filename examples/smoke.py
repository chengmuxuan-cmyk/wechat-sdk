"""冒烟测试示例

此示例用于快速验证 WeChat_SDK 的基本功能，检测微信客户端并显示信息。

作者: CMX

使用场景:
    - 安装SDK后验证环境配置是否正确
    - 调试时检查微信客户端是否可被识别
    - CI/CD流程中的基础连接测试
    - 排查"无法检测到微信"类问题
    
功能说明:
    - 尝试自动检测系统中的微信客户端
    - 显示检测到的客户端详细信息
    - 不会执行任何发送消息的操作（安全测试）
    
运行方式:
    uv run python examples/smoke.py
    
成功输出示例:
    {
        'profile': 'wechat39',
        'mode': 'auto',
        'language': 'cn',
        'window': {
            'hwnd': 123456,
            'title': '微信',
            'rect': (100, 100, 900, 700)
        }
    }
    Smoke check passed. This script does not send messages.

失败情况:
    如果微信未启动或版本不支持，会抛出异常：
    - "No supported WeChat window found"
    - "Unsupported WeChat version"
    
故障排查:
    1. 确认微信客户端已启动并登录
    2. 检查微信版本是否在支持范围内（3.9.x或4.x）
    3. 运行diagnose.py获取更详细的诊断信息
    4. 确保微信窗口未被最小化或隐藏
    
扩展用法:
    # 在代码中进行环境检查
    try:
        client = WeChatClient.auto()
        print("环境检查通过")
    except Exception as e:
        print(f"环境检查失败: {e}")
        sys.exit(1)
"""

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：执行冒烟测试，验证客户端连接
    
    该函数执行最基础的连接测试：
    1. 调用WeChatClient.auto()检测微信客户端
    2. 如果成功，打印客户端信息
    3. 如果失败，抛出异常并终止
    
    这是所有自动化脚本的第一步，确保后续操作的基础环境正常。
    
    返回的信息包括:
        - profile: 微信版本标识（wechat39/wechat4等）
        - mode: 交互模式（auto/background/foreground）
        - language: 界面语言（cn/en等）
        - window: 窗口详细信息
          - hwnd: 窗口句柄
          - title: 窗口标题
          - rect: 窗口位置和大小
        
    实际应用:
        - 在正式脚本开始前进行预检
        - Docker容器或CI环境中验证依赖
        - 技术支持时快速定位问题
    """
    # 自动检测并创建微信客户端实例
    # 如果检测失败，这里会抛出异常
    client = WeChatClient.auto()
    
    # 打印客户端详细信息
    # 这有助于确认检测到的微信版本和配置是否正确
    print(client.info())
    
    # 提示信息：本脚本不执行任何消息发送操作
    print("Smoke check passed. This script does not send messages.")


if __name__ == "__main__":
    main()
