from __future__ import annotations

from pathlib import Path
import re
import time
from typing import Iterable, Optional

import win32gui

from wechat_sdk.core.capability import CapabilityRegistry
from wechat_sdk.core.interaction import InteractionPolicy
from wechat_sdk.core.pipeline import PipelineRunner
from wechat_sdk.core.profile import ClientProfile
from wechat_sdk.core.selectors import SelectorRegistry
from wechat_sdk.core.window import detect_wechat_window
from wechat_sdk.logging import logger
from wechat_sdk.msgs.base import Message
from wechat_sdk.params import WindowInfo


class WeChatClient:
    """微信客户端主类，提供自动化操作的统一接口
    
    该类封装了与Windows微信客户端交互的所有核心功能，包括：
    - 会话管理（切换聊天、获取会话列表）
    - 消息操作（发送文本/文件、读取历史消息）
    - 联系人管理（获取好友列表、搜索联系人、查看详情）
    - 群组操作（获取群成员列表）
    
    支持多种交互模式：auto（自动）、background（后台）、foreground（前台）
    
    示例:
        >>> client = WeChatClient.auto(mode="auto")
        >>> client.send_msg("Hello", who="文件传输助手")
    """
    
    def __init__(
        self,
        window: WindowInfo,
        profile: ClientProfile,
        mode: str = "auto",
        language: str = "cn",
    ) -> None:
        """初始化微信客户端
        
        Args:
            window: 窗口信息对象，包含窗口句柄、标题等信息
            profile: 客户端配置文件，定义选择器和能力元数据
            mode: 交互模式，可选值：
                - "auto": 优先后台操作，必要时切换到前台
                - "background": 纯后台操作，不唤醒微信窗口
                - "foreground": 始终在前台操作，用户可观察动作
            language: 语言设置，默认为"cn"（中文）
        """
        self.window = window
        self.profile = profile
        self.mode = mode
        self.language = language
        self.capabilities = CapabilityRegistry()  # 能力注册表，检查功能支持
        self.selectors = SelectorRegistry(profile.selectors_file, language=language)  # 选择器注册表
        self.interaction = InteractionPolicy(window.hwnd, mode=mode)  # 交互策略管理器
        self.pipeline = PipelineRunner()  # 管道运行器，执行操作流水线
        self._current_chat: Optional[str] = None  # 当前聊天对象名称
        self._last_message_ids: set[str] = set()  # 上次读取的消息ID集合，用于检测新消息
        self._register_pipeline_steps()  # 注册管道步骤

    @classmethod
    def auto(cls, mode: str = "auto", version: Optional[str] = None, language: str = "cn") -> "WeChatClient":
        """自动检测并创建微信客户端实例
        
        该方法会自动检测系统中运行的微信窗口，并根据版本加载相应的配置。
        
        Args:
            mode: 交互模式，可选值：
                - "auto": 优先后台操作，必要时切换到前台
                - "background": 纯后台操作
                - "foreground": 始终在前台操作
            version: 指定的微信版本（可选），如"3.9"或"4.0"
            language: 语言设置，默认为"cn"
            
        Returns:
            WeChatClient: 微信客户端实例
            
        Raises:
            Exception: 如果未检测到运行中的微信窗口
            
        示例:
            >>> client = WeChatClient.auto(mode="foreground")
            >>> print(client.info())
        """
        window, profile = detect_wechat_window()
        if version and version not in profile.profile_id:
            logger.info("Requested version=%s but detected profile=%s", version, profile.profile_id)
        return cls(window=window, profile=profile, mode=mode, language=language)

    def info(self) -> dict:
        """获取客户端信息
        
        Returns:
            dict: 包含配置文件、模式、语言和窗口信息的字典
            
        示例:
            >>> client = WeChatClient.auto()
            >>> info = client.info()
            >>> print(info["profile"])  # 输出: wechat39 或 wechat4
        """
        return {
            "profile": self.profile.profile_id,
            "mode": self.mode,
            "language": self.language,
            "window": self.get_window_info(),
        }

    def get_window_info(self) -> dict:
        """获取窗口信息
        
        Returns:
            dict: 窗口信息字典，包含hwnd、title、rect等字段
        """
        return self.window.__dict__.copy()

    def diagnose(self) -> list[str]:
        """诊断微信窗口状态
        
        用于调试和故障排查，检测系统中的微信窗口情况。
        
        Returns:
            list[str]: 诊断结果列表
        """
        from wechat_sdk.core.diagnostics import diagnose_wechat_windows

        return diagnose_wechat_windows()

    def chat_with(self, who: str):
        """切换到指定聊天会话
        
        通过搜索功能快速定位并打开与指定联系人或群组的聊天窗口。
        
        Args:
            who: 联系人名称或群组名称
            
        Returns:
            聊天对象名称
            
        示例:
            >>> client.chat_with("文件传输助手")
            '文件传输助手'
        """
        self.capabilities.ensure_supported("chat.chat_with", self.profile.profile_id)
        return self.pipeline.run("chat_with", {"client": self, "who": who})

    def current_chat(self) -> Optional[str]:
        """获取当前聊天对象的名称
        
        Returns:
            Optional[str]: 当前聊天对象名称，如果未打开任何聊天则返回None
            
        示例:
            >>> client.chat_with("张三")
            >>> print(client.current_chat())  # 输出: 张三
        """
        self.capabilities.ensure_supported("chat.current", self.profile.profile_id)
        return self._uia_current_chat() or self._current_chat or self.window.title or None

    def get_session_list(self) -> list[str]:
        """获取会话列表
        
        读取左侧会话列表中的所有聊天会话名称（包括个人聊天和群组）。
        
        Returns:
            list[str]: 会话名称列表
            
        示例:
            >>> sessions = client.get_session_list()
            >>> print(sessions[:5])  # 输出前5个会话
        """
        self.capabilities.ensure_supported("chat.get_session_list", self.profile.profile_id)
        return self.interaction.run(
            "chat.get_session_list",
            self._copy_session_list,
            foreground_required=True,
        )

    def get_sessions(self) -> list[str]:
        """获取会话列表（get_session_list的别名）
        
        Returns:
            list[str]: 会话名称列表
        """
        self.capabilities.ensure_supported("chat.get_sessions", self.profile.profile_id)
        return self.get_session_list()

    def get_unread_sessions(self, personal_only: bool = True, max_sessions: Optional[int] = None) -> list[dict]:
        """获取未读会话列表
        
        扫描会话列表，找出有未读消息的会话。可选择仅包含个人聊天或限制返回数量。
        
        Args:
            personal_only: 是否只返回个人聊天（排除群组和公众号），默认为True
            max_sessions: 最大返回会话数量，None表示不限制
            
        Returns:
            list[dict]: 未读会话信息列表，每个字典包含：
                - name: 会话名称
                - unread_count: 未读消息数
                - muted: 是否免打扰
                - preview: 最后一条消息预览
                
        示例:
            >>> unread = client.get_unread_sessions(personal_only=True, max_sessions=10)
            >>> for session in unread:
            ...     print(f"{session['name']}: {session['unread_count']}条未读")
        """
        self.capabilities.ensure_supported("chat.get_unread_sessions", self.profile.profile_id)
        return self.interaction.run(
            "chat.get_unread_sessions",
            lambda: self._uia_unread_sessions(personal_only=personal_only, max_sessions=max_sessions),
            foreground_required=True,
        )

    def switch_to_chat_tab(self):
        """切换到"微信"标签页（聊天列表）
        
        确保当前显示的是聊天列表界面。
        
        Returns:
            bool: 是否成功切换
        """
        self.capabilities.ensure_supported("chat.switch_to_chat_tab", self.profile.profile_id)
        return self.interaction.run(
            "chat.switch_to_chat_tab",
            lambda: self._uia_click_tab("微信"),
            foreground_required=True,
        )

    def switch_to_contact_tab(self):
        """切换到"通讯录"标签页
        
        确保当前显示的是通讯录界面。
        
        Returns:
            bool: 是否成功切换
        """
        self.capabilities.ensure_supported("chat.switch_to_contact_tab", self.profile.profile_id)
        return self.interaction.run(
            "chat.switch_to_contact_tab",
            lambda: self._uia_click_tab("通讯录"),
            foreground_required=True,
        )

    def send_msg(self, text: str, who: Optional[str] = None, at=None, clear: bool = True):
        """发送文本消息
        
        向指定联系人或群组发送文本消息。如果未指定接收者，则发送到当前聊天。
        
        Args:
            text: 要发送的文本内容
            who: 接收者名称（可选），如果为None则发送到当前聊天
            at: @某人（暂未实现）
            clear: 发送前是否清空输入框，默认为True
            
        Returns:
            bool: 是否发送成功
            
        示例:
            >>> client.send_msg("你好！", who="张三")
            >>> client.send_msg("测试消息")  # 发送到当前聊天
        """
        self.capabilities.ensure_supported("message.send_text", self.profile.profile_id)
        return self.pipeline.run(
            "send_text",
            {"client": self, "text": text, "who": who, "at": at, "clear": clear},
        )

    def send_file(self, path_or_paths, who: Optional[str] = None):
        """发送文件/图片
        
        向指定联系人或群组发送文件或图片。支持单个文件或多个文件批量发送。
        
        Args:
            path_or_paths: 文件路径或路径列表
            who: 接收者名称（可选），如果为None则发送到当前聊天
            
        Returns:
            bool: 是否发送成功
            
        示例:
            >>> client.send_file("C:/image.png", who="张三")
            >>> client.send_file(["file1.pdf", "file2.docx"], who="李四")
        """
        self.capabilities.ensure_supported("message.send_file", self.profile.profile_id)
        paths = self._normalize_paths(path_or_paths)
        return self.pipeline.run("send_file", {"client": self, "paths": paths, "who": who})

    def get_all_message(self):
        """获取当前聊天的所有可见消息
        
        读取当前聊天窗口中显示的所有消息记录。
        
        Returns:
            list[Message]: 消息对象列表
            
        注意:
            - 只能获取当前屏幕可见的消息
            - 如需更多历史消息，使用load_more_message()加载
        """
        self.capabilities.ensure_supported("message.get_all", self.profile.profile_id)
        return self.interaction.run(
            "message.get_all",
            self._copy_all_messages,
            foreground_required=True,
        )

    def get_next_new_message(self):
        """获取下一条新消息
        
        检测自上次调用以来收到的新消息。首次调用时会初始化消息ID集合。
        
        Returns:
            dict: 新消息字典，键为聊天名称，值为消息列表。如果没有新消息则返回空字典
            
        示例:
            >>> new_msgs = client.get_next_new_message()
            >>> if new_msgs:
            ...     for chat, messages in new_msgs.items():
            ...         print(f"{chat}: {len(messages)}条新消息")
        """
        self.capabilities.ensure_supported("message.get_next_new", self.profile.profile_id)
        messages = self.get_all_message()
        message_ids = {self._message_id(message) for message in messages}
        if not self._last_message_ids:
            self._last_message_ids = message_ids
            return {}
        new_messages = [message for message in messages if self._message_id(message) not in self._last_message_ids]
        self._last_message_ids = message_ids
        if not new_messages:
            return {}
        return {self.current_chat() or "current": new_messages}

    def get_new_message(self):
        """获取新消息（get_next_new_message的别名）
        
        Returns:
            dict: 新消息字典
        """
        self.capabilities.ensure_supported("message.get_new", self.profile.profile_id)
        return self.get_next_new_message()

    def get_all_new_message(self):
        """获取所有新消息（get_next_new_message的别名）
        
        Returns:
            dict: 新消息字典
        """
        self.capabilities.ensure_supported("message.get_all_new", self.profile.profile_id)
        return self.get_next_new_message()

    def get_unread_messages(self, personal_only: bool = True, max_sessions: Optional[int] = None):
        """获取未读消息内容
        
        遍历所有未读会话，读取其中的未读消息内容。
        
        Args:
            personal_only: 是否只读取个人聊天，默认为True
            max_sessions: 最大处理的会话数量，None表示不限制
            
        Returns:
            dict: 未读消息字典，键为聊天名称，值为消息列表
            
        示例:
            >>> unread_msgs = client.get_unread_messages(max_sessions=5)
            >>> for chat, messages in unread_msgs.items():
            ...     print(f"{chat}: {[m.content for m in messages]}")
        """
        self.capabilities.ensure_supported("message.get_unread", self.profile.profile_id)
        return self.interaction.run(
            "message.get_unread",
            lambda: self._uia_get_unread_messages(personal_only=personal_only, max_sessions=max_sessions),
            foreground_required=True,
        )

    def load_more_message(self, pages: int = 1):
        """加载更多历史消息
        
        向上滚动聊天窗口以加载更多历史消息。
        
        Args:
            pages: 加载页数，每页约10-20条消息，默认为1
            
        Returns:
            list[Message]: 加载后的所有消息列表
        """
        self.capabilities.ensure_supported("message.load_more", self.profile.profile_id)
        return self.interaction.run(
            "message.load_more",
            lambda: self._uia_load_more_messages(pages=pages),
            foreground_required=True,
        )

    def get_history(self, max_pages: int = 10, limit: Optional[int] = None):
        """获取聊天历史记录
        
        从当前聊天中读取历史消息，自动翻页加载。
        
        Args:
            max_pages: 最大翻页次数，默认为10
            limit: 最大返回消息数量，None表示不限制
            
        Returns:
            list[Message]: 历史消息列表（按时间顺序）
            
        示例:
            >>> history = client.get_history(max_pages=5, limit=100)
            >>> print(f"获取到{len(history)}条历史消息")
        """
        self.capabilities.ensure_supported("message.get_history", self.profile.profile_id)
        return self.interaction.run(
            "message.get_history",
            lambda: self._uia_get_history(max_pages=max_pages, limit=limit),
            foreground_required=True,
        )

    def get_all_friends(self, max_pages: int = 20) -> list[str]:
        """获取所有好友列表
        
        从通讯录中读取所有联系人名称，自动翻页直到列表末尾。
        
        Args:
            max_pages: 最大翻页次数，防止无限循环，默认为20
            
        Returns:
            list[str]: 好友名称列表
            
        注意:
            - 会自动切换到通讯录标签页
            - 可能需要较长时间（取决于好友数量）
        """
        self.capabilities.ensure_supported("contact.get_all_friends", self.profile.profile_id)
        return self.interaction.run(
            "contact.get_all_friends",
            lambda: self._uia_get_all_friends(max_pages=max_pages),
            foreground_required=True,
        )

    def search_contact(self, keyword: str) -> list[str]:
        """搜索联系人
        
        在通讯录中搜索匹配的联系人。
        
        Args:
            keyword: 搜索关键词（姓名、微信号等）
            
        Returns:
            list[str]: 匹配的联系人名称列表
            
        示例:
            >>> results = client.search_contact("张三")
            >>> print(results)
        """
        self.capabilities.ensure_supported("contact.search", self.profile.profile_id)
        return self.interaction.run(
            "contact.search",
            lambda: self._uia_search_contacts(keyword),
            foreground_required=True,
        )

    def get_friend_details(self, who: Optional[str] = None) -> dict:
        """获取联系人详情
        
        读取指定联系人的详细信息。如果未指定联系人，则读取当前聊天的联系人信息。
        
        Args:
            who: 联系人名称（可选），如果为None则读取当前聊天的联系人
            
        Returns:
            dict: 联系人详细信息，包含：
                - name: 联系人名称
                - wechat_id: 微信号
                - texts: 所有文本内容
                - raw: 原始控件信息
                
        示例:
            >>> details = client.get_friend_details("张三")
            >>> print(details["wechat_id"])
        """
        self.capabilities.ensure_supported("contact.get_friend_details", self.profile.profile_id)
        return self.interaction.run(
            "contact.get_friend_details",
            lambda: self._uia_get_friend_details(who=who),
            foreground_required=True,
        )

    def get_new_friends(self, max_pages: int = 5) -> list[dict]:
        """获取新的朋友请求
        
        读取通讯录中的新的朋友请求。
        
        Args:
            max_pages: 最大翻页次数，默认为5
            
        Returns:
            list[dict]: 新朋友请求信息列表，每个字典包含：
                - id: 控件唯一标识
                - text: 请求内容
                - status: 请求状态（等待验证、已添加、已过期、已拒绝）
                - raw: 原始控件信息
                
        示例:
            >>> new_friends = client.get_new_friends()
            >>> for friend in new_friends:
            ...     print(f"{friend['text']} - {friend['status']}")
        """
        self.capabilities.ensure_supported("contact.get_new_friends", self.profile.profile_id)
        return self.interaction.run(
            "contact.get_new_friends",
            lambda: self._uia_get_new_friends(max_pages=max_pages),
            foreground_required=True,
        )

    def get_group_members(self, max_pages: int = 50) -> list[str]:
        """获取群成员列表
        
        读取当前聊天的群成员列表。
        
        Args:
            max_pages: 最大翻页次数，默认为50
            
        Returns:
            list[str]: 群成员名称列表
            
        注意:
            - 会自动打开聊天信息面板
            - 可能需要较长时间（取决于群成员数量）
        """
        self.capabilities.ensure_supported("group.get_members", self.profile.profile_id)
        return self.interaction.run(
            "group.get_members",
            lambda: self._uia_get_group_members(max_pages=max_pages),
            foreground_required=True,
        )

    def get_dialog(self):
        """
        获取对话信息。

        该方法用于检查当前配置文件是否支持 dialog.get 功能，如果支持则继续执行，
        否则会抛出异常。目前该功能已注册但尚未在此阶段实现迁移。

        Raises:
            NotImplementedError: 当 dialog.get 功能已注册但未在此阶段实现时抛出此异常。
        """
        self.capabilities.ensure_supported("dialog.get", self.profile.profile_id)
        raise NotImplementedError("dialog.get is registered but not migrated in this phase")

    def _register_pipeline_steps(self) -> None:
        """
        注册管道步骤。

        该方法用于注册聊天相关的管道处理步骤，包括确保聊天会话、发送文本消息和发送文件消息的处理逻辑。
        每个步骤都通过 lambda 函数封装，以便在管道执行时调用相应的实现方法。
        """
        self.pipeline.register("ensure_chat", lambda context: context["client"]._ensure_chat(context.get("who")))
        self.pipeline.register("send_text", lambda context: context["client"]._send_text_impl(context))
        self.pipeline.register("send_file", lambda context: context["client"]._send_file_impl(context))

    def _ensure_chat(self, who: Optional[str]):
        """
        确保与指定用户的聊天会话已打开。

        Args:
            who: 聊天对象的名称或标识，如果为空则返回 None。

        Returns:
            聊天对象名称，如果 who 为空则返回 None。
        """
        if not who:
            return None
        return self.interaction.run("chat.chat_with", lambda: self._keyboard_chat_with(who), foreground_required=True)

    def _send_text_impl(self, context: dict):
        """
        发送文本消息的实现方法。

        Args:
            context: 包含消息发送上下文的字典，必须包含 'text' 键，可选包含 'who' 和 'clear' 键。

        Returns:
            发送结果，由交互运行器返回。
        """
        who = context.get("who")
        text = context["text"]
        return self.interaction.run(
            "message.send_text",
            lambda: self._keyboard_send_text(text, who=who, clear=context.get("clear", True)),
            foreground_required=True,
        )

    def _send_file_impl(self, context: dict):
        """
        发送文件消息的实现方法。

        Args:
            context: 包含文件发送上下文的字典，必须包含 'paths' 键，可选包含 'who' 键。

        Returns:
            发送结果，由交互运行器返回。
        """
        who = context.get("who")
        paths = context["paths"]
        return self.interaction.run(
            "message.send_file",
            lambda: self._keyboard_send_file(paths, who=who),
            foreground_required=True,
        )

    def _keyboard_chat_with(self, who: str):
        """
        通过键盘操作切换到指定的聊天会话。

        该方法使用快捷键 Ctrl+F 打开搜索框，粘贴目标联系人名称，然后按回车键进入聊天。

        Args:
            who: 聊天对象的名称。

        Returns:
            聊天对象名称。
        """
        from wechat_sdk.core.clipboard import set_text
        from wechat_sdk.core.keyboard import hotkey, press

        hotkey("ctrl", "f", wait=0.2)
        set_text(who)
        hotkey("ctrl", "v", wait=0.8)
        press("enter", wait=0.5)
        self._current_chat = who
        self._last_message_ids = set()
        return who

    def _keyboard_send_text(self, text: str, who: Optional[str] = None, clear: bool = True):
        """
        通过键盘操作发送文本消息。

        该方法首先确保与目标用户的聊天会话已打开（如果提供了 who 参数），
        然后清空输入框（如果 clear 为 True），将文本粘贴到输入框并发送。

        Args:
            text: 要发送的文本内容。
            who: 聊天对象的名称，如果提供则先切换到该聊天。
            clear: 是否在发送前清空输入框，默认为 True。

        Returns:
            始终返回 True 表示操作完成。
        """
        from wechat_sdk.core.clipboard import set_text
        from wechat_sdk.core.keyboard import hotkey, press

        if who:
            self._keyboard_chat_with(who)
        if clear:
            hotkey("ctrl", "a", wait=0.1)
        set_text(text)
        hotkey("ctrl", "v", wait=0.1)
        press("enter", wait=0.1)
        return True

    def _keyboard_send_file(self, paths: list[str], who: Optional[str] = None):
        """
        通过键盘操作发送文件消息。

        该方法首先确保与目标用户的聊天会话已打开（如果提供了 who 参数），
        然后将文件路径复制到剪贴板，粘贴并发送文件。

        Args:
            paths: 要发送的文件路径列表。
            who: 聊天对象的名称，如果提供则先切换到该聊天。

        Returns:
            始终返回 True 表示操作完成。
        """
        from wechat_sdk.core.clipboard import set_files
        from wechat_sdk.core.keyboard import hotkey, press

        if who:
            self._keyboard_chat_with(who)
        set_files(paths)
        hotkey("ctrl", "v", wait=0.3)
        press("enter", wait=0.2)
        return True

    def _window_rect(self) -> tuple[int, int, int, int]:
        """
        获取微信窗口的矩形区域坐标。

        Returns:
            包含窗口左上角和右下角坐标的元组 (left, top, right, bottom)。
        """
        return win32gui.GetWindowRect(self.window.hwnd)

    def _click_relative(self, x_ratio: float, y_ratio: float) -> None:
        """
        在窗口内按相对坐标点击。

        根据窗口大小和给定的相对比例计算实际点击位置，然后执行鼠标点击操作。

        Args:
            x_ratio: X 轴方向的相对比例（0.0-1.0）。
            y_ratio: Y 轴方向的相对比例（0.0-1.0）。
        """
        from wechat_sdk.core.mouse import click

        left, top, right, bottom = self._window_rect()
        x = left + int((right - left) * x_ratio)
        y = top + int((bottom - top) * y_ratio)
        click(x, y)

    def _copy_selected_text(self) -> str:
        """
        复制当前选中的文本内容。

        通过快捷键 Ctrl+A 全选文本，然后 Ctrl+C 复制到剪贴板，最后从剪贴板读取文本。

        Returns:
            复制的文本内容。
        """
        from wechat_sdk.core.clipboard import get_text
        from wechat_sdk.core.keyboard import hotkey

        hotkey("ctrl", "a", wait=0.1)
        hotkey("ctrl", "c", wait=0.2)
        return get_text()

    def _copy_session_list(self) -> list[str]:
        """
        获取会话列表。

        首先尝试通过 UIA 获取会话列表，如果失败则通过点击相对位置并复制文本来解析会话列表。

        Returns:
            会话名称列表。
        """
        sessions = self._uia_session_list()
        if sessions:
            return sessions
        self._click_relative(0.24, 0.50)
        text = self._copy_selected_text()
        return self._parse_session_text(text)

    def _copy_all_messages(self):
        """
        获取所有消息。

        首先尝试通过 UIA 获取消息列表，如果失败则通过点击相对位置并复制文本来解析消息。

        Returns:
            消息对象列表，每个消息包含 sender、content 和 raw 信息。
        """
        messages = self._uia_all_messages()
        if messages:
            return messages
        self._click_relative(0.68, 0.50)
        text = self._copy_selected_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return [
            Message(sender="", content=line, raw={"line": index, "source": "clipboard"})
            for index, line in enumerate(lines)
        ]

    def _uia_controls(self):
        """
        获取窗口内所有的 UIA 控件。

        通过 UIA 自动化接口查找窗口内的所有 descendant 控件，并将它们包装为 UIAControl 对象。

        Returns:
            UIAControl 对象列表。
        """
        from wechat_sdk.core.uia import UIAControl, TreeScope_Descendants, automation, control_from_handle

        root = control_from_handle(self.window.hwnd)
        items = root.element.FindAll(TreeScope_Descendants, automation().CreateTrueCondition())
        return [UIAControl(items.GetElement(index)) for index in range(items.Length)]

    def _uia_current_chat(self) -> Optional[str]:
        """
        获取当前聊天会话的名称。

        通过遍历 UIA 控件查找带有 'current_chat_name_label' 后缀 AutomationId 的控件，
        并返回其 Name 属性作为当前聊天名称。

        Returns:
            当前聊天会话名称，如果未找到则返回 None。
        """
        try:
            for control in self._uia_controls():
                if control.AutomationId.endswith("current_chat_name_label") and control.Name:
                    self._current_chat = control.Name
                    return control.Name
        except Exception:
            logger.debug("Unable to read current chat from UIA", exc_info=True)
        return None

    def _uia_click_tab(self, name: str) -> bool:
        """
        点击指定的标签页。

        遍历所有 UIA 控件，查找 ClassName 为 'mmui::XTabBarItem' 且 Name 匹配的控件，然后点击它。

        Args:
            name: 标签页的名称。

        Returns:
            如果找到并点击成功返回 True，否则返回 False。
        """
        for control in self._uia_controls():
            if control.ClassName == "mmui::XTabBarItem" and control.Name == name:
                self._click_control(control)
                return True
        return False

    def _uia_session_list(self) -> list[str]:
        """
        通过 UIA 获取会话列表。

        遍历所有 UIA 控件，筛选出 ClassName 为 'mmui::ChatSessionCell' 的控件，
        解析其 Name 属性获取会话名称，并去重后返回列表。

        Returns:
            会话名称列表，如果发生异常则返回空列表。
        """
        try:
            sessions = []
            for control in self._uia_controls():
                if control.ClassName != "mmui::ChatSessionCell":
                    continue
                name = self._parse_session_name(control.Name)
                if name and name not in sessions:
                    sessions.append(name)
            return sessions
        except Exception:
            logger.debug("Unable to read session list from UIA", exc_info=True)
            return []

    def _uia_unread_sessions(self, personal_only: bool = True, max_sessions: Optional[int] = None) -> list[dict]:
        """
        获取未读会话列表。

        切换到聊天标签页，遍历所有会话控件，筛选出有未读消息、未静音且符合个人会话条件的会话。

        Args:
            personal_only: 是否只返回个人会话，排除群聊等，默认为 True。
            max_sessions: 最大返回会话数量，如果为 None 则不限制。

        Returns:
            未读会话信息列表，每个元素包含会话名称、未读数等信息。
        """
        self.switch_to_chat_tab()
        sessions = []
        for control in self._uia_session_controls():
            parsed = self._parse_session_cell(control)
            if not parsed["unread_count"]:
                continue
            if parsed["muted"]:
                continue
            if personal_only and not self._looks_like_personal_session(parsed["name"]):
                continue
            parsed.pop("_control", None)
            sessions.append(parsed)
            if max_sessions is not None and len(sessions) >= max_sessions:
                break
        return sessions

    def _uia_get_unread_messages(self, personal_only: bool = True, max_sessions: Optional[int] = None):
        """
        获取未读消息内容。

        切换到聊天标签页，遍历所有未读会话，逐个点击进入并获取最新的未读消息。

        Args:
            personal_only: 是否只获取个人会话的消息，默认为 True。
            max_sessions: 最大处理的会话数量，如果为 None 则不限制。

        Returns:
            字典，键为聊天名称，值为该聊天的未读消息列表。
        """
        payload = {}
        self.switch_to_chat_tab()
        sessions = []
        for control in self._uia_session_controls():
            session = self._parse_session_cell(control)
            if not session["unread_count"]:
                continue
            if session["muted"]:
                continue
            if personal_only and not self._looks_like_personal_session(session["name"]):
                continue
            sessions.append(session)
            if max_sessions is not None and len(sessions) >= max_sessions:
                break
        for session in sessions:
            control = session.get("_control")
            if not control:
                continue
            self._click_control(control)
            time.sleep(0.5)
            chat_name = self.current_chat() or session["name"]
            if personal_only and not self._looks_like_personal_session(chat_name):
                continue
            messages = self.get_all_message()
            unread_count = max(1, int(session["unread_count"]))
            payload[chat_name] = messages[-unread_count:] if len(messages) > unread_count else messages
        return payload

    def _uia_session_controls(self):
        """
        获取所有会话控件。

        筛选出 ClassName 为 'mmui::ChatSessionCell' 且 Name 不为空的 UIA 控件。

        Returns:
            会话控件列表。
        """
        return [
            control for control in self._uia_controls()
            if control.ClassName == "mmui::ChatSessionCell" and control.Name.strip()
        ]

    def _parse_session_cell(self, control) -> dict:
        """
        解析会话单元格控件的信息。

        从控件的 Name 属性中提取会话名称、未读消息数、免打扰状态和预览消息。

        Args:
            control: UIA 会话单元格控件。

        Returns:
            包含会话信息的字典，包括 name、unread_count、muted、preview 和 raw 等信息。
        """
        lines = [line.strip() for line in control.Name.splitlines() if line.strip()]
        unread_count = 0
        for line in lines[1:]:
            match = re.fullmatch(r"\[(\d+)条\]", line)
            if match:
                unread_count = int(match.group(1))
                break
        preview_lines = [
            line for line in lines[1:]
            if not re.fullmatch(r"\[(\d+)条\]", line) and line != "消息免打扰"
        ]
        return {
            "name": lines[0] if lines else "",
            "unread_count": unread_count,
            "muted": "消息免打扰" in lines,
            "preview": preview_lines[0] if preview_lines else "",
            "raw": {
                "source": "uia",
                "runtime_id": self._uia_runtime_id(control),
                "class_name": control.ClassName,
                "automation_id": control.AutomationId,
                "rect": control.BoundingRectangle,
                "line_count": len(lines),
            },
            "_control": control,
        }

    @staticmethod
    def _looks_like_personal_session(name: str) -> bool:
        """
        判断会话名称是否为个人会话。

        检查会话名称中是否包含群聊、公众号等非个人会话的关键词。

        Args:
            name: 会话名称。

        Returns:
            如果是个人会话返回 True，否则返回 False。
        """
        if not name:
            return False
        blocked = ("群", "公众号", "服务号", "订阅号", "企业微信联系人")
        return not any(keyword in name for keyword in blocked)

    def _uia_get_all_friends(self, max_pages: int = 20) -> list[str]:
        """
        获取所有好友列表。

        切换到联系人标签页，通过分页滚动的方式遍历所有可见的联系人控件，收集好友名称。

        Args:
            max_pages: 最大翻页次数，默认为 20。

        Returns:
            好友名称列表。
        """
        from wechat_sdk.core.keyboard import press

        self.switch_to_contact_tab()
        contact_list = self._uia_find_first(class_name="mmui::StickyHeaderRecyclerListView", automation_id="primary_table_.contact_list")
        if contact_list:
            self._click_control(contact_list)
            press("home", wait=0.2)
        contact_group = self._uia_contact_group()
        if contact_group and not self._uia_visible_user_contact_controls():
            self._click_control(contact_group)
        friends: list[str] = []
        stale_pages = 0
        for _ in range(max_pages):
            before = len(friends)
            for name in self._uia_visible_user_contact_names():
                if name not in friends:
                    friends.append(name)
            if len(friends) == before:
                stale_pages += 1
                if stale_pages >= 2:
                    break
            else:
                stale_pages = 0
            press("pagedown", wait=0.2)
        return friends

    def _uia_search_contacts(self, keyword: str) -> list[str]:
        """
        搜索联系人。

        切换到联系人标签页，在搜索框中输入关键词，然后返回匹配的联系人列表。

        Args:
            keyword: 搜索关键词。

        Returns:
            匹配的联系人名称列表，如果未找到搜索框则返回空列表。
        """
        from wechat_sdk.core.clipboard import set_text
        from wechat_sdk.core.keyboard import hotkey

        self.switch_to_contact_tab()
        search = self._uia_find_first(class_name="mmui::XValidatorTextEdit", name="搜索")
        if not search:
            return []
        self._click_control(search)
        hotkey("ctrl", "a", wait=0.1)
        set_text(keyword)
        hotkey("ctrl", "v", wait=0.5)
        if keyword:
            return self._uia_visible_contact_names()
        return self._uia_visible_user_contact_names()

    def _uia_get_friend_details(self, who: Optional[str] = None) -> dict:
        """
        获取好友详细信息。

        如果提供了 who 参数，则先搜索该联系人并点击进入详情页；
        否则获取第一个联系人的详情。然后遍历所有 UIA 控件提取姓名、微信号等信息。

        Args:
            who: 联系人名称，如果为 None 则获取第一个联系人的详情。

        Returns:
            包含好友详细信息的字典，包括 name、wechat_id、texts 和 raw 等字段。
        """
        if who:
            matches = self._uia_search_contacts(who)
            if not matches:
                return {}
            contact = self._uia_find_first(class_name="mmui::ContactsCellItemView", contains_name=who)
        else:
            self.switch_to_contact_tab()
            contact_list = self._uia_find_first(class_name="mmui::StickyHeaderRecyclerListView", automation_id="primary_table_.contact_list")
            if contact_list:
                self._click_control(contact_list)
            controls = self._uia_visible_user_contact_controls()
            contact = controls[0] if controls else None
        if contact:
            self._click_control(contact)
        controls = self._uia_controls()
        details = {
            "name": "",
            "wechat_id": "",
            "texts": [],
            "raw": [],
        }
        last_label = ""
        for control in controls:
            if control.AutomationId.endswith("display_name_text") and control.Name:
                details["name"] = control.Name
            elif control.ClassName == "mmui::ContactHeadView" and control.Name and not details["name"]:
                details["name"] = control.Name
            elif control.ClassName == "mmui::XTextView" and control.Name.endswith("："):
                last_label = control.Name.strip("：")
            elif control.ClassName == "mmui::ProfileTextView" and control.Name:
                text = control.Name.strip()
                if last_label and last_label not in details:
                    details[last_label] = text
                    if "微信号" in last_label:
                        details["wechat_id"] = text
                    last_label = ""
                if text not in details["texts"]:
                    details["texts"].append(text)
            if control.ClassName.startswith("mmui::Profile") or control.AutomationId.startswith("right_v_view"):
                details["raw"].append(
                    {
                        "control_type": control.ControlTypeName,
                        "class_name": control.ClassName,
                        "name": control.Name,
                        "automation_id": control.AutomationId,
                    }
                )
        return details

    def _uia_contact_group(self):
        """
        查找联系人分组控件。

        遍历所有 UIA 控件，查找 ClassName 为 'mmui::ContactsCellGroupView' 且名称包含"联系人"的控件。

        Returns:
            联系人分组控件，如果未找到则返回 None。
        """
        for control in self._uia_controls():
            if control.ClassName == "mmui::ContactsCellGroupView" and "联系人" in control.Name:
                return control
        return None

    def _uia_visible_user_contact_controls(self):
        """
        获取可见的个人联系人控件列表。

        首先查找联系人分组控件，然后筛选出位于分组下方的个人联系人控件。
        如果未找到分组，则返回所有个人联系人控件。

        Returns:
            个人联系人控件列表。
        """
        controls = self._uia_controls()
        contact_group = next(
            (
                control for control in controls
                if control.ClassName == "mmui::ContactsCellGroupView" and "联系人" in control.Name
            ),
            None,
        )
        if not contact_group or not contact_group.BoundingRectangle:
            return [
                control for control in controls
                if control.ClassName == "mmui::ContactsCellItemView" and control.Name.strip()
            ]
        group_bottom = contact_group.BoundingRectangle[3]
        user_controls = []
        for control in controls:
            if control.ClassName != "mmui::ContactsCellItemView" or not control.BoundingRectangle:
                continue
            if control.BoundingRectangle[1] >= group_bottom:
                user_controls.append(control)
        return user_controls

    def _uia_visible_user_contact_names(self) -> list[str]:
        """
        获取可见的个人联系人名称列表。

        遍历所有可见的个人联系人控件，提取其名称并去重。

        Returns:
            个人联系人名称列表。
        """
        names = []
        for control in self._uia_visible_user_contact_controls():
            name = control.Name.strip()
            if name and name not in names:
                names.append(name)
        return names

    def _uia_visible_contact_names(self) -> list[str]:
        """
        获取所有可见的联系人名称列表。

        遍历所有 UIA 控件，筛选出 ClassName 为 'mmui::ContactsCellItemView' 的控件，
        提取其名称并去重。

        Returns:
            联系人名称列表。
        """
        names = []
        for control in self._uia_controls():
            if control.ClassName != "mmui::ContactsCellItemView":
                continue
            name = control.Name.strip()
            if name and name not in names:
                names.append(name)
        return names

    def _uia_get_new_friends(self, max_pages: int = 5) -> list[dict]:
        """
        获取新朋友列表。

        切换到联系人标签页，点击"新的朋友"入口，然后通过分页滚动获取所有新朋友信息。

        Args:
            max_pages: 最大翻页次数，默认为 5。

        Returns:
            新朋友信息列表，每个元素包含 id、text、status 和 raw 等信息。
        """
        from wechat_sdk.core.keyboard import press

        self.switch_to_contact_tab()
        entry = self._uia_wait_first(
            timeout=2.0,
            class_name="mmui::ContactsCellGroupView",
            contains_name="新的朋友",
        )
        if not entry:
            return []
        self._click_control(entry)
        time.sleep(0.5)

        friends: list[dict] = []
        seen = set()
        for _ in range(max(1, max_pages)):
            before = len(friends)
            for control in self._uia_new_friend_controls():
                item = self._parse_new_friend_item(control)
                key = item.get("id") or item["text"]
                if key in seen:
                    continue
                seen.add(key)
                friends.append(item)
            if len(friends) == before:
                break
            press("pagedown", wait=0.2)
        return friends

    def _uia_new_friend_controls(self):
        """
        获取新朋友列表中的单元格控件。

        查找联系人列表控件，然后筛选出位于列表区域内的 TableCell 控件，并按位置排序。

        Returns:
            新朋友单元格控件列表，按垂直位置排序。
        """
        controls = self._uia_controls()
        contact_list = self._uia_find_first(
            class_name="mmui::StickyHeaderRecyclerListView",
            automation_id="primary_table_.contact_list",
        )
        rect = contact_list.BoundingRectangle if contact_list else None
        cells = []
        for control in controls:
            if control.ClassName != "mmui::XTableCell" or not control.Name.strip():
                continue
            if rect and control.BoundingRectangle:
                left, top, right, bottom = control.BoundingRectangle
                if left < rect[0] or right > rect[2] or bottom < rect[1] or top > rect[3] + 80:
                    continue
            cells.append(control)
        return sorted(cells, key=lambda control: control.BoundingRectangle or (0, 0, 0, 0))

    def _parse_new_friend_item(self, control) -> dict:
        """
        解析新朋友单元格的信息。

        从控件的 Name 属性中提取文本内容和状态（如等待验证、已添加等）。

        Args:
            control: 新朋友单元格控件。

        Returns:
            包含新朋友信息的字典，包括 id、text、status 和 raw 等字段。
        """
        text = control.Name.strip()
        status = ""
        for candidate in ("等待验证", "已添加", "已过期", "已拒绝"):
            if text.endswith(candidate):
                status = candidate
                break
        return {
            "id": repr(self._uia_runtime_id(control)),
            "text": text,
            "status": status,
            "raw": {
                "source": "uia",
                "runtime_id": self._uia_runtime_id(control),
                "class_name": control.ClassName,
                "automation_id": control.AutomationId,
                "rect": control.BoundingRectangle,
            },
        }

    def _uia_load_more_messages(self, pages: int = 1):
        """
        加载更多消息。

        通过向上翻页的方式加载历史消息，每次翻一页。

        Args:
            pages: 要加载的页数，默认为 1。

        Returns:
            所有消息列表。
        """
        for _ in range(max(1, pages)):
            self._uia_page_up_message_list(steps=1)
            time.sleep(0.2)
        return self._uia_all_messages()

    def _uia_get_history(self, max_pages: int = 10, limit: Optional[int] = None):
        """
        获取历史消息。

        通过向上翻页的方式逐步加载历史消息，直到达到最大页数或消息数量限制。
        使用消息 ID 去重，避免重复加载相同的消息。

        Args:
            max_pages: 最大翻页次数，默认为 10。
            limit: 最大返回消息数量，如果为 None 则不限制。

        Returns:
            历史消息列表，按时间顺序排列。
        """
        if limit is not None and limit <= 0:
            return []
        history = []
        seen = set()
        stale_pages = 0

        for _ in range(max(1, max_pages)):
            page_messages = self._uia_all_messages()
            new_page = []
            for message in page_messages:
                message_id = self._message_id(message)
                if message_id in seen:
                    continue
                seen.add(message_id)
                new_page.append(message)
            if new_page:
                history = new_page + history
                stale_pages = 0
            else:
                stale_pages += 1
                if stale_pages >= 2:
                    break
            if limit is not None and len(history) >= limit:
                return history[-limit:]
            self._uia_page_up_message_list(steps=1)
            time.sleep(0.2)
        return history[-limit:] if limit is not None else history

    def _uia_page_up_message_list(self, steps: int) -> None:
        """
        向上滚动消息列表。

        首先点击消息列表控件使其获得焦点，然后按指定步数执行 PageUp 操作。

        Args:
            steps: 向上滚动的步数。
        """
        from wechat_sdk.core.keyboard import press

        message_list = self._uia_message_list()
        if message_list:
            self._click_control(message_list)
        for _ in range(steps):
            press("pageup", wait=0.1)

    def _uia_message_list(self):
        """
        获取消息列表控件。

        查找 ClassName 为 'mmui::RecyclerListView' 且 AutomationId 为 'chat_message_list' 的控件。

        Returns:
            消息列表控件，如果未找到则返回 None。
        """
        return self._uia_find_first(class_name="mmui::RecyclerListView", automation_id="chat_message_list")

    def _uia_get_group_members(self, max_pages: int = 50) -> list[str]:
        """
        获取群组成员列表。

        打开聊天信息面板，展开群组成员列表，然后通过滚动加载所有成员名称。

        Args:
            max_pages: 最大滚动次数，默认为 50。

        Returns:
            群组成员名称列表。
        """
        import win32api
        import win32con

        if not self._uia_open_chat_info_panel():
            return []
        self._uia_expand_group_members()
        self._uia_scroll_group_member_panel(direction=1, steps=60, wait=0.03)

        members: list[str] = []
        stale_pages = 0
        for _ in range(max_pages):
            before = len(members)
            for name in self._uia_visible_group_member_names():
                if name not in members:
                    members.append(name)
            if len(members) == before:
                stale_pages += 1
                if stale_pages >= 20:
                    break
            else:
                stale_pages = 0
            member_list = self._uia_group_member_list()
            rect = member_list.BoundingRectangle if member_list else None
            if rect:
                left, top, right, bottom = rect
                win32api.SetCursorPos((left + (right - left) // 2, top + (bottom - top) // 2))
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -120, 0)
            time.sleep(0.2)
        return members

    def _uia_open_chat_info_panel(self) -> bool:
        """
        打开聊天信息面板。

        如果群组成员列表或聊天信息面板已存在，则直接返回；
        否则查找并点击"聊天信息"按钮，等待面板加载完成。

        Returns:
            如果成功打开聊天信息面板返回 True，否则返回 False。
        """
        if self._uia_group_member_list():
            return True
        if self._uia_chat_info_panel():
            self._uia_scroll_group_member_panel(direction=1, steps=60, wait=0.03)
            return self._uia_group_member_list() is not None
        button = next(
            (
                control for control in self._uia_controls()
                if control.Name == "聊天信息" or "more_button" in control.AutomationId
            ),
            None,
        )
        if not button:
            return False
        self._click_control(button)
        time.sleep(0.5)
        self._uia_scroll_group_member_panel(direction=1, steps=60, wait=0.03)
        return self._uia_group_member_list() is not None

    def _uia_expand_group_members(self) -> None:
        """
        展开群组成员列表。

        检查当前可见的成员数量，如果少于预期则点击展开按钮加载更多成员。

        该方法会根据当前显示的成员数量和预期的成员总数来判断是否需要展开更多成员。
        """
        members = self._uia_visible_group_member_controls()
        expected = self._group_member_count_hint()
        if not members or len(members) >= 20:
            return
        if expected is not None and len(members) >= expected:
            return
        bottoms = [control.BoundingRectangle[3] for control in members if control.BoundingRectangle]
        member_list = self._uia_group_member_list()
        if not bottoms or not member_list or not member_list.BoundingRectangle:
            return
        left, top, right, bottom = member_list.BoundingRectangle
        click_y = min(max(bottoms) + 20, bottom - 8)
        self._click_xy(left + (right - left) // 2, click_y)
        time.sleep(0.5)

    def _uia_scroll_group_member_panel(self, direction: int, steps: int, wait: float) -> None:
        """
        滚动群组成员面板。

        将鼠标移动到成员列表区域，然后按指定方向和步数执行滚轮操作。

        Args:
            direction: 滚动方向，1 表示向下，-1 表示向上。
            steps: 滚动步数。
            wait: 每步之间的等待时间（秒）。
        """
        import win32api
        import win32con

        member_list = self._uia_group_member_list() or self._uia_chat_info_panel()
        rect = member_list.BoundingRectangle if member_list else None
        if rect:
            left, top, right, bottom = rect
            win32api.SetCursorPos((left + (right - left) // 2, top + (bottom - top) // 2))
        for _ in range(steps):
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, direction * 120, 0)
            time.sleep(wait)

    def _uia_group_member_list(self):
        """
        获取群组成员列表控件。

        查找 ClassName 为 'QFReuseGridWidget' 且 AutomationId 为 'chat_member_list' 的控件。

        Returns:
            群组成员列表控件，如果未找到则返回 None。
        """
        return self._uia_find_first(class_name="QFReuseGridWidget", automation_id="chat_member_list")

    def _uia_chat_info_panel(self):
        """
        获取聊天信息面板控件。

        查找 ClassName 为 'mmui::ChatRoomMemberInfoView' 的控件。

        Returns:
            聊天信息面板控件，如果未找到则返回 None。
        """
        return self._uia_find_first(class_name="mmui::ChatRoomMemberInfoView")

    def _uia_visible_group_member_controls(self):
        """
        获取可见的群组成员控件列表。

        筛选出 ClassName 为 'mmui::ChatMemberCell' 且名称不为空的控件。

        Returns:
            群组成员控件列表。
        """
        return [
            control for control in self._uia_controls()
            if control.ClassName == "mmui::ChatMemberCell" and control.Name.strip()
        ]

    def _uia_visible_group_member_names(self) -> list[str]:
        """
        获取可见的群组成员名称列表。

        获取所有可见的群组成员控件，按位置排序后提取名称。

        Returns:
            群组成员名称列表。
        """
        controls = sorted(
            self._uia_visible_group_member_controls(),
            key=lambda control: control.BoundingRectangle or (0, 0, 0, 0),
        )
        return [control.Name.strip() for control in controls]

    def _group_member_count_hint(self) -> Optional[int]:
        """
        从当前聊天名称中提取群组成员数量提示。

        尝试从聊天名称末尾的括号中提取数字，例如 "测试群(50)" 会返回 50。

        Returns:
            群组成员数量，如果未找到则返回 None。
        """
        chat = self.current_chat() or ""
        match = re.search(r"[（(](\d+)[）)]\s*$", chat)
        return int(match.group(1)) if match else None

    def _uia_find_first(self, **criteria):
        """
        查找第一个匹配的 UIA 控件。

        遍历所有 UIA 控件，根据给定的条件（如 class_name、automation_id、name 等）进行匹配。

        Args:
            **criteria: 匹配条件，支持 class_name、control_type、automation_id、name、contains_name 等。

        Returns:
            第一个匹配的控件，如果未找到则返回 None。
        """
        for control in self._uia_controls():
            if self._uia_matches(control, criteria):
                return control
        return None

    def _uia_wait_first(self, timeout: float = 1.0, **criteria):
        """
        等待第一个匹配的 UIA 控件出现。

        在指定的超时时间内循环查找匹配的控件，直到找到或超时。

        Args:
            timeout: 超时时间（秒），默认为 1.0。
            **criteria: 匹配条件，传递给 _uia_find_first 方法。

        Returns:
            找到的控件，如果超时仍未找到则返回 None。
        """
        deadline = time.time() + timeout
        while True:
            control = self._uia_find_first(**criteria)
            if control or time.time() >= deadline:
                return control
            time.sleep(0.05)

    def _uia_all_messages(self) -> list[Message]:
        """
        获取所有消息。

        遍历所有 UIA 控件，筛选出消息项控件，提取消息内容、类型和元数据。

        Returns:
            消息对象列表，如果发生异常则返回空列表。
        """
        try:
            messages = []
            for index, control in enumerate(self._uia_controls()):
                if not self._is_message_item(control):
                    continue
                content = control.Name.strip()
                if not content:
                    continue
                messages.append(
                    Message(
                        sender="",
                        content=content,
                        type=self._message_type_from_class(control.ClassName),
                        raw={
                            "index": index,
                            "source": "uia",
                            "runtime_id": self._uia_runtime_id(control),
                            "class_name": control.ClassName,
                            "automation_id": control.AutomationId,
                            "rect": control.BoundingRectangle,
                        },
                    )
                )
            return messages
        except Exception:
            logger.debug("Unable to read messages from UIA", exc_info=True)
            return []

    @staticmethod
    def _parse_session_name(text: str) -> str:
        """
        解析会话名称。

        从多行文本中提取第一个非空行作为会话名称。

        Args:
            text: 包含会话名称的文本。

        Returns:
            会话名称，如果未找到则返回空字符串。
        """
        for line in text.splitlines():
            item = line.strip()
            if item:
                return item
        return ""

    @staticmethod
    def _is_message_item(control) -> bool:
        """
        判断控件是否为消息项。

        检查控件的类型是否为 ListItemControl，且 ClassName 以 'mmui::Chat' 开头并以 'ItemView' 结尾。

        Args:
            control: UIA 控件。

        Returns:
            如果是消息项返回 True，否则返回 False。
        """
        return (
            control.ControlTypeName == "ListItemControl"
            and control.ClassName.startswith("mmui::Chat")
            and control.ClassName.endswith("ItemView")
        )

    @staticmethod
    def _uia_matches(control, criteria: dict) -> bool:
        """
        检查控件是否匹配给定的条件。

        依次检查 class_name、control_type、automation_id、name 和 contains_name 等条件。

        Args:
            control: UIA 控件。
            criteria: 匹配条件字典。

        Returns:
            如果所有条件都匹配返回 True，否则返回 False。
        """
        class_name = criteria.get("class_name")
        if class_name is not None and control.ClassName != class_name:
            return False
        control_type = criteria.get("control_type")
        if control_type is not None and control.ControlTypeName != control_type:
            return False
        automation_id = criteria.get("automation_id")
        if automation_id is not None and control.AutomationId != automation_id:
            return False
        name = criteria.get("name")
        if name is not None and control.Name != name:
            return False
        contains_name = criteria.get("contains_name")
        if contains_name is not None and contains_name not in control.Name:
            return False
        return True

    @staticmethod
    def _message_type_from_class(class_name: str) -> str:
        """
        根据控件类名推断消息类型。

        Args:
            class_name: 控件的 ClassName。

        Returns:
            消息类型，可能是 'voice'、'rich' 或 'text'。
        """
        if "Voice" in class_name:
            return "voice"
        if "Refer" in class_name or "Bubble" in class_name:
            return "rich"
        return "text"

    @staticmethod
    def _uia_runtime_id(control):
        """
        获取控件的运行时 ID。

        Args:
            control: UIA 控件。

        Returns:
            运行时 ID 元组，如果获取失败则返回 None。
        """
        try:
            return tuple(control.element.GetRuntimeId())
        except Exception:
            return None

    @staticmethod
    def _click_control(control) -> None:
        """
        点击控件的中心位置。

        Args:
            control: UIA 控件，必须具有有效的 BoundingRectangle。
        """
        from wechat_sdk.core.mouse import click

        rect = control.BoundingRectangle
        if not rect:
            return
        left, top, right, bottom = rect
        click(left + (right - left) // 2, top + (bottom - top) // 2)

    @staticmethod
    def _click_xy(x: int, y: int) -> None:
        """
        点击指定的坐标位置。

        Args:
            x: X 坐标。
            y: Y 坐标。
        """
        from wechat_sdk.core.mouse import click

        click(x, y)

    @staticmethod
    def _parse_session_text(text: str) -> list[str]:
        """
        解析会话文本。

        将多行文本按行分割，提取非空行并去重。

        Args:
            text: 包含会话信息的文本。

        Returns:
            会话名称列表。
        """
        sessions = []
        for line in text.splitlines():
            item = line.strip()
            if item and item not in sessions:
                sessions.append(item)
        return sessions

    @staticmethod
    def _message_id(message) -> str:
        """
        生成消息的唯一标识符。

        优先使用消息的 id 属性，如果不存在则使用 raw 属性和 content 属性组合生成。

        Args:
            message: 消息对象。

        Returns:
            消息的唯一标识符字符串。
        """
        message_id = getattr(message, "id", None)
        if message_id:
            return str(message_id)
        raw = getattr(message, "raw", None)
        content = getattr(message, "content", repr(message))
        return f"{raw!r}:{content}"

    @staticmethod
    def _normalize_paths(path_or_paths) -> list[str]:
        """
        标准化文件路径。

        将单个路径或路径列表转换为字符串路径列表，并验证文件是否存在。

        Args:
            path_or_paths: 单个路径（字符串或 Path 对象）或路径列表。

        Returns:
            标准化的文件路径列表。

        Raises:
            TypeError: 如果输入类型不正确。
            FileNotFoundError: 如果文件不存在。
        """
        if isinstance(path_or_paths, (str, Path)):
            paths = [str(path_or_paths)]
        elif isinstance(path_or_paths, Iterable):
            paths = [str(path) for path in path_or_paths]
        else:
            raise TypeError("path_or_paths must be a path or iterable of paths")
        for path in paths:
            if not Path(path).exists():
                raise FileNotFoundError(path)
        return paths
