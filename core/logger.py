"""Logging configuration for Shelly MQTT-RPC Manager"""
import logging
import os
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from typing import Optional


class LoggerSetup:
    """Configure and setup application logging"""
    
    _initialized = False
    
    @staticmethod
    def setup(log_level: str = "INFO", log_file: Optional[str] = None, 
              max_bytes: int = 10485760, backup_count: int = 5) -> logging.Logger:
        """
        Setup logging with console and file handlers.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            max_bytes: Maximum size of log file before rotation (default 10MB)
            backup_count: Number of backup files to keep
            
        Returns:
            Configured logger instance
        """
        if LoggerSetup._initialized:
            return logging.getLogger("shelly_mqtt_rpc")
        
        # Get logger
        logger = logging.getLogger("shelly_mqtt_rpc")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Console handler with Rich
        console_handler = RichHandler(
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            show_time=True,
            show_path=False,
            markup=True
        )
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file:
            # Ensure log directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # Don't propagate to root logger
        logger.propagate = False
        
        LoggerSetup._initialized = True
        return logger
    
    @staticmethod
    def get_logger(name: str = "shelly_mqtt_rpc") -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @staticmethod
    def reset():
        """Reset logger initialization state (useful for testing)"""
        LoggerSetup._initialized = False
        logger = logging.getLogger("shelly_mqtt_rpc")
        logger.handlers.clear()


def get_logger(name: str = "shelly_mqtt_rpc") -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

