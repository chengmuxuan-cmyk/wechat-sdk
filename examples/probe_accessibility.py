"""MSAA (Microsoft Active Accessibility) 探测工具

此示例演示如何使用微软活动辅助性(MSAA) API探测微信窗口的可访问性信息。

作者: CMX

技术背景:
    MSAA是Windows的辅助技术API，比UI Automation更底层。
    某些应用（特别是使用Qt框架的）可能对UIA支持不完整，
    但实现了MSAA接口。这个工具用于探索这种情况。

使用场景:
    - 当UI Automation无法识别某些控件时
    - 调试Qt框架应用的辅助性问题
    - 探索微信旧版本或特殊版本的UI结构
    - 研究不同辅助性API的差异
    - 为SDK选择最佳的技术方案
    
功能说明:
    - 枚举系统中所有微信相关窗口
    - 通过MSAA API获取窗口的可访问性对象
    - 递归遍历所有子元素
    - 显示每个元素的名称、角色、状态、位置等信息
    
运行方式:
    uv run python examples/probe_accessibility.py

输出示例:
    HWND 123456 title='微信' class='WeChatMainWndForPC' process='WeChat.exe'
      - name='微信' role='client' state='' loc=(0, 0, 800, 600)
        - name='聊天列表' role='list' state='' loc=(0, 0, 200, 600)
          - name='张三' role='list item' state='' loc=(0, 0, 200, 50)
          ...

字段说明:
    - name: 元素的可访问性名称
    - role: 元素角色（client、list、button等）
    - state: 元素状态（focused、selected等）
    - loc: 位置和大小 (left, top, width, height)

注意事项:
    - MSAA是较老的技术，UIA是其继任者
    - 现代应用通常同时支持两种API
    - 输出可能非常长，建议重定向到文件
    - 某些元素可能无法访问（权限或实现问题）
    
与UIA的区别:
    - MSAA: 更底层，基于COM接口，角色系统简单
    - UIA: 更现代，功能更丰富，层次更清晰
    - WeChat_SDK主要使用UIA，此工具仅用于调试
    
扩展用法:
    # 保存ToFile
    uv run python examples/probe_accessibility.py > msaa_tree.txt
    
    # 在代码中使用MSAA
    from examples.probe_accessibility import accessible_from_hwnd, dump_accessible
    acc = accessible_from_hwnd(hwnd)
    dump_accessible(acc, max_depth=5)
"""
from __future__ import annotations

import ctypes
from ctypes import byref
from typing import Any

import comtypes
import comtypes.client
from comtypes.automation import VARIANT
import win32gui
import win32process

from wechat_sdk.core.window import enum_windows


# MSAA常量定义
OBJID_CLIENT = 0xFFFFFFFC  # 客户端对象的ID
IID_IAccessible = comtypes.GUID("{618736E0-3C3D-11CF-810C-00AA00389B71}")  # IAccessible接口GUID


def _load_accessibility():
    """加载MSAA可访问性模块
    
    动态加载oleacc.dll并返回IAccessible接口类型。
    使用懒加载避免不必要的DLL加载。
    
    Returns:
        IAccessible接口类型
    """
    comtypes.client.GetModule("oleacc.dll")
    from comtypes.gen.Accessibility import IAccessible

    return IAccessible


def accessible_from_hwnd(hwnd: int):
    """从窗口句柄获取MSAA可访问性对象
    
    调用Windows API AccessibleObjectFromWindow获取窗口的IAccessible接口。
    
    Args:
        hwnd: 窗口句柄
        
    Returns:
        IAccessible COM对象指针
        
    Raises:
        OSError: 如果API调用失败
        
    技术细节:
        - OBJID_CLIENT表示请求客户端区域的 accessibles对象
        - 返回的对象可以查询子元素和属性
    """
    IAccessible = _load_accessibility()
    ptr = ctypes.POINTER(IAccessible)()
    result = ctypes.oledll.oleacc.AccessibleObjectFromWindow(
        hwnd,
        OBJID_CLIENT,
        byref(IID_IAccessIBLE),
        byref(ptr),
    )
    if result:
        raise OSError(result, f"AccessibleObjectFromWindow failed: 0x{result:08X}")
    return ptr


def _child_id(value: int = 0) -> VARIANT:
    """创建子元素ID的VARIANT对象
    
    MSAA使用VARIANT类型来表示子元素ID。
    CHILDID_SELF (0) 表示元素本身，正整数表示子元素索引。
    
    Args:
        value: 子元素ID，0表示元素本身
        
    Returns:
        VARIANT对象
    """
    variant = VARIANT()
    variant.value = value
    return variant


def _safe(call, default: Any = ""):
    """安全地调用COM方法
    
    包装COM调用，捕获异常并返回默认值。
    MSAA的许多属性可能在某些元素上不可用。
    
    Args:
        call: 无参数callable，执行COM调用
        default: 失败时的默认返回值
        
    Returns:
        调用结果或默认值
    """
    try:
        value = call()
        return default if value is None else value
    except Exception:
        return default


def _acc_name(acc, child_id: int = 0) -> str:
    """获取元素的可访问性名称
    
    Args:
        acc: IAccessible对象
        child_id: 子元素ID，0表示元素本身
        
    Returns:
        元素名称字符串
    """
    return str(_safe(lambda: acc.accName[_child_id(child_id)], ""))


def _acc_role(acc, child_id: int = 0):
    """获取元素的角色
    
    角色标识元素的类型和功能，如按钮、列表、文本等。
    
    Args:
        acc: IAccessible对象
        child_id: 子元素ID
        
    Returns:
        角色标识（整数或字符串）
    """
    return _safe(lambda: acc.accRole[_child_id(child_id)], "")


def _acc_state(acc, child_id: int = 0):
    """获取元素的状态
    
    状态表示元素的当前状况，如聚焦、选中、禁用等。
    
    Args:
        acc: IAccessible对象
        child_id: 子元素ID
        
    Returns:
        状态标志（位掩码）
    """
    return _safe(lambda: acc.accState[_child_id(child_id)], "")


def _acc_location(acc, child_id: int = 0):
    """获取元素的位置和大小
    
    Args:
        acc: IAccessible对象
        child_id: 子元素ID
        
    Returns:
        tuple: (left, top, width, height) 或 None
    """
    try:
        left = ctypes.c_long()
        top = ctypes.c_long()
        width = ctypes.c_long()
        height = ctypes.c_long()
        acc.accLocation(byref(left), byref(top), byref(width), byref(height), _child_id(child_id))
        return (left.value, top.value, width.value, height.value)
    except Exception:
        return None


def _children(acc):
    """获取元素的所有子元素
    
    Args:
        acc: IAccessible对象
        
    Returns:
        list: 子元素列表，可能是IAccessible对象或子元素ID（整数）
    """
    count = int(_safe(lambda: acc.accChildCount, 0) or 0)
    if count <= 0:
        return []
    variants = (VARIANT * count)()
    obtained = ctypes.c_long()
    result = ctypes.oledll.oleacc.AccessibleChildren(acc, 0, count, variants, byref(obtained))
    if result:
        return []
    return [variants[index].value for index in range(obtained.value)]


def dump_accessible(acc, depth: int = 0, max_depth: int = 5, child_id: int = 0) -> None:
    """递归导出MSAA可访问性树
    
    以树形格式打印元素及其所有子元素的信息。
    
    Args:
        acc: IAccessible对象
        depth: 当前深度（用于缩进）
        max_depth: 最大递归深度
        child_id: 子元素ID
    """
    indent = "  " * depth
    print(
        f"{indent}- name={_acc_name(acc, child_id)!r} role={_acc_role(acc, child_id)!r} "
        f"state={_acc_state(acc, child_id)!r} loc={_acc_location(acc, child_id)}"
    )
    if depth >= max_depth or child_id != 0:
        return
    for child in _children(acc)[:80]:
        if isinstance(child, int):
            # 子元素ID，需要在父对象上查询
            dump_accessible(acc, depth + 1, max_depth, child)
        else:
            # 子对象，直接递归
            dump_accessible(child, depth + 1, max_depth)


def weixin_windows():
    """查找所有微信相关窗口
    
    综合多种方法检测微信窗口，包括：
    1. 标准窗口枚举
    2. Qt框架特定的类名检测
    3. 进程名称匹配
    
    Returns:
        list: 窗口信息列表，每项为(hwnd, title, class_name, process_name)
    """
    targets = []
    
    # 方法1：标准窗口枚举
    for window in enum_windows():
        text = " ".join([window.title, window.class_name, window.process_name, window.exe_path]).lower()
        if any(keyword in text for keyword in ("weixin", "wechat", "微信", "qt51514")):
            targets.append((window.hwnd, window.title, window.class_name, window.process_name))

    # 方法2：使用win32gui再次枚举（可能发现更多窗口）
    def callback(hwnd, _):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            # 特别关注Qt框架的微信窗口
            if class_name.startswith("Qt51514") or title in ("微信", "Weixin"):
                item = (hwnd, title, class_name, "")
                if item not in targets:
                    targets.append(item)
        except Exception:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return targets


def main() -> None:
    """主函数：探测微信窗口的MSAA可访问性
    
    该函数执行以下步骤：
    1. 查找所有微信相关窗口
    2. 对每个窗口：
       a. 打印窗口基本信息
       b. 获取MSAA可访问性对象
       c. 递归导出可访问性树
       
    这对于：
    - 了解微信的辅助性实现
    - 调试UI识别问题
    - 对比MSAA和UIA的差异
    非常有帮助。
    """
    for hwnd, title, class_name, process_name in weixin_windows():
        print(f"HWND {hwnd} title={title!r} class={class_name!r} process={process_name!r}")
        try:
            # 获取MSAA对象并导出树（深度8层）
            dump_accessible(accessible_from_hwnd(hwnd), max_depth=8)
        except Exception as exc:
            print(f"  failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
