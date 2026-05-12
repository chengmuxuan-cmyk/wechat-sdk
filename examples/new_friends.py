"""新朋友请求列表示例

此示例演示如何获取并显示微信"新的朋友"列表中的好友请求。

作者: CMX

使用场景:
    - 监控新的好友申请
    - 自动处理好友请求
    - 统计好友申请数量
    - 批量管理待验证联系人
    
功能说明:
    - 切换到通讯录标签页
    - 进入"新的朋友"页面
    - 读取所有可见的好友请求
    - 显示每个请求的状态和内容
    
命令行参数:
    --pages: 扫描页数，默认3页
            每页约10-20个请求
    
运行方式:
    # 查看默认数量的新朋友请求
    uv run python examples/new_friends.py
    
    # 查看更多历史请求
    uv run python examples/new_friends.py --pages 10

输出示例:
    new_friend_count: 8
    1. 等待验证 张三
    2. 等待验证 李四(来自群聊)
    3. 已添加 王五
    4. 已拒绝 赵六
    5. 已过期 钱七
    ...

状态说明:
    - 等待验证: 待处理的好友申请
    - 已添加: 已通过的好友
    - 已拒绝: 已拒绝的申请
    - 已过期: 超过有效期的申请
    
注意事项:
    - 只能读取当前屏幕可见的请求
    - 更多历史请求需要滚动加载（通过--pages参数）
    - "新的朋友"入口必须在通讯录中可见
    
扩展用法:
    # 在代码中使用
    client = WeChatClient.auto()
    
    # 获取所有新朋友请求
    new_friends = client.get_new_friends(max_pages=5)
    
    # 筛选待处理的请求
    pending = [f for f in new_friends if f["status"] == "等待验证"]
    
    # 自动通过所有请求（需谨慎）
    for friend in pending:
        accept_friend_request(friend)
        
    # 统计各状态数量
    from collections import Counter
    status_count = Counter(f["status"] for f in new_friends)
    print(status_count)
"""

from argparse import ArgumentParser

from wechat_sdk import WeChatClient


def main() -> None:
    """主函数：获取并打印新朋友请求列表
    
    该函数演示了如何读取好友请求：
    1. 解析命令行参数（扫描页数）
    2. 创建微信客户端实例
    3. 调用get_new_friends()获取请求列表
    4. 格式化输出每个请求的状态和内容
    
    返回的每个请求包含:
        - id: 请求的唯一标识
        - text: 请求文本（包含申请人信息和来源）
        - status: 请求状态（等待验证/已添加/已拒绝/已过期）
        - raw: 原始UIA信息
        
    工作流程:
        - 切换到通讯录标签页
        - 点击"新的朋友"入口
        - 滚动加载多页数据
        - 解析每个请求项的信息
        
    实际应用:
        - 自动化好友管理
        - 监控特定人员的好友申请
        - 批量处理待验证请求
        - 好友申请数据分析
        
    注意:
        - 确保微信已登录且网络正常
        - "新的朋友"页面可能需要加载时间
        - 某些请求可能因隐私设置无法查看详情
    """
    # 解析命令行参数
    parser = ArgumentParser(description="Read the WeChat new-friend request list.")
    parser.add_argument("--pages", type=int, default=3,
                       help="扫描页数，每页约10-20个请求，默认3页")
    args = parser.parse_args()

    # 自动检测并创建微信客户端实例
    client = WeChatClient.auto(mode="auto")
    
    # 获取新朋友请求列表
    # max_pages: 控制滚动次数，加载更多历史请求
    friends = client.get_new_friends(max_pages=args.pages)
    
    # 输出请求总数
    print(f"new_friend_count: {len(friends)}")
    
    # 遍历并打印每个请求
    # enumerate(start=1) 让序号从1开始
    for index, item in enumerate(friends, start=1):
        # 获取请求状态，如果为空则显示"unknown"
        status = item.get("status") or "unknown"
        
        # 格式化输出：状态 + 请求文本
        # 例如："等待验证 张三(来自群聊)"
        print(f"{index}. {status} {item['text']}")


if __name__ == "__main__":
    main()
