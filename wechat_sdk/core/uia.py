"""
UIAutomation核心模块

提供Windows UI Automation (UIA)的底层封装，用于识别和操作微信客户端的UI元素。
这是整个SDK的核心技术基础，通过系统级UI自动化实现与微信的交互。

作者: CMX

主要功能:
    - UI元素树遍历和查找
    - 控件属性读取（名称、类型、位置等）
    - 基于多种条件的元素匹配
    - UI树结构调试输出

技术原理:
    Windows UI Automation是微软提供的辅助技术和自动化测试框架，
    可以访问应用程序的UI元素树，读取控件信息并执行操作。
    相比图像识别或内存注入，UIA更稳定且不易被检测。

主要类:
    UIAControl: UI控件的封装，提供属性访问和查找方法
    UIAFinder: 基于选择器的UI元素查找器

常量:
    TreeScope_Element/Children/Descendants: 搜索范围枚举
    UIA_*PropertyId: UIA属性ID常量
    CONTROL_TYPE_NAMES: 控件类型名称映射

使用示例:
    >>> from wechat_sdk.core.uia import control_from_handle
    >>> root = control_from_handle(hwnd)
    >>> buttons = root.FindAll(max_depth=5, 
    ...     predicate=lambda c: c.ClassName == "Button")
    >>> for btn in buttons:
    ...     print(f"按钮: {btn.Name}, 位置: {btn.BoundingRectangle}")
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import time
from typing import Any, Callable, Iterable, Optional

import comtypes.client
from comtypes import GUID

from wechat_sdk.errors import ControlNotFoundError


# UI Automation搜索范围常量
# 定义在UIAutomation API中，用于指定元素搜索的深度范围
TreeScope_Element = 1      # 只搜索当前元素本身
TreeScope_Children = 2     # 只搜索直接子元素
TreeScope_Descendants = 4  # 搜索所有后代元素（递归）

# UI Automation属性ID常量
# 这些ID定义在UIAutomation API中，用于获取控件的不同属性
UIA_BoundingRectanglePropertyId = 30001  # 控件的边界矩形（位置和大小）
UIA_ControlTypePropertyId = 30003        # 控件类型（按钮、文本框等）
UIA_NamePropertyId = 30005               # 控件名称（显示文本）
UIA_AutomationIdPropertyId = 30011       # 自动化ID（开发时指定的唯一标识）
UIA_ClassNamePropertyId = 30012          # 控件类名（技术类型标识）
UIA_NativeWindowHandlePropertyId = 30020 # 原生窗口句柄

# 控件类型ID到名称的映射表
# Windows UIA定义了多种标准控件类型，每种有唯一的数字ID
# 这个字典将数字ID转换为可读的名称
CONTROL_TYPE_NAMES = {
    50000: "ButtonControl",         # 按钮
    50001: "CalendarControl",       # 日历
    50002: "CheckBoxControl",       # 复选框
    50003: "ComboBoxControl",       # 下拉框
    50004: "EditControl",           # 编辑框/文本输入框
    50005: "HyperlinkControl",      # 超链接
    50006: "ImageControl",          # 图片
    50007: "ListItemControl",       # 列表项
    50008: "ListControl",           # 列表
    50009: "MenuControl",           # 菜单
    50010: "MenuBarControl",        # 菜单栏
    50011: "MenuItemControl",       # 菜单项
    50012: "ProgressBarControl",    # 进度条
    50013: "RadioButtonControl",    # 单选按钮
    50014: "ScrollBarControl",      # 滚动条
    50015: "SliderControl",         # 滑块
    50016: "SpinnerControl",        # 微调器
    50017: "StatusBarControl",      # 状态栏
    50018: "TabControl",            # 标签页控件
    50019: "TabItemControl",        # 标签页项
    50020: "TextControl",           # 文本
    50021: "ToolBarControl",        # 工具栏
    50022: "ToolTipControl",        # 提示框
    50023: "TreeControl",           # 树形控件
    50024: "TreeItemControl",       # 树节点
    50025: "CustomControl",         # 自定义控件
    50026: "GroupControl",          # 分组
    50027: "ThumbControl",          # 缩略图
    50028: "DataGridControl",       # 数据网格
    50029: "DataItemControl",       # 数据项
    50030: "DocumentControl",       # 文档
    50031: "SplitButtonControl",    # 分割按钮
    50032: "WindowControl",         # 窗口
    50033: "PaneControl",           # 面板
    50034: "HeaderControl",         # 头部
    50035: "HeaderItemControl",     # 头部项
    50036: "TableControl",          # 表格
    50037: "TitleBarControl",       # 标题栏
    50038: "SeparatorControl",      # 分隔符
    50039: "SemanticZoomControl",   # 语义缩放
    50040: "AppBarControl",         # 应用栏
}

# 反向映射：从名称到ID的转换
# 支持完整名称（如"ButtonControl"）和简写（如"Button"）
CONTROL_TYPE_IDS = {value: key for key, value in CONTROL_TYPE_NAMES.items()}
CONTROL_TYPE_IDS.update({value.replace("Control", ""): key for key, value in CONTROL_TYPE_NAMES.items()})

# 全局UIA自动化对象实例（单例模式）
_automation = None


def automation():
    """获取UI Automation主对象实例
    
    使用单例模式确保全局只有一个IUIAutomation实例。
    首次调用时会加载UIAutomationCore.dll并创建COM对象。
    
    Returns:
        IUIAutomation: COM自动化接口对象
        
    技术细节:
        - 使用comtypes库进行COM互操作
        - GUID "{ff48dba4-60ef-4201-aa87-54103eef594e}" 是IUIAutomation的CLSID
        - 懒加载模式，只在首次使用时初始化
        
    示例:
        >>> uia = automation()
        >>> root = uia.ElementFromHandle(hwnd)
    """
    global _automation
    if _automation is None:
        # 加载UI Automation类型库
        comtypes.client.GetModule("UIAutomationCore.dll")
        from comtypes.gen import UIAutomationClient

        # 创建IUIAutomation COM对象
        _automation = comtypes.client.CreateObject(
            GUID("{ff48dba4-60ef-4201-aa87-54103eef594e}"),
            interface=UIAutomationClient.IUIAutomation,
        )
    return _automation


def _prop(element, prop_id: int, default=None):
    """安全地获取UI元素的属性值
    
    内部辅助函数，处理属性访问可能出现的异常。
    
    Args:
        element: UIA元素对象
        prop_id: 属性ID（如UIA_NamePropertyId）
        default: 获取失败时的默认返回值
        
    Returns:
        属性值，如果获取失败则返回default
        
    注意:
        - 某些属性可能在特定元素上不可用
        - COM调用可能抛出异常，需要安全处理
    """
    try:
        value = element.GetCurrentPropertyValue(prop_id)
        return default if value is None else value
    except Exception:
        return default


def _rect_tuple(value) -> tuple[int, int, int, int] | None:
    """将UIA矩形对象转换为Python元组
    
    UIA的矩形有两种表示方式：
    1. 对象形式：有left, top, right, bottom属性
    2. 数组形式：[left, top, width, height]
    
    本函数统一转换为(left, top, right, bottom)元组格式。
    
    Args:
        value: UIA矩形对象或数组
        
    Returns:
        tuple[int, int, int, int]: (left, top, right, bottom)格式的矩形
        None: 如果转换失败
        
    示例:
        >>> _rect_tuple(uia_rect)
        (100, 200, 300, 400)  # left=100, top=200, right=300, bottom=400
    """
    if value is None:
        return None
    try:
        # 尝试对象形式（有left, top, right, bottom属性）
        left = int(value.left)
        top = int(value.top)
        return (left, top, left + int(value.right), top + int(value.bottom))
    except Exception:
        try:
            # 尝试数组形式 [left, top, width, height]
            left, top, width, height = (int(item) for item in value)
            return (left, top, left + width, top + height)
        except Exception:
            return None


@dataclass(frozen=True)
class UIAControl:
    """UI Automation控件的封装类
    
    该类封装了Windows UIA的IUIAutomationElement接口，提供Pythonic的属性访问
   和方法调用。是不可变对象（frozen），确保线程安全。
    
    主要功能:
        - 读取控件的各种属性（名称、类型、位置等）
        - 遍历子控件和后代控件
        - 基于条件查找匹配的控件
        - 焦点设置和基本操作
        
    属性说明:
        Name: 控件的显示名称或文本内容
        ClassName: 控件的技术类名（如"Button"、"Edit"）
        AutomationId: 开发者设置的自动化ID（最稳定的标识符）
        ControlType: 控件类型的数字ID
        ControlTypeName: 控件类型的可读名称
        NativeWindowHandle: 原生窗口句柄（如果有）
        BoundingRectangle: 控件在屏幕上的位置和大小
        
    性能提示:
        - 每次属性访问都会触发COM调用，有一定开销
        - 频繁访问时应缓存结果
        - FindAll/F findFirst会遍历UI树，尽量限制max_depth
        
    示例:
        >>> control = control_from_handle(hwnd)
        >>> print(f"窗口标题: {control.Name}")
        >>> print(f"控件类型: {control.ControlTypeName}")
        >>> print(f"位置: {control.BoundingRectangle}")
        >>> 
        >>> # 查找所有按钮
        >>> buttons = control.FindAll(
        ...     max_depth=5,
        ...     predicate=lambda c: c.ControlTypeName == "ButtonControl"
        ... )
    """
    element: Any  # 底层的IUIAutomationElement COM对象

    @property
    def Name(self) -> str:
        """获取控件名称
        
        通常是控件显示的文本内容，如按钮上的文字、输入框的内容等。
        对于容器控件，可能是空字符串。
        
        Returns:
            str: 控件名称，如果获取失败返回空字符串
        """
        return str(_prop(self.element, UIA_NamePropertyId, "") or "")

    @property
    def ClassName(self) -> str:
        """获取控件类名
        
        控件的技术类型标识，如"WeChatMainWndForPC"、"mmui::XTextView"等。
        类名通常比Name更稳定，适合用于控件识别。
        
        Returns:
            str: 控件类名，如果获取失败返回空字符串
            
        注意:
            - 微信使用了大量自定义控件类（以mmui::开头）
            - 类名在不同微信版本间可能变化
        """
        return str(_prop(self.element, UIA_ClassNamePropertyId, "") or "")

    @property
    def AutomationId(self) -> str:
        """获取自动化ID
        
        开发者在创建控件时设置的唯一标识符，是最稳定的控件识别方式。
        但很多第三方应用（包括微信）不一定设置了这个属性。
        
        Returns:
            str: 自动化ID，如果未设置或获取失败返回空字符串
            
        提示:
            - 优先使用AutomationId进行控件定位（如果可用）
            - 其次考虑ClassName + Name的组合
        """
        return str(_prop(self.element, UIA_AutomationIdPropertyId, "") or "")

    @property
    def ControlType(self) -> int:
        """获取控件类型ID
        
        Windows标准控件类型的数字标识，如50000表示按钮。
        
        Returns:
            int: 控件类型ID，如果获取失败返回0
        """
        return int(_prop(self.element, UIA_ControlTypePropertyId, 0) or 0)

    @property
    def ControlTypeName(self) -> str:
        """获取控件类型名称
        
        将ControlType的数字ID转换为可读的英文名称。
        
        Returns:
            str: 控件类型名称（如"ButtonControl"），未知类型返回数字字符串
        """
        return CONTROL_TYPE_NAMES.get(self.ControlType, str(self.ControlType))

    @property
    def NativeWindowHandle(self) -> int:
        """获取原生窗口句柄
        
        如果控件是一个独立的Windows窗口，返回其句柄。
        大多数子控件没有独立的窗口句柄。
        
        Returns:
            int: 窗口句柄，如果没有返回0
        """
        return int(_prop(self.element, UIA_NativeWindowHandlePropertyId, 0) or 0)

    @property
    def BoundingRectangle(self) -> tuple[int, int, int, int] | None:
        """获取控件的边界矩形
        
        返回控件在屏幕上的绝对位置和大小。
        
        Returns:
            tuple[int, int, int, int]: (left, top, right, bottom)格式的矩形
            None: 如果获取失败
            
        用途:
            - 计算控件的中心点用于点击
            - 判断控件是否可见（矩形是否在屏幕内）
            - 检查控件之间的相对位置关系
        """
        return _rect_tuple(_prop(self.element, UIA_BoundingRectanglePropertyId))

    def Exists(self, timeout: float = 0) -> bool:
        """检查控件是否存在
        
        可选地等待一段时间，适用于等待控件出现的场景。
        
        Args:
            timeout: 超时时间（秒），0表示立即检查不等待
            
        Returns:
            bool: 控件是否存在
            
        示例:
            # 立即检查
            if control.Exists():
                print("控件存在")
            
            # 等待最多5秒
            if control.Exists(timeout=5.0):
                print("控件已出现")
        """
        if timeout:
            deadline = time.time() + timeout
            while time.time() < deadline:
                if self.element is not None:
                    return True
                time.sleep(0.05)
        return self.element is not None

    def SetFocus(self) -> None:
        """设置焦点到该控件
        
        使控件获得输入焦点，相当于用户点击了该控件。
        常用于激活输入框、按钮等可交互控件。
        
        注意:
            - 某些控件可能不支持设置焦点
            - 可能需要窗口处于前台状态
        """
        self.element.SetFocus()

    def GetChildren(self) -> list["UIAControl"]:
        """获取所有直接子控件
        
        返回当前控件的第一层子控件列表，不递归查找。
        
        Returns:
            list[UIAControl]: 子控件列表
            
        性能:
            - 只获取直接子节点，速度较快
            - 如需深层查找，使用FindAll方法
        """
        walker = automation().RawViewWalker
        children = []
        child = walker.GetFirstChildElement(self.element)
        while child:
            children.append(UIAControl(child))
            child = walker.GetNextSiblingElement(child)
        return children

    def FindAll(self, max_depth: int = 6, predicate: Optional[Callable[["UIAControl"], bool]] = None) -> list["UIAControl"]:
        """查找所有匹配的子孙控件
        
        深度优先遍历UI树，返回所有满足条件的控件。
        
        Args:
            max_depth: 最大搜索深度，默认6层
                      限制递归深度以提高性能
            predicate: 过滤函数，接收UIAControl参数，返回bool
                      如果为None，返回所有控件
            
        Returns:
            list[UIAControl]: 匹配的控件列表
            
        性能提示:
            - 搜索范围越大，耗时越长
            - 建议设置合理的max_depth
            - predicate函数会被频繁调用，应保持简单
            
        示例:
            # 查找所有文本控件
            texts = root.FindAll(
                max_depth=10,
                predicate=lambda c: c.ControlTypeName == "TextControl"
            )
            
            # 查找名称包含"发送"的按钮
            send_buttons = root.FindAll(
                max_depth=5,
                predicate=lambda c: (
                    c.ControlTypeName == "ButtonControl" and
                    "发送" in c.Name
                )
            )
        """
        found: list[UIAControl] = []

        def walk(node: UIAControl, depth: int) -> None:
            """递归遍历UI树"""
            if depth > max_depth:
                return
            if predicate is None or predicate(node):
                found.append(node)
            for child in node.GetChildren():
                walk(child, depth + 1)

        walk(self, 0)
        return found

    def FindFirst(self, max_depth: int = 6, **criteria):
        """查找第一个匹配的控件
        
        根据多个条件查找第一个符合条件的控件。
        
        Args:
            max_depth: 最大搜索深度，默认6
            **criteria: 匹配条件，支持：
                - control_type: 控件类型（名称或ID）
                - name: 精确匹配名称
                - contains_name: 名称包含某文本
                - regex_name: 名称匹配正则表达式
                - class_name: 精确匹配类名
                - automation_id: 精确匹配自动化ID
            
        Returns:
            UIAControl: 第一个匹配的控件，未找到返回None
            
        示例:
            # 查找名称为"发送"的按钮
            btn = root.FindFirst(
                max_depth=5,
                control_type="ButtonControl",
                name="发送"
            )
            
            # 查找类名包含"Edit"的控件
            edit = root.FindFirst(
                class_name="Edit"
            )
            
            # 查找名称包含"消息"的控件
            msg = root.FindFirst(
                contains_name="消息"
            )
        """
        for control in self.FindAll(max_depth=max_depth, predicate=lambda item: _matches(item, criteria)):
            if control is not self:
                return control
        return None


def control_from_handle(hwnd: int) -> UIAControl:
    """从窗口句柄创建UIA控件对象
    
    将Windows窗口句柄转换为UIA控件，作为UI树的根节点。
    
    Args:
        hwnd: Windows窗口句柄
        
    Returns:
        UIAControl: 根控件对象
        
    示例:
        >>> import win32gui
        >>> hwnd = win32gui.FindWindow(None, "微信")
        >>> root = control_from_handle(hwnd)
        >>> print(root.Name)  # 输出窗口标题
    """
    return UIAControl(automation().ElementFromHandle(hwnd))


def _matches(control: UIAControl, criteria: dict[str, Any]) -> bool:
    """检查控件是否匹配所有给定条件
    
    内部辅助函数，用于FindFirst等方法的条件匹配。
    
    Args:
        control: 待检查的控件
        criteria: 匹配条件字典，支持的键：
            - control_type: 控件类型
            - name: 精确名称匹配
            - contains_name: 名称包含检查
            - regex_name: 名称正则匹配
            - class_name: 类名匹配
            - automation_id: 自动化ID匹配
            
    Returns:
        bool: 是否匹配所有条件
        
    匹配逻辑:
        - 所有条件必须同时满足（AND关系）
        - 空条件或未设置的条件视为匹配
    """
    # 检查控件类型
    control_type = criteria.get("control_type")
    if control_type:
        expected = CONTROL_TYPE_IDS.get(control_type, control_type)
        if isinstance(expected, int):
            if control.ControlType != expected:
                return False
        elif control.ControlTypeName != expected:
            return False
    
    # 检查精确名称匹配
    name = criteria.get("name")
    if name is not None and control.Name != name:
        return False
    
    # 检查名称包含
    contains_name = criteria.get("contains_name")
    if contains_name is not None and contains_name not in control.Name:
        return False
    
    # 检查名称正则匹配
    regex_name = criteria.get("regex_name")
    if regex_name is not None and not re.search(regex_name, control.Name):
        return False
    
    # 检查类名
    class_name = criteria.get("class_name")
    if class_name is not None and control.ClassName != class_name:
        return False
    
    # 检查自动化ID
    automation_id = criteria.get("automation_id")
    if automation_id is not None and control.AutomationId != automation_id:
        return False
    
    return True


def dump_tree(control, max_depth: int = 2) -> list[str]:
    """将UI控件树转储为文本格式
    
    用于调试和探索UI结构，生成人类可读的树形文本。
    
    Args:
        control: 根控件
        max_depth: 最大深度，默认2层（避免输出过多）
        
    Returns:
        list[str]: 每行一个节点的文本列表
        
    输出格式:
        每行包含：类型、类名、名称、自动化ID、句柄、位置矩形
        
    示例:
        >>> lines = dump_tree(root, max_depth=3)
        >>> for line in lines:
        ...     print(line)
        - type=WindowControl, class='WeChatMainWndForPC', name='微信', ...
          - type=PaneControl, class='mmui::XXX', name='', ...
            - type=ButtonControl, class='Button', name='发送', ...
    """
    lines = []

    def walk(node: UIAControl, depth: int) -> None:
        """递归遍历并格式化输出"""
        indent = "  " * depth  # 缩进表示层级
        rect = node.BoundingRectangle
        lines.append(
            f"{indent}- type={node.ControlTypeName}, class={node.ClassName!r}, "
            f"name={node.Name!r}, automation_id={node.AutomationId!r}, hwnd={node.NativeWindowHandle}, rect={rect}"
        )
        if depth >= max_depth:
            return
        try:
            children = node.GetChildren()
        except Exception:
            return
        # 限制子节点数量，避免输出过多
        for child in children[:80]:
            walk(child, depth + 1)
        if len(children) > 80:
            lines.append(f"{indent}  ... {len(children) - 80} more children")

    walk(control, 0)
    return lines


class UIAFinder:
    """基于选择器的UI元素查找器
    
    提供更高级的控件查找功能，支持路径式查找和多步定位。
    适用于复杂UI结构中精确定位目标控件。
    
    选择器格式:
        {
            "path": [
                {
                    "class_name": "mmui::XXX",
                    "found_index": 0,
                    "search_depth": 6
                },
                {
                    "name": "发送",
                    "control_type": "ButtonControl"
                }
            ]
        }
    
    使用示例:
        >>> finder = UIAFinder(root_control)
        >>> try:
        ...     button = finder.find_required(selector, timeout=2.0)
        ...     button.SetFocus()
        ... except ControlNotFoundError:
        ...     print("未找到控件")
    """
    
    def __init__(self, root) -> None:
        """初始化查找器
        
        Args:
            root: UI树根控件（UIAControl对象）
        """
        self.root = root

    def find(self, selector: dict[str, Any]):
        """根据选择器查找控件
        
        按照路径逐步查找，每一步都基于上一步的结果继续搜索。
        
        Args:
            selector: 选择器字典，包含"path"键
                     path是步骤列表，每个步骤定义查找条件
            
        Returns:
            UIAControl: 找到的控件
            
        Raises:
            ControlNotFoundError: 任何一步查找失败时抛出
            
        查找过程:
            1. 从root开始
            2. 对path中的每个步骤：
               a. 在当前控件的子孙中查找匹配的元素
               b. 取第found_index个匹配项
               c. 作为下一步的起点
            3. 返回最后一步找到的控件
        """
        control = self.root
        for step in selector.get("path", []):
            search_depth = step.get("search_depth", 6)
            found_index = step.get("found_index", 0)
            
            # 在当前层级查找所有匹配的控件
            matches = [
                item for item in control.FindAll(max_depth=search_depth)
                if item is not control and _matches(item, step)
            ]
            
            # 检查是否找到足够的匹配项
            if len(matches) <= found_index:
                raise ControlNotFoundError(f"Control not found for selector step: {step}")
            
            # 取指定索引的控件作为下一步的起点
            control = matches[found_index]
        return control

    def find_required(self, selector: dict[str, Any], timeout: float = 0.5):
        """带超时重试的控件查找
        
        在指定时间内反复尝试查找，适用于等待控件出现的场景。
        
        Args:
            selector: 选择器字典
            timeout: 超时时间（秒），默认0.5秒
            
        Returns:
            UIAControl: 找到的控件
            
        Raises:
            ControlNotFoundError: 超时后仍未找到控件
            
        适用场景:
            - 等待异步加载的控件
            - 等待动画结束后再查找
            - 提高查找的成功率
            
        示例:
            >>> finder = UIAFinder(root)
            >>> try:
            ...     btn = finder.find_required(selector, timeout=3.0)
            ...     print("找到按钮")
            ... except ControlNotFoundError:
            ...     print("超时未找到")
        """
        deadline = time.time() + timeout
        last_error = None
        
        # 持续尝试直到超时
        while True:
            try:
                return self.find(selector)
            except ControlNotFoundError as exc:
                last_error = exc
                if time.time() >= deadline:
                    break
                time.sleep(0.05)  # 短暂等待后重试
        
        raise ControlNotFoundError(f"Control not found for selector: {selector}") from last_error
