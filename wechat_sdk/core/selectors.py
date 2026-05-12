from typing import Any

from .config import load_yaml


class SelectorRegistry:
    """选择器注册表，管理UI元素的选择器配置和多语言文本"""
    
    def __init__(self, selectors_file: str, language: str = "cn") -> None:
        """初始化选择器注册表
        
        Args:
            selectors_file: 选择器配置文件名（如 selectors.wechat4.yaml）
            language: 语言设置（cn/cn_t/en）
        """
        self.language = language
        self._selectors = load_yaml(selectors_file).get("selectors", {})
        self._i18n = load_yaml("i18n.yaml").get("texts", {})

    def get(self, key: str) -> dict[str, Any]:
        """获取指定键的选择器配置
        
        Args:
            key: 选择器键名
            
        Returns:
            dict[str, Any]: 选择器配置字典
            
        Raises:
            KeyError: 当选择器不存在时抛出
        """
        selector = self._selectors.get(key)
        if selector is None:
            raise KeyError(f"Selector not found: {key}")
        return self._resolve_language(selector)

    def text(self, key: str) -> str:
        """获取多语言文本
        
        Args:
            key: 文本键名
            
        Returns:
            str: 当前语言的文本，如果不存在则返回中文或键名本身
        """
        values = self._i18n.get(key, {})
        return values.get(self.language, values.get("cn", key))

    def _resolve_language(self, value):
        """递归解析选择器中的多语言配置
        
        Args:
            value: 待解析的值（可能是字典、列表或其他类型）
            
        Returns:
            解析后的值，多语言字段会被替换为当前语言的文本
        """
        if isinstance(value, dict):
            if any(lang in value for lang in ("cn", "cn_t", "en")):
                return value.get(self.language, value.get("cn", ""))
            return {k: self._resolve_language(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_language(item) for item in value]
        return value
