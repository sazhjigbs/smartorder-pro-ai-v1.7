"""
Centralized Logger
Système de logging unifié avec rotation et format structuré

Author: MAIGA ABOUBACAR
Date: 2025-10-27
"""

import os
import sys
import logging
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# ANSI color codes for console
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m'       # Reset
}


class JsonFormatter(logging.Formatter):
    """Format logs as JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Format logs with colors for console"""
    
    def format(self, record):
        levelname = record.levelname
        color = COLORS.get(levelname, COLORS['RESET'])
        reset = COLORS['RESET']
        
        # Format: [TIME] [LEVEL] logger - message
        formatted = f"{color}[{self.formatTime(record, '%H:%M:%S')}] [{levelname}]{reset} {record.name} - {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class CentralizedLogger:
    """
    Centralized logging system
    
    Features:
    - Multiple log levels per module
    - Rotating file handlers
    - JSON structured logging
    - Console output with colors
    - Module-specific configuration
    """
    
    def __init__(self,
                 log_dir: str = "logs",
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 json_logs: bool = True,
                 console_logs: bool = True):
        """
        Initialize Centralized Logger
        
        Args:
            log_dir: Directory for log files
            log_level: Default log level
            max_file_size: Max size before rotation (bytes)
            backup_count: Number of backup files to keep
            json_logs: Enable JSON formatted logs
            console_logs: Enable console output
        """
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.json_logs = json_logs
        self.console_logs = console_logs
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Module-specific log levels
        self.module_levels = {}
        
        # Initialize root logger
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Setup root logger with handlers"""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)  # Capture all levels
        
        # Clear existing handlers
        root.handlers.clear()
        
        # File handler (all logs)
        self._add_file_handler(root, 'all.log', logging.DEBUG)
        
        # File handler (errors only)
        self._add_file_handler(root, 'error.log', logging.ERROR)
        
        # Console handler
        if self.console_logs:
            self._add_console_handler(root)
    
    def _add_file_handler(self,
                          logger,
                          filename: str,
                          level: int):
        """Add rotating file handler"""
        filepath = self.log_dir / filename
        
        handler = RotatingFileHandler(
            filepath,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        handler.setLevel(level)
        
        # Use JSON formatter if enabled
        if self.json_logs:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
            ))
        
        logger.addHandler(handler)
    
    def _add_console_handler(self, logger):
        """Add console handler with colors"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)
        handler.setFormatter(ColoredConsoleFormatter())
        
        logger.addHandler(handler)
    
    def get_logger(self, name: str, level: Optional[str] = None) -> logging.Logger:
        """
        Get or create logger for a module
        
        Args:
            name: Logger name (usually module name)
            level: Log level (optional, uses default if not specified)
        
        Returns:
            Logger instance
        """
        logger = logging.getLogger(name)
        
        # Set module-specific level if provided
        if level:
            log_level = getattr(logging, level.upper())
            logger.setLevel(log_level)
            self.module_levels[name] = log_level
        
        return logger
    
    def set_module_level(self, module: str, level: str):
        """
        Set log level for specific module
        
        Args:
            module: Module name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper())
        logger = logging.getLogger(module)
        logger.setLevel(log_level)
        self.module_levels[module] = log_level
    
    def get_module_levels(self) -> Dict:
        """Get all module-specific log levels"""
        return {
            module: logging.getLevelName(level)
            for module, level in self.module_levels.items()
        }
    
    def log_with_context(self,
                         logger: logging.Logger,
                         level: str,
                         message: str,
                         context: Dict = None):
        """
        Log with additional context data
        
        Args:
            logger: Logger instance
            level: Log level
            message: Log message
            context: Additional context data (will be added to JSON logs)
        """
        # Create log record with extra data
        if context:
            extra = {'extra_data': context}
        else:
            extra = {}
        
        log_func = getattr(logger, level.lower())
        log_func(message, extra=extra)


# Global logger instance
_global_logger = None


def get_logger(name: str = None, level: str = None) -> logging.Logger:
    """
    Get logger (creates centralized logger if not exists)
    
    Args:
        name: Logger name
        level: Log level (optional)
    
    Returns:
        Logger instance
    """
    global _global_logger
    
    if _global_logger is None:
        # Initialize centralized logger from env
        log_dir = os.getenv('LOG_DIR', 'logs')
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        _global_logger = CentralizedLogger(
            log_dir=log_dir,
            log_level=log_level
        )
    
    if name:
        return _global_logger.get_logger(name, level)
    else:
        return logging.getLogger()


def setup_logging(log_dir: str = "logs",
                  log_level: str = "INFO",
                  json_logs: bool = True,
                  console_logs: bool = True):
    """
    Setup centralized logging system
    
    Args:
        log_dir: Directory for log files
        log_level: Default log level
        json_logs: Enable JSON formatted logs
        console_logs: Enable console output
    """
    global _global_logger
    
    _global_logger = CentralizedLogger(
        log_dir=log_dir,
        log_level=log_level,
        json_logs=json_logs,
        console_logs=console_logs
    )


# Test function
if __name__ == "__main__":
    # Setup logging
    setup_logging(log_dir="test_logs", log_level="DEBUG")
    
    # Get loggers for different modules
    main_logger = get_logger("main")
    trading_logger = get_logger("trading", level="INFO")
    api_logger = get_logger("api", level="DEBUG")
    
    # Test logging
    print("\nTesting centralized logger...")
    print("=" * 50)
    
    main_logger.debug("This is a debug message")
    main_logger.info("✅ Bot started successfully")
    main_logger.warning("⚠️ High CPU usage detected")
    main_logger.error("❌ Failed to connect to exchange")
    
    trading_logger.info("📈 Order placed: BUY 0.001 BTC")
    
    try:
        raise Exception("Simulated error")
    except Exception:
        api_logger.exception("Exception occurred")
    
    print("\nLogs written to test_logs/")
    print("Check test_logs/all.log for all logs")
    print("Check test_logs/error.log for errors only")
