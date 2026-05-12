from typing import Optional

import psutil
import win32gui
import win32process

from wechat_sdk.logging import logger
from wechat_sdk.params import WindowInfo

from .profile import ClientProfile, load_profiles, match_profile


def get_path_by_hwnd(hwnd: int) -> str:
    """鏍规嵁绐楀彛鍙ユ焺鑾峰彇杩涚▼璺緞
    
    Args:
        hwnd: 绐楀彛鍙ユ焺
        
    Returns:
        str: 杩涚▼鍙墽琛屾枃浠惰矾寰勶紝澶辫触鏃惰繑鍥炵┖瀛楃涓?    """
    try:
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(process_id).exe()
    except Exception:
        return ""


def get_version_by_path(file_path: str) -> Optional[str]:
    """鏍规嵁鏂囦欢璺緞鑾峰彇鐗堟湰鍙?    
    Args:
        file_path: 鏂囦欢璺緞
        
    Returns:
        Optional[str]: 鐗堟湰鍙峰瓧绗︿覆锛屾牸寮忎负 "涓荤増鏈?娆＄増鏈?淇鐗堟湰.鏋勫缓鐗堟湰"锛屽け璐ユ椂杩斿洖 None
    """
    if not file_path:
        return None
    try:
        import win32api

        info = win32api.GetFileVersionInfo(file_path, "\\")
        return "{}.{}.{}.{}".format(
            win32api.HIWORD(info["FileVersionMS"]),
            win32api.LOWORD(info["FileVersionMS"]),
            win32api.HIWORD(info["FileVersionLS"]),
            win32api.LOWORD(info["FileVersionLS"]),
        )
    except Exception:
        return None


def enum_windows() -> list[WindowInfo]:
    """鏋氫妇鎵€鏈夌獥鍙ｅ苟鏀堕泦绐楀彛淇℃伅
    
    Returns:
        list[WindowInfo]: 绐楀彛淇℃伅鍒楄〃
    """
    windows = []

    def callback(hwnd: int, _: object) -> bool:
        try:
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            exe_path = ""
            try:
                process = psutil.Process(process_id)
                process_name = process.name()
                exe_path = process.exe()
            except Exception:
                pass
            windows.append(
                WindowInfo(
                    hwnd=hwnd,
                    title=win32gui.GetWindowText(hwnd),
                    class_name=win32gui.GetClassName(hwnd),
                    process_name=process_name,
                    exe_path=exe_path,
                    version=get_version_by_path(exe_path),
                    visible=bool(win32gui.IsWindowVisible(hwnd)),
                )
            )
        except Exception:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return windows


def detect_wechat_window() -> tuple[WindowInfo, ClientProfile]:
    """妫€娴嬪井淇＄獥鍙ｅ苟鍖归厤瀵瑰簲鐨勫鎴风閰嶇疆
    
    Returns:
        tuple[WindowInfo, ClientProfile]: 绐楀彛淇℃伅鍜屽鎴风閰嶇疆
        
    Raises:
        WeChatWindowNotFoundError: 鏈娴嬪埌杩愯鐨勫井淇″疄渚?    """
    profiles = load_profiles()
    for window in enum_windows():
        profile = match_profile(
            profiles.values(),
            process_name=window.process_name,
            class_name=window.class_name,
            title=window.title,
            version=window.version,
        )
        if profile:
            matched = WindowInfo(
                hwnd=window.hwnd,
                title=window.title,
                class_name=window.class_name,
                process_name=window.process_name,
                exe_path=window.exe_path,
                version=window.version,
                visible=window.visible,
                profile_id=profile.profile_id,
            )
            logger.info("Matched WeChat client: %s", matched)
            return matched, profile
    from wechat_sdk.errors import WeChatWindowNotFoundError

    raise WeChatWindowNotFoundError("No supported WeChat client window found")


def activate_window(hwnd: int) -> None:
    """婵€娲绘寚瀹氱獥鍙?    
    Args:
        hwnd: 绐楀彛鍙ユ焺
    """
    import win32con

    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
    )
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_NOTOPMOST,
        0,
        0,
        0,
        0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE,
    )
    win32gui.SetForegroundWindow(hwnd)


def current_foreground_hwnd() -> int:
    """鑾峰彇褰撳墠鍓嶅彴绐楀彛鐨勫彞鏌?    
    Returns:
        int: 鍓嶅彴绐楀彛鍙ユ焺
    """
    return win32gui.GetForegroundWindow()
