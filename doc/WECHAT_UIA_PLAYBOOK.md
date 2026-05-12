# WeChat UIA Playbook

这份文件记录微信 4 UIAutomation 探测成功流程，以及以后遇到微信 5/6/7/8 时的迁移方法。

## 目标

新版本微信适配时，不先猜 API，也不直接重写业务代码。先确认客户端是否暴露稳定 UIA 树，再把节点映射到 SDK 能力。

核心判断标准：

- UIA 根节点能看到 `mmui::MainWindow`，说明主界面树已暴露。
- 能看到 `session_list`、`chat_message_list`、`chat_input_field`，说明会话、消息、输入框可以走 UIA。
- 如果只能看到 `Qt51514QWindowIcon`，说明当前只拿到了外壳窗口，不能直接按 3.9/4.x 的 UIA 能力同步。

## 微信 4 成功流程

1. 退出微信。
2. 打开 Windows 讲述人。
   - 快捷键：`Win + Ctrl + Enter`
   - 设置路径：`Windows 设置 -> 辅助功能 -> 讲述人`
3. 保持讲述人开启，再启动并登录微信。
4. 等待几分钟，让微信初始化无障碍树。
5. 可关闭讲述人。
   - 再按一次 `Win + Ctrl + Enter`
6. 执行 UIA dump：

```powershell
.\.venv\Scripts\python.exe examples\dump_uia_tree.py
```

成功时应该看到类似节点：

```text
WindowControl class='mmui::MainWindow' name='微信'
ListControl class='mmui::XTableView' name='会话' aid='session_list'
ListControl class='mmui::RecyclerListView' name='消息' aid='chat_message_list'
EditControl class='mmui::ChatInputField' aid='chat_input_field'
```

## 本次微信 4 已确认节点

当前验证环境：

- Process: `Weixin.exe`
- Version: `4.1.9.30`
- Top-level class: `Qt51514QWindowIcon`
- UIA root class after accessibility unlock: `mmui::MainWindow`

关键节点：

| 功能 | UIA 节点 |
| --- | --- |
| 当前聊天名 | `automation_id` 以 `current_chat_name_label` 结尾 |
| 会话列表 | `ListControl class='mmui::XTableView' name='会话' automation_id='session_list'` |
| 会话项 | `ListItemControl class='mmui::ChatSessionCell' automation_id='session_item_<name>'` |
| 消息列表 | `ListControl class='mmui::RecyclerListView' name='消息' automation_id='chat_message_list'` |
| 文本消息 | `ListItemControl class='mmui::ChatTextItemView'` |
| 语音消息 | `ListItemControl class='mmui::ChatVoiceItemView'` |
| 富内容消息 | `ListItemControl class='mmui::ChatBubbleReferItemView'` 或 `mmui::ChatBubbleItemView` |
| 输入框 | `EditControl class='mmui::ChatInputField' automation_id='chat_input_field'` |
| 发送按钮 | `ButtonControl class='mmui::XOutlineButton' name='发送'` |
| 搜索框 | `EditControl class='mmui::XValidatorTextEdit' name='搜索'` |
| 发送文件按钮 | `ButtonControl class='mmui::XButton' name='发送文件'` |

## SDK 映射原则

优先复用 3.9 的方法结构，但不要复用旧选择器。

| SDK 能力 | 微信 4 实现策略 |
| --- | --- |
| `chat_with` | 可继续用 `Ctrl+F` 搜索进入会话；后续可替换为 UIA 搜索框 |
| `send_msg` | 当前保留键盘/剪贴板发送链路，已经验证可用 |
| `send_file` | 当前保留剪贴板文件发送链路，降低风险 |
| `current_chat` | 从 `current_chat_name_label` 读取 |
| `get_session_list` | 从 `mmui::ChatSessionCell` 读取首行会话名 |
| `get_all_message` | 从 `chat_message_list` 下的消息 item 读取 |
| `get_next_new_message` | 基于消息节点 `RuntimeId` 去重 |
| listener | 基于 `get_next_new_message` 轮询 |

发送类能力先保持已验证路径。读取类能力优先走 UIA，失败再回退剪贴板方案。

## 新版本微信迁移流程

遇到微信 5/6/7/8 时按这个顺序做：

1. 检测窗口。
   - 确认进程名、窗口类名、版本号。
   - 入口：`WeChatClient.auto(mode="auto")`
2. 解锁 UIA 树。
   - 如果 dump 只有外壳，按“先开讲述人，再启动微信”的流程重试。
3. dump 完整树。
   - 先用 `examples/dump_uia_tree.py` 看整体结构。
   - 再聚焦查找 `session`、`message`、`input`、`search`、`send` 相关节点。
4. 建立选择器映射。
   - 新版本如果仍是 `mmui::`，优先沿用微信 4 selector。
   - 如果 class name 或 automation_id 变化，只更新 selector，不重写业务方法。
5. 验证能力。
   - `current_chat`
   - `get_session_list`
   - `get_all_message`
   - `get_next_new_message`
   - listener `poll_once`
   - 最后再验证发送类能力。
6. 固化结果。
   - 更新 selector 配置。
   - 记录新版本进程、窗口类、关键节点。
   - 补一条最小 smoke 验证命令。

## 判断是否可以复用 3.9

可以复用的是方法思路：

- 通过 UIA 找窗口和控件。
- 通过列表节点读取会话和消息。
- 通过输入框、按钮或键盘链路发送内容。
- listener 基于新消息差异轮询。

不能直接复用的是节点配置：

- 微信 3.9 常见控件树和微信 4 的 Qt `mmui::` 树不同。
- 微信 4/未来版本要以实际 dump 出来的 `class_name`、`automation_id`、`control_type` 为准。

## 排障

问题：只看到 `Qt51514QWindowIcon`。

处理：

1. 退出微信。
2. 开启 Windows 讲述人。
3. 重新启动并登录微信。
4. 等几分钟。
5. 重新 dump。

问题：`get_session_list` 为空。

处理：

1. 确认当前在微信主界面的“微信”tab。
2. dump 是否有 `session_list`。
3. 如果只有 `mmui::ChatSessionList` 没有 item，可能是列表虚拟化或窗口未激活，先点击/激活微信再 dump。

问题：`get_all_message` 为空。

处理：

1. 确认右侧确实打开了聊天会话。
2. dump 是否有 `chat_message_list`。
3. 查找消息 item class，例如 `mmui::ChatTextItemView`、`mmui::ChatVoiceItemView`。

问题：listener 重复或漏消息。

处理：

1. 优先使用 UIA `RuntimeId` 去重。
2. 如果新版本 RuntimeId 不稳定，再补充消息 class、content、rect、index 的组合 key。

## 当前经验

这次微信 4 的关键经验是：窗口检测能成功，不代表 UIA 树已经可用。发送消息可以通过键盘/剪贴板成功，但读取会话和消息必须先确认内部 UIA 树是否暴露。

以后适配新版本时，先做树探测，再同步能力。
