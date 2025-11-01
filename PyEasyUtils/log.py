import sys
from loguru import logger
from pathlib import Path
from enum import Enum
from typing import Optional

#############################################################################################################

class loggerLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def no(self):
        return logger.level(self.name).no


_format = " | ".join([
    '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>',
    '<level>{level: <8}</level>',
    #'<magenta>{process}</magenta>:<yellow>{thread}</yellow>',
    '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
])


class loggerManager:
    """
    Manage logger
    """
    def __init__(self):
        self.isLoggerInitialized = False

    def createLogger(self,
        name: str,
        level: loggerLevel = loggerLevel.INFO,
        format: str = _format,
        outputPath: Optional[str] = None,
        rotation: str = "10 MB",
        useStdIO: bool = True,
    ):
        if not self.isLoggerInitialized:
            logger.remove()
            self.isLoggerInitialized = True

        filter = lambda record: record["extra"].get("name") == name

        stream = (sys.stdout or sys.stderr or None) if useStdIO else None
        if stream:
            logger.add(
                stream,
                format = format,
                level = level.value,
                filter = filter,
            )

        if outputPath:
            dir = Path(outputPath).parent
            dir.mkdir(parents = True, exist_ok=True)

            logger.add(
                Path(outputPath).as_posix(),
                level = level.value,
                format = format,
                backtrace = True,
                diagnose = True,
                enqueue = True,
                rotation = rotation,
                filter = filter,
            )

        return logger.bind(name = name)

#############################################################################################################