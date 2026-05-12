"""UI Automation树结构导出工具

此示例演示如何枚举系统中的微信窗口并导出其UI元素树结构。

作者: CMX

使用场景:
    - 调试和探索微信的UI结构
    - 查找特定控件的路径和属性
    - 开发新功能时分析UI布局
    - 排查控件识别问题
    - 生成UI自动化测试的选择器
    
功能说明:
    - 枚举系统中所有窗口
    - 过滤出微信相关窗口（标题或类名包含wechat/weixin/微信）
    - 显示窗口基本信息（句柄、标题、类名、进程等）
    - 递归导出UI元素树（最多8层深度）
    - 每个节点显示：类型、类名、名称、自动化ID、位置等
    
运行方式:
    uv run python examples/dump_uia_tree.py

输出示例:
    hwnd=123456 visible=True title='微信' class='WeChatMainWndForPC' process='WeChat.exe' version=3.9.0.0
      - type=WindowControl, class='WeChatMainWndForPC', name='微信', automation_id='', hwnd=123456, rect=(100, 100, 900, 700)
        - type=PaneControl, class='mmui::XXX', name='', automation_id='', hwnd=0, rect=(...)
          - type=ButtonControl, class='Button', name='发送', automation_id='send_btn', hwnd=0, rect=(...)
          ...

输出字段说明:
    - type: UI控件类型（ButtonControl、TextControl等）
    - class: 控件类名（微信自定义控件以mmui::开头）
    - name: 控件显示的文本内容
    - automation_id: 开发者设置的自动化ID（如果有）
    - hwnd: 原生窗口句柄（大多数子控件为0）
    - rect: 控件在屏幕上的位置和大小 (left, top, right, bottom)

注意事项:
    - 输出可能非常长，建议重定向到文件查看
    - max_depth=8 限制输出深度，避免过多内容
    - 某些窗口可能无法访问（权限问题）
    - UI树结构在不同微信版本间可能有差异
    
扩展用法:
    # 保存ToFile
    uv run python examples/dump_uia_tree.py > uia_tree.txt
    
    # 只查看特定窗口
    # 修改代码中的关键词过滤条件
    
    # 调整深度
    # 修改dump_tree的max_depth参数
    
    # 在代码中使用
    from wechat_sdk.core import uia
    root = uia.control_from_handle(hwnd)
    tree = uia.dump_tree(root, max_depth=5)
    for line in tree:
        print(line)
        
    # 查找特定控件
    buttons = root.FindAll(
        max_depth=10,
        predicate=lambda c: c.ControlTypeName == "ButtonControl"
    )
"""
from wechat_sdk.core import uia
from wechat_sdk.core.window import enum_windows


def main() -> None:
    """主函数：枚举微信窗口并导出UI树
    
    该函数执行以下步骤：
    1. 枚举系统中所有顶级窗口
    2. 过滤出微信相关窗口
    3. 对每个微信窗口：
       a. 打印窗口基本信息
       b. 创建UIA根控件
       c. 递归导出UI元素树
       
    窗口过滤逻辑:
        - 检查窗口的标题、类名、进程名、路径
        - 转换为小写后匹配关键词
        - 关键词：wechat、weixin、微信
        
    UI树导出:
        - 从窗口根节点开始
        - 深度优先遍历所有子控件
        - 限制最大深度为8层
        - 每行显示一个控件的详细信息
        
    异常处理:
        - 如果某个窗口无法访问，捕获异常并继续
        - 不影响其他窗口的处理
        
    实际应用:
        - 开发新feature时探索UI结构
        - 编写选择器前的调研
        - 调试控件识别问题
        - 文档化UI布局
        
    提示:
        - 输出较多时建议使用grep或findstr过滤
        - 可以结合文本编辑器的搜索功能定位控件
        - 对比不同版本的UI树可以发现变化
    """
    # 枚举系统中所有顶级窗口
    for window in enum_windows():
        # 构建窗口的文本标识（用于过滤）
        # 包含：标题、类名、进程名、可执行文件路径
        text = " ".join([window.title, window.class_name, window.process_name, window.exe_path]).lower()
        
        # 过滤出微信相关窗口
        # 检查是否包含wechat、weixin或微信关键词
        if not any(keyword in text for keyword in ("wechat", "weixin", "微信")):
            continue
        
        # 打印窗口基本信息
        # 包括：句柄、可见性、标题、类名、进程名、版本号
        print(
            f"hwnd={window.hwnd} visible={window.visible} title={window.title!r} "
            f"class={window.class_name!r} process={window.process_name!r} version={window.version}"
        )
        
        # 尝试导出UI元素树
        try:
            # 从窗口句柄创建UIA根控件
            root = uia.control_from_handle(window.hwnd)
            
            # 递归导出UI树，限制深度为8层
            # 每行添加缩进以便阅读
            for line in uia.dump_tree(root, max_depth=8):
                print("  " + line)
        except Exception as exc:
            # 如果导出失败（权限问题、窗口已关闭等）
            # 打印错误信息但不中断程序
            print(f"  failed: {exc}")


if __name__ == "__main__":
    main()
