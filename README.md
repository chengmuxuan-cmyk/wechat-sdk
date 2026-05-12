# WeChat_SDK



`WeChat_SDK` 是一个基于 Windows UIAutomation 技术的微信自动化 SDK，可用于学习和研究目的。通过该 SDK，您可以实现一些业务功能（如客服系统等），但仅限于学习研究用途。代码注释很详细了，可查看 examples 更多示例。

## 支持的微信版本

- **微信 3.9.12+**
- **微信 4.1.6+ ~ 4.1.9+**

## 特性

- 基于可配置的客户档案、能力元数据、选择器 YAML 文件和管道式操作
- 支持微信 3.9、4.x 及未来版本共享相同的公共 API
- 提供多种交互模式（后台/前台）
- 支持消息监听和事件处理.
- 完整的类型提示和详细的中文注释

## 安装

```powershell
uv sync
```

## 快速开始

```python
from wechat_sdk import WeChatClient

wx = WeChatClient.auto()
print(wx.info())
wx.send_msg("hello", who="文件传输助手")
```

## 交互模式

```python
WeChatClient.auto(mode="auto")        # 优先后台模式，失败时回退到前台模式
WeChatClient.auto(mode="background")  # 纯后台模式，不会唤醒微信界面
WeChatClient.auto(mode="foreground")  # 前台模式，会唤醒微信以便用户观察操作
```

## 消息监听器

```python
from wechat_sdk import MessageListener, WeChatClient

wx = WeChatClient.auto()
listener = MessageListener(wx, whitelist=["文件传输助手"])

@listener.on_message
def handle_message(event):
    if event.message.content == "ping":
        event.client.send_msg("pong", who=event.chat_name)

listener.start()
```

SDK 仅提供事件发射功能，不决定自动回复策略。业务应用需自行实现回复逻辑。

## 核心 API

### WeChatClient 主要方法

```python
# 初始化客户端
wx = WeChatClient.auto()

# 获取当前登录用户信息
info = wx.info()

# 发送文本消息
wx.send_msg("消息内容", who="联系人名称")

# 发送文件
wx.send_file(["文件路径"], who="联系人名称")

# 获取当前聊天对象
current_chat = wx.current_chat()

# 获取所有消息
messages = wx.get_all_message()

# 获取未读会话
unread_sessions = wx.get_unread_sessions()

# 获取好友列表
friends = wx.get_all_friends()

# 搜索联系人
contacts = wx.search_contacts("关键词")

# 获取群组成员
members = wx.get_group_members()
```

### MessageListener 使用方法

```python
# 创建监听器
listener = MessageListener(
    client=wx,
    whitelist=["联系人1", "联系人2"],  # 白名单
    blacklist=[],                      # 黑名单
    interval=1.0                       # 检查间隔（秒）
)

# 注册消息处理器
@listener.on_message
def handle_message(event):
    print(f"收到来自 {event.chat_name} 的消息: {event.message.content}")

# 启动监听
listener.start()

# 停止监听
listener.stop()
```

## 示例程序

```powershell
uv run python examples\diagnose.py    # 诊断工具
uv run python examples\smoke.py       # 冒烟测试
uv run python examples\send_text.py   # 发送文本消息示例
uv run python examples\listener.py    # 消息监听示例
```

## 项目结构

```
wechat_sdk/
├── __init__.py              # 包初始化，导出主要类
├── client.py                # WeChatClient 主类实现
├── listener.py              # MessageListener 消息监听器
├── models.py                # 数据模型定义（Message、Event 等）
├── core/                    # 核心功能模块
│   ├── uia.py              # UIAutomation 底层封装
│   ├── keyboard.py         # 键盘操作封装
│   ├── mouse.py            # 鼠标操作封装
│   └── clipboard.py        # 剪贴板操作封装
├── profiles/                # 配置文件目录
│   ├── wechat_39.yaml      # 微信 3.9 版本配置
│   └── wechat_4x.yaml      # 微信 4.x 版本配置
├── selectors/               # UI 元素选择器配置
│   ├── chat_selectors.yaml # 聊天相关选择器
│   └── contact_selectors.yaml # 联系人相关选择器
└── examples/                # 示例代码目录
    ├── diagnose.py         # 诊断工具
    ├── smoke.py            # 冒烟测试
    ├── send_text.py        # 发送文本示例
    └── listener.py         # 消息监听示例
```

## 技术说明

本 SDK 基于 Windows UIAutomation API 实现，通过模拟键盘鼠标操作和读取界面元素来实现微信自动化。这种技术方案具有以下特点：

- ✅ 无需逆向微信协议
- ✅ 相对安全稳定
- ✅ 易于维护和扩展
- ⚠️ 依赖微信界面结构，微信版本更新可能需要调整选择器配置

### 工作原理

1. **UIAutomation 扫描**：通过 Windows UIAutomation API 扫描微信窗口中的所有 UI 控件
2. **元素定位**：根据预定义的 YAML 选择器配置文件定位目标控件
3. **模拟操作**：通过键盘、鼠标、剪贴板等模拟用户操作
4. **事件监听**：定期扫描界面变化，检测新消息并触发事件

### 配置系统

- **Profiles**：不同微信版本的配置档案，包含版本特征、能力声明等
- **Selectors**：UI 元素的选择器规则，支持多版本适配
- **Pipeline**：管道式操作流程，支持步骤注册和链式调用

## 使用场景

- 📚 **学习研究**：学习 UIAutomation 技术和 Windows 自动化编程
- 🔧 **功能测试**：测试微信相关功能的自动化脚本
- 💡 **原型开发**：快速验证想法和概念验证

## 注意事项

1. 本 SDK 仅供学习和研究使用
2. 请勿用于任何违法违规活动
3. 使用时请遵守微信用户协议和相关法律法规
4. 因使用本 SDK 产生的任何问题，作者不承担任何责任
5. 建议在使用前运行 `examples/diagnose.py` 进行环境诊断
6. 微信版本更新后可能需要更新配置文件

## 常见问题

### Q: 为什么无法找到微信窗口？
A: 请确保微信已登录并处于运行状态，然后运行诊断工具检查。

### Q: 消息监听延迟较大怎么办？
A: 可以调整监听器的 `interval` 参数，但过小的值可能影响性能。

### Q: 微信更新后功能失效怎么办？
A: 需要更新对应的 YAML 配置文件中的选择器规则，或提交 Issue 请求支持新版本。

### Q: 是否支持多开微信？
A: 目前主要针对单实例微信设计，多开环境下可能存在冲突。

## 贡献指南

欢迎提交 Issue 和 Pull Request！在提交前请确保：
1. 代码有详细的中文注释
2. 添加相应的测试用例
3. 遵循项目的代码规范

## License

本项目仅用于学习交流，请遵守相关法律法规。

---

> ⚠️ **免责声明**：代码仅用于对 UIAutomation 技术的交流学习使用，禁止用于实际生产项目。请勿用于任何非法商业活动，因此造成的一切后果由使用者自行承担！如因此产生任何法律纠纷，均与作者无关！