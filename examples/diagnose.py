"""微信客户端诊断示例

此示例演示如何诊断当前运行的微信实例，检测窗口信息并显示匹配结果。

作者: CMX

使用场景:
    - 调试微信自动化脚本连接问题
    - 检查系统中是否有运行中的微信客户端
    - 验证微信版本是否被SDK支持
    - 排查多开微信时的窗口识别问题
    - 收集微信窗口的技术信息（句柄、标题等）

功能说明:
    - 尝试自动检测并连接微信客户端
    - 显示检测到的客户端配置信息
    - 列出系统中所有可能的微信相关窗口
    - 帮助识别为什么某些微信窗口无法被SDK识别
    
运行方式:
    uv run python examples/diagnose.py
    
输出示例:
    Matched client:
    {'profile': 'wechat39', 'mode': 'auto', 'language': 'cn', ...}
    
    Candidate windows:
    - hwnd=123456, title='微信', class='WeChatMainWndForPC'
    - hwnd=789012, title='微信 (多开)', class='WeChatMainWndForPC'

常见问题排查:
    1. 如果显示"No supported client matched"：
       - 确认微信客户端已启动并登录
       - 检查微信版本是否在SDK支持范围内（3.9.x或4.x）
       - 查看"Candidate windows"部分是否有微信窗口
    
    2. 如果检测到多个微信窗口：
       - SDK会自动选择第一个匹配的窗口
       - 如需指定特定窗口，可能需要修改窗口检测逻辑
    
    3. 如果窗口信息为空：
       - 微信可能未启动或未登录
       - 可能使用了不被支持的微信版本
"""

from wechat_sdk import WeChatClient
from wechat_sdk.core.diagnostics import diagnose_wechat_windows


def main() -> None:
    """主函数：执行微信客户端诊断
    
    该函数执行两个诊断步骤：
    1. 尝试自动连接微信客户端并显示其信息
    2. 列出系统中所有候选的微信相关窗口
    
    诊断流程:
        - 调用WeChatClient.auto()尝试自动检测
        - 如果成功，打印客户端配置信息（版本、模式、语言等）
        - 如果失败，显示错误信息
        - 调用diagnose_wechat_windows()获取所有候选窗口
        - 逐行打印窗口详细信息
    
    返回的信息包括:
        - profile: 检测到的微信版本配置文件（如wechat39、wechat4）
        - mode: 交互模式（auto/background/foreground）
        - language: 界面语言（cn/en等）
        - window: 窗口详细信息（hwnd句柄、title标题、rect位置等）
        
    实际应用:
        - 在自动化脚本启动前进行环境检查
        - 技术支持时收集系统信息
        - 开发新功能时验证UI元素可访问性
    """
    # 尝试自动检测并创建微信客户端实例
    try:
        client = WeChatClient.auto()
        print("Matched client:")
        # 打印客户端详细信息
        # 包括：配置文件、交互模式、语言设置、窗口信息
        print(client.info())
    except Exception as exc:
        # 如果检测失败，显示错误信息
        # 常见原因：微信未启动、版本不支持、窗口不可见等
        print(f"No supported client matched: {exc}")

    # 显示所有候选窗口信息
    # 即使未能成功匹配，也会列出所有检测到的微信相关窗口
    # 这有助于排查为什么某些窗口未被识别
    print("\nCandidate windows:")
    for line in diagnose_wechat_windows():
        print(line)


if __name__ == "__main__":
    main()
