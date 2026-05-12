"""
管道运行器模块

实现基于配置的操作流水线，将复杂操作分解为多个步骤依次执行。
支持步骤注册、上下文传递和错误处理。

作者: CMX

主要类:
    PipelineRunner: 管道运行器
    
设计理念:
    - 配置驱动：通过pipelines.yaml定义操作流程
    - 步骤化：将复杂操作拆分为可复用的小步骤
    - 上下文传递：步骤间通过context字典共享数据
    - 灵活扩展：可以动态注册新的步骤处理器
    
使用场景:
    - 发送消息（确保聊天 -> 输入文本 -> 发送）
    - 文件传输（验证路径 -> 切换到聊天 -> 粘贴文件）
    - 任何需要多步完成的操作

配置文件示例 (pipelines.yaml):
    ```yaml
    pipelines:
      send_text:
        - ensure_chat      # 第一步：确保在正确的聊天中
        - send_text        # 第二步：发送文本
      send_file:
        - ensure_chat
        - send_file
    ```

使用示例:
    >>> runner = PipelineRunner()
    >>> # 注册步骤处理器
    >>> runner.register("ensure_chat", lambda ctx: ensure_chat(ctx["who"]))
    >>> runner.register("send_text", lambda ctx: send_text(ctx["text"]))
    >>> 
    >>> # 执行管道
    >>> result = runner.run("send_text", {"who": "张三", "text": "Hello"})
"""
from typing import Callable

from wechat_sdk.logging import logger

from .config import load_yaml


class PipelineRunner:
    """管道运行器，按顺序执行预定义的操作步骤
    
    该类实现了命令模式的变体，将操作流程定义为配置化的步骤序列。
    
    核心概念:
        - Pipeline（管道）: 一个命名的步骤序列
        - Step（步骤）: 管道中的一个环节，由注册的函数处理
        - Context（上下文）: 在步骤间传递的数据字典
        
    工作流程:
        1. 从pipelines.yaml加载管道定义
        2. 注册各个步骤的处理函数
        3. 调用run()执行指定管道
        4. 按顺序执行每个步骤，传递context
        5. 返回最后一步的结果
        
    优势:
        - 解耦：步骤定义与执行逻辑分离
        - 可配置：修改流程无需改代码
        - 可测试：可以单独测试每个步骤
        - 可扩展：轻松添加新步骤
        
    注意事项:
        - 步骤执行是同步的，不支持异步
        - 步骤间通过context共享状态，注意命名冲突
        - 某一步失败会中断整个管道
        
    示例:
        >>> runner = PipelineRunner()
        >>> 
        >>> # 注册步骤
        >>> def step1(context):
        ...     print(f"步骤1: {context['data']}")
        ...     context['step1_result'] = 'ok'
        >>> 
        >>> def step2(context):
        ...     print(f"步骤2: {context['step1_result']}")
        ...     return 'final_result'
        >>> 
        >>> runner.register("step1", step1)
        >>> runner.register("step2", step2)
        >>> 
        >>> # 执行
        >>> result = runner.run("my_pipeline", {"data": "test"})
        >>> print(result)  # 输出: final_result
    """
    
    def __init__(self) -> None:
        """初始化管道运行器，加载 pipelines.yaml 配置
        
        构造函数会：
        1. 从config目录加载pipelines.yaml文件
        2. 解析所有管道定义
        3. 初始化空的步骤注册表
        
        配置格式:
            pipelines:
              pipeline_name:
                - step1
                - step2
                - step3
                
        注意:
            - 此时只加载配置，不验证步骤是否存在
            - 步骤需要在运行时前通过register()注册
            - 如果配置文件不存在，使用空字典
        """
        self._pipelines = load_yaml("pipelines.yaml").get("pipelines", {})
        self._steps: dict[str, Callable] = {}  # 步骤名称 -> 处理函数

    def register(self, name: str, func: Callable) -> None:
        """注册一个管道步骤处理函数
        
        将步骤名称映射到具体的处理函数。
        
        Args:
            name: 步骤名称，必须与pipelines.yaml中定义的一致
            func: 处理函数，签名为 func(context: dict) -> Any
                 接收上下文字典，可以读取和修改它
                 
        注意:
            - 同名步骤会被覆盖
            - 建议在应用启动时注册所有步骤
            - 处理函数应该保持无副作用（除了修改context）
            
        示例:
            >>> # 简单步骤
            >>> runner.register("validate", lambda ctx: validate_input(ctx))
            >>> 
            >>> # 复杂步骤
            >>> def process_data(context):
            ...     data = context['raw_data']
            ...     processed = transform(data)
            ...     context['processed_data'] = processed
            ...     return processed
            >>> runner.register("process", process_data)
        """
        self._steps[name] = func

    def run(self, pipeline_name: str, context: dict):
        """执行指定的管道
        
        这是核心方法，按配置顺序执行管道中的所有步骤。
        
        Args:
            pipeline_name: 管道名称，必须在pipelines.yaml中定义
            context: 执行上下文字典，在步骤间传递
                   初始可以包含输入参数
                   
        Returns:
            最后一个步骤的返回值
            如果管道为空，返回None
            
        Raises:
            KeyError: 以下情况会抛出KeyError：
                - 管道名称不存在
                - 某个步骤未注册
                
        执行流程:
            1. 查找管道定义（步骤列表）
            2. 遍历每个步骤：
               a. 查找注册的处理器
               b. 调用处理器，传入context
               c. 保存返回值
            3. 返回最后一步的结果
            
        上下文传递:
            - 所有步骤共享同一个context字典
            - 前面的步骤可以写入数据供后续步骤使用
            - 注意避免步骤间的隐式依赖
            
        日志记录:
            - DEBUG级别：记录每个步骤的执行
            
        使用示例:
            >>> # 定义上下文
            >>> context = {
            ...     "client": wechat_client,
            ...     "who": "张三",
            ...     "text": "Hello"
            ... }
            >>> 
            >>> # 执行发送消息管道
            >>> result = runner.run("send_text", context)
            >>> print(result)  # True或False
            
        错误处理:
            >>> try:
            ...     result = runner.run("complex_pipeline", context)
            ... except KeyError as e:
            ...     print(f"管道配置错误: {e}")
            ...     # 检查pipelines.yaml或步骤注册
        """
        # 获取管道定义的步骤列表
        steps = self._pipelines.get(pipeline_name)
        if steps is None:
            raise KeyError(f"Pipeline not found: {pipeline_name}")
        
        result = None
        
        # 依次执行每个步骤
        for step in steps:
            logger.debug("Pipeline step: %s.%s", pipeline_name, step)
            
            # 查找步骤处理器
            try:
                handler = self._steps[step]
            except KeyError as exc:
                raise KeyError(f"Pipeline step not registered: {step}") from exc
            
            # 执行步骤，传入context
            # 步骤可以读取和修改context
            result = handler(context)
        
        # 返回最后一步的结果
        return result
