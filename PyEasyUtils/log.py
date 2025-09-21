import sys
from loguru import logger
from pathlib import Path
from typing import Optional

#############################################################################################################

class loggerManager:
    """
    Manage logger
    """
    def __init__(self):
        self.isLoggerInitialized = False

    def createLogger(self,
        name: str,
        level: str = "INFO",
        format: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        outputPath: Optional[str] = None,
        rotation: str = "10 MB",
    ):
        if not self.isLoggerInitialized:
            logger.remove()
            self.isLoggerInitialized = True

        filter = lambda record: record["extra"].get("name") == name

        logger.add(
            sys.stderr,
            format = format,
            level = level,
            filter = filter,
        )

        if outputPath:
            dir = Path(outputPath).parent
            dir.mkdir(parents = True) if not dir.exists() else None

            logger.add(
                Path(outputPath).as_posix(),
                level = level,
                format = format,
                backtrace = True,
                diagnose = True,
                enqueue = True,
                rotation = rotation,
                filter = filter,
            )

        return logger.bind(name = name)

#############################################################################################################