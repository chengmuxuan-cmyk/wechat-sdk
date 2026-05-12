from .clipboard import set_files, set_text


def paste_text(control, text: str, wait_time: float = 0.1) -> None:
    set_text(text)
    control.SendKeys("{Ctrl}v", waitTime=wait_time)


def paste_files(control, paths, wait_time: float = 0.2) -> None:
    set_files(paths)
    control.SendKeys("{Ctrl}v", waitTime=wait_time)


def submit(control, wait_time: float = 0.1) -> None:
    control.SendKeys("{Enter}", waitTime=wait_time)


def clear(control, wait_time: float = 0.0) -> None:
    control.SendKeys("{Ctrl}a", waitTime=wait_time)
