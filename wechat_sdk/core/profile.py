from dataclasses import dataclass
from typing import Iterable, Optional

from .config import load_yaml


@dataclass(frozen=True)
class ClientProfile:
    """客户端配置数据类，存储微信版本的配置信息"""
    profile_id: str  # 配置文件ID
    version_range: str  # 版本范围
    process_names: tuple[str, ...]  # 进程名称列表
    class_names: tuple[str, ...]  # 窗口类名列表
    titles: tuple[str, ...]  # 窗口标题列表
    selectors_file: str  # 选择器配置文件


def load_profiles() -> dict[str, ClientProfile]:
    """加载所有客户端配置文件
    
    Returns:
        dict[str, ClientProfile]: 配置文件ID到配置的映射
    """
    data = load_yaml("clients.yaml")
    profiles = {}
    for profile_id, raw in data.get("clients", {}).items():
        window = raw.get("window", {})
        profiles[profile_id] = ClientProfile(
            profile_id=profile_id,
            version_range=raw.get("version_range", ""),
            process_names=tuple(raw.get("process_names", [])),
            class_names=tuple(window.get("class_names", [])),
            titles=tuple(window.get("titles", [])),
            selectors_file=raw.get("selectors", ""),
        )
    return profiles


def _version_tuple(version: Optional[str]) -> tuple[int, ...]:
    """将版本号字符串转换为元组
    
    Args:
        version: 版本号字符串（如 "3.9.0.1"）
        
    Returns:
        tuple[int, ...]: 版本号元组（如 (3, 9, 0, 1)）
    """
    if not version:
        return ()
    parts = []
    for part in version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts)


def _compare(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    """比较两个版本号元组
    
    Args:
        left: 左侧版本号元组
        right: 右侧版本号元组
        
    Returns:
        int: -1（小于）、0（等于）、1（大于）
    """
    max_len = max(len(left), len(right))
    left = left + (0,) * (max_len - len(left))
    right = right + (0,) * (max_len - len(right))
    return (left > right) - (left < right)


def version_in_range(version: Optional[str], version_range: str) -> bool:
    """检查版本号是否在指定范围内
    
    Args:
        version: 待检查的版本号
        version_range: 版本范围表达式（支持 >=、>、<=、<、==）
        
    Returns:
        bool: 版本号是否在范围内
    """
    if not version_range:
        return True
    current = _version_tuple(version)
    if not current:
        return True
    for clause in version_range.split(","):
        clause = clause.strip()
        if clause.startswith(">="):
            if _compare(current, _version_tuple(clause[2:])) < 0:
                return False
        elif clause.startswith(">"):
            if _compare(current, _version_tuple(clause[1:])) <= 0:
                return False
        elif clause.startswith("<="):
            if _compare(current, _version_tuple(clause[2:])) > 0:
                return False
        elif clause.startswith("<"):
            if _compare(current, _version_tuple(clause[1:])) >= 0:
                return False
        elif clause.startswith("=="):
            if _compare(current, _version_tuple(clause[2:])) != 0:
                return False
    return True


def match_profile(
    profiles: Iterable[ClientProfile],
    process_name: str,
    class_name: str,
    title: str,
    version: Optional[str],
) -> Optional[ClientProfile]:
    """根据进程名、类名、标题和版本号匹配客户端配置
    
    Args:
        profiles: 客户端配置列表
        process_name: 进程名称
        class_name: 窗口类名
        title: 窗口标题
        version: 版本号
        
    Returns:
        Optional[ClientProfile]: 匹配到的配置，若无匹配则返回 None
    """
    for profile in profiles:
        process_ok = not profile.process_names or process_name in profile.process_names
        class_ok = not profile.class_names or class_name in profile.class_names
        title_ok = not profile.titles or title in profile.titles
        version_ok = version_in_range(version, profile.version_range)
        if process_ok and class_ok and title_ok and version_ok:
            return profile
    return None
