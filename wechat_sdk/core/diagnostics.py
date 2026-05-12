from wechat_sdk.logging import logger

from . import uia
from .window import enum_windows


def diagnose_wechat_windows() -> list[str]:
    lines = []
    for window in enum_windows():
        text = " ".join([window.title, window.class_name, window.process_name, window.exe_path]).lower()
        if not any(keyword in text for keyword in ("wechat", "weixin", "微信")):
            continue
        line = (
            f"hwnd={window.hwnd} visible={window.visible} title={window.title!r} "
            f"class={window.class_name!r} process={window.process_name!r} version={window.version}"
        )
        lines.append(line)
        try:
            lines.extend("  " + item for item in uia.dump_tree(uia.control_from_handle(window.hwnd), max_depth=2))
        except Exception as exc:
            logger.debug("Failed to dump UIA tree for hwnd=%s: %s", window.hwnd, exc)
    return lines
