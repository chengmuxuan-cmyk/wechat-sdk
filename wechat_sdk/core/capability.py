"""
能力管理模块

定义和管理WeChat_SDK支持的各种功能能力。
通过配置文件（capabilities.yaml）声明不同微信版本支持的功能，
实现版本适配和功能检查。

作者: CMX

主要类:
    Capability: 能力数据类，描述单个功能的详细信息
    CapabilityRegistry: 能力注册表，管理和查询所有能力
    
设计理念:
    - 配置驱动：通过YAML文件声明能力，而非硬编码
    - 版本适配：不同微信版本可能支持不同的功能集
    - 提前检查：在执行操作前验证能力是否可用
    - 优雅降级：不支持的功能抛出明确异常

使用示例:
    >>> registry = CapabilityRegistry()
    >>> # 检查"发送文本"能力是否在当前版本支持
    >>> cap = registry.ensure_supported("message.send_text", "wechat39")
    >>> print(f"默认模式: {cap.default_mode}")
"""
from dataclasses import dataclass
from typing import Optional

from wechat_sdk.errors import CapabilityNotSupportedError, CapabilityUnknownError

from .config import load_yaml


@dataclass(frozen=True)
class Capability:
    """能力数据类，定义特定功能的支持情况
    
    该类描述了SDK中一个具体功能（能力）的元数据，包括：
    - 功能标识符
    - 默认的交互模式
    - 关联的管道处理器
    - 各微信版本的支持状态
    - 必需的UI选择器
    
    Attributes:
        capability_id: 能力的唯一标识符
                      格式通常为 "{模块}.{功能}"，如 "message.send_text"
                      
        default_mode: 默认的交互模式
                     可选值："auto"、"background"、"foreground"
                     某些功能可能需要前台操作才能正常工作
                     
        pipeline: 关联的管道处理器名称（可选）
                 如果设置了，该能力会通过PipelineRunner执行
                 None表示直接调用方法，不经过管道
                 
        supported: 各配置文件的支持状态字典
                  键：配置文件ID（如"wechat39"、"wechat4"）
                  值：支持状态（"supported"、"unsupported"）
                  
        required_selectors: 必需的选择器ID列表
                          这些选择器必须在selectors.yaml中定义
                          用于确保UI元素可以被正确定位
                          
    使用场景:
        - 在执行操作前检查功能是否可用
        - 根据微信版本提供不同的实现
        - 生成能力支持矩阵文档
        
    示例:
        >>> cap = Capability(
        ...     capability_id="message.send_text",
        ...     default_mode="auto",
        ...     pipeline="send_text",
        ...     supported={"wechat39": "supported", "wechat4": "supported"},
        ...     required_selectors=("chat_input", "send_button")
        ... )
        >>> print(cap.status_for("wechat39"))  # 输出: supported
    """
    capability_id: str  # 能力ID
    default_mode: str  # 默认模式
    pipeline: Optional[str]  # 管道名称（可选）
    supported: dict[str, str]  # 支持的配置文件及状态
    required_selectors: tuple[str, ...]  # 必需的选择器列表

    def status_for(self, profile_id: str) -> str:
        """获取指定配置文件的支持状态
        
        Args:
            profile_id: 配置文件ID（如"wechat39"、"wechat4"）
            
        Returns:
            str: 支持状态，可能的值：
                - "supported": 支持该功能
                - "unsupported": 不支持该功能
                - "unknown": 未知状态（配置文件中未声明）
                
        示例:
            >>> cap.status_for("wechat39")
            'supported'
            >>> cap.status_for("wechat4")
            'unsupported'
        """
        return self.supported.get(profile_id, "unknown")


class CapabilityRegistry:
    """能力注册表，管理和查询功能支持情况
    
    该类从capabilities.yaml配置文件加载所有能力定义，
    提供查询和验证功能。
    
    主要功能:
        - 加载和解析能力配置
        - 查询特定能力的详细信息
        - 验证功能在指定微信版本上是否可用
        - 提供所有已注册能力的列表
        
    配置来源:
        config/capabilities.yaml 文件定义了所有能力，格式如下：
        ```yaml
        capabilities:
          message.send_text:
            default_mode: auto
            pipeline: send_text
            supported:
              wechat39: supported
              wechat4: supported
            required_selectors:
              - chat_input
        ```
        
    线程安全:
        - 初始化后对象是不可变的（frozen dataclass）
        - 可以安全地在多线程环境中使用
        
    示例:
        >>> registry = CapabilityRegistry()
        >>> 
        >>> # 获取能力信息
        >>> cap = registry.get("message.send_text")
        >>> print(cap.default_mode)
        >>> 
        >>> # 验证能力是否可用
        >>> try:
        ...     registry.ensure_supported("message.send_text", "wechat39")
        ...     print("功能可用")
        ... except CapabilityNotSupportedError:
        ...     print("功能不可用")
        >>> 
        >>> # 列出所有能力
        >>> for cap_id, cap in registry.all().items():
        ...     print(f"{cap_id}: {cap.default_mode}")
    """
    
    def __init__(self) -> None:
        """初始化能力注册表，加载 capabilities.yaml 配置
        
        构造函数会：
        1. 从config目录加载capabilities.yaml文件
        2. 解析所有能力定义
        3. 创建Capability对象并存储
        
        异常处理:
            - 如果配置文件不存在或格式错误，会抛出异常
            - 建议在应用启动时捕获并处理这些异常
        """
        data = load_yaml("capabilities.yaml")
        self._capabilities = {}
        
        # 遍历配置中的所有能力定义
        for capability_id, raw in data.get("capabilities", {}).items():
            # 创建Capability对象
            self._capabilities[capability_id] = Capability(
                capability_id=capability_id,
                default_mode=raw.get("default_mode", "auto"),  # 默认auto模式
                pipeline=raw.get("pipeline"),  # 管道处理器（可选）
                supported=raw.get("supported", {}),  # 支持状态字典
                required_selectors=tuple(raw.get("required_selectors", [])),  # 必需选择器
            )

    def get(self, capability_id: str) -> Capability:
        """获取指定能力的配置
        
        Args:
            capability_id: 能力ID（如"message.send_text"）
            
        Returns:
            Capability: 能力配置对象
            
        Raises:
            CapabilityUnknownError: 如果能力ID不存在
            
        示例:
            >>> cap = registry.get("message.send_text")
            >>> print(cap.pipeline)  # 输出: send_text
        """
        try:
            return self._capabilities[capability_id]
        except KeyError as exc:
            raise CapabilityUnknownError(f"Unknown capability: {capability_id}") from exc

    def ensure_supported(self, capability_id: str, profile_id: str) -> Capability:
        """确保指定能力在给定配置文件中受支持
        
        这是最常用的方法，在执行任何操作前都应该调用此方法验证。
        
        Args:
            capability_id: 能力ID
            profile_id: 配置文件ID（如当前检测到的微信版本）
            
        Returns:
            Capability: 能力配置对象（如果验证通过）
            
        Raises:
            CapabilityNotSupportedError: 如果能力在该版本上不支持
            CapabilityUnknownError: 如果能力ID不存在
            
        验证逻辑:
            1. 查找能力定义
            2. 检查该能力对指定profile_id的支持状态
            3. 如果状态是"unsupported"或"unknown"，抛出异常
            4. 否则返回能力对象
            
        使用模式:
            >>> def send_text(self, text):
            ...     # 在执行前验证能力
            ...     self.capabilities.ensure_supported(
            ...         "message.send_text",
            ...         self.profile.profile_id
            ...     )
            ...     # 执行实际操作
            ...     self._do_send(text)
            
        示例:
            >>> # 验证通过
            >>> registry.ensure_supported("message.send_text", "wechat39")
            Capability(...)
            >>> 
            >>> # 验证失败，抛出异常
            >>> registry.ensure_supported("future.feature", "wechat39")
            CapabilityNotSupportedError: Capability future.feature is unknown...
        """
        capability = self.get(capability_id)
        status = capability.status_for(profile_id)
        
        # 检查支持状态
        if status in {"unsupported", "unknown"}:
            raise CapabilityNotSupportedError(
                f"Capability {capability_id} is {status} for profile {profile_id}"
            )
        
        return capability

    def all(self) -> dict[str, Capability]:
        """获取所有已注册的能力
        
        Returns:
            dict[str, Capability]: 能力ID到能力配置的映射字典
            
        注意:
            - 返回的是副本，修改不会影响内部状态
            - 可用于生成文档或调试信息
            
        示例:
            >>> all_caps = registry.all()
            >>> print(f"共{len(all_caps)}个能力")
            >>> for cap_id in sorted(all_caps.keys()):
            ...     print(f"  - {cap_id}")
        """
        return dict(self._capabilities)
