from typing import Iterable
import ctypes
import os
import time

from wechat_sdk.errors import ClipboardError


class _DROPFILES(ctypes.Structure):
    _fields_ = [
        ("pFiles", ctypes.c_uint),
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
        ("fNC", ctypes.c_int),
        ("fWide", ctypes.c_bool),
    ]


def _dropfiles_header() -> bytes:
    payload = _DROPFILES()
    payload.pFiles = ctypes.sizeof(_DROPFILES)
    payload.fWide = True
    return bytes(payload)


def set_text(text: str) -> None:
    try:
        import pyperclip

        pyperclip.copy(text)
    except Exception as exc:
        raise ClipboardError(f"Failed to set clipboard text: {exc}") from exc


def get_text() -> str:
    try:
        import pyperclip

        value = pyperclip.paste()
        return "" if value is None else str(value)
    except Exception as exc:
        raise ClipboardError(f"Failed to get clipboard text: {exc}") from exc


def set_files(paths: Iterable[str]) -> None:
    file_paths = [os.path.realpath(str(path)) for path in paths]
    for path in file_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(path)

    files = ("\0".join(file_paths)).replace("/", "\\")
    data = files.encode("utf-16-le") + b"\0\0"
    payload = _dropfiles_header() + data

    try:
        import win32clipboard

        deadline = time.time() + 10
        while True:
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, payload)
                return
            except Exception:
                if time.time() > deadline:
                    raise
                time.sleep(0.05)
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass
    except Exception as exc:
        raise ClipboardError(f"Failed to set clipboard files: {exc}") from exc
