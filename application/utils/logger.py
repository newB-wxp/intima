# -*- coding: utf-8 -*-
"""
Bibi 统一日志管理模块。

功能：
- 统一日志格式：时间 + 级别 + 模块 + 消息
- 日志输出到 logs/app.log（按天轮转，保留 30 天）
- DEV_MODE=True 时同时输出到控制台
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler


LOG_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

CONSOLE_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)


def get_logs_dir(app) -> str:
    """获取 logs 目录路径，不存在则创建。"""
    logs_dir = os.path.join(app.root_path, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def init_app_logger(app) -> None:
    """
    初始化应用日志系统。

    配置规则：
    - 文件日志：logs/app.log，按天轮转，保留 30 天
    - 控制台日志：仅在 DEV_MODE=True 时启用
    - 日志级别：DEV_MODE 下 DEBUG，生产环境 INFO
    """
    dev_mode = app.config.get('DEV_MODE', False)
    log_level = logging.DEBUG if dev_mode else logging.INFO

    # 移除 Flask 默认 handler
    del app.logger.handlers[:]

    # 文件 handler — 按天轮转，保留 30 天
    logs_dir = get_logs_dir(app)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(logs_dir, 'app.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8',
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(LOG_FORMAT)
    app.logger.addHandler(file_handler)

    # 控制台 handler — 仅开发模式
    if dev_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(CONSOLE_FORMAT)
        app.logger.addHandler(console_handler)

    app.logger.setLevel(log_level)
    app.logger.info(
        'Logger initialized | DEV_MODE=%s | level=%s | log_dir=%s',
        dev_mode, logging.getLevelName(log_level), logs_dir
    )


def get_logger(name: str) -> logging.Logger:
    """获取指定模块的 logger 实例。"""
    return logging.getLogger(name)
