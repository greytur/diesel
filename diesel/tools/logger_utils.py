# diesel/tools/logger.py
# Logger Utilities
import logging
import sys
import os


USE_COLOR = sys.platform != "win32" or "ANSICON" in os.environ

class PadLvlWithFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
    }
    RESET = "\033[0m"

    def __init__(self, *args, sep='@', pad=9, use_color=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.sep = sep
        self.pad = pad
        self.use_color = use_color and USE_COLOR

    def format(self, record):
        level_bracket = f"[{record.levelname}]"
        if self.use_color and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            level_bracket = f"{color}{level_bracket}{self.RESET}"
        record.levelname = f"{level_bracket:<{self.pad}}{self.sep}"
        return super().format(record)

# Single/Sole logger instance
_logger = None

def get_logger(level=logging.INFO):
    global _logger
    if _logger is None:
        handler = logging.StreamHandler()
        formatter = PadLvlWithFormatter(
            "%(levelname)s%(asctime)s %(message)s",
            datefmt="%I:%M:%S %p",
            use_color=True
        )
        handler.setFormatter(formatter)

        _logger = logging.getLogger("diesel.engine")
        _logger.addHandler(handler)
        _logger.setLevel(level)
        _logger.propagate = False
    return _logger


__all__ = [
    "PadLvlWithFormatter", "get_logger", "USE_COLOR"
]

# ---  DOCUMENT STATUS ---
# XXX: Currently Finalized (For Current Build)