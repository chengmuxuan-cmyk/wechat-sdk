from __future__ import annotations

import time
from typing import Union

import win32api
import win32con

Key = Union[str, int]

_KEYS = {
    "ctrl": win32con.VK_CONTROL,
    "control": win32con.VK_CONTROL,
    "enter": win32con.VK_RETURN,
    "return": win32con.VK_RETURN,
    "esc": win32con.VK_ESCAPE,
    "escape": win32con.VK_ESCAPE,
    "home": win32con.VK_HOME,
    "pageup": win32con.VK_PRIOR,
    "page_up": win32con.VK_PRIOR,
    "pagedown": win32con.VK_NEXT,
    "page_down": win32con.VK_NEXT,
    "a": ord("A"),
    "f": ord("F"),
    "v": ord("V"),
}


def _vk(key: Key) -> int:
    if isinstance(key, int):
        return key
    try:
        return _KEYS[key.lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported key: {key}") from exc


def key_down(key: Key) -> None:
    win32api.keybd_event(_vk(key), 0, 0, 0)


def key_up(key: Key) -> None:
    win32api.keybd_event(_vk(key), 0, win32con.KEYEVENTF_KEYUP, 0)


def press(key: Key, wait: float = 0.05) -> None:
    key_down(key)
    key_up(key)
    time.sleep(wait)


def hotkey(*keys: Key, wait: float = 0.05) -> None:
    for key in keys:
        key_down(key)
    for key in reversed(keys):
        key_up(key)
    time.sleep(wait)
