"""
WeChat_SDK 日志配置模块

提供统一的日志记录功能，支持控制台和文件双输出。
所有SDK内部日志都通过此模块的logger对象记录。

作者: CMX

功能特点:
    - 双输出：同时输出到控制台和文件
    - 分级记录：控制台显示INFO及以上，文件记录DEBUG及以上
    - 自动归档：日志文件按时间戳命名，保存在logs目录
    - UTF-8编码：完整支持中文日志
    - 单例模式：同名logger只创建一次
    
日志格式:
    %(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s
    
    示例输出:
    2024-01-15 10:30:45,123 - wechat_sdk - INFO - client.py:234 - Message sent successfully

使用方式:
    # 在SDK内部使用（推荐）
    from wechat_sdk.logging import logger
    logger.info("操作成功")
    logger.error("发生错误", exc_info=True)
    
    # 自定义logger实例
    from wechat_sdk.logging import get_logger
    my_logger = get_logger("my_module")
    my_logger.debug("调试信息")
    
日志级别:
    DEBUG:   详细的调试信息（仅文件）
    INFO:    一般信息（控制台+文件）
    WARNING: 警告信息（控制台+文件）
    ERROR:   错误信息（控制台+文件）
    CRITICAL: 严重错误（控制台+文件）

配置说明:
    console_level: 控制台最低日志级别，默认INFO
    file_level: 文件最低日志级别，默认DEBUG
    log_file: 自定义日志文件路径，None则自动生成
    
日志文件位置:
    - 默认：当前工作目录/logs/wechat_sdk_YYYYMMDDHHmmss.log
    - 可通过log_file参数自定义
"""
from datetime import datetime
import logging as std_logging
import os
from pathlib import Path


# 默认日志格式器
# 包含：时间、模块名、级别、文件名、行号、消息内容
DEFAULT_LOG_FORMAT = std_logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)


def get_logger(
    name: str = "wechat_sdk",
    console_level: int = std_logging.INFO,
    file_level: int = std_logging.DEBUG,
    log_file: str = None,
) -> std_logging.Logger:
    """获取或创建logger实例
    
    这是一个工厂函数，用于创建配置好的logger对象。
    如果同名logger已存在，直接返回（单例模式）。
    
    Args:
        name: logger名称，默认为"wechat_sdk"
              不同模块可以使用不同的name来区分日志来源
              
        console_level: 控制台输出的最低日志级别
                      默认INFO，即只显示INFO及以上级别
                      设为DEBUG可看到更详细的信息
                      
        file_level: 文件记录的最低日志级别
                   默认DEBUG，记录所有级别的日志
                   适合问题排查和审计
                   
        log_file: 日志文件路径
                 None: 自动生成（logs目录下，带时间戳）
                 字符串: 使用指定路径
                 
    Returns:
        logging.Logger: 配置好的logger对象
        
    工作流程:
        1. 获取或创建logger
        2. 设置根级别为DEBUG（最详细）
        3. 检查是否已有handlers（避免重复添加）
        4. 添加控制台handler（彩色输出，简洁格式）
        5. 添加文件handler（完整信息，持久化存储）
        
    示例:
        >>> # 使用默认配置
        >>> logger = get_logger()
        >>> 
        >>> # 自定义配置
        >>> logger = get_logger(
        ...     name="my_app",
        ...     console_level=logging.DEBUG,
        ...     log_file="/var/log/myapp.log"
        ... )
        >>> 
        >>> # 在不同模块中使用不同的logger
        >>> client_logger = get_logger("client")
        >>> listener_logger = get_logger("listener")
    """
    # 获取logger实例
    logger = std_logging.getLogger(name)
    
    # 设置最低级别为DEBUG
    # 具体输出由各个handler的级别控制
    logger.setLevel(std_logging.DEBUG)
    
    # 如果已有handlers，说明已经初始化过，直接返回
    # 这避免了重复添加handler导致日志重复输出
    if logger.handlers:
        return logger

    # === 配置控制台输出 ===
    console_handler = std_logging.StreamHandler()
    console_handler.setLevel(console_level)  # 控制台显示INFO及以上
    console_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(console_handler)

    # === 配置文件输出 ===
    if not log_file:
        # 自动生成日志文件路径
        # 在当前工作目录下创建logs子目录
        log_root = Path(os.getcwd()) / "logs"
        log_root.mkdir(parents=True, exist_ok=True)  # 递归创建目录
        
        # 文件名包含时间戳，便于追溯
        log_file = str(log_root / f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.log")

    # 创建文件handler
    file_handler = std_logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)  # 文件记录DEBUG及以上
    file_handler.setFormatter(DEFAULT_LOG_FORMAT)
    logger.addHandler(file_handler)
    
    return logger


# 默认的logger实例
# SDK内部代码直接使用这个logger
# 应用代码也可以通过导入此logger来保持日志一致性
logger = get_logger()
