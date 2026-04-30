import logging
import structlog
from pathlib import Path
from platformdirs import PlatformDirs
from logging.handlers import RotatingFileHandler
from src.dependencies.config import Config, EnvType


def config_logger(config: Config) -> None:
    """configures loggign with structlogs and the stdlib logger for 3rd party support"""
    if config.env_type == EnvType.DEVELOPMENT:
        log_level = logging.DEBUG
        log_file: str = "app.log"
    elif config.env_type == EnvType.PRODUCTION:
        log_level = logging.INFO
        log_dir = PlatformDirs(
            appname="AVIT-Training", appauthor="AVIT, LLC", ensure_exists=True
        )
        log_file: Path = log_dir.user_log_path / "app.log"
    else:
        raise ValueError(
            f"Invalid env_type: {config.env_type}. Must be member of EnvType class"
        )

    log_format: str = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d]: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    file_handler: RotatingFileHandler = RotatingFileHandler(
        filename=log_file, maxBytes=5 * 1024 * 1024, encoding="utf-8", backupCount=5
    )
    file_handler.setFormatter(fmt=formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt=formatter)

    # Root logger for 3rd part support
    root_logger = logging.getLogger()
    root_logger.setLevel(level=log_level)
    root_logger.addHandler(hdlr=file_handler)
    root_logger.addHandler(hdlr=stream_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if config.env_type == EnvType.DEVELOPMENT
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(min_level=log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
        if config.env_type == EnvType.PRODUCTION
        else False,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.getLogger(name)
